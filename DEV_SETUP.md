# Quiz Platform - Local Development Setup

## Overview
This guide covers setting up the development environment on:
- **MacBook Air M3 (16GB)**: Primary development machine
- **AMD Ryzen 7 5700G + RTX 4060 (32GB)**: Integration testing machine

---

## MacBook Air M3 - Primary Development

### Prerequisites
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install node@20 python@3.12 docker colima
```

### Start Colima (Docker on macOS)
```bash
# Start Docker VM with reasonable resources
colima start --cpu 4 --memory 8 --disk 60

# Verify
docker version
```

### Backend Development
```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create local .env for development
cat > .env << EOF
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
LLM_PROVIDER=auto
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF

# Run backend with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Create local env for Vite
cat > .env.local << EOF
VITE_API_BASE_URL=http://localhost:8000
EOF

# Start dev server (port 3000)
npm run dev
```

### Access Local Development
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## AMD Ryzen 7 5700G + RTX 4060 - Integration Testing

### Prerequisites (Ubuntu/Debian)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo apt install docker-compose-plugin

# Install development tools
sudo apt install git nodejs npm python3.12 python3.12-venv
```

### Full Stack Testing with Docker
```bash
# Clone repository
git clone <your-repo-url> quiz-platform
cd quiz-platform

# Create test .env
cp .env.example .env
# Edit .env with your API keys

# Build and start full stack
docker compose up -d --build

# Verify services
docker compose ps
docker compose logs -f
```

### Test Endpoints
```bash
# Frontend (via nginx proxy)
curl http://localhost/health

# Backend API
curl http://localhost:8000/health
curl http://localhost:8000/api/quiz/health

# Generate quiz test
curl -X POST http://localhost:8000/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"topic":"Docker basics","difficulty":"easy","count":3,"question_type":"single"}'
```

### Load Testing (Optional)
```bash
# Install hey (Go-based load tester)
go install github.com/rakyll/hey@latest

# Test frontend
hey -n 1000 -c 50 http://localhost/

# Test API
hey -n 100 -c 10 -m POST -H "Content-Type: application/json" \
  -d '{"topic":"test","difficulty":"easy","count":5,"question_type":"single"}' \
  http://localhost:8000/api/quiz/generate
```

### GPU Acceleration (Optional - for local LLM if added later)
```bash
# NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test GPU access
docker run --rm --gpus all nvidia/cuda:12.4-base nvidia-smi
```

---

## Cross-Machine Development Workflow

### 1. Code on MacBook Air M3
```bash
# Make changes to frontend/src/ or backend/app/
# Frontend changes hot-reload automatically
# Backend changes hot-reload with uvicorn --reload
```

### 2. Test on Ryzen/RTX 4060
```bash
# Sync changes from MacBook
rsync -avz --exclude node_modules --exclude .git --exclude __pycache__ \
  --exclude venv --exclude .env \
  ~/Developer/Coding/quiz-platform/ user@ryzen-machine:~/quiz-platform/

# On Ryzen machine
cd ~/quiz-platform
docker compose up -d --build
```

### 3. Deploy to Home Server
```bash
# From either machine
rsync -avz --exclude node_modules --exclude .git --exclude __pycache__ \
  --exclude venv \
  ~/Developer/Coding/quiz-platform/ user@home-server:~/quiz-platform/

# On home server
cd ~/quiz-platform
docker compose up -d --build
```

---

## IDE Setup (VS Code Recommended)

### Extensions
- Python (Microsoft)
- TypeScript/JavaScript Language Features
- Tailwind CSS IntelliSense
- Docker
- REST Client (for API testing)

### Settings (`.vscode/settings.json`)
```json
{
  "python.defaultInterpreterPath": "./backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit"
  },
  "files.associations": {
    "*.css": "tailwindcss"
  }
}
```

### Launch Configurations (`.vscode/launch.json`)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Backend: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--port", "8000"],
      "cwd": "${workspaceFolder}/backend",
      "envFile": "${workspaceFolder}/backend/.env",
      "console": "integratedTerminal"
    },
    {
      "name": "Frontend: Vite Dev Server",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev"],
      "cwd": "${workspaceFolder}/frontend",
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Testing API Endpoints

### Using VS Code REST Client (`.vscode/api.http`)
```
@baseUrl = http://localhost:8000
@topic = Python decorators

### Health Check
GET {{baseUrl}}/health

### Detailed Health
GET {{baseUrl}}/api/quiz/health

### Generate Quiz - Single Choice
POST {{baseUrl}}/api/quiz/generate
Content-Type: application/json

{
  "topic": "{{topic}}",
  "difficulty": "medium",
  "count": 5,
  "question_type": "single"
}

### Generate Quiz - Multi Choice
POST {{baseUrl}}/api/quiz/generate
Content-Type: application/json

{
  "topic": "{{topic}}",
  "difficulty": "hard",
  "count": 10,
  "question_type": "multi"
}

### Generate Quiz - Mixed
POST {{baseUrl}}/api/quiz/generate
Content-Type: application/json

{
  "topic": "{{topic}}",
  "difficulty": "easy",
  "count": 15,
  "question_type": "mixed"
}
```

---

## Debugging Tips

### Backend Debugging
```bash
# View logs with colors
docker compose logs -f quiz-api | sed 's/\\n/\n/g'

# Enter container for debugging
docker compose exec quiz-api python -c "from app.config import get_settings; print(get_settings().has_gemini)"

# Check memory usage
docker stats quiz-platform-api --no-stream
```

### Frontend Debugging
```bash
# View nginx logs
docker compose logs -f quiz-frontend

# Check built assets
docker compose exec quiz-frontend ls -la /usr/share/nginx/html/

# Rebuild only frontend
docker compose build --no-cache quiz-frontend
docker compose up -d quiz-frontend
```

### Network Debugging
```bash
# Check container networking
docker compose exec quiz-frontend ping quiz-api
docker compose exec quiz-api ping quiz-frontend

# Test internal API call
docker compose exec quiz-frontend wget -qO- http://quiz-api:8000/health
```

---

## Common Issues

### Port Conflicts
```bash
# Check what's using ports
sudo lsof -i :8000
sudo lsof -i :3000
sudo lsof -i :80
sudo lsof -i :443

# Kill conflicting processes
sudo kill -9 <PID>
```

### Permission Errors
```bash
# Fix Docker permissions
sudo chown -R $USER:$USER ~/quiz-platform
docker compose down -v
docker compose up -d --build
```

### Memory Issues
```bash
# Check available memory
free -h

# Adjust docker-compose.yml limits if needed
# Increase memory limits for quiz-api if OOM killed
```

---

## Useful Aliases (Add to ~/.bashrc or ~/.zshrc)

```bash
# Quiz Platform aliases
alias qp-up='docker compose up -d --build'
alias qp-down='docker compose down'
alias qp-logs='docker compose logs -f'
alias qp-ps='docker compose ps'
alias qp-restart='docker compose restart'
alias qp-rebuild='docker compose down && docker compose up -d --build'
alias qp-test-api='curl -X POST http://localhost:8000/api/quiz/generate -H "Content-Type: application/json" -d '"'"'{"topic":"test","difficulty":"easy","count":3,"question_type":"single"}'"'"''
```