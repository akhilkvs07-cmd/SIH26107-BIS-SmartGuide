# Oracle Cloud Always Free deployment

This folder contains the production deployment files for SIH26107 BIS SmartGuide.

## Architecture

- Ubuntu VM on Oracle Cloud Always Free
- Gunicorn runs the Flask backend on `127.0.0.1:5000`
- Nginx serves the existing `index.html`
- Nginx reverse-proxies the backend API endpoints
- systemd automatically restarts the backend after reboot/crash

Oracle's current Always Free allowance includes an Ampere A1 option with up to 2 OCPUs and 12 GB RAM total for an Always Free tenancy, plus 200 GB block volume storage. Capacity is subject to availability and Oracle's Always Free rules.

## One-time VM setup

Create an Ubuntu Always Free VM in the Oracle Cloud Console. After SSH-ing into the VM, run:

```bash
sudo apt-get update
sudo apt-get install -y git
cd /tmp
git clone https://github.com/akhilkvs07-cmd/SIH26107-BIS-SmartGuide.git
cd SIH26107-BIS-SmartGuide
sudo bash deploy/oracle/setup.sh
```

The setup script installs Python, Nginx and the backend dependencies, creates the Python virtual environment, enables the systemd service, and configures Nginx.

## Oracle networking

In the Oracle Cloud Console, allow inbound TCP:

- 80 for HTTP
- 443 for HTTPS
- 22 for SSH (keep this restricted to your own IP when practical)

The Linux firewall and the Oracle Cloud security list/NSG are separate controls. Both must allow the required traffic.

## Verify

On the VM:

```bash
curl http://127.0.0.1:5000/health
sudo systemctl status bis-smartguide --no-pager
sudo systemctl status nginx --no-pager
```

From another device:

```text
http://YOUR_PUBLIC_IP/health
```

The website is:

```text
http://YOUR_PUBLIC_IP/
```

## HTTPS

For a real SIH demo, HTTPS is recommended. After assigning a stable public IP and a domain name pointing to it, install Certbot and run:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.example
```

Certbot can configure the Nginx certificate and renewal for the domain.

## Updating the application

After a GitHub push:

```bash
cd /opt/SIH26107-BIS-SmartGuide
sudo -u ubuntu git pull --ff-only
sudo -u ubuntu /opt/SIH26107-BIS-SmartGuide/backend/venv/bin/pip install -r backend/requirements.txt
sudo systemctl restart bis-smartguide
sudo systemctl reload nginx
```

## Useful troubleshooting

```bash
sudo journalctl -u bis-smartguide -n 100 --no-pager
sudo journalctl -u bis-smartguide -f
sudo nginx -t
sudo journalctl -u nginx -n 100 --no-pager
```

Never put Oracle passwords, private SSH keys, API keys, OTPs, or payment information in this repository.
