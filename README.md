# Quiz Lab — Dynamic MCQ Practice Platform

A full-stack quiz platform that generates multiple-choice questions dynamically using AI. Supports both web scraping and LLM-based question generation with dual deployment options.

## Features

- **AI-Powered Generation**: Uses Google Gemini or OpenAI to generate contextual MCQs
- **Web Scraping Fallback**: Attempts to find existing questions via DuckDuckGo first
- **Flexible Configuration**: Choose topic, difficulty (Easy/Medium/Hard), question count (1-50), and type (Single/Multi/Mixed)
- **File Upload**: Import questions from text files with standard MCQ format
- **Interactive UI**: 
  - Dark/light mode toggle
  - Real-time progress tracking
  - Question palette for navigation
  - Visual feedback (correct/incorrect/missed)
  - AI explanation buttons (ChatGPT/Gemini deep-dive)
  - Summary scorecard with statistics
- **Dual Deployment**: Docker for home servers, AWS Lambda for serverless

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

### Docker Deployment

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
   docker-compose up --build
   ```
   
3. Open http://localhost in your browser

**Resource Usage**: The Docker setup is optimized for low-spec home servers (~150MB RAM total).

### AWS Lambda Deployment

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

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes* | - | Google Gemini API key |
| `OPENAI_API_KEY` | No | - | OpenAI fallback key |
| `LLM_PROVIDER` | No | `auto` | Provider: `gemini`, `openai`, or `auto` |
| `LLM_MODEL` | No | `gemini-1.5-flash` | Model override |
| `CACHE_TTL_SECONDS` | No | `3600` | Response cache duration |
| `RATE_LIMIT_PER_MINUTE` | No | `10` | API rate limit |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |

*At least one LLM API key is required.

### LLM Provider Selection

- `auto` (default): Try Gemini first, fall back to OpenAI
- `gemini`: Use Google Gemini only
- `openai`: Use OpenAI only

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
    "model": "gemini-1.5-flash",
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
