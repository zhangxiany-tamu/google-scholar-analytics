#!/bin/bash

# Google Scholar Profile Analyzer - Google Cloud Deployment Script
# Project: curious-kingdom-465619-v1

echo "🚀 Starting Google Scholar Profile Analyzer deployment..."

# Set project configuration
gcloud config set project curious-kingdom-465619-v1

# Enable required APIs
echo "📋 Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sql-component.googleapis.com
gcloud services enable appengine.googleapis.com
gcloud services enable container.googleapis.com

# Create Cloud SQL instance (if not exists)
echo "🗄️ Setting up Cloud SQL database..."
gcloud sql instances create scholar-db \
  --database-version=POSTGRES_13 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --storage-type=SSD \
  --storage-size=10GB \
  --backup-start-time=03:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=04 \
  --maintenance-release-channel=production \
  --deletion-protection || echo "Database instance already exists"

# Create database
gcloud sql databases create scholar_db --instance=scholar-db || echo "Database already exists"

# Set database password
gcloud sql users set-password postgres --instance=scholar-db --password=scholar_password_2024

# Option 1: Deploy using Cloud Run (Recommended)
echo "🐳 Deploying to Cloud Run..."

# Build and deploy backend
gcloud builds submit ./backend --tag gcr.io/curious-kingdom-465619-v1/scholar-backend

gcloud run deploy scholar-backend \
  --image gcr.io/curious-kingdom-465619-v1/scholar-backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8000 \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "DATABASE_URL=postgresql://postgres:scholar_password_2024@/scholar_db?host=/cloudsql/curious-kingdom-465619-v1:us-central1:scholar-db" \
  --add-cloudsql-instances curious-kingdom-465619-v1:us-central1:scholar-db

# Get backend URL
BACKEND_URL=$(gcloud run services describe scholar-backend --region=us-central1 --format='value(status.url)')
echo "Backend deployed at: $BACKEND_URL"

# Build and deploy frontend
gcloud builds submit ./frontend --tag gcr.io/curious-kingdom-465619-v1/scholar-frontend

gcloud run deploy scholar-frontend \
  --image gcr.io/curious-kingdom-465619-v1/scholar-frontend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 3000 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 5 \
  --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL"

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe scholar-frontend --region=us-central1 --format='value(status.url)')

echo "✅ Deployment completed successfully!"
echo "🌐 Frontend URL: $FRONTEND_URL"
echo "🔗 Backend URL: $BACKEND_URL"
echo ""
echo "📊 You can now access your Google Scholar Profile Analyzer at:"
echo "   $FRONTEND_URL" 