#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/SIH26107-BIS-SmartGuide"
REPO_URL="https://github.com/akhilkvs07-cmd/SIH26107-BIS-SmartGuide.git"
SERVICE_SRC="$APP_DIR/deploy/oracle/bis-smartguide.service"
NGINX_SRC="$APP_DIR/deploy/oracle/bis-smartguide.nginx.conf"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script with sudo: sudo bash deploy/oracle/setup.sh"
  exit 1
fi

echo "[1/8] Installing system packages..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y git python3 python3-venv python3-pip nginx

echo "[2/8] Getting the SIH26107 repository..."
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only
else
  mkdir -p /opt
  git clone "$REPO_URL" "$APP_DIR"
fi

chown -R ubuntu:ubuntu "$APP_DIR"

echo "[3/8] Creating Python virtual environment..."
sudo -u ubuntu python3 -m venv "$APP_DIR/backend/venv"
sudo -u ubuntu "$APP_DIR/backend/venv/bin/python" -m pip install --upgrade pip

 echo "[4/8] Installing backend dependencies..."
sudo -u ubuntu "$APP_DIR/backend/venv/bin/pip" install -r "$APP_DIR/backend/requirements.txt"

echo "[5/8] Installing systemd service..."
cp "$SERVICE_SRC" /etc/systemd/system/bis-smartguide.service
systemctl daemon-reload
systemctl enable bis-smartguide
systemctl restart bis-smartguide

echo "[6/8] Installing Nginx configuration..."
cp "$NGINX_SRC" /etc/nginx/sites-available/bis-smartguide
ln -sf /etc/nginx/sites-available/bis-smartguide /etc/nginx/sites-enabled/bis-smartguide
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx
systemctl restart nginx

echo "[7/8] Opening the local Linux firewall if UFW is enabled..."
if command -v ufw >/dev/null 2>&1; then
  ufw allow 'Nginx Full' || true
fi

echo "[8/8] Verifying the backend..."
sleep 2
curl -fsS http://127.0.0.1:5000/health

echo
echo "=============================================="
echo "BIS SmartGuide deployment is running."
echo "Backend: http://127.0.0.1:5000/health"
echo "Website: http://<YOUR-ORACLE-PUBLIC-IP>/"
echo ""
echo "Next: in the Oracle Cloud Console, allow inbound TCP 80 and 443 in the VM subnet/security list."
echo "For HTTPS, point a domain at the VM and run the Certbot setup described in deploy/oracle/README.md."
echo "=============================================="
