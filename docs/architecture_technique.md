# Architecture technique VelibData

## Objectif

Ce document cartographie l'architecture reelle du repository VelibData a l'etat actuel. Le projet vise un pipeline de donnees Azure pour le contexte MSPR EPSI TPRE924/944, avec ingestion des APIs Velib et Open-Meteo, stockage Bronze, chargement Azure SQL, transformations dbt Silver/Gold et consommation Power BI.

## Vue d'ensemble du flux

Flux fonctionnel cible porte par le repository :

```text
APIs Velib + Open-Meteo
        |
        v
Python ingestion
        |
        v
ADLS Gen2 Bronze - JSON brut partitionne
        |
        v
Azure SQL Bronze - tables relationnelles brutes
        |
        v
dbt Silver - staging et intermediate
        |
        v
dbt Gold - marts analytiques
        |
        v
Power BI - tableaux de bord
```

## Composants applicatifs

### Ingestion API

Le code Python recupere trois sources :

- `station_status` depuis l'API Velib Metropole.
- `station_information` depuis l'API Velib Metropole.
- meteo horaire Paris depuis Open-Meteo.

Le module principal d'ingestion ecrit les donnees brutes dans ADLS Gen2 Bronze au format JSON avec partitionnement par source et date :

```text
bronze/{source}/year=YYYY/month=MM/day=DD/{source}_{timestamp}.json
```

Etat actuel :

- ingestion asynchrone des trois sources presente ;
- retry HTTP avec `tenacity` present ;
- ecriture ADLS Bronze presente ;
- authentification ADLS basee sur `ADLS_ACCOUNT_KEY` attendue par la configuration ;
- pas de controle qualite applicatif avance avant ecriture ;
- pas d'appel Event Hubs dans le pipeline principal.

### Event Hubs

Le repository contient un producteur Event Hubs separe capable d'envoyer des payloads JSON vers trois hubs :

- `velib-availability`
- `velib-station-info`
- `velib-weather`

Etat actuel :

- module producteur implemente ;
- recuperation de la connection string depuis Key Vault prevue ;
- module non raccorde au `main` d'ingestion ;
- pas de consumer applicatif ;
- Event Hubs est donc provisionne dans l'infra, mais pas encore utilise dans le flux operationnel principal.

### ADLS Gen2 Bronze

ADLS Gen2 est la zone de conservation des fichiers bruts. Les donnees y sont stockees en JSON, par source et par date.

Role :

- conserver les donnees sources non transformees ;
- permettre un rejeu vers SQL ou vers une future couche Silver fichier ;
- fournir une preuve d'historique technique.

Limite actuelle :

- le stockage Bronze ADLS conserve plusieurs fichiers, mais le chargement SQL ne charge que le dernier fichier par source.

### Azure SQL Bronze

Un script Python charge les derniers fichiers JSON presents dans ADLS vers Azure SQL, schema `bronze`.

Tables attendues :

- `bronze.station_status`
- `bronze.station_info`
- `bronze.weather`

Strategie actuelle :

- creation du schema et des tables si absents ;
- selection du fichier JSON le plus recent par source ;
- `TRUNCATE TABLE` puis `INSERT`.

Limites :

- pas d'historisation relationnelle, car les tables sont remplacees a chaque execution ;
- variables SQL attendues mais non documentees dans `.env.example` ;
- Azure SQL n'est pas provisionne par Terraform dans l'etat actuel ;
- pas de metadonnees de batch comme `source_file`, `batch_id`, `loaded_at` stable.

## Transformations dbt

Le projet dbt est situe dans `dbt_velibdata/`.

### Sources dbt

Les sources declarent le schema SQL `bronze` :

- `station_status`
- `station_info`
- `weather`

### Couche Silver

Les modeles `staging` nettoient et typent les donnees :

- `stg_station_status`
- `stg_station_info`
- `stg_weather`

Les modeles `intermediate` enrichissent les donnees :

- `int_station_availability` : jointure statut station + referentiel station.
- `int_availability_weather` : jointure disponibilite + meteo horaire.

### Couche Gold

Les marts Gold disponibles sont :

- `mart_station_kpis` : indicateurs par station.
- `mart_city_overview` : vue globale ville.
- `mart_weather_impact` : analyse disponibilite selon conditions meteo.

Etat actuel :

- structure dbt coherente ;
- tests dbt basiques presents sur quelques champs ;
- absence de `profiles.yml.example` ;
- absence de CI dbt dediee ;
- marts surtout orientes snapshot, pas analyse historique complete.

## Infrastructure Terraform

Terraform est organise en modules :

- `foundation` : resource group, Key Vault, access policy utilisateur.
- `storage` : compte ADLS Gen2 et filesystems `bronze`, `silver`, `gold`.
- `eventhubs` : namespace Event Hubs, trois hubs, regles d'autorisation, secrets Key Vault.
- `adf` : Azure Data Factory, managed identity, RBAC ADLS/Event Hubs, linked services.
- `monitoring` : Log Analytics, Application Insights, action group, alertes, budget.

Etat actuel :

- socle Azure largement scaffoldé ;
- pas de serveur Azure SQL ni database dans Terraform ;
- pas de pipelines ADF, datasets, triggers ou activites de copie ;
- monitoring principalement centre sur Event Hubs et budget ;
- Key Vault present, mais toutes les applications ne l'utilisent pas encore de maniere homogene.

## Role des services Azure

### Key Vault

Key Vault centralise les secrets d'infrastructure :

- connection string ADLS ;
- nom du compte ADLS ;
- connection strings Event Hubs ;
- tenant id.

Limite actuelle :

- certains secrets attendus par le code ne sont pas provisionnes ou documentes, notamment SQL et `ADLS_ACCOUNT_KEY`.

### Azure Data Factory

ADF est prevu comme orchestrateur cloud du pipeline.

Etat actuel :

- Data Factory et managed identity sont provisionnes ;
- linked service ADLS present ;
- linked service Event Hubs/Blob declare ;
- pas de pipeline end-to-end implemente.

### Event Hubs

Event Hubs est prevu pour decoupler ingestion et traitement evenementiel.

Etat actuel :

- namespace et hubs provisionnes ;
- producteur Python disponible ;
- non branche au flux principal.

### Monitoring

Monitoring provisionne :

- Log Analytics Workspace ;
- Application Insights ;
- action group email ;
- alerte absence de messages Event Hubs ;
- alerte erreurs Event Hubs ;
- budget Azure.

Limite actuelle :

- alertes peu utiles tant qu'Event Hubs n'est pas utilise par le flux principal ;
- pas d'alertes sur fraicheur ADLS, erreurs Python, echec SQL, echec dbt ou qualite des donnees.

## Limites connues majeures

- Azure SQL n'est pas provisionne par Terraform.
- ADF n'orchestre pas encore le pipeline.
- Event Hubs est implemente partiellement mais non utilise dans le flux principal.
- Le chargement SQL Bronze remplace les tables a chaque cycle.
- dbt n'a pas de profil exemple ni de pipeline CI dedie.
- La qualite de donnees est limitee a quelques tests dbt.
- Les dossiers `quality`, `ml` et `notebooks` sont des placeholders.
- La documentation d'exploitation et de runbook etait absente avant ce dossier.

## Synthese

Le repository contient une base solide : ingestion API, stockage Bronze ADLS, chargement SQL Bronze, modeles dbt Silver/Gold et socle Terraform Azure. L'architecture cible est lisible, mais le pipeline n'est pas encore industrialise de bout en bout. Les principaux travaux restants concernent l'orchestration ADF, l'infrastructure Azure SQL, la gestion homogene des secrets, l'historisation, la qualite de donnees et la supervision operationnelle.
