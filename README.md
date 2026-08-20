# Quiz Lab — Dynamic MCQ Practice Platform

A full-stack quiz platform that generates multiple-choice questions dynamically using AI. Supports both web scraping and LLM-based question generation with flexible quiz modes for practice and examination.

## Features

- **AI-Powered Generation**: Uses Google Gemini or OpenAI to generate contextual MCQs
- **Web Scraping Fallback**: Attempts to find existing questions via DuckDuckGo first
- **Flexible Configuration**: Choose topic, difficulty (Easy/Medium/Hard), question count (1-50), and type (Single/Multi/Mixed)
- **File Upload**: Import questions from text files with standard MCQ format
- **Two Quiz Modes**:
  - **Mock Quiz**: Flexible timing, no pressure, instant feedback on each question
  - **Exam Quiz**: AWS-style timed exam with strict rules, results only after submission
- **Interactive UI**:
  - Dark/light mode toggle
  - Real-time progress tracking
  - Question palette for navigation
  - Visual feedback (correct/incorrect/missed) — only after submission in Exam mode
  - AI explanation buttons (ChatGPT/Gemini deep-dive)
  - Summary scorecard with statistics
- **Dual Deployment**: Docker for home servers, AWS Lambda for serverless
- **Self-Hosted with Tailscale**: Secure access from any device on your Tailnet

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker (for containerized deployment)
- AWS CLI + SAM CLI (for serverless deployment)
- At least one LLM API key (Gemini or OpenAI)

### Local Development

1. **Clone and configure**:
   ```bash
   cd quiz-platform
   
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your API keys
   
   # Frontend
   cd ../frontend
   npm install
   ```

2. **Run backend** (from `backend/` directory):
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   
3. **Run frontend** (from `frontend/` directory):
   ```bash
   npm run dev
   ```
   
4. Open http://localhost:3000 in your browser

### Docker Deployment (Recommended for Home Server)

1. **Configure environment**:
   ```bash
   cd quiz-platform
   # Create .env file with your API keys
   cat > .env << EOF
   GEMINI_API_KEY=your_gemini_key
   OPENAI_API_KEY=your_openai_key
   LLM_PROVIDER=auto
   EOF
   ```

2. **Build and run**:
   ```bash
   docker compose up --build -d
   ```
   
3. Open http://localhost in your browser

**Resource Usage**: The Docker setup is optimized for low-spec home servers (~250MB RAM total).

### Build Steps (Production)

```bash
# Frontend build
cd frontend
npm run build
# Output in frontend/dist/

# Backend Docker build
cd ../backend
docker build -t quiz-api .

# Full stack build
cd ..
docker compose build
```

### Run Steps (Production)

```bash
# Start all services in background
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Restart specific service
docker compose restart quiz-api
```

---

## Exposing to Public via Tailscale (Home Server)

Since the home server runs on Tailscale, you can securely expose the app to all devices on your Tailnet without opening ports to the internet.

### Option 1: Tailscale Funnel (Easiest - HTTPS automatically)

```bash
# Start the app
docker compose up -d

# Expose port 80 (HTTP) or 443 (HTTPS) via Tailscale Funnel
# For HTTPS (recommended):
tailscale funnel 443

# For HTTP:
tailscale funnel 80
```

Your app will be available at: `https://<your-device>.<your-tailnet>.ts.net`

### Option 2: Tailscale Serve (Local network only)

```bash
# Serve on Tailscale IP (accessible only from devices on your Tailnet)
tailscale serve --https=443 --bg
# or HTTP
tailscale serve 80
```

Access at: `http://<tailscale-ip>` or `https://<tailscale-ip>`

### Option 3: Tailscale SSH + Cloudflare Tunnel (Public internet)

For public internet access without exposing your home IP:

```bash
# 1. Create Cloudflare Tunnel
cloudflared tunnel create quiz-platform

# 2. Configure tunnel (cloudflared.yml)
tunnel: <tunnel-id>
credentials-file: /path/to/credentials.json
ingress:
  - hostname: quiz.yourdomain.com
    service: http://localhost:80
  - service: http_status:404

# 3. Run tunnel
cloudflared tunnel run quiz-platform
```

### Tailscale Funnel + Custom Domain (Best of both)

```bash
# 1. Add custom domain to Tailscale
# In Tailscale admin console: DNS → Custom Domains → Add quiz.yourdomain.com

# 2. Run funnel on port 443
tailscale funnel 443

# 3. Your app is at https://quiz.yourdomain.com (works globally!)
```

### Verify Tailscale Exposure

```bash
# Check funnel status
tailscale funnel status

# Test from another device on tailnet
curl https://<your-device>.<your-tailnet>.ts.net/api/quiz/health
```

---

## AWS Lambda Deployment

1. **Install SAM CLI**:
   ```bash
   pip install aws-sam-cli
   aws sam --version
   ```

2. **Configure and deploy**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env or use SAM parameters
   
   sam deploy --guided
   ```
   
3. Follow the prompts. The API URL will be output after deployment.

**Note**: Set API keys via AWS Systems Manager Parameter Store or Lambda environment variables.

---

## Quiz Modes

### Mock Quiz (Practice Mode)
- **Timing**: Flexible — no timer, take as long as you need
- **Feedback**: Instant — after selecting an answer in single-select questions, correct/incorrect is shown immediately
- **Navigation**: Free — jump between questions anytime using palette
- **Answers**: Revealed immediately after selection (single-select) or on "Check Answer" (multi-select)
- **Best for**: Learning, concept reinforcement, casual practice

### Exam Quiz (Test Mode)
- **Timing**: Strict — AWS-style timer rules:
  - **AWS Certified Cloud Practitioner**: 90 minutes for 65 questions (~1.4 min/q)
  - **AWS Associate Exams**: 130 minutes for 65 questions (~2 min/q)
  - **AWS Professional/Specialty**: 170 minutes for 75 questions (~2.3 min/q)
  - **Custom**: Configure your own time per question
- **Feedback**: Delayed — no inline feedback during exam, all results shown only after submission
- **Navigation**: Restricted — can navigate but no answer checking until submit
- **Answers**: Hidden until final submission; correct answers revealed only in results
- **Proctoring**: Tab-switch/focus-loss warnings (configurable)
- **Auto-submit**: Exam submits automatically when timer expires
- **Best for**: Certification prep, timed practice, exam simulation

### Switching Modes
Select quiz mode in the configuration panel before generating questions. The mode persists until changed.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes* | - | Google Gemini API key |
| `OPENAI_API_KEY` | No | - | OpenAI fallback key |
| `LLM_PROVIDER` | No | `auto` | Provider: `gemini`, `openai`, or `auto` |
| `LLM_MODEL` | No | `gemini-3.6-flash` | Model override |
| `CACHE_TTL_SECONDS` | No | `3600` | Response cache duration |
| `RATE_LIMIT_PER_MINUTE` | No | `10` | API rate limit |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `CORS_ORIGINS` | No | `*` | Comma-separated allowed origins |

*At least one LLM API key is required.

### LLM Provider Selection

- `auto` (default): Try Gemini first, fall back to OpenAI
- `gemini`: Use Google Gemini only
- `openai`: Use OpenAI only

---

## API Reference

### POST /api/quiz/generate

Generate a quiz based on parameters.

**Request**:
```json
{
  "topic": "AWS S3 storage fundamentals",
  "difficulty": "medium",
  "count": 10,
  "question_type": "mixed"
}
```

**Response**:
```json
{
  "success": true,
  "questions": [
    {
      "id": "1",
      "type": "single",
      "question": "What is the maximum size of an S3 object?",
      "options": {
        "A": "5 TB",
        "B": "5 GB",
        "C": "1 TB",
        "D": "500 GB"
      },
      "correct_answers": ["A"],
      "explanation": "S3 objects can range from 0 to 5 TB..."
    }
  ],
  "metadata": {
    "provider": "gemini",
    "model": "gemini-3.6-flash",
    "source": "llm",
    "cached": false,
    "generated_at": "2024-01-15T10:30:00Z"
  }
}
```

### GET /api/health

Check API and provider status.

**Response**:
```json
{
  "status": "healthy",
  "providers": {
    "gemini": true,
    "openai": false
  },
  "cache": {
    "size": 42,
    "hits": 128,
    "misses": 42
  }
}
```

---

## File Upload Format

Upload text files with questions in standard MCQ format:

```
Q1. What is the maximum size of an S3 object?
A) 5 TB
B) 5 GB
C) 1 TB
D) 500 GB
Answer: A

Q2. Which S3 storage class is most cost-effective for infrequent access?
A) Standard
B) Intelligent-Tiering
C) Standard-IA
D) One Zone-IA
Answer: C
Explanation: Standard-IA is designed for data accessed less than once a month.

Q3. Select all S3 features that provide security:
A) Server-side encryption
B) Bucket policies
C) Transfer Acceleration
D) Object Lock
Answer: A, B, D
```

---

## Project Structure

```
quiz-platform/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + Mangum handler
│   │   ├── config.py            # Pydantic settings
│   │   ├── routes/
│   │   │   └── quiz.py          # API endpoints
│   │   ├── services/
│   │   │   ├── llm/             # LLM providers (Gemini, OpenAI)
│   │   │   ├── scraping/        # Web scraping (DuckDuckGo)
│   │   │   ├── cache.py         # Response caching
│   │   │   └── generator.py     # Quiz orchestrator
│   │   ├── models/              # Pydantic models
│   │   └── utils/               # Helpers
│   ├── tests/                   # Test suite
│   ├── requirements.txt
│   ├── Dockerfile
│   └── template.yaml            # AWS SAM template
├── frontend/
│   ├── src/
│   │   ├── index.html           # HTML template
│   │   ├── main.js              # Entry point
│   │   ├── api/                 # API client
│   │   ├── components/          # UI components
│   │   ├── utils/               # Utilities
│   │   └── styles/              # CSS
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── nginx.conf
└── README.md
```

---

## Development

### Running Tests

**Backend**:
```bash
cd backend
pip install -r requirements-dev.txt
pytest -v
```

**Frontend**:
```bash
cd frontend
npm run test
```

### Building for Production

**Frontend**:
```bash
cd frontend
npm run build
# Output in frontend/dist/
```

**Backend Docker**:
```bash
cd backend
docker build -t quiz-api .
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Vite)                       │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Quiz     │  │ Quiz         │  │ ProgressBar / Summary │ │
│  │ Config   │──│ Renderer     │──│ Cards                 │ │
│  └──────────┘  └──────────────┘  └───────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP POST /api/quiz/generate
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │ Routes   │──│ Generator│──│ Cache (TTL)              │  │
│  │ /quiz    │  │ Service  │  └──────────────────────────┘  │
│  └──────────┘  └────┬─────┘                                  │
│                     │                                        │
│         ┌───────────┴───────────┐                           │
│         ▼                       ▼                           │
│  ┌─────────────┐        ┌─────────────┐                    │
│  │ Scraper     │        │ LLM Factory │                    │
│  │ (DDG)       │        │             │                    │
│  └─────────────┘        └──────┬──────┘                    │
│                                │                            │
│                    ┌───────────┴───────────┐               │
│                    ▼                       ▼               │
│             ┌──────────┐           ┌──────────┐           │
│             │ Gemini   │           │ OpenAI   │           │
│             │ Provider │           │ Provider │           │
│             └──────────┘           └──────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## Tailscale Network Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Tailnet (Private)                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Laptop     │    │  Phone      │    │  Tablet     │     │
│  │  (TS IP)    │    │  (TS IP)    │    │  (TS IP)    │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Home Server (Docker)                   │   │
│  │  ┌─────────┐  ┌─────────┐  ┌────────────────────┐  │   │
│  │  │ Nginx   │──│ Frontend│──│ Backend (FastAPI)  │  │   │
│  │  │ Proxy   │  │ (Nginx) │  │ Port 8000          │  │   │
│  │  └─────────┘  └─────────┘  └────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │ Tailscale   │    │ Tailscale   │    │ Cloudflare  │    │
│  │ Funnel      │    │ Serve       │    │ Tunnel      │    │
│  │ (Public)    │    │ (Tailnet)   │    │ (Public)    │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## License

MIT License - feel free to use for personal or commercial projects.

## Contributing

Contributions welcome! Please read our contributing guidelines and submit pull requests to the main repository.

## Acknowledgments

- Google Gemini API for primary LLM generation
- OpenAI API for fallback generation
- DuckDuckGo for web scraping
- Tailwind CSS for styling
- Vite for fast frontend builds
- Tailscale for secure networking