# Production Deployment & Operational Hardening Runbook

This runbook outlines the deployment procedure for **ScamShield AI** in a high-availability production Linux environment with Nginx reverse proxying, TLS termination, systemd supervision, and automated SQLite backup rotation.

---

## 1. System Requirements & Architecture

- **Operating System:** Ubuntu 22.04 LTS / Debian 12 / RHEL 9
- **Python Version:** 3.11+
- **Process Supervisor:** `systemd`
- **Reverse Proxy:** `nginx` (>= 1.20)
- **SSL/TLS Provider:** Let's Encrypt (`certbot`)
- **Port Allocation:**
  - `443` (Public HTTPS)
  - `80` (HTTP -> HTTPS Redirect)
  - `127.0.0.1:8000` (Private Uvicorn loopback)

---

## 2. Directory Layout & User Provisioning

Create a dedicated unprivileged system user and group:

```bash
sudo useradd -r -s /usr/sbin/nologin -d /opt/scamshield scamshield
sudo mkdir -p /opt/scamshield /var/log/scamshield /var/lib/scamshield /var/backups/scamshield
sudo chown -R scamshield:scamshield /opt/scamshield /var/log/scamshield /var/lib/scamshield /var/backups/scamshield
```

Copy the application codebase into `/opt/scamshield`:

```bash
sudo cp -r . /opt/scamshield/
cd /opt/scamshield
```

---

## 3. Virtual Environment & Dependency Installation

```bash
sudo -u scamshield python3.11 -m venv /opt/scamshield/.venv
sudo -u scamshield /opt/scamshield/.venv/bin/pip install --upgrade pip
sudo -u scamshield /opt/scamshield/.venv/bin/pip install -r /opt/scamshield/requirements.txt
```

---

## 4. Environment Variables Configuration

Copy the template and set production values:

```bash
sudo cp /opt/scamshield/deploy/env.production.example /opt/scamshield/.env
sudo chown scamshield:scamshield /opt/scamshield/.env
sudo chmod 600 /opt/scamshield/.env
```

Generate a secure random secret key:

```bash
openssl rand -hex 32
```
Paste this into `AUTH_SECRET_KEY` inside `/opt/scamshield/.env`.

Configure `TRUSTED_PROXIES`:
- If Nginx runs on the same physical or virtual host: `TRUSTED_PROXIES=127.0.0.1,::1`
- If behind an external load balancer (e.g. AWS ALB): Set to the VPC CIDR (e.g., `10.0.0.0/16`).

---

## 5. Systemd Service Installation

Install and activate the systemd unit file:

```bash
sudo cp /opt/scamshield/deploy/systemd/scamshield.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable scamshield.service
sudo systemctl start scamshield.service
sudo systemctl status scamshield.service
```

Inspect live service logs:
```bash
journalctl -u scamshield.service -f
```

---

## 6. Nginx Reverse Proxy & TLS Configuration

Install Nginx and Certbot:

```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx
```

Install the Nginx configuration:

```bash
sudo cp /opt/scamshield/deploy/nginx/scamshield.conf /etc/nginx/sites-available/scamshield.conf
sudo ln -s /etc/nginx/sites-available/scamshield.conf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
```

Obtain TLS Certificate:

```bash
sudo certbot --nginx -d scamshield.yourdomain.com
```

Test and reload Nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 7. Health Probes & Monitoring

ScamShield provides three distinct health check endpoints:

| Endpoint | Type | Description | Expected HTTP Status |
|---|---|---|---|
| `/api/v1/health` | Comprehensive | Returns model status, classifier type, and DB connectivity | `200 OK` (or `degraded`) |
| `/api/v1/health/live` | Liveness | Lightweight process heartbeat probe | `200 OK` |
| `/api/v1/health/ready` | Readiness | Verifies ML model bundle loaded and database connection | `200 OK` (or `503 Unavailable`) |

Verify using `curl`:
```bash
curl -I http://127.0.0.1:8000/api/v1/health
curl -I http://127.0.0.1:8000/api/v1/health/live
curl -I http://127.0.0.1:8000/api/v1/health/ready
```

---

## 8. Automated Database Backup Cron

Set up an automated hourly snapshot using the zero-downtime online SQLite backup utility:

```bash
sudo crontab -u scamshield -e
```

Add the following cron entry (runs every hour at minute 0):

```cron
0 * * * * /opt/scamshield/.venv/bin/python /opt/scamshield/scripts/backup_db.py >> /var/log/scamshield/backup.log 2>&1
```

Verify backup creation:
```bash
ls -lh /var/backups/scamshield/
```
The rotation retention will automatically keep the 10 most recent snapshots and purge older files.
