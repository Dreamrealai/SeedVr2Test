# Deployment Guide

## Prerequisites

- RunPod account with API key
- AWS account (for S3 storage) or Cloudflare R2
- Docker and Docker Compose installed
- Domain name (optional, for production)

## RunPod Setup

### 1. Build and Push Docker Image

```bash
# Build the Docker image
cd runpod
docker build -t your-registry/seedvr2-handler:latest .

# Push to your container registry
docker push your-registry/seedvr2-handler:latest
```

### 2. Create RunPod Serverless Endpoint

1. Log in to RunPod dashboard
2. Go to Serverless > Endpoints
3. Click "New Endpoint"
4. Configure:
   - Name: `seedvr2-7b`
   - Container Image: `your-registry/seedvr2-handler:latest`
   - GPU Type: H100 80GB
   - Min Workers: 0
   - Max Workers: 4
   - Idle Timeout: 60 seconds
   - Environment Variables:
     - `S3_BUCKET`: your-bucket-name
     - `AWS_ACCESS_KEY_ID`: your-key
     - `AWS_SECRET_ACCESS_KEY`: your-secret

5. Copy the Endpoint ID

### 3. Configure Environment

Update `.env` with your RunPod endpoint:

```
RUNPOD_API_KEY=your_api_key
RUNPOD_ENDPOINT_ID=your_endpoint_id
```

## Backend Deployment

### Option 1: Railway/Render

1. Create a new project
2. Connect your GitHub repository
3. Set environment variables from `.env.example`
4. Deploy

### Option 2: VPS (Ubuntu)

```bash
# Install dependencies
sudo apt update
sudo apt install python3.10 python3.10-venv nginx certbot

# Clone repository
git clone https://github.com/yourusername/seedvr2-runpod-gui.git
cd seedvr2-runpod-gui

# Set up Python environment
python3.10 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Set up systemd service
sudo cp scripts/seedvr2-api.service /etc/systemd/system/
sudo systemctl enable seedvr2-api
sudo systemctl start seedvr2-api

# Configure Nginx
sudo cp scripts/nginx.conf /etc/nginx/sites-available/seedvr2
sudo ln -s /etc/nginx/sites-available/seedvr2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Set up SSL with Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

## Frontend Deployment

### Option 1: Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Build and deploy:
   ```bash
   cd frontend
   npm run build
   vercel --prod
   ```

### Option 2: Netlify

1. Build the frontend:
   ```bash
   cd frontend
   npm run build
   ```
2. Drag and drop `build` folder to Netlify

### Option 3: Self-hosted with Nginx

```bash
# Build frontend
cd frontend
npm run build

# Copy to web root
sudo cp -r build/* /var/www/seedvr2/

# Configure Nginx (see scripts/nginx-frontend.conf)
```

## Database Setup

### PostgreSQL

```bash
# Create database
sudo -u postgres psql
CREATE DATABASE seedvr2;
CREATE USER seedvr2_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE seedvr2 TO seedvr2_user;
\q

# Run migrations
cd backend
alembic upgrade head
```

### Redis

```bash
# Install Redis
sudo apt install redis-server

# Start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

## Production Checklist

- [ ] Set strong passwords for all services
- [ ] Enable HTTPS on all endpoints
- [ ] Set up monitoring (e.g., Datadog, New Relic)
- [ ] Configure backups for database
- [ ] Set up error tracking (e.g., Sentry)
- [ ] Configure rate limiting
- [ ] Set up CDN for static assets
- [ ] Enable CORS only for your domain
- [ ] Set up health checks
- [ ] Configure auto-scaling for RunPod

## Monitoring

### RunPod Monitoring

Monitor your endpoint at: https://runpod.io/console/serverless

Key metrics:
- Active workers
- Queue length
- Average processing time
- Error rate

### Application Monitoring

Set up monitoring for:
- API response times
- Error rates
- Video processing success rate
- Storage usage
- Cost per video

## Cost Optimization

1. **Auto-scaling**: Set min workers to 0 to avoid idle costs
2. **Storage**: Clean up processed videos after 24 hours
3. **Caching**: Cache model weights in RunPod
4. **Batching**: Process multiple videos per GPU when possible

## Troubleshooting

### Common Issues

1. **RunPod timeout**: Increase timeout in endpoint settings
2. **Out of memory**: Reduce batch size or video resolution
3. **Slow uploads**: Use multipart uploads for large videos
4. **Model loading slow**: Ensure model is cached in Docker image

### Debug Commands

```bash
# Check RunPod logs
curl -X GET "https://api.runpod.ai/v2/{endpoint_id}/logs" \
  -H "Authorization: Bearer {api_key}"

# Test endpoint
curl -X POST "https://api.runpod.ai/v2/{endpoint_id}/run" \
  -H "Authorization: Bearer {api_key}" \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": true}}'
```