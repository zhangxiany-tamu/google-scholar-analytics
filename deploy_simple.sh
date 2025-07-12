#!/bin/bash

# Simple deployment script for immediate deployment
# This will deploy without Redis initially, cache will be disabled until Redis is ready

set -e

PROJECT_ID="curious-kingdom-465619-v1"
REGION="us-central1"

echo "🚀 Starting simple deployment to Google Cloud Platform..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Set the project
gcloud config set project $PROJECT_ID

# Build and push images
echo "🏗️  Building Docker images..."

# Build backend
docker build -t gcr.io/$PROJECT_ID/scholar-backend:latest ./backend
docker push gcr.io/$PROJECT_ID/scholar-backend:latest

# Build frontend  
docker build -t gcr.io/$PROJECT_ID/scholar-frontend:latest ./frontend
docker push gcr.io/$PROJECT_ID/scholar-frontend:latest

# Deploy backend to Cloud Run
echo "🚀 Deploying backend..."
gcloud run deploy scholar-backend \
    --image=gcr.io/$PROJECT_ID/scholar-backend:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --port=8000 \
    --memory=4Gi \
    --cpu=2 \
    --max-instances=10 \
    --set-env-vars="REDIS_URL=redis://localhost:6379"

# Get backend URL
BACKEND_URL=$(gcloud run services describe scholar-backend --region=$REGION --format="value(status.url)")
echo "✅ Backend deployed at: $BACKEND_URL"

# Deploy frontend to Cloud Run
echo "🚀 Deploying frontend..."
gcloud run deploy scholar-frontend \
    --image=gcr.io/$PROJECT_ID/scholar-frontend:latest \
    --region=$REGION \
    --platform=managed \
    --allow-unauthenticated \
    --port=3000 \
    --memory=1Gi \
    --cpu=1 \
    --max-instances=5 \
    --set-env-vars="NEXT_PUBLIC_API_URL=$BACKEND_URL"

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe scholar-frontend --region=$REGION --format="value(status.url)")

echo "✅ Deployment completed!"
echo ""
echo "🌐 Your application is available at:"
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
echo ""
echo "⚠️  Note: Redis caching is disabled until Redis instance is ready."
echo "   Run 'gcloud redis instances list --region=$REGION' to check Redis status."