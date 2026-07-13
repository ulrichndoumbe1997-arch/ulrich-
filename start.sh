#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  ULRICH — Script de démarrage
#  Usage : ./start.sh
# ═══════════════════════════════════════════════════════════════

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ██╗   ██╗██╗     ██████╗ ██╗ ██████╗██╗  ██╗"
echo "  ██║   ██║██║     ██╔══██╗██║██╔════╝██║  ██║"
echo "  ██║   ██║██║     ██████╔╝██║██║     ███████║"
echo "  ██║   ██║██║     ██╔══██╗██║██║     ██╔══██║"
echo "  ╚██████╔╝███████╗██║  ██║██║╚██████╗██║  ██║"
echo "   ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝"
echo -e "${NC}"
echo "  Network Supervision Tool — Phase 1"
echo "  ════════════════════════════════════"
echo ""

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Installe Docker Desktop d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
    echo "❌ docker-compose n'est pas disponible."
    exit 1
fi

echo -e "${YELLOW}▶ Démarrage des services ULRICH...${NC}"
echo ""

# Lancer les services
docker compose up -d --build

echo ""
echo -e "${GREEN}✅ ULRICH est démarré !${NC}"
echo ""
echo "  🌐 API Documentation  : http://localhost:8000/docs"
echo "  🖥️  Frontend           : http://localhost:3000"
echo "  📊 Interface complète : http://localhost:80"
echo ""
echo "  Commandes utiles :"
echo "  • Voir les logs    : docker compose logs -f backend"
echo "  • Arrêter          : docker compose down"
echo "  • Réinitialiser DB : docker compose down -v && docker compose up -d"
echo ""
