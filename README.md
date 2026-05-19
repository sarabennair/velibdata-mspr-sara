# VelibData Pipeline

Pipeline de donnees complet pour le projet VelibData — MSPR TPRE924/944, EPSI 2025-2026.

## Setup rapide

1. Installer [uv](https://docs.astral.sh/uv/)
2. Cloner le repo et lancer :

```bash
git clone https://github.com/zied-CH/velibdata-pipeline.git
cd velibdata-pipeline
make setup
```

3. Lancer l ingestion :

```bash
make ingest
```

## Commandes

| Commande | Description |
|----------|-------------|
| make setup | Setup complet |
| make test | Lance les tests |
| make lint | Verifie le code |
| make format | Formate le code |
| make ingest | Lance l ingestion |
| make clean | Nettoie les caches |
