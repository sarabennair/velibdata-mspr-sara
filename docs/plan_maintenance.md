# Plan de maintenance VelibData

## Objectif

Ce document propose les procedures de maintenance preventive, corrective, supervision, alerting, sauvegarde et restauration pour le pipeline VelibData.

Le plan tient compte de l'etat actuel du repository :

- ingestion Python vers ADLS Bronze ;
- chargement Azure SQL Bronze par script ;
- transformations dbt Silver/Gold ;
- socle Terraform pour Storage, Key Vault, Event Hubs, ADF et Monitoring ;
- orchestration ADF encore a implementer ;
- Azure SQL non provisionne par Terraform dans l'etat actuel.

## Perimetre de maintenance

Composants a maintenir :

- code d'ingestion Python ;
- APIs externes Velib et Open-Meteo ;
- ADLS Gen2 et fichiers Bronze ;
- Azure SQL Bronze ;
- projet dbt Silver/Gold ;
- Terraform Azure ;
- Key Vault et secrets ;
- Event Hubs ;
- Azure Data Factory ;
- Monitoring Azure ;
- futurs rapports Power BI.

## Maintenance preventive

### Tous les jours

- Verifier que l'ingestion a produit des fichiers dans ADLS Bronze pour les trois sources.
- Controler la fraicheur des donnees :
  - dernier fichier `station_status` ;
  - dernier fichier `station_info` ;
  - dernier fichier `weather`.
- Verifier que le chargement SQL Bronze s'est termine sans erreur.
- Verifier que les modeles dbt Silver/Gold se sont executes.
- Verifier les volumes :
  - nombre de stations dans `station_status` ;
  - nombre de stations dans `station_info` ;
  - nombre de lignes meteo horaires.
- Verifier les alertes Azure Monitor et les notifications email.

### Toutes les semaines

- Examiner les logs d'ingestion et les erreurs HTTP.
- Controler les couts Azure et la consommation du budget.
- Verifier les droits Key Vault et les identites managées.
- Executer les tests dbt complets.
- Controler la coherence des marts Gold utilises par Power BI.
- Verifier que les fichiers Bronze ne croissent pas de facon anormale.

### Tous les mois

- Revoir les versions des dependances Python.
- Revoir les versions Terraform provider AzureRM.
- Verifier les politiques de retention ADLS.
- Tester une procedure de restauration a partir d'un fichier Bronze.
- Revoir les alertes et seuils de supervision.
- Exporter ou archiver les preuves d'execution pour le dossier MSPR.

## Maintenance corrective

### Incident API Velib indisponible

Symptomes :

- erreurs HTTP sur `station_status` ou `station_information` ;
- aucun nouveau fichier Bronze pour une source Velib ;
- baisse ou absence de donnees dans les marts.

Actions :

1. Verifier l'accessibilite de l'URL API.
2. Consulter les logs Python.
3. Relancer l'ingestion apres retour du service.
4. Si une fenetre de donnees est manquante, documenter l'incident.
5. Verifier que SQL Bronze et dbt ont ete rejoues apres correction.

### Incident Open-Meteo indisponible

Symptomes :

- absence de nouveau fichier `weather` ;
- marts meteo incomplets ;
- champs meteo nuls dans `int_availability_weather`.

Actions :

1. Verifier l'API Open-Meteo.
2. Relancer uniquement l'ingestion meteo si le pipeline le permet.
3. Rejouer le chargement Bronze SQL.
4. Rejouer dbt.
5. Controler `mart_weather_impact`.

### Incident ADLS

Symptomes :

- erreur d'authentification ADLS ;
- erreur de creation de fichier ;
- absence de fichiers Bronze.

Actions :

1. Verifier le nom du compte ADLS et du container Bronze.
2. Verifier le secret ou la cle utilisee par le code.
3. Verifier les roles RBAC sur le compte de stockage.
4. Tester une ecriture manuelle controlee dans un environnement de test.
5. Relancer l'ingestion.

### Incident Azure SQL

Symptomes :

- erreur ODBC ;
- timeout SQL ;
- tables Bronze absentes ;
- echec dbt sur sources manquantes.

Actions :

1. Verifier la disponibilite du serveur SQL.
2. Verifier les variables `SQL_SERVER`, `SQL_DATABASE`, `SQL_USER`, `SQL_PASSWORD`.
3. Verifier firewall et connectivite.
4. Verifier l'existence du schema `bronze`.
5. Relancer `load_bronze`.
6. Relancer dbt.

### Incident dbt

Symptomes :

- echec `dbt run` ;
- echec `dbt test` ;
- marts Gold absents ou incomplets.

Actions :

1. Identifier le modele en echec.
2. Verifier les sources Bronze.
3. Verifier les types et colonnes attendues.
4. Corriger les donnees sources ou le mapping si necessaire.
5. Relancer `dbt run`.
6. Relancer `dbt test`.
7. Verifier Power BI apres correction.

## Supervision

### Indicateurs techniques a suivre

- derniere heure d'ingestion reussie ;
- nombre de fichiers Bronze par source et par jour ;
- taille des fichiers Bronze ;
- nombre de lignes chargees dans SQL Bronze ;
- duree d'execution ingestion ;
- duree d'execution chargement SQL ;
- duree d'execution dbt ;
- nombre de tests dbt en erreur ;
- nombre d'erreurs HTTP API ;
- cout Azure mensuel.

### Indicateurs data quality

- `station_id` non nul ;
- unicite de `station_id` dans le referentiel station ;
- latitude et longitude non nulles ;
- `bikes_available >= 0` ;
- `docks_available >= 0` ;
- `total_capacity > 0` ;
- `bikes_available + docks_available` coherent avec la capacite ;
- `temperature_celsius` dans une plage plausible ;
- fraicheur maximale acceptable pour `station_status`.

## Alerting recommande

Alertes a ajouter ou renforcer :

- aucun fichier Bronze genere depuis plus de X minutes ;
- volume de stations inferieur a un seuil attendu ;
- echec du chargement SQL ;
- echec dbt run ou dbt test ;
- fraicheur des sources dbt depassee ;
- taux d'erreurs HTTP superieur a un seuil ;
- cout Azure superieur a 50, 80 et 95 pour cent du budget ;
- Event Hubs sans message uniquement si Event Hubs devient partie du flux actif.

## Sauvegarde

### ADLS Bronze

ADLS Bronze est la source de rejeu principale. Les fichiers bruts doivent etre conserves avec une retention adaptee au besoin MSPR.

Bonnes pratiques :

- activer soft delete ;
- conserver les fichiers par partition datee ;
- ne pas modifier les fichiers bruts apres ingestion ;
- documenter toute suppression exceptionnelle ;
- envisager lifecycle management pour archiver les donnees anciennes.

### Azure SQL

Pour Azure SQL :

- activer les sauvegardes automatiques Azure SQL ;
- definir une retention adaptee au projet ;
- documenter le point de restauration disponible ;
- sauvegarder les scripts de creation schema/tables ;
- conserver ADLS Bronze comme source de reconstruction.

### dbt

Pour dbt :

- versionner tous les modeles ;
- conserver les artefacts de run importants en CI si possible ;
- sauvegarder les definitions de marts via Git ;
- documenter les changements de schema.

## Restauration

### Restaurer SQL Bronze depuis ADLS

Procedure :

1. Identifier les fichiers Bronze de reference.
2. Verifier leur validite JSON.
3. Relancer le script de chargement Bronze.
4. Controler les nombres de lignes.
5. Relancer dbt.
6. Verifier les marts Gold.
7. Rafraichir Power BI.

### Restaurer un mart Gold

Procedure :

1. Verifier que les sources Bronze SQL sont presentes.
2. Executer les modeles staging.
3. Executer les modeles intermediate.
4. Executer les marts Gold.
5. Executer les tests dbt.
6. Controler les valeurs metier principales.

## Limites actuelles du plan

- L'orchestration ADF n'etant pas encore implementee, certaines procedures supposent une execution manuelle ou CI.
- Azure SQL n'etant pas provisionne par Terraform, la maintenance SQL depend d'une ressource externe au repository.
- Les alertes actuelles sont surtout centrees sur Event Hubs, qui n'est pas encore utilise par le flux principal.
- Great Expectations est declare comme dependance, mais aucun controle n'est encore implemente.

## Recommandations prioritaires

1. Ajouter Azure SQL dans Terraform.
2. Documenter et centraliser tous les secrets dans Key Vault.
3. Ajouter une orchestration ADF end-to-end.
4. Ajouter des tests dbt et controles qualite plus complets.
5. Mettre en place des alertes sur fraicheur, volume et echec pipeline.
6. Transformer le chargement SQL Bronze en mode historise ou incremental.
