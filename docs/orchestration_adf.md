# Proposition d'orchestration ADF

## Objectif

Ce document propose une orchestration Azure Data Factory end-to-end pour le pipeline VelibData.

Flux cible :

```text
APIs Velib + Open-Meteo
        |
        v
Ingestion Python
        |
        v
ADLS Gen2 Bronze
        |
        v
Azure SQL Bronze
        |
        v
dbt Silver/Gold
        |
        v
Power BI
```

## Etat actuel ADF

Le module Terraform ADF cree actuellement :

- une Azure Data Factory ;
- une managed identity system-assigned ;
- un role `Storage Blob Data Contributor` sur ADLS ;
- un role `Azure Event Hubs Data Receiver` sur Event Hubs ;
- un access policy Key Vault en lecture ;
- un linked service ADLS Gen2 ;
- un linked service lie a Event Hubs/Blob.

Limites actuelles :

- aucun pipeline ADF ;
- aucun trigger ;
- aucun dataset ;
- aucune activite de copie ;
- aucune activite dbt ;
- pas de gestion d'erreur end-to-end ;
- pas de notification operationnelle par pipeline.

## Pipeline ADF recommande

Nom propose :

```text
pl_velibdata_end_to_end
```

Frequence proposee :

- toutes les 5 a 15 minutes pour `station_status` si besoin proche temps reel ;
- toutes les 1 a 6 heures pour `weather` ;
- une fois par jour pour `station_info`, car le referentiel change peu.

Pour simplifier la MSPR, un pipeline unique planifie toutes les 15 minutes peut suffire, avec `station_info` recharge moins frequemment via condition.

## Etapes du pipeline

### 1. Initialisation

Activites :

- definir un `pipeline_run_id` ;
- definir un timestamp UTC ;
- lire les secrets necessaires depuis Key Vault.

Parametres utiles :

- `run_id`
- `execution_timestamp`
- `bronze_container`
- `sql_server`
- `sql_database`

### 2. Ingestion API vers ADLS Bronze

Options possibles :

#### Option A - ADF appelle le code Python existant

ADF peut declencher :

- Azure Function ;
- Azure Container App ;
- Azure Batch ;
- Databricks job ;
- ou GitHub Actions via webhook.

Cette option reutilise le code Python existant.

Avantages :

- moins de duplication ;
- logique HTTP deja implementee ;
- retries deja presents ;
- structure de fichiers Bronze deja definie.

Inconvenients :

- necessite un runtime Azure pour executer Python ;
- necessite de packager l'application.

#### Option B - ADF copie directement les APIs REST

ADF peut utiliser des linked services REST et Copy Activity.

Avantages :

- orchestration 100 pour cent ADF ;
- peu de code.

Inconvenients :

- transformations JSON plus contraignantes ;
- retries et packaging metier moins souples ;
- risque de dupliquer la logique existante.

Recommendation :

Utiliser l'option A pour rester coherent avec le repository actuel.

### 3. Validation Bronze ADLS

Apres ingestion :

- verifier l'existence des trois fichiers attendus ;
- verifier la taille minimale ;
- verifier que le JSON est lisible ;
- verifier le nombre de stations.

Activites possibles :

- Azure Function de controle ;
- Notebook ;
- script Python ;
- validation via metadata ADF pour existence et taille.

Seuils recommandes :

- `station_status.station_count > 1000` ;
- `station_info.station_count > 1000` ;
- `weather.hourly.time` non vide.

### 4. Chargement Azure SQL Bronze

ADF doit declencher le script de chargement Bronze ou une procedure equivalente.

Approches possibles :

- executer le script Python `load_bronze.py` via Azure Function ou Container App ;
- remplacer le script par Copy Activity ADLS JSON vers Azure SQL ;
- utiliser Stored Procedures SQL pour charger des fichiers externes si l'environnement le permet.

Recommendation MSPR :

- court terme : executer le script Python existant dans un runtime Azure ;
- moyen terme : rendre le chargement incremental et historise.

Sorties attendues :

- tables `bronze.station_status`, `bronze.station_info`, `bronze.weather` chargees ;
- nombre de lignes loggue ;
- statut de chargement conserve.

### 5. Execution dbt Silver/Gold

ADF doit ensuite declencher dbt.

Options :

- dbt Cloud job via API ;
- Azure Container App executant `dbt run` et `dbt test` ;
- GitHub Actions workflow dispatch ;
- VM ou self-hosted runner.

Recommendation :

- pour une MSPR simple : GitHub Actions ou Container App ;
- pour une architecture plus professionnelle : dbt Cloud job appele par ADF.

Commandes cibles :

```text
dbt deps
dbt run
dbt test
```

Ordre logique :

1. `dbt run --select staging`
2. `dbt test --select staging`
3. `dbt run --select intermediate`
4. `dbt run --select marts`
5. `dbt test`

### 6. Rafraichissement Power BI

Apres succes dbt :

- declencher le refresh du dataset Power BI via API REST ;
- ou laisser Power BI faire un refresh planifie.

Recommendation :

- pour demonstration MSPR : refresh planifie Power BI suffit ;
- pour pipeline complet : appel API Power BI depuis ADF apres dbt.

### 7. Notification et logs

En fin de pipeline :

- envoyer notification succes/echec ;
- ecrire un log de run ;
- exposer les metriques dans Log Analytics.

Canaux possibles :

- Azure Monitor Action Group ;
- email ;
- Teams webhook ;
- tableau de supervision.

## Gestion des erreurs

### Strategie generale

Chaque etape doit avoir :

- timeout ;
- retry ;
- branche d'echec ;
- log explicite ;
- notification si critique.

### Erreurs critiques

- API indisponible apres retries ;
- aucun fichier Bronze produit ;
- chargement SQL en erreur ;
- dbt run en erreur ;
- dbt test en erreur sur test critique ;
- dataset Power BI non rafraichi.

### Erreurs non critiques

- `station_info` absent sur un cycle court si un referentiel recent existe ;
- meteo temporairement absente si les marts acceptent des valeurs nulles ;
- alerte volume faible a investiguer mais pas forcement bloquante.

## Usage d'Event Hubs

Deux architectures sont possibles.

### Mode actuel simplifie

```text
Python ingestion -> ADLS Bronze -> SQL Bronze -> dbt
```

Event Hubs reste provisionne mais non utilise.

Avantage :

- plus simple a demontrer ;
- moins de composants actifs.

Limite :

- Event Hubs ne justifie pas son cout et ses alertes.

### Mode evenementiel cible

```text
Python ingestion -> Event Hubs -> Capture/Consumer -> ADLS Bronze -> SQL Bronze -> dbt
```

Dans ce cas :

- le module `eventhub_producer` doit etre appele par l'ingestion ;
- Event Hubs Capture ou un consumer doit ecrire les messages ;
- ADF orchestre le traitement des fichiers captures ou declenche le downstream.

Recommendation :

- choisir explicitement un seul mode pour eviter une architecture hybride incomplete ;
- pour MSPR, le mode simplifie est acceptable si Event Hubs est documente comme option cible ;
- si Event Hubs est exige, le brancher reellement au pipeline.

## Datasets ADF proposes

Datasets ADLS :

- `ds_adls_bronze_station_status_json`
- `ds_adls_bronze_station_info_json`
- `ds_adls_bronze_weather_json`

Datasets SQL :

- `ds_sql_bronze_station_status`
- `ds_sql_bronze_station_info`
- `ds_sql_bronze_weather`

Linked services :

- `ls_adls_velibdata`
- `ls_keyvault_velibdata`
- `ls_azure_sql_velibdata`
- optionnel : `ls_eventhub_velibdata`
- optionnel : `ls_powerbi_api`

## Triggers proposes

### Trigger ingestion principale

Nom :

```text
tr_velibdata_ingestion_15min
```

Frequence :

```text
Every 15 minutes
```

### Trigger referentiel station

Nom :

```text
tr_velibdata_station_info_daily
```

Frequence :

```text
Daily
```

### Trigger maintenance

Nom :

```text
tr_velibdata_quality_daily
```

Frequence :

```text
Daily after midnight
```

## Journalisation recommandee

Chaque run doit produire :

- `pipeline_run_id` ;
- timestamp debut et fin ;
- statut ;
- duree ;
- fichiers Bronze generes ;
- nombres de lignes chargees ;
- resultats dbt ;
- message d'erreur si echec.

Table technique recommandee :

```text
ops.pipeline_runs
```

Champs utiles :

- `pipeline_run_id`
- `pipeline_name`
- `started_at`
- `ended_at`
- `status`
- `source`
- `records_read`
- `records_written`
- `error_message`

## Ordre d'implementation recommande

1. Ajouter Azure SQL dans Terraform.
2. Ajouter les secrets SQL dans Key Vault.
3. Packager l'ingestion Python dans un runtime Azure.
4. Creer le pipeline ADF end-to-end minimal.
5. Ajouter le declenchement du chargement SQL Bronze.
6. Ajouter l'execution dbt.
7. Ajouter tests et notifications.
8. Ajouter refresh Power BI.
9. Decider si Event Hubs est actif ou seulement cible.

## Definition de succes

Le pipeline ADF est considere complet lorsque :

- un trigger declenche automatiquement le flux ;
- les donnees API arrivent dans ADLS Bronze ;
- Azure SQL Bronze est charge ;
- dbt produit les modeles Silver et Gold ;
- les tests critiques passent ;
- Power BI peut consommer les marts Gold ;
- un echec produit une alerte exploitable ;
- un run complet est tracable de bout en bout.
