# Proposition de dashboard Power BI

## Objectif

Ce document propose un tableau de bord Power BI base sur les marts Gold dbt du projet VelibData.

Le dashboard doit permettre de suivre :

- la disponibilite des velos par station ;
- l'etat global du reseau Velib ;
- la repartition velos mecaniques et electriques ;
- les stations vides, pleines ou en tension ;
- l'impact de la meteo sur la disponibilite ;
- la qualite et la fraicheur des donnees.

## Sources Gold disponibles

Les marts Gold actuellement presents dans dbt sont :

### `mart_station_kpis`

Grain :

- une ligne par station pour le snapshot courant.

Colonnes principales :

- `station_id`
- `station_code`
- `station_name`
- `latitude`
- `longitude`
- `total_capacity`
- `bikes_available`
- `mechanical_bikes`
- `electric_bikes`
- `docks_available`
- `fill_rate_pct`
- `availability_status`
- `electric_ratio_pct`
- `is_active`
- `last_reported_at`

Usage Power BI :

- carte des stations ;
- classement des stations en tension ;
- indicateurs par station ;
- filtres actifs/inactifs.

### `mart_city_overview`

Grain :

- une ligne agregee pour la ville.

Colonnes principales :

- `total_stations`
- `total_bikes_available`
- `total_mechanical`
- `total_electric`
- `total_docks_available`
- `total_capacity`
- `avg_fill_rate_pct`
- `stations_empty`
- `stations_full`
- `stations_low`
- `snapshot_at`

Usage Power BI :

- KPIs globaux ;
- synthese executive ;
- suivi de l'etat instantane du reseau.

### `mart_weather_impact`

Grain :

- agregation par heure et condition meteo.

Colonnes principales :

- `weather_category`
- `cycling_conditions`
- `temperature_celsius`
- `precipitation_mm`
- `wind_speed_kmh`
- `nb_observations`
- `avg_fill_rate_pct`
- `avg_bikes_available`
- `avg_electric_bikes`
- `avg_mechanical_bikes`
- `pct_stations_empty`
- `pct_stations_full`
- `snapshot_hour`

Usage Power BI :

- analyse meteo ;
- comparaison des conditions de cyclabilite ;
- correlation meteo/disponibilite.

## Pages recommandees

## Page 1 - Vue reseau

Objectif :

Donner une vision immediate de l'etat global du reseau Velib.

Visuels :

- cartes KPI :
  - total stations ;
  - velos disponibles ;
  - bornes disponibles ;
  - taux de remplissage moyen ;
  - stations vides ;
  - stations pleines.
- donut ou barre empilee :
  - repartition velos mecaniques vs electriques.
- jauge :
  - taux de remplissage moyen.
- indicateur de fraicheur :
  - `snapshot_at` ou max `last_reported_at`.

Source principale :

- `mart_city_overview`

Filtres :

- date/heure si l'historisation est ajoutee ;
- statut actif ;
- type de disponibilite.

## Page 2 - Carte des stations

Objectif :

Identifier rapidement les zones sous tension.

Visuels :

- carte Power BI avec latitude/longitude ;
- couleur par `availability_status` :
  - `empty` ;
  - `full` ;
  - `low` ;
  - `normal` ;
  - `high`.
- taille du point selon `total_capacity` ou `bikes_available`.
- table detail station.

Source principale :

- `mart_station_kpis`

Tooltips :

- nom station ;
- velos disponibles ;
- velos electriques ;
- velos mecaniques ;
- bornes disponibles ;
- taux de remplissage ;
- derniere remontee.

Filtres :

- statut de disponibilite ;
- station active ;
- ratio electrique ;
- capacite.

## Page 3 - Stations critiques

Objectif :

Prioriser les stations a surveiller ou reequilibrer.

Visuels :

- table top stations vides ;
- table top stations pleines ;
- bar chart des stations avec le plus faible `fill_rate_pct` ;
- bar chart des stations avec le plus fort `fill_rate_pct` ;
- segmentation actif/inactif.

Source principale :

- `mart_station_kpis`

Mesures utiles :

```text
Stations vides = count rows where availability_status = "empty"
Stations pleines = count rows where availability_status = "full"
Stations en tension = empty + full + low
```

## Page 4 - Impact meteo

Objectif :

Comprendre comment les conditions meteo influencent la disponibilite.

Visuels :

- courbe `avg_fill_rate_pct` par `snapshot_hour` ;
- bar chart `avg_bikes_available` par `weather_category` ;
- bar chart `pct_stations_empty` par `cycling_conditions` ;
- scatter plot :
  - X = temperature ;
  - Y = taux de remplissage moyen ;
  - taille = nombre d'observations ;
  - couleur = categorie meteo.

Source principale :

- `mart_weather_impact`

Filtres :

- categorie meteo ;
- conditions de cyclabilite ;
- temperature ;
- precipitation.

## Page 5 - Qualite et exploitation

Objectif :

Donner une vue operationnelle de la sante des donnees.

Visuels recommandes :

- derniere date de donnees par source ;
- nombre de lignes par mart ;
- statut des tests dbt ;
- nombre de stations sans coordonnees ;
- nombre de stations inactives ;
- statut du dernier refresh Power BI.

Sources :

- marts Gold actuels ;
- future table d'exploitation `ops.pipeline_runs` ;
- artefacts dbt ou logs de pipeline si disponibles.

Limite actuelle :

- cette page necessite des tables de monitoring qui ne sont pas encore implementees.

## Modele semantique Power BI

### Tables a importer

- `gold.mart_city_overview`
- `gold.mart_station_kpis`
- `gold.mart_weather_impact`

### Relations recommandees

Etat actuel :

- `mart_city_overview` est une table agregee sans cle station.
- `mart_station_kpis` porte le detail station.
- `mart_weather_impact` porte des agregations meteo par heure et categorie.

Relations possibles :

- pas de relation obligatoire pour un dashboard snapshot ;
- relation temporelle possible via une future dimension temps ;
- relation station possible si un historique station est ajoute.

### Dimensions recommandees a ajouter plus tard

- `dim_station`
- `dim_time`
- `dim_weather_code`
- `dim_availability_status`

Ces dimensions faciliteraient les filtres, l'historisation et la lisibilite Power BI.

## Mesures DAX proposees

Exemples de mesures :

```text
Total Velos Disponibles =
SUM(mart_station_kpis[bikes_available])
```

```text
Total Velos Electriques =
SUM(mart_station_kpis[electric_bikes])
```

```text
Total Velos Mecaniques =
SUM(mart_station_kpis[mechanical_bikes])
```

```text
Taux Remplissage Moyen =
AVERAGE(mart_station_kpis[fill_rate_pct])
```

```text
Stations Vides =
CALCULATE(
    COUNTROWS(mart_station_kpis),
    mart_station_kpis[availability_status] = "empty"
)
```

```text
Stations Pleines =
CALCULATE(
    COUNTROWS(mart_station_kpis),
    mart_station_kpis[availability_status] = "full"
)
```

```text
Stations Actives =
CALCULATE(
    COUNTROWS(mart_station_kpis),
    mart_station_kpis[is_active] = 1
)
```

```text
Ratio Electrique Moyen =
AVERAGE(mart_station_kpis[electric_ratio_pct])
```

## Rafraichissement

Mode recommande :

- Import Power BI pour de meilleures performances sur ce volume.
- Refresh planifie apres execution dbt.
- DirectQuery possible si besoin de quasi temps reel, mais moins necessaire pour une MSPR.

Frequence :

- toutes les 15 minutes si le pipeline est completement automatise ;
- horaire pour une demonstration stable ;
- quotidienne pour le referentiel station.

## Limites actuelles pour Power BI

- Les marts Gold actuels sont principalement des snapshots.
- L'historique est limite si Azure SQL Bronze continue en `TRUNCATE + INSERT`.
- Il manque une table technique de suivi des runs.
- Il manque une dimension temps.
- Il manque une dimension station dediee.
- Les tests qualite ne sont pas encore assez riches pour alimenter une page exploitation complete.

## Evolutions recommandees

### Historisation

Ajouter des marts historiques :

- disponibilite station par heure ;
- disponibilite ville par heure ;
- impact meteo par jour ;
- taux de stations vides/pleines dans le temps.

### Reequilibrage

Ajouter des indicateurs :

- stations regulierement vides ;
- stations regulierement pleines ;
- zones a forte tension ;
- score de priorite de reequilibrage.

### Prediction

Si une partie ML est attendue :

- predire `bikes_available` par station et heure ;
- predire risque station vide ;
- utiliser meteo, heure, jour semaine et historique.

## Definition de succes

Le dashboard Power BI est considere satisfaisant pour la MSPR si :

- les KPIs globaux sont visibles en premiere page ;
- les stations sont consultables sur une carte ;
- les stations critiques sont identifiables ;
- l'impact meteo est analysable ;
- la fraicheur des donnees est visible ;
- les donnees proviennent des marts Gold dbt ;
- les limites connues sont documentees.
