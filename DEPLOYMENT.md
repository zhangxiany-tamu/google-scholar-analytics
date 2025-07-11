# Google Cloud Deployment Guide

## Project Information
- **Project ID**: curious-kingdom-465619-v1
- **Project Number**: 771064042567
- **Recommended Region**: us-central1

## Prerequisites

1. **Google Cloud CLI**: Ensure you have the Google Cloud CLI installed and authenticated
   ```bash
   gcloud auth login
   gcloud config set project curious-kingdom-465619-v1
   ```

2. **Docker**: Required for building container images
3. **Billing**: Ensure billing is enabled for your Google Cloud project

## Deployment Options

### Option 1: Automated Deployment (Recommended)

Run the automated deployment script:

```bash
./deploy.sh
```

This script will:
- Enable required Google Cloud APIs
- Create Cloud SQL PostgreSQL instance
- Build and deploy both backend and frontend to Cloud Run
- Set up proper environment variables and database connections

### Option 2: Manual Cloud Run Deployment

#### Step 1: Enable APIs
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com
```

#### Step 2: Create Cloud SQL Database
```bash
gcloud sql instances create scholar-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=us-central1

gcloud sql databases create scholar_db --instance=scholar-db
gcloud sql users set-password postgres --instance=scholar-db --password=your_password
```

#### Step 3: Deploy Backend
```bash
gcloud builds submit ./backend --tag gcr.io/curious-kingdom-465619-v1/scholar-backend

gcloud run deploy scholar-backend \
  --image gcr.io/curious-kingdom-465619-v1/scholar-backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --add-cloudsql-instances curious-kingdom-465619-v1:us-central1:scholar-db
```

#### Step 4: Deploy Frontend
```bash
gcloud builds submit ./frontend --tag gcr.io/curious-kingdom-465619-v1/scholar-frontend

gcloud run deploy scholar-frontend \
  --image gcr.io/curious-kingdom-465619-v1/scholar-frontend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 3000 \
  --memory 1Gi
```

### Option 3: App Engine Deployment

#### Deploy Backend
```bash
cd backend
gcloud app deploy app.yaml
```

#### Deploy Frontend
```bash
cd frontend
gcloud app deploy app.yaml
```

## Architecture

### Cloud Run (Recommended)
- **Backend**: FastAPI application with PostgreSQL database
- **Frontend**: Next.js application
- **Database**: Cloud SQL PostgreSQL
- **Scaling**: Automatic based on traffic
- **Cost**: Pay-per-use, very cost-effective

### App Engine
- **Backend**: Standard environment with Python 3.9
- **Frontend**: Standard environment with Node.js 18
- **Database**: Cloud SQL PostgreSQL
- **Scaling**: Automatic scaling with configurable limits

## Environment Variables

### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection (optional, for caching)

### Frontend
- `NEXT_PUBLIC_API_URL`: Backend API URL

## Monitoring and Logs

### View Logs
```bash
# Cloud Run logs
gcloud logs tail --service=scholar-backend
gcloud logs tail --service=scholar-frontend

# App Engine logs
gcloud app logs tail -s backend
gcloud app logs tail -s frontend
```

### Monitor Performance
- Visit Google Cloud Console → Cloud Run/App Engine
- Monitor CPU, memory, and request metrics
- Set up alerts for high error rates or latency

## Cost Optimization

### Cloud Run
- **Free Tier**: 2 million requests per month
- **Estimated Cost**: $5-20/month for moderate usage
- **Scaling**: Scales to zero when not in use

### Cloud SQL
- **Free Tier**: db-f1-micro instance
- **Estimated Cost**: $7-15/month
- **Optimization**: Consider Cloud SQL Proxy for connection pooling

## Security

1. **Database Security**:
   - Private IP for Cloud SQL
   - Strong passwords
   - Regular backups

2. **Application Security**:
   - HTTPS enforced
   - Environment variables for secrets
   - IAM roles and permissions

## Troubleshooting

### Common Issues

1. **Build Failures**:
   - Check Dockerfile syntax
   - Verify dependencies in requirements.txt/package.json

2. **Database Connection**:
   - Ensure Cloud SQL instance is running
   - Verify connection string format
   - Check IAM permissions

3. **Frontend API Calls**:
   - Verify NEXT_PUBLIC_API_URL is set correctly
   - Check CORS settings in backend

### Debug Commands
```bash
# Check service status
gcloud run services list

# View service details
gcloud run services describe scholar-backend --region=us-central1

# Check recent deployments
gcloud run revisions list --service=scholar-backend --region=us-central1
```

## Updating the Application

1. **Update code** in your local repository
2. **Push to GitHub** (optional)
3. **Redeploy** using the deployment script:
   ```bash
   ./deploy.sh
   ```

Or manually rebuild and deploy:
```bash
gcloud builds submit ./backend --tag gcr.io/curious-kingdom-465619-v1/scholar-backend
gcloud run deploy scholar-backend --image gcr.io/curious-kingdom-465619-v1/scholar-backend --region us-central1
``` 