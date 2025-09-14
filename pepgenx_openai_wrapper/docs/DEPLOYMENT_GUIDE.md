# PepGenX OpenAI Wrapper - Deployment Guide

This guide provides comprehensive instructions for deploying the PepGenX OpenAI Wrapper in various environments.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose (for containerized deployment)
- PepGenX API credentials
- OKTA access token
- SSL certificates (for production HTTPS)

## Environment Setup

### 1. Configuration Files

Create the required configuration files:

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Required environment variables:
```bash
# PepGenX API Configuration
PEPGENX_API_URL=https://your-pepgenx-api-endpoint.com/api/generate
PEPGENX_PROJECT_ID=your-project-id
PEPGENX_TEAM_ID=your-team-id
PEPGENX_API_KEY=your-pepgenx-api-key

# OKTA Token Configuration
OKTA_TOKEN_FILE=okta_token.json

# OpenAI Wrapper Configuration
OPENAI_WRAPPER_API_KEYS=sk-prod-key1,sk-prod-key2,sk-prod-key3
OPENAI_WRAPPER_HOST=0.0.0.0
OPENAI_WRAPPER_PORT=8000

# Security
SECRET_KEY=your-very-secure-secret-key-here

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS (adjust for your domain)
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST=20
```

### 2. OKTA Token File

Create `okta_token.json`:
```json
{
  "access_token": "your-okta-access-token-here",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

This is the easiest way to deploy with monitoring included.

```bash
# Clone repository
git clone <repository-url>
cd pepgenx_openai_wrapper

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Create OKTA token file
echo '{"access_token": "your-token", "expires_in": 3600}' > okta_token.json

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f pepgenx-wrapper

# Start with monitoring (Prometheus + Grafana)
docker-compose --profile monitoring up -d
```

### Option 2: Docker Only

```bash
# Build image
docker build -t pepgenx-openai-wrapper .

# Run container
docker run -d \
  --name pepgenx-wrapper \
  -p 8000:8000 \
  -v $(pwd)/okta_token.json:/app/okta_token.json:ro \
  -v $(pwd)/.env:/app/.env:ro \
  --restart unless-stopped \
  pepgenx-openai-wrapper

# Check logs
docker logs -f pepgenx-wrapper
```

### Option 3: Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Create OKTA token file
echo '{"access_token": "your-token", "expires_in": 3600}' > okta_token.json

# Start application
python start.py

# Or use uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Option 4: Kubernetes

Create Kubernetes manifests:

```yaml
# pepgenx-wrapper-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pepgenx-wrapper
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pepgenx-wrapper
  template:
    metadata:
      labels:
        app: pepgenx-wrapper
    spec:
      containers:
      - name: pepgenx-wrapper
        image: pepgenx-openai-wrapper:latest
        ports:
        - containerPort: 8000
        env:
        - name: PEPGENX_API_URL
          valueFrom:
            secretKeyRef:
              name: pepgenx-secrets
              key: api-url
        - name: PEPGENX_API_KEY
          valueFrom:
            secretKeyRef:
              name: pepgenx-secrets
              key: api-key
        # Add other environment variables
        volumeMounts:
        - name: okta-token
          mountPath: /app/okta_token.json
          subPath: okta_token.json
          readOnly: true
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: okta-token
        secret:
          secretName: okta-token-secret

---
apiVersion: v1
kind: Service
metadata:
  name: pepgenx-wrapper-service
spec:
  selector:
    app: pepgenx-wrapper
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy to Kubernetes:
```bash
# Create secrets
kubectl create secret generic pepgenx-secrets \
  --from-literal=api-url="https://your-api-url" \
  --from-literal=api-key="your-api-key"

kubectl create secret generic okta-token-secret \
  --from-file=okta_token.json

# Deploy application
kubectl apply -f pepgenx-wrapper-deployment.yaml

# Check status
kubectl get pods
kubectl logs -f deployment/pepgenx-wrapper
```

## Production Considerations

### 1. Security

- **HTTPS**: Always use HTTPS in production
- **API Keys**: Store API keys securely (environment variables, secrets management)
- **OKTA Tokens**: Implement automatic token refresh
- **Network Security**: Use firewalls and VPNs
- **Container Security**: Run as non-root user, scan images

### 2. Monitoring

Set up comprehensive monitoring:

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access monitoring
# Prometheus: http://localhost:9091
# Grafana: http://localhost:3000 (admin/admin)
```

Configure alerts for:
- High error rates
- Slow response times
- OKTA token expiration
- PepGenX API failures

### 3. Logging

Configure centralized logging:

```bash
# Example with ELK stack
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  elasticsearch:7.14.0

docker run -d \
  --name logstash \
  -p 5000:5000 \
  --link elasticsearch:elasticsearch \
  logstash:7.14.0

docker run -d \
  --name kibana \
  -p 5601:5601 \
  --link elasticsearch:elasticsearch \
  kibana:7.14.0
```

### 4. Load Balancing

For high availability, use a load balancer:

```nginx
# nginx.conf
upstream pepgenx_wrapper {
    server pepgenx-wrapper-1:8000;
    server pepgenx-wrapper-2:8000;
    server pepgenx-wrapper-3:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://pepgenx_wrapper;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Auto-scaling

Configure auto-scaling based on metrics:

```yaml
# kubernetes-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pepgenx-wrapper-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pepgenx-wrapper
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Testing Deployment

### 1. Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/health/ready

# Detailed health (requires API key)
curl -H "Authorization: Bearer sk-your-key" \
  http://localhost:8000/health/detailed
```

### 2. API Testing

```bash
# Test chat completion
curl -X POST "http://localhost:8000/v1/chat/completions" \
  -H "Authorization: Bearer sk-your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Test models endpoint
curl -H "Authorization: Bearer sk-your-api-key" \
  http://localhost:8000/v1/models
```

### 3. Comprehensive Testing

```bash
# Run test suite
python test_wrapper.py --url http://localhost:8000 --api-key sk-your-key

# Load testing with Apache Bench
ab -n 100 -c 10 -H "Authorization: Bearer sk-your-key" \
  -H "Content-Type: application/json" \
  -p test_payload.json \
  http://localhost:8000/v1/chat/completions
```

## Maintenance

### 1. OKTA Token Refresh

Set up automatic token refresh:

```bash
#!/bin/bash
# refresh_token.sh
curl -X POST "https://your-okta-domain/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=refresh_token&refresh_token=$REFRESH_TOKEN" \
  > okta_token.json

# Restart wrapper to pick up new token
docker-compose restart pepgenx-wrapper
```

Add to crontab:
```bash
# Refresh token every hour
0 * * * * /path/to/refresh_token.sh
```

### 2. Log Rotation

Configure log rotation:

```bash
# /etc/logrotate.d/pepgenx-wrapper
/app/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 appuser appuser
    postrotate
        docker-compose restart pepgenx-wrapper
    endscript
}
```

### 3. Backup

Backup configuration and tokens:

```bash
#!/bin/bash
# backup.sh
tar -czf backup-$(date +%Y%m%d).tar.gz \
  .env \
  okta_token.json \
  docker-compose.yml \
  logs/
```

## Troubleshooting

### Common Issues

1. **OKTA Token Expired**:
   ```bash
   # Check token status
   curl -H "Authorization: Bearer sk-your-key" \
     http://localhost:8000/health/detailed
   
   # Refresh token
   ./refresh_token.sh
   ```

2. **PepGenX API Connection Issues**:
   ```bash
   # Check network connectivity
   curl -v https://your-pepgenx-api-url
   
   # Check wrapper logs
   docker-compose logs pepgenx-wrapper
   ```

3. **High Memory Usage**:
   ```bash
   # Monitor memory
   docker stats pepgenx-wrapper
   
   # Restart if needed
   docker-compose restart pepgenx-wrapper
   ```

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in .env file
LOG_LEVEL=DEBUG

# Restart service
docker-compose restart pepgenx-wrapper
```

## Support

For deployment support:
- Check health endpoints for system status
- Review application logs
- Monitor metrics dashboards
- Consult API documentation at `/docs`
