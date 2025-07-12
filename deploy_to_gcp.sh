#!/bin/bash

# Google Cloud Platform Deployment Script for Scholar Profile Analyzer
# Project: curious-kingdom-465619-v1

set -e

PROJECT_ID="curious-kingdom-465619-v1"
REGION="us-central1"

echo "🚀 Starting deployment to Google Cloud Platform..."
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"

# Set the project
gcloud config set project $PROJECT_ID

# Check if Redis instance is ready
echo "📡 Checking Redis instance status..."
REDIS_STATUS=$(gcloud redis instances describe redis-cache --region=$REGION --format="value(state)" 2>/dev/null || echo "NOT_FOUND")

if [ "$REDIS_STATUS" != "READY" ]; then
    echo "⚠️  Redis instance not ready. Current status: $REDIS_STATUS"
    echo "🔄 Creating Redis instance if needed..."
    
    if [ "$REDIS_STATUS" = "NOT_FOUND" ]; then
        gcloud redis instances create redis-cache \
            --size=1 \
            --region=$REGION \
            --redis-version=redis_7_0 \
            --network=default
    fi
    
    echo "⏳ Waiting for Redis instance to be ready..."
    while [ "$REDIS_STATUS" != "READY" ]; do
        sleep 10
        REDIS_STATUS=$(gcloud redis instances describe redis-cache --region=$REGION --format="value(state)" 2>/dev/null || echo "CREATING")
        echo "Redis status: $REDIS_STATUS"
    done
fi

# Get Redis host IP
REDIS_HOST=$(gcloud redis instances describe redis-cache --region=$REGION --format="value(host)")
echo "✅ Redis instance ready at: $REDIS_HOST"

# Update environment variables with actual Redis host
echo "🔧 Updating deployment configuration with Redis host..."

# Deploy using Cloud Build
echo "🏗️  Starting Cloud Build deployment..."
gcloud builds submit --config=cloudbuild.yaml \
    --substitutions=_REDIS_HOST=$REDIS_HOST

echo "✅ Deployment completed!"
echo ""
echo "🌐 Your services should be available at:"
echo "Backend: https://scholar-backend-$(echo $PROJECT_ID | cut -d'-' -f3)-uc.a.run.app"
echo "Frontend: https://scholar-frontend-$(echo $PROJECT_ID | cut -d'-' -f3)-uc.a.run.app"
echo ""
echo "📊 To check service status:"
echo "gcloud run services list --region=$REGION"