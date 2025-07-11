# Google Scholar Profile Analyzer

A comprehensive web application for analyzing Google Scholar profiles with advanced statistics, authorship classification, and research area insights.

## Features

- **Statistical Analysis**: Citation trends, h-index progression, impact metrics
- **Authorship Classification**: Automatic separation of first-authored, corresponding, and student-authored papers
- **Research Area Analysis**: AI-powered classification of publications by research domains
- **Collaboration Networks**: Analysis of co-author relationships and collaboration patterns
- **Interactive Visualizations**: Charts, graphs, and network diagrams
- **Profile Comparison**: Side-by-side analysis of multiple researchers

## Tech Stack

### Frontend
- **Next.js 14** with TypeScript
- **Tailwind CSS** for styling
- **Chart.js/D3.js** for data visualization
- **React Hooks** for state management

### Backend
- **FastAPI** with Python 3.11
- **PostgreSQL** for relational data
- **Redis** for caching and sessions
- **SQLAlchemy** for database ORM
- **Beautiful Soup** for web scraping

### Infrastructure
- **Docker** containers
- **Docker Compose** for local development
- **PostgreSQL** database with optimized schemas
- **Redis** for caching and session management

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd google-scholar-analyzer
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development Setup

#### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

#### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Database Setup
```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d scholar_analyzer

# The schema is automatically loaded via Docker
```

## Project Structure

```
google-scholar-analyzer/
├── frontend/                 # Next.js React application
│   ├── src/
│   │   ├── app/             # App router pages
│   │   ├── components/      # React components
│   │   └── hooks/           # Custom React hooks
│   ├── package.json
│   └── Dockerfile
├── backend/                  # FastAPI Python application
│   ├── main.py              # FastAPI app and routes
│   ├── scholar_scraper.py   # Google Scholar scraping
│   ├── requirements.txt
│   └── Dockerfile
├── database/
│   └── schema.sql           # PostgreSQL database schema
├── docker-compose.yml       # Docker services configuration
└── README.md
```

## API Endpoints

### Core Endpoints
- `POST /api/scholar/import/{google_scholar_id}` - Import Google Scholar profile
- `GET /api/scholar/profile/{profile_id}` - Get profile data
- `GET /api/publications/{profile_id}` - Get publications
- `GET /api/analysis/{profile_id}/overview` - Get analysis overview
- `GET /api/analysis/{profile_id}/authorship` - Get authorship analysis

### Example Usage

```bash
# Import a profile
curl -X POST "http://localhost:8000/api/scholar/import/ABC123XYZ"

# Get analysis results
curl "http://localhost:8000/api/analysis/profile_ABC123XYZ/overview"
```

## Database Schema

### Key Tables
- **users**: User authentication and profiles
- **scholar_profiles**: Google Scholar profile data
- **publications**: Publication information and metrics
- **authorship_roles**: Author position classification
- **research_areas**: Hierarchical research domain taxonomy
- **citation_history**: Time-series citation data
- **analysis_results**: Cached analysis computations

## Features in Development

- [ ] Machine learning models for research area classification
- [ ] Advanced collaboration network analysis
- [ ] Integration with ResearchGate API
- [ ] Batch profile comparison tools
- [ ] Export to PDF reports
- [ ] Real-time citation tracking
- [ ] Email notifications for profile updates

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Important Notes

### Web Scraping Ethics
- This tool respects Google Scholar's robots.txt
- Implements rate limiting to avoid overwhelming servers
- For production use, consider using official APIs where available
- Always comply with terms of service and fair use policies

### Development Considerations
- Replace mock data with real implementations
- Add proper error handling and logging
- Implement user authentication and authorization
- Add comprehensive testing suite
- Configure production environment variables

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes. Users are responsible for complying with Google Scholar's terms of service and respecting rate limits when scraping data.