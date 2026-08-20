# Quiz Platform - Self-Hosted Deployment Guide

## Overview
This guide covers deploying the Quiz Platform on a home server with public exposure via **Tailscale Funnel** (Method A) or **Cloudflare Tunnel** (Method B). The entire stack runs in Docker containers with a memory footprint under 250MB total.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PUBLIC INTERNET                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│    TAILSCALE FUNNEL     │     │   CLOUDFLARE TUNNEL     │
│  (tailscale funnel 443) │     │  (cloudflared tunnel)   │
└───────────┬─────────────┘     └───────────┬─────────────┘
            │                               │
            └───────────────┬───────────────┘
                            ▼
         ┌─────────────────────────────────────────┐
         │         HOME SERVER (TAILSCALE)         │
         │  ┌───────────────────────────────────┐  │
         │  │         NGINX PROXY (Port 80/443)  │  │
         │  │  • SSL Termination                │  │
         │  │  • Rate Limiting                  │  │
         │  │  • Security Headers               │  │
         │  └──────────────┬────────────────────┘  │
         │                 │                       │
         │    ┌────────────┴────────────┐          │
         │    ▼                         ▼          │
         │ ┌─────────┐             ┌─────────┐      │
         │ │ FRONTEND│             │  BACKEND │      │
         │ │  (Nginx)│             │ (FastAPI)│      │
         │ │ Port 8080           │ Port 8000       │
         │ └─────────┘             └─────────┘      │
         └─────────────────────────────────────────┘
```

---

## Prerequisites

### Home Server
- Linux (Ubuntu/Debian/Arch) with Docker and Docker Compose
- Tailscale installed and authenticated (`sudo tailscale up`)
- At least 512MB RAM available (containers use <250MB)
- Connected to Tailscale network (tailnet)

### Development Machines
- **MacBook Air M3 (16GB)**: Code editing, frontend builds
- **AMD Ryzen 7 5700G + RTX 4060 (32GB)**: Local container testing

### API Keys Required
- **Gemini API**: https://aistudio.google.com/apikey (free tier available)
- **OpenAI API**: https://platform.openai.com/api-keys (optional, paid)

---

## Quick Start

### 1. Clone and Configure
```bash
# On home server
git clone <your-repo-url> quiz-platform
cd quiz-platform

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required `.env` values:**
```bash
GEMINI_API_KEY=your_actual_gemini_key
OPENAI_API_KEY=your_actual_openai_key  # optional
CORS_ORIGINS=https://your-tailnet.ts.net,https://your-domain.com
```

### 2. Deploy Stack
```bash
# Build and start all services
docker compose up -d --build

# Check status
docker compose ps
docker compose logs -f
```

### 3. Verify Local Access
```bash
# Frontend
curl http://localhost:8080/health

# Backend API
curl http://localhost:8000/health
curl http://localhost:8000/api/quiz/health
```

---

## Method A: Tailscale Funnel (Easiest, No Domain Required)

### Enable Funnel
```bash
# On home server (must be in Tailscale network)
tailscale funnel 443

# Check status
tailscale funnel status
```

### Get Public URL
```bash
# Tailscale provides a URL like:
# https://your-device.your-tailnet.ts.net
tailscale status --json | jq -r '.Self.DNSName'
```

### Update CORS
```bash
# Add Funnel URL to CORS_ORIGINS in .env
CORS_ORIGINS=https://your-device.your-tailnet.ts.net

# Restart to apply
docker compose restart quiz-api quiz-proxy
```

### Test Public Access
```bash
# From anywhere on the internet
curl https://your-device.your-tailnet.ts.net/health
```

---

## Method B: Cloudflare Tunnel (Production, Custom Domain)

### Prerequisites
- Free Cloudflare account
- Custom domain (e.g., `quiz.example.com`)
- Domain nameservers pointing to Cloudflare

### Setup Cloudflare Tunnel

#### 1. Install cloudflared
```bash
# On home server
# Ubuntu/Debian
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb

# Or use Docker (recommended)
```

#### 2. Authenticate
```bash
cloudflared tunnel login
# Opens browser - authorize your domain
```

#### 3. Create Tunnel
```bash
cloudflared tunnel create quiz-platform
# Note the Tunnel ID and credentials file path
```

#### 4. Configure DNS
```bash
cloudflared tunnel route dns quiz-platform quiz.your-domain.com
```

#### 5. Create Config
Create `cloudflared.yml`:
```yaml
tunnel: <TUNNEL_ID>
credentials-file: /home/user/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: quiz.your-domain.com
    service: https://localhost:443
    originRequest:
      noTLSVerify: true
  - service: http_status:404
```

#### 6. Run Tunnel
```bash
# Test
cloudflared tunnel --config cloudflared.yml run quiz-platform

# Run as systemd service (production)
sudo cloudflared service install --config cloudflared.yml
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### Update CORS
```bash
# Add custom domain to CORS_ORIGINS
CORS_ORIGINS=https://quiz.your-domain.com

# Restart
docker compose restart quiz-api quiz-proxy
```

---

## Development Workflow

### Local Development (MacBook Air M3)

```bash
# 1. Start backend locally
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Start frontend dev server
cd frontend
npm install
npm run dev  # Runs on http://localhost:3000

# 3. Proxy API calls to backend (vite.config.js handles this)
```

### Integration Testing (Ryzen 7 5700G + RTX 4060)

```bash
# Build and test full Docker stack locally
docker compose -f docker-compose.yml up -d --build

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8000/health

# Run load test (optional)
hey -n 100 -c 10 http://localhost:8080/
```

### Sync Changes to Home Server
```bash
# From MacBook
rsync -avz --exclude node_modules --exclude .git --exclude __pycache__ \
  ./quiz-platform/ user@home-server:~/quiz-platform/

# On home server
cd ~/quiz-platform
docker compose up -d --build
```

---

## Configuration Reference

### Environment Variables (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes* | - | Google Gemini API key |
| `OPENAI_API_KEY` | No | - | OpenAI API key |
| `LLM_PROVIDER` | No | `auto` | `auto`, `gemini`, `openai` |
| `LLM_MODEL` | No | `gemini-1.5-flash` | Model identifier |
| `CACHE_TTL_SECONDS` | No | `3600` | Cache time-to-live |
| `CACHE_MAX_SIZE` | No | `100` | Max cache entries |
| `RATE_LIMIT_PER_MINUTE` | No | `10` | API rate limit |
| `LOG_LEVEL` | No | `INFO` | Log verbosity |
| `CORS_ORIGINS` | No | `*` | Comma-separated allowed origins |

*At least one LLM API key required.

### Resource Limits (docker-compose.yml)

| Service | Memory Limit | CPU Limit |
|---------|-------------|-----------|
| quiz-api | 150MB | 0.5 cores |
| quiz-frontend | 50MB | 0.25 cores |
| quiz-proxy | 32MB | 0.25 cores |
| **Total** | **~232MB** | **1.0 cores** |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Backend health check |
| `GET` | `/api/quiz/health` | Detailed health with provider status |
| `POST` | `/api/quiz/generate` | Generate quiz questions |

### Generate Quiz Request
```json
POST /api/quiz/generate
{
  "topic": "AWS S3 storage fundamentals",
  "difficulty": "medium",
  "count": 10,
  "question_type": "mixed"
}
```

### Generate Quiz Response
```json
{
  "success": true,
  "questions": [
    {
      "id": 1,
      "type": "single",
      "question": "What is the default storage class in S3?",
      "options": {
        "A": "S3 Standard",
        "B": "S3 Glacier",
        "C": "S3 Intelligent-Tiering",
        "D": "S3 One Zone-IA"
      },
      "correct_answers": ["A"],
      "explanation": "S3 Standard is the default storage class..."
    }
  ],
  "metadata": {
    "provider": "gemini",
    "model": "gemini-1.5-flash",
    "source": "llm",
    "cached": false,
    "generated_at": "2026-01-15T10:30:00Z"
  }
}
```

---

## Security Checklist

- [ ] **CORS_ORIGINS** restricted to your public URLs only (not `*`)
- [ ] **Tailscale ACLs** configured to restrict tailnet access
- [ ] **Cloudflare WAF** rules enabled (if using Cloudflare Tunnel)
- [ ] **Rate limiting** active on `/api/` endpoints
- [ ] **Security headers** present (HSTS, CSP, X-Frame-Options)
- [ ] **Non-root containers** running as `appuser`/`nginxuser`
- [ ] **API keys** stored in `.env` (not in images or git)
- [ ] **HTTPS only** in production (Tailscale/Cloudflare handles this)

---

## Monitoring & Logs

```bash
# View all logs
docker compose logs -f

# View specific service
docker compose logs -f quiz-api
docker compose logs -f quiz-frontend
docker compose logs -f quiz-proxy

# Check resource usage
docker stats

# Health checks
curl https://your-url/health
curl https://your-url/api/quiz/health
```

---

## Troubleshooting

### Backend won't start (502 Bad Gateway)
```bash
# Check logs
docker compose logs quiz-api

# Common issues:
# - Missing GEMINI_API_KEY or OPENAI_API_KEY in .env
# - Port 8000 already in use
# - Memory limit too low (increase in docker-compose.yml)
```

### Frontend shows blank page
```bash
# Check nginx config
docker compose exec quiz-frontend cat /etc/nginx/conf.d/default.conf

# Rebuild frontend
docker compose build --no-cache quiz-frontend
docker compose up -d quiz-frontend
```

### CORS errors in browser
```bash
# Verify CORS_ORIGINS includes your public URL
# Must match exactly: https://your-domain.com (no trailing slash)
# Restart quiz-api and quiz-proxy after changes
```

### Tailscale Funnel not working
```bash
# Verify Tailscale is running
tailscale status

# Check funnel is active
tailscale funnel status

# Ensure port 443 is exposed in docker-compose.yml proxy
```

### Cloudflare Tunnel 502 errors
```bash
# Check tunnel status
cloudflared tunnel info <tunnel-name>

# Verify ingress rules match hostname
# Check cloudflared logs
journalctl -u cloudflared -f
```

---

## Updating the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and deploy
docker compose up -d --build

# Or rebuild specific service
docker compose build --no-cache quiz-api
docker compose up -d quiz-api
```

---

## Backup & Recovery

```bash
# Backup .env and config
tar -czf quiz-platform-backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml nginx.conf cloudflared.yml

# Restore
tar -xzf quiz-platform-backup-20260115.tar.gz
docker compose up -d
```

---

## Support

- **Issues**: GitHub Issues
- **Tailscale Docs**: https://tailscale.com/kb/1223/funnel
- **Cloudflare Tunnel Docs**: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/