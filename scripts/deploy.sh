#!/usr/bin/env bash
#
# KnowledgeForge deployment script for Ubuntu VPS (Vultr/DigitalOcean/etc.)
#
# Usage:
#   1. Clone repo:  git clone https://github.com/sudo-change/kb.git && cd kb
#   2. Copy .env:   cp .env.example .env && nano .env  (fill in secrets)
#   3. Run:         bash scripts/deploy.sh
#
# What it does:
#   - Installs Docker + Docker Compose if missing
#   - Creates required directories (data/, cookies/)
#   - Builds and starts the full stack
#   - Validates all services are healthy
#
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*" >&2; }

# ── 1. Check prerequisites ──
info "Checking prerequisites..."

if ! command -v docker &>/dev/null; then
    info "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    warn "Docker installed. You may need to log out/in for group changes."
fi

if ! docker compose version &>/dev/null 2>&1; then
    if ! docker-compose version &>/dev/null 2>&1; then
        error "Docker Compose not found. Install: https://docs.docker.com/compose/install/"
        exit 1
    fi
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

info "Docker Compose: $($COMPOSE_CMD version --short 2>/dev/null || echo 'ok')"

# ── 2. Directory setup ──
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"
info "Working directory: $REPO_ROOT"

mkdir -p data cookies
touch data/.gitkeep cookies/.gitkeep

# ── 3. Environment file check ──
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        warn "No .env found. Copying .env.example → .env"
        cp .env.example .env
        warn "Edit .env with your secrets before continuing:"
        warn "  nano .env"
        exit 1
    else
        error "No .env file found. Create one with:"
        error "  TELEGRAM_BOT_TOKEN=your_token"
        error "  TELEGRAM_CHAT_ID=your_chat_id"
        error "  TELEGRAM_TOPIC_IDS={\"bugbounty\":2,\"ai-money\":3,...}"
        error "  TELEGRAM_API_ID=your_api_id"
        error "  TELEGRAM_API_HASH=your_api_hash"
        exit 1
    fi
fi

info "Environment file: .env found"

# ── 4. Build and start ──
info "Building Docker images..."
$COMPOSE_CMD build

info "Starting services..."
$COMPOSE_CMD up -d

# ── 5. Wait for health checks ──
info "Waiting for services to become healthy..."
sleep 10

SERVICES=("rsshub" "collector" "api")
ALL_HEALTHY=true

for svc in "${SERVICES[@]}"; do
    status=$($COMPOSE_CMD ps --format '{{.Status}}' "$svc" 2>/dev/null || echo "not found")
    if echo "$status" | grep -qi "healthy\|running\|up"; then
        info "  $svc: $status"
    else
        warn "  $svc: $status"
        ALL_HEALTHY=false
    fi
done

# ── 6. Validate RSSHub ──
info "Validating RSSHub..."
if curl -sf http://localhost:1200/healthz >/dev/null 2>&1; then
    info "  RSSHub healthy"
else
    warn "  RSSHub not responding yet (may still be starting)"
fi

# ── 7. Validate API ──
info "Validating API..."
if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    info "  API healthy"
else
    warn "  API not responding yet (may still be starting)"
fi

# ── 8. Summary ──
echo ""
echo "════════════════════════════════════════════════════════"
info "KnowledgeForge deployment complete!"
echo ""
info "Services:"
$COMPOSE_CMD ps
echo ""
info "Useful commands:"
echo "  Logs:           $COMPOSE_CMD logs -f"
echo "  Collector logs: $COMPOSE_CMD logs -f collector"
echo "  Stop:           $COMPOSE_CMD down"
echo "  Restart:        $COMPOSE_CMD restart"
echo "  Force collect:  $COMPOSE_CMD exec collector python collector/main.py --once"
echo "  API docs:       http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "════════════════════════════════════════════════════════"
