# ⬡ ULRICH — Network Supervision Tool

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Docker](https://img.shields.io/badge/docker-ready-green)
![Python](https://img.shields.io/badge/python-3.11-yellow)
![React](https://img.shields.io/badge/react-18-cyan)

> **ULRICH** est un outil de supervision réseau complet développé dans le cadre du projet **KARA**. Il permet de découvrir, surveiller et alerter sur l'état des équipements d'un réseau informatique en temps réel.

---

## 📋 Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| 🔍 **Découverte automatique** | Scan du réseau et détection de tous les équipements connectés |
| 🗺️ **Carte topologique** | Visualisation graphique et interactive du réseau |
| 📊 **Tableau de bord** | Statistiques en temps réel par type et par zone |
| 🚨 **Alertes automatiques** | Détection des pannes et création d'incidents |
| 🔌 **Surveillance des ports** | Vérification des services HTTP, HTTPS, SSH, DNS... |
| 🏢 **Gestion des zones** | Organisation des équipements par zone géographique |
| 🔐 **Authentification** | Accès sécurisé par login/mot de passe |
| 📡 **Monitoring continu** | Ping automatique toutes les 60 secondes |

---

## 🏗️ Architecture

```
ulrich/
├── backend/          # API REST Python FastAPI
│   └── app/
│       ├── api/      # Endpoints REST
│       ├── models/   # Modèles base de données
│       ├── services/ # Scanner réseau, monitoring, alertes
│       └── schemas/  # Validation des données
├── frontend/         # Interface React
├── nginx/            # Reverse proxy
├── scripts/          # Initialisation base de données
└── docker-compose.yml
```

---

## 🛠️ Stack technique

| Composant | Technologie |
|---|---|
| **Backend** | Python 3.11 + FastAPI |
| **Frontend** | React 18 |
| **Base de données** | PostgreSQL 15 |
| **Cache** | Redis 7 |
| **Proxy** | Nginx |
| **Découverte réseau** | Nmap + ICMP Ping |
| **Conteneurisation** | Docker + Docker Compose |

---

## 🚀 Installation et démarrage

### Prérequis
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé
- Windows 10/11, macOS ou Linux

### Démarrage en 3 étapes

```bash
# 1. Cloner le projet
git clone https://github.com/ulrichndoumbe1997-arch/ulrich-
cd ulrich-

# 2. Lancer tous les services
docker compose up -d

# 3. Ouvrir dans le navigateur
# http://localhost:3000
```

### Identifiants par défaut
- **Utilisateur** : `admin`
- **Mot de passe** : `Admin1234!`

---

## 📱 Utilisation

### 1. Scanner le réseau
1. Connecte-toi sur `http://localhost:3000`
2. Va dans **"Scanner"**
3. Entre ta plage réseau (ex: `192.168.1.0/24`)
4. Clique sur **"Lancer le scan"**

### 2. Trouver ta plage réseau
```bash
# Windows
ipconfig
# Cherche "Adresse IPv4" sous Wi-Fi
# Ex: 192.168.1.49 → plage = 192.168.1.0/24
```

### 3. Visualiser la carte
- Clique sur **"Carte réseau"**
- Clique sur un équipement pour voir ses détails et ports ouverts

### 4. Gérer les alertes
- Les incidents sont créés automatiquement quand un équipement tombe en panne
- Va dans **"Alertes"** pour acquitter ou résoudre les incidents

---

## 🔒 Sécurité

- Authentification par login/mot de passe
- Sessions sécurisées avec token localStorage
- API REST sécurisée

---

## 📊 Endpoints API principaux

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/devices/` | Liste tous les équipements |
| POST | `/api/v1/devices/` | Ajouter un équipement |
| POST | `/api/v1/scan/` | Lancer un scan réseau |
| GET | `/api/v1/dashboard/stats` | Statistiques globales |
| GET | `/api/v1/zones/` | Liste les zones |
| POST | `/api/v1/scan/ports/{ip}` | Scanner les ports d'un équipement |

Documentation API complète : `http://localhost:8000/docs`

---

## 👤 Auteur

**Ulrich Ndoumbe**
- GitHub: [@ulrichndoumbe1997-arch](https://github.com/ulrichndoumbe1997-arch)

---

## 📄 Licence

Projet développé dans le cadre du projet **KARA** — Supervision réseau.
