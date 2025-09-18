# CBM Analytics - Deployment Guide

This guide covers deploying the CBM Analytics application in various environments.

## Quick Start (Development)

```bash
# Clone the repository
git clone <repository-url>
cd cbm-analytics

# Start the application
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Production Deployment

### 1. Environment Configuration

Create a production `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - MAX_UPLOAD_SIZE=52428800  # 50MB
      - CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
    volumes:
      - /tmp/uploads:/tmp/uploads
    command: gunicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
    restart: unless-stopped

  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "3000:80"
    environment:
      - REACT_APP_API_URL=https://api.yourdomain.com
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

### 2. Production Frontend Dockerfile

Create `frontend/Dockerfile.prod`:

```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 3. Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:80;
    }

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # API routes
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # File upload settings
            client_max_body_size 50M;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # Frontend routes
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### 4. SSL Certificate Setup

```bash
# Using Let's Encrypt (recommended)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to ssl directory
mkdir ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/key.pem
```

### 5. Deploy to Production

```bash
# Deploy with production configuration
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Update application
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d --build
```

## Cloud Deployment Options

### AWS ECS with Fargate

1. **Build and push images to ECR**:
```bash
# Create ECR repositories
aws ecr create-repository --repository-name cbm-analytics-backend
aws ecr create-repository --repository-name cbm-analytics-frontend

# Build and push images
docker build -t cbm-analytics-backend ./backend
docker tag cbm-analytics-backend:latest <account-id>.dkr.ecr.<region>.amazonaws.com/cbm-analytics-backend:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/cbm-analytics-backend:latest
```

2. **Create ECS task definition** with appropriate CPU/memory settings
3. **Set up Application Load Balancer** for routing
4. **Configure auto-scaling** based on CPU/memory usage

### Google Cloud Run

```bash
# Build and deploy backend
gcloud builds submit --tag gcr.io/PROJECT-ID/cbm-analytics-backend ./backend
gcloud run deploy cbm-analytics-backend --image gcr.io/PROJECT-ID/cbm-analytics-backend --platform managed

# Build and deploy frontend
gcloud builds submit --tag gcr.io/PROJECT-ID/cbm-analytics-frontend ./frontend
gcloud run deploy cbm-analytics-frontend --image gcr.io/PROJECT-ID/cbm-analytics-frontend --platform managed
```

### Azure Container Instances

```bash
# Create resource group
az group create --name cbm-analytics --location eastus

# Deploy containers
az container create --resource-group cbm-analytics --name cbm-backend --image cbm-analytics-backend:latest --ports 8000
az container create --resource-group cbm-analytics --name cbm-frontend --image cbm-analytics-frontend:latest --ports 3000
```

## Monitoring and Maintenance

### Health Checks

The application includes health check endpoints:
- Backend: `GET /health`
- Add monitoring for these endpoints

### Logging

```bash
# View application logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Set up log rotation
echo '/var/lib/docker/containers/*/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}' | sudo tee /etc/logrotate.d/docker
```

### Backup Strategy

```bash
# Backup uploaded files (if persistent storage is used)
tar -czf backup-$(date +%Y%m%d).tar.gz /tmp/uploads

# Database backup (if database is added)
# docker-compose exec db pg_dump -U user dbname > backup.sql
```

### Performance Optimization

1. **Enable gzip compression** in nginx
2. **Set up CDN** for static assets
3. **Configure caching headers** for API responses
4. **Monitor resource usage** and scale accordingly
5. **Optimize Docker images** with multi-stage builds

### Security Checklist

- [ ] SSL/TLS certificates configured
- [ ] Security headers enabled
- [ ] File upload size limits set
- [ ] CORS properly configured
- [ ] Regular security updates
- [ ] Access logs monitored
- [ ] Rate limiting implemented
- [ ] Firewall rules configured

## Troubleshooting

### Common Issues

1. **File upload fails**:
   - Check `MAX_UPLOAD_SIZE` environment variable
   - Verify nginx `client_max_body_size` setting
   - Check disk space in `/tmp/uploads`

2. **CORS errors**:
   - Verify `CORS_ORIGINS` environment variable
   - Check frontend `REACT_APP_API_URL` setting

3. **Memory issues**:
   - Increase container memory limits
   - Monitor pandas memory usage for large files
   - Consider streaming processing for very large files

4. **Performance issues**:
   - Check container resource limits
   - Monitor database query performance
   - Enable application profiling

### Debug Mode

```bash
# Enable debug logging
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up

# Access container for debugging
docker-compose exec backend bash
docker-compose exec frontend sh
```