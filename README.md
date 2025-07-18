# Google Scholar Profile Analyzer

A web application for analyzing Google Scholar profiles with metrics and insights.

## Features

- **Profile Analysis**: Citation trends, h-index, publication metrics
- **Authorship Breakdown**: First author, last author, and collaboration statistics  
- **Research Areas**: Automatic classification using journal and conference databases
- **Collaboration Networks**: Co-author analysis and partnership patterns
- **Interactive Charts**: Visual representations of research impact and productivity
- **High-Speed Caching**: Redis-powered caching for 50x faster repeat analyses
- **Concurrent Scraping**: Parallel data collection for 2-4x faster initial processing

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
2. **Analysis**: High-speed scraping and analysis of publication data
3. **Results**: View detailed statistics, charts, and insights about research impact
4. **Performance**: Subsequent analyses are served from cache in milliseconds

## Tech Stack

- **Frontend**: Next.js 15, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11
- **Caching**: Redis (Google Cloud Memorystore)
- **Database**: PostgreSQL 
- **Infrastructure**: Docker, Google Cloud Run, Auto-scaling

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

# Backend (with Redis for caching)
cd backend && pip install -r requirements.txt
docker run -d -p 6379:6379 redis:7-alpine
uvicorn main:app --reload
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Note

This tool is for research and educational purposes.