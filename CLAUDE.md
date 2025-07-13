# Claude Code Instructions for Scholar Analytics Project

## Critical Deployment Notes

### Frontend Deployment Requirements

**CRITICAL**: When deploying the frontend, you MUST set `NEXT_PUBLIC_API_URL` at BUILD time, not runtime. Next.js requires environment variables starting with `NEXT_PUBLIC_` to be available during the build process.

#### Correct Deployment Process:

1. **Use the custom Dockerfile**: Always use `Dockerfile.fixed` for frontend builds
2. **Build with Cloud Build config**: Use `cloudbuild-fixed.yaml` for proper Docker build
3. **Backend API URL**: `NEXT_PUBLIC_API_URL=https://scholar-backend-z3scmppagq-uc.a.run.app`

#### Commands for Correct Deployment:

```bash
# Build frontend with API URL
cd frontend
gcloud builds submit . --config=cloudbuild-fixed.yaml

# Deploy with proper image
gcloud run deploy scholar-frontend \
  --image gcr.io/curious-kingdom-465619-v1/scholar-frontend:v2.0.1-with-api-url \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --port 3000 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 5 \
  --min-instances 1 \
  --update-labels version=v2-0-1-fixed
```

### Common Issues and Solutions

#### "Failed to fetch" Error
- **Cause**: NEXT_PUBLIC_API_URL not set at build time
- **Solution**: Redeploy using `Dockerfile.fixed` with Cloud Build

#### Cold Start Issues
- **Frontend**: Ensure min-instances=1 is set
- **Backend**: Ensure min-instances=1 is set
- **Traffic Routing**: Check traffic goes to correct revision with min-instances

#### Mobile Layout Issues
- **Location**: `/frontend/src/app/analysis/[profileId]/page.tsx` lines 750-770
- **Fix**: Use `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4` and `flex flex-col` layout

### Project Structure

```
/Users/xianyangzhang/My Drive/Google Scholar Profile Analyzer/
├── frontend/
│   ├── Dockerfile.fixed          # Use this for builds with API URL
│   ├── cloudbuild-fixed.yaml     # Use this for Cloud Build
│   └── src/app/analysis/[profileId]/page.tsx  # Author cards layout
├── backend/
└── CLAUDE.md                     # This file
```

### Service URLs
- **Frontend**: https://scholar-frontend-771064042567.us-central1.run.app
- **Backend**: https://scholar-backend-z3scmppagq-uc.a.run.app

### Version Management
- Update `package.json` version when making changes
- Use proper version labels in deployments (replace dots with dashes: v2-0-1)

## Testing Commands

```bash
# Test backend directly
curl -X POST https://scholar-backend-z3scmppagq-uc.a.run.app/api/scholar/import/mXSv_1UAAAAJ

# Check current revision
gcloud run services describe scholar-frontend --region=us-central1 --format="value(status.traffic[].revisionName)"

# List revisions
gcloud run revisions list --service=scholar-frontend --region=us-central1
```

## GitHub Upload Instructions

### For Code Updates
When uploading to GitHub, follow these guidelines:

1. **README.md**: Keep it simple, concise, and low-key - avoid mentioning AI assistance
2. **Commit Messages**: Use standard format without AI attribution
3. **Files to Include**: All deployment configs and optimizations
4. **Files to Exclude**: Temporary build files, logs

### Standard Commit Process
```bash
# Add all relevant changes
git add frontend/ backend/ *.md *.yaml *.sh

# Commit with descriptive message
git commit -m "Update mobile layout and improve deployment process"

# Push to GitHub
git push origin master
```

## Remember: Always use Dockerfile.fixed and cloudbuild-fixed.yaml for frontend deployments!