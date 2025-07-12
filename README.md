# Google Scholar Profile Analyzer

A web application for analyzing Google Scholar profiles with comprehensive metrics and insights.

## Features

- **Profile Analysis**: Citation trends, h-index, publication metrics
- **Authorship Breakdown**: First author, last author, and collaboration statistics  
- **Research Areas**: Automatic classification using journal and conference databases
- **Collaboration Networks**: Co-author analysis and partnership patterns
- **Interactive Charts**: Visual representations of research impact and productivity

## Quick Start

### Option 1: Use Live Version
Visit [https://scholar-frontend-771064042567.us-central1.run.app](https://scholar-frontend-771064042567.us-central1.run.app) and enter any Google Scholar profile URL.

### Option 2: Run Locally

**Prerequisites**: Docker and Docker Compose

```bash
# Clone and start
git clone https://github.com/zhangxiany-tamu/google-scholar-analytics.git
cd google-scholar-analytics
docker-compose up -d

# Access at http://localhost:3000
```

## How It Works

1. **Import**: Paste a Google Scholar profile URL
2. **Analysis**: The system scrapes publication data and performs analysis
3. **Results**: View detailed statistics, charts, and insights about research impact

## Tech Stack

- **Frontend**: Next.js 15, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL + Redis
- **Infrastructure**: Docker, Google Cloud Run

## Project Structure

```
├── frontend/          # Next.js application
├── backend/           # FastAPI server
├── database/          # Schema and migrations
└── docker-compose.yml # Local development setup
```

## Development

```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend  
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
```

## API Usage

```bash
# Import a profile
curl -X POST "https://scholar-backend-771064042567.us-central1.run.app/api/scholar/import/{profile_id}"

# Get analysis
curl "https://scholar-backend-771064042567.us-central1.run.app/api/analysis/{profile_id}/complete"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Note

This tool is for research and educational purposes.