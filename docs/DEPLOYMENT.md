# Deployment Guide

Complete guide for deploying the FFmpeg WebSocket Media Processing Service to various environments.

## Table of Contents

1. [Quick Deploy (Docker)](#quick-deploy-docker)
2. [Production Deployment](#production-deployment)
3. [Cloud Deployments](#cloud-deployments)
4. [Kubernetes](#kubernetes)
5. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Quick Deploy (Docker)

### Single Server Deployment

**Prerequisites**:
- Docker & Docker Compose installed
- Port 8080, 8081 available

**Deploy**:
```bash
# Clone/copy project
cd /path/to/doramee

# Configure environment
cp .env.example .env
nano .env  # Edit configuration

# Start service
docker-compose up -d

# Check status
docker-compose ps
curl http://localhost:8081/health
```

**Access**:
- WebSocket: `ws://your-server:8080`
- Health: `http://your-server:8081/health`
- RabbitMQ UI: `http://your-server:15672` (guest/guest)

---

## Production Deployment

### Option 1: Docker Compose (Recommended)

#### 1. Prepare Server

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install docker-compose-plugin
```

#### 2. Configure for Production

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  rabbitmq:
    image: rabbitmq:3-management
    container_name: ffmpeg-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: admin
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    ports:
      - "5672:5672"
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    restart: unless-stopped
    healthcheck:
      test: rabbitmq-diagnostics -q ping
      interval: 30s
      timeout: 10s
      retries: 3

  ffmpeg-service:
    build: .
    image: ffmpeg-websocket-service:latest
    container_name: ffmpeg-ws-service
    depends_on:
      - rabbitmq
    ports:
      - "8080:8080"
      - "8081:8081"
    environment:
      - WS_HOST=0.0.0.0
      - WS_PORT=8080
      - HEALTH_PORT=8081
      - MAX_CONCURRENT_JOBS=8
      - FFMPEG_TIMEOUT_SECONDS=600
      - TEMP_DIR=/tmp/ffmpeg-jobs
      - MAX_FILE_SIZE_MB=1000
      - LOG_LEVEL=INFO
      - RABBITMQ_URL=amqp://admin:${RABBITMQ_PASSWORD}@rabbitmq/
    volumes:
      - ffmpeg-temp:/tmp/ffmpeg-jobs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8081/health')"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s

  # Optional: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: ffmpeg-nginx
    depends_on:
      - ffmpeg-service
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    restart: unless-stopped

volumes:
  ffmpeg-temp:
  rabbitmq_data:
```

#### 3. Environment Configuration

Create `.env.prod`:
```bash
# Generate strong password
RABBITMQ_PASSWORD=$(openssl rand -base64 32)

# Optional: Add to .env.prod
echo "RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD}" > .env.prod
```

#### 4. Deploy

```bash
# Build and start
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check health
curl http://localhost:8081/health
```

#### 5. Configure Nginx (Optional)

Create `nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    # WebSocket upgrade support
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=websocket:10m rate=10r/s;

    upstream ffmpeg_websocket {
        server ffmpeg-service:8080;
    }

    upstream ffmpeg_health {
        server ffmpeg-service:8081;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # WebSocket endpoint
        location /ws {
            limit_req zone=websocket burst=20;

            proxy_pass http://ffmpeg_websocket;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

            # Timeouts for long-running jobs
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://ffmpeg_health/health;
            proxy_set_header Host $host;
        }

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }
}
```

### Option 2: Systemd Service (Native)

#### 1. Install Dependencies

```bash
# Install Python 3.10+
sudo apt-get install python3.10 python3.10-venv python3-pip

# Install FFmpeg
sudo apt-get install ffmpeg

# Install RabbitMQ
sudo apt-get install rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
```

#### 2. Setup Application

```bash
# Create app user
sudo useradd -r -s /bin/bash -d /opt/ffmpeg-service ffmpeg

# Copy application
sudo cp -r /path/to/doramee /opt/ffmpeg-service/
sudo chown -R ffmpeg:ffmpeg /opt/ffmpeg-service

# Install dependencies
sudo -u ffmpeg bash -c "
  cd /opt/ffmpeg-service &&
  python3 -m venv venv &&
  source venv/bin/activate &&
  pip install uv &&
  uv pip install -e .
"

# Configure
sudo -u ffmpeg cp /opt/ffmpeg-service/.env.example /opt/ffmpeg-service/.env
sudo nano /opt/ffmpeg-service/.env
```

#### 3. Create Systemd Service

Create `/etc/systemd/system/ffmpeg-service.service`:
```ini
[Unit]
Description=FFmpeg WebSocket Media Processing Service
After=network.target rabbitmq-server.service
Wants=rabbitmq-server.service

[Service]
Type=simple
User=ffmpeg
Group=ffmpeg
WorkingDirectory=/opt/ffmpeg-service
Environment="PATH=/opt/ffmpeg-service/venv/bin:/usr/bin"
ExecStart=/opt/ffmpeg-service/venv/bin/python -m src.main_rabbitmq
Restart=always
RestartSec=10

# Resource limits
LimitNOFILE=65536
MemoryLimit=4G
CPUQuota=400%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ffmpeg-service

[Install]
WantedBy=multi-user.target
```

#### 4. Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start
sudo systemctl enable ffmpeg-service
sudo systemctl start ffmpeg-service

# Check status
sudo systemctl status ffmpeg-service

# View logs
sudo journalctl -u ffmpeg-service -f
```

---

## Cloud Deployments

### AWS (EC2 + ECS)

#### EC2 Single Instance

```bash
# Launch EC2 instance
# - AMI: Ubuntu 22.04 LTS
# - Type: t3.large or larger
# - Storage: 50GB+ EBS
# - Security Group: Open ports 80, 443, 8080, 8081

# SSH and deploy
ssh ubuntu@ec2-instance
git clone your-repo
cd doramee
docker-compose -f docker-compose.prod.yml up -d
```

#### ECS Fargate

Create `task-definition.json`:
```json
{
  "family": "ffmpeg-service",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "ffmpeg-service",
      "image": "your-registry/ffmpeg-websocket-service:latest",
      "portMappings": [
        {"containerPort": 8080, "protocol": "tcp"},
        {"containerPort": 8081, "protocol": "tcp"}
      ],
      "environment": [
        {"name": "MAX_CONCURRENT_JOBS", "value": "8"},
        {"name": "RABBITMQ_URL", "value": "amqp://user:pass@mq.amazonaws.com"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ffmpeg-service",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

Deploy:
```bash
# Create cluster
aws ecs create-cluster --cluster-name ffmpeg-cluster

# Register task
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster ffmpeg-cluster \
  --service-name ffmpeg-service \
  --task-definition ffmpeg-service \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
```

### Google Cloud (GKE)

See [Kubernetes section](#kubernetes) below.

### DigitalOcean

```bash
# Create Droplet
# - Ubuntu 22.04
# - 4GB RAM minimum
# - Add SSH key

# Deploy
ssh root@droplet-ip
git clone your-repo
cd doramee
docker-compose up -d
```

---

## Kubernetes

### Kubernetes Deployment

#### 1. Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ffmpeg-service
```

#### 2. RabbitMQ Deployment

```yaml
# rabbitmq.yaml
apiVersion: v1
kind: Service
metadata:
  name: rabbitmq
  namespace: ffmpeg-service
spec:
  ports:
    - name: amqp
      port: 5672
    - name: management
      port: 15672
  selector:
    app: rabbitmq
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: rabbitmq
  namespace: ffmpeg-service
spec:
  serviceName: rabbitmq
  replicas: 1
  selector:
    matchLabels:
      app: rabbitmq
  template:
    metadata:
      labels:
        app: rabbitmq
    spec:
      containers:
      - name: rabbitmq
        image: rabbitmq:3-management
        ports:
        - containerPort: 5672
        - containerPort: 15672
        env:
        - name: RABBITMQ_DEFAULT_USER
          value: admin
        - name: RABBITMQ_DEFAULT_PASS
          valueFrom:
            secretKeyRef:
              name: rabbitmq-secret
              key: password
        volumeMounts:
        - name: rabbitmq-data
          mountPath: /var/lib/rabbitmq
  volumeClaimTemplates:
  - metadata:
      name: rabbitmq-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

#### 3. FFmpeg Service Deployment

```yaml
# ffmpeg-service.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ffmpeg-config
  namespace: ffmpeg-service
data:
  MAX_CONCURRENT_JOBS: "8"
  LOG_LEVEL: "INFO"
  MAX_FILE_SIZE_MB: "1000"
---
apiVersion: v1
kind: Service
metadata:
  name: ffmpeg-service
  namespace: ffmpeg-service
spec:
  type: LoadBalancer
  ports:
    - name: websocket
      port: 8080
      targetPort: 8080
    - name: health
      port: 8081
      targetPort: 8081
  selector:
    app: ffmpeg-service
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ffmpeg-service
  namespace: ffmpeg-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ffmpeg-service
  template:
    metadata:
      labels:
        app: ffmpeg-service
    spec:
      containers:
      - name: ffmpeg-service
        image: your-registry/ffmpeg-websocket-service:latest
        ports:
        - containerPort: 8080
        - containerPort: 8081
        envFrom:
        - configMapRef:
            name: ffmpeg-config
        env:
        - name: RABBITMQ_URL
          value: "amqp://admin:$(RABBITMQ_PASSWORD)@rabbitmq:5672/"
        - name: RABBITMQ_PASSWORD
          valueFrom:
            secretKeyRef:
              name: rabbitmq-secret
              key: password
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 4. Deploy to Kubernetes

```bash
# Create secret
kubectl create secret generic rabbitmq-secret \
  --from-literal=password=$(openssl rand -base64 32) \
  -n ffmpeg-service

# Apply manifests
kubectl apply -f namespace.yaml
kubectl apply -f rabbitmq.yaml
kubectl apply -f ffmpeg-service.yaml

# Check status
kubectl get pods -n ffmpeg-service
kubectl get svc -n ffmpeg-service

# Get external IP
kubectl get svc ffmpeg-service -n ffmpeg-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Basic health
curl http://your-server:8081/health

# Detailed check
watch -n 5 'curl -s http://localhost:8081/health | jq'
```

### Monitoring Setup

#### Prometheus + Grafana

```yaml
# prometheus-config.yaml
scrape_configs:
  - job_name: 'ffmpeg-service'
    static_configs:
      - targets: ['ffmpeg-service:8081']
    metrics_path: '/health'
    scrape_interval: 30s
```

### Log Management

#### Docker Logs
```bash
# View logs
docker-compose logs -f ffmpeg-service

# Save logs
docker-compose logs ffmpeg-service > service.log
```

#### Systemd Logs
```bash
# View logs
sudo journalctl -u ffmpeg-service -f

# Last 100 lines
sudo journalctl -u ffmpeg-service -n 100

# Save logs
sudo journalctl -u ffmpeg-service > service.log
```

### Backup

```bash
# Backup RabbitMQ data
docker exec ffmpeg-rabbitmq rabbitmqctl export_definitions /tmp/definitions.json
docker cp ffmpeg-rabbitmq:/tmp/definitions.json ./backup/

# Backup configuration
tar -czf config-backup.tar.gz .env docker-compose.yml nginx.conf
```

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker-compose build

# Rolling update
docker-compose up -d

# Or zero-downtime with multiple instances
docker-compose scale ffmpeg-service=2
docker-compose up -d --no-deps --build ffmpeg-service
docker-compose scale ffmpeg-service=1
```

### Scaling

#### Horizontal Scaling
```bash
# Docker Compose
docker-compose up -d --scale ffmpeg-service=4

# Kubernetes
kubectl scale deployment ffmpeg-service --replicas=5 -n ffmpeg-service
```

#### Vertical Scaling
```bash
# Update resource limits in docker-compose.yml or k8s manifests
# Then redeploy
```

---

## Security Checklist

- [ ] Change default RabbitMQ credentials
- [ ] Enable SSL/TLS (use Nginx or Traefik)
- [ ] Configure firewall (only open necessary ports)
- [ ] Enable rate limiting
- [ ] Set up log rotation
- [ ] Configure max file size limits
- [ ] Use non-root user
- [ ] Enable Docker security options
- [ ] Regular security updates
- [ ] Monitor for suspicious activity

---

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs ffmpeg-service

# Check ports
sudo netstat -tlnp | grep 8080

# Check RabbitMQ
docker-compose logs rabbitmq
```

### High Memory Usage
```bash
# Check container stats
docker stats

# Reduce MAX_CONCURRENT_JOBS in .env
# Restart service
```

### Slow Performance
```bash
# Check system resources
htop

# Check FFmpeg processes
ps aux | grep ffmpeg

# Increase workers
# Set MAX_CONCURRENT_JOBS=8 in .env
```

---

## Quick Reference

| Deployment Type | Best For | Complexity | Scalability |
|----------------|----------|------------|-------------|
| Docker Compose | Small-medium | Low | Vertical only |
| Systemd | Single server | Medium | Limited |
| Kubernetes | Enterprise | High | Excellent |
| Cloud (ECS/GKE) | Production | Medium-High | Excellent |

**Recommended**: Docker Compose for quick setup, Kubernetes for production scale.

---

**Next Steps**: See [RABBITMQ_INTEGRATION.md](RABBITMQ_INTEGRATION.md) for distributed deployment details.
