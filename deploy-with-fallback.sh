#!/bin/bash

# Safe deployment script with fallback capability
# Usage: ./deploy-with-fallback.sh [optimized|original|rollback]

set -e

PROJECT_ID="curious-kingdom-465619-v1"
REGION="us-central1"
SERVICE_NAME="scholar-backend"

# Get current version for rollback
CURRENT_VERSION=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(spec.template.metadata.labels.version)' 2>/dev/null || echo "v1.0.0")

echo "🚀 Starting safe deployment..."
echo "📍 Current version: $CURRENT_VERSION"

DEPLOYMENT_TYPE=${1:-optimized}

case $DEPLOYMENT_TYPE in
  "optimized")
    echo "🔧 Deploying OPTIMIZED version..."
    NEW_VERSION="v1-1-0-optimized"
    
    # Build optimized version
    echo "🏗️ Building optimized backend..."
    cd ./backend
    # Use Cloud Build to build with custom Dockerfile
    cat > cloudbuild-temp.yaml << EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-f', 'Dockerfile.optimized', '-t', 'gcr.io/$PROJECT_ID/scholar-backend:$NEW_VERSION', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/scholar-backend:$NEW_VERSION']
EOF
    gcloud builds submit . --config=cloudbuild-temp.yaml
    rm cloudbuild-temp.yaml
    cd ..
    
    # Deploy with new version label
    echo "🚀 Deploying optimized backend..."
    gcloud run deploy $SERVICE_NAME \
      --image gcr.io/$PROJECT_ID/scholar-backend:$NEW_VERSION \
      --region $REGION \
      --platform managed \
      --allow-unauthenticated \
      --port 8000 \
      --memory 4Gi \
      --cpu 2 \
      --max-instances 10 \
      --min-instances 1 \
      --set-env-vars "DATABASE_URL=postgresql://postgres:password@/postgres?host=/cloudsql/$PROJECT_ID:$REGION:scholar-db,REDIS_URL=redis://\${_REDIS_HOST}:6379" \
      --add-cloudsql-instances $PROJECT_ID:$REGION:scholar-db \
      --tag optimized \
      --update-labels version=$NEW_VERSION
    ;;
    
  "original")
    echo "📦 Deploying ORIGINAL version..."
    NEW_VERSION="v1-0-0-original"
    
    # Build original version
    echo "🏗️ Building original backend..."
    gcloud builds submit ./backend --tag gcr.io/$PROJECT_ID/scholar-backend:$NEW_VERSION
    
    # Deploy original version
    echo "🚀 Deploying original backend..."
    gcloud run deploy $SERVICE_NAME \
      --image gcr.io/$PROJECT_ID/scholar-backend:$NEW_VERSION \
      --region $REGION \
      --platform managed \
      --allow-unauthenticated \
      --port 8000 \
      --memory 4Gi \
      --cpu 2 \
      --max-instances 10 \
      --min-instances 1 \
      --set-env-vars "DATABASE_URL=postgresql://postgres:password@/postgres?host=/cloudsql/$PROJECT_ID:$REGION:scholar-db,REDIS_URL=redis://\${_REDIS_HOST}:6379" \
      --add-cloudsql-instances $PROJECT_ID:$REGION:scholar-db \
      --tag original \
      --update-labels version=$NEW_VERSION
    ;;
    
  "rollback")
    echo "⏪ Rolling back to previous version..."
    
    # Get previous revision
    PREVIOUS_REVISION=$(gcloud run revisions list --service=$SERVICE_NAME --region=$REGION --limit=2 --format='value(metadata.name)' | tail -n 1)
    
    if [ -z "$PREVIOUS_REVISION" ]; then
      echo "❌ No previous revision found for rollback"
      exit 1
    fi
    
    echo "📍 Rolling back to revision: $PREVIOUS_REVISION"
    
    # Update traffic to previous revision
    gcloud run services update-traffic $SERVICE_NAME \
      --region=$REGION \
      --to-revisions=$PREVIOUS_REVISION=100
    ;;
    
  *)
    echo "❌ Invalid deployment type. Use: optimized, original, or rollback"
    exit 1
    ;;
esac

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo "✅ Deployment completed!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📊 Version deployed: $NEW_VERSION"
echo ""
echo "🔍 Test the service:"
echo "   curl $SERVICE_URL/health"
echo ""
echo "⏪ To rollback if issues occur:"
echo "   ./deploy-with-fallback.sh rollback"
echo ""

# Test deployment
echo "🧪 Testing deployment..."
sleep 5

if curl -s "$SERVICE_URL/health" > /dev/null; then
  echo "✅ Health check passed!"
else
  echo "⚠️ Health check failed - consider rolling back"
fi