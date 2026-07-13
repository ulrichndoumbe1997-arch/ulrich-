# ULRICH — Network Supervision Tool

Outil de supervision réseau complet — 100% open source, déployable avec Docker.

## Prérequis

- Docker Desktop (https://www.docker.com/products/docker-desktop/)
- VS Code (https://code.visualstudio.com/)

## Démarrage rapide

```bash
# 1. Cloner / copier le projet dans un dossier
cd ulrich/

# 2. Lancer tous les services
docker compose up -d --build

# 3. Attendre ~30 secondes puis ouvrir
#    http://localhost:8000/docs   ← API interactive
#    http://localhost:3000        ← Interface (Phase 2)
```

## Structure du projet

```
ulrich/
├── docker-compose.yml          ← Orchestration des services
├── start.sh                    ← Script de démarrage
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             ← Point d'entrée FastAPI
│       ├── core/
│       │   └── config.py       ← Configuration centrale
│       ├── db/
│       │   └── database.py     ← Connexion PostgreSQL
│       ├── models/
│       │   ├── device.py       ← Modèles Device, Zone, Ping, SNMP
│       │   └── user.py         ← Modèle utilisateur
│       ├── schemas/
│       │   └── schemas.py      ← Validation Pydantic
│       ├── services/
│       │   └── discovery/
│       │       └── scanner.py  ← Scanner réseau (Ping + Nmap + SNMP)
│       └── api/routes/
│           ├── devices.py      ← CRUD équipements + historique
│           └── network.py      ← Scanner, Zones, Dashboard
├── scripts/
│   └── init_db.sql             ← Initialisation base de données
└── nginx/
    └── nginx.conf              ← Reverse proxy
```

## Endpoints API principaux

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET  | `/api/v1/devices/` | Liste tous les équipements |
| POST | `/api/v1/devices/` | Ajouter manuellement |
| POST | `/api/v1/scan/` | Lancer un scan réseau |
| GET  | `/api/v1/dashboard/stats` | Statistiques globales |
| GET  | `/api/v1/zones/` | Liste les zones réseau |
| POST | `/api/v1/devices/{id}/ping` | Ping manuel |
| GET  | `/api/v1/devices/{id}/history` | Historique disponibilité |

## Lancer un scan réseau

Depuis l'interface Swagger (`http://localhost:8000/docs`), appelle :

```json
POST /api/v1/scan/
{
  "network": "192.168.1.0/24",
  "snmp_community": "public"
}
```

## Phases du projet

- [x] **Phase 1** — Fondations & Découverte réseau (EN COURS)
- [ ] **Phase 2** — Visualisation graphique (carte topologique)
- [ ] **Phase 3** — Tableau de bord & Statistiques
- [ ] **Phase 4** — Alertes & Notifications
- [ ] **Phase 5** — Déploiement & Finalisation

## Identifiants par défaut

- **Utilisateur admin** : `admin`
- **Mot de passe** : `Admin1234!`
- **Base de données** : `postgresql://ulrich:ulrich_secret@localhost:5432/ulrich`
