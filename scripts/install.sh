#!/usr/bin/env bash
set -euo pipefail

REPO="AldarKose/replenish-server"
APP_DIR="/opt/replenish"
TZ_DEFAULT="Europe/Berlin"

if [[ $EUID -ne 0 ]]; then
  echo "Запусти от root: sudo bash install.sh"
  exit 1
fi

if ! grep -qi ubuntu /etc/os-release; then
  echo "❌ Поддерживается только Ubuntu 20.04+"
  exit 1
fi

apt update -y
apt install -y curl ca-certificates openssl docker.io docker-compose-plugin
systemctl enable --now docker

mkdir -p "$APP_DIR"
cd "$APP_DIR"

POSTGRES_PASSWORD="$(openssl rand -hex 16)"
API_KEY="$(openssl rand -hex 24)"
TZ="${TZ:-$TZ_DEFAULT}"

cat > "$APP_DIR/.env" <<EOF
POSTGRES_DB=replenish
POSTGRES_USER=replenish
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
API_KEY=$API_KEY
TZ=$TZ
EOF

URL="https://github.com/${REPO}/archive/refs/heads/main.tar.gz"
curl -fsSL "$URL" -o /tmp/replenish.tar.gz
tar -xzf /tmp/replenish.tar.gz -C "$APP_DIR"
cd "$APP_DIR"/replenish-server-main/server

docker compose --env-file "$APP_DIR/.env" up -d

IP="$(hostname -I | awk '{print $1}')"

echo ""
echo "=== УСТАНОВКА ЗАВЕРШЕНА ==="
echo "URL: http://$IP:8000"
echo "X-Api-Key: $API_KEY"
echo ""
echo "Проверка:"
echo "curl -H \"X-Api-Key: $API_KEY\" http://127.0.0.1:8000/health"
