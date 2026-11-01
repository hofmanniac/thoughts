# Thoughts Framework - Deployment Guide

## Deployment Overview

The Thoughts framework supports multiple deployment patterns, from single-node development environments to distributed production systems. This guide covers deployment strategies, configuration management, and operational considerations.

## Development Deployment

### Local Development Setup

#### Prerequisites
```bash
# Python 3.8+
python --version

# Git for version control
git --version

# Optional: Docker for containerized services
docker --version
```

#### Installation
```bash
# Clone repository
git clone https://github.com/hofmanniac/thoughts
cd thoughts

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

#### Development Configuration
```json
{
  "workspace": {
    "environment": "development",
    "debug": true,
    "logging": {"level": "DEBUG", "output": ["console"]},
    "persistence": {
      "path": "./dev_data",
      "cleanup_on_start": true
    },
    "resources": {
      "memory_limit": "512MB",
      "execution_timeout": 300
    }
  }
}
```

#### Running Development Server
```bash
# Start interactive console
python cli.py

# Run specific examples
python cli.py --example chatbot

# Run with custom configuration
python cli.py --config ./configs/development.json
```

## Single-Node Production

### Server Preparation

#### System Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended  
- **Storage**: 20GB+ available space
- **OS**: Linux (Ubuntu 20.04+), macOS, Windows Server

#### Installation Script
```bash
#!/bin/bash
# production-install.sh

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.9+
sudo apt install python3.9 python3.9-venv python3-pip -y

# Create application user
sudo useradd -m -s /bin/bash thoughts
sudo mkdir -p /opt/thoughts
sudo chown thoughts:thoughts /opt/thoughts

# Switch to application user
sudo -u thoughts bash << 'EOF'
cd /opt/thoughts

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install Thoughts framework
pip install thoughts-framework

# Create directory structure
mkdir -p {configs,data,logs,memory}
EOF
```

### Production Configuration
```json
{
  "name": "ProductionAssistant",
  "version": "1.0.0",
  "workspace": {
    "environment": "production",
    "debug": false,
    "logging": {
      "level": "INFO",
      "format": "json",
      "output": ["file"],
      "file_path": "/opt/thoughts/logs/application.log",
      "rotation": {"max_size": "100MB", "backup_count": 10}
    },
    "persistence": {
      "path": "/opt/thoughts/data",
      "backup": {
        "enabled": true,
        "interval": "daily",
        "retention": "30d",
        "location": "/opt/thoughts/backups"
      }
    },
    "resources": {
      "memory_limit": "2GB",
      "execution_timeout": 120,
      "concurrent_sessions": 50
    },
    "security": {
      "rate_limiting": {"requests_per_minute": 100},
      "audit_logging": true,
      "session_encryption": true
    }
  }
}
```

### Service Configuration (systemd)
```ini
# /etc/systemd/system/thoughts.service
[Unit]
Description=Thoughts Framework Service
After=network.target

[Service]
Type=simple
User=thoughts
Group=thoughts
WorkingDirectory=/opt/thoughts
Environment=PATH=/opt/thoughts/venv/bin
ExecStart=/opt/thoughts/venv/bin/python -m thoughts.server --config /opt/thoughts/configs/production.json
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/thoughts/data /opt/thoughts/logs /opt/thoughts/memory

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy
```nginx
# /etc/nginx/sites-available/thoughts
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Containerized Deployment

### Docker Configuration

#### Dockerfile
```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install thoughts framework
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 thoughts && \
    mkdir -p /app/data /app/logs /app/memory && \
    chown -R thoughts:thoughts /app

USER thoughts

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "from thoughts.health import health_check; exit(0 if health_check() else 1)"

EXPOSE 8000

CMD ["python", "-m", "thoughts.server", "--config", "/app/configs/production.json"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  thoughts:
    build: .
    ports:
      - "8000:8000"
    environment:
      - THOUGHTS_ENV=production
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./configs:/app/configs:ro
      - thoughts_data:/app/data
      - thoughts_logs:/app/logs
      - thoughts_memory:/app/memory
    depends_on:
      - redis
      - postgres
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=thoughts
      - POSTGRES_USER=thoughts
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - thoughts
    restart: unless-stopped

volumes:
  thoughts_data:
  thoughts_logs:
  thoughts_memory:
  redis_data:
  postgres_data:
```

## Kubernetes Deployment

### Namespace and ConfigMap
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: thoughts

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: thoughts-config
  namespace: thoughts
data:
  production.json: |
    {
      "name": "KubernetesThoughts",
      "workspace": {
        "environment": "production",
        "logging": {"level": "INFO", "format": "json"},
        "resources": {"memory_limit": "1GB"}
      }
    }
```

### Deployment and Service
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: thoughts
  namespace: thoughts
spec:
  replicas: 3
  selector:
    matchLabels:
      app: thoughts
  template:
    metadata:
      labels:
        app: thoughts
    spec:
      containers:
      - name: thoughts
        image: thoughts:latest
        ports:
        - containerPort: 8000
        env:
        - name: THOUGHTS_ENV
          value: "production"
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: thoughts-secrets
              key: openai-api-key
        volumeMounts:
        - name: config
          mountPath: /app/configs
        - name: data
          mountPath: /app/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: thoughts-config
      - name: data
        persistentVolumeClaim:
          claimName: thoughts-data

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: thoughts-service
  namespace: thoughts
spec:
  selector:
    app: thoughts
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: thoughts-ingress
  namespace: thoughts
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - thoughts.example.com
    secretName: thoughts-tls
  rules:
  - host: thoughts.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: thoughts-service
            port:
              number: 80
```

### Persistent Storage
```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: thoughts-data
  namespace: thoughts
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

## Distributed Deployment

### Architecture Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Gateway   │    │  Message Queue  │
│                 │    │                 │    │    (Redis)      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         │                                               │
         v                                               v
┌─────────────────┐                            ┌─────────────────┐
│ Cortex Controller│                            │ Workspace Nodes │
│   - Coordination │                            │ - Agent Execution│
│   - Scheduling   │                            │ - Session Mgmt  │
│   - Monitoring   │                            │ - Local Memory  │
└─────────┬───────┘                            └─────────┬───────┘
          │                                               │
          └───────────────┬───────────────────────────────┘
                          │
                          v
                ┌─────────────────┐
                │ Shared Services │
                │ - Vector DB     │
                │ - Graph DB      │
                │ - File Storage  │
                │ - Monitoring    │
                └─────────────────┘
```

### Cortex Controller Configuration
```json
{
  "name": "DistributedCortex",
  "mode": "controller",
  "workspace_nodes": [
    {"host": "node1.thoughts.local", "capacity": 100},
    {"host": "node2.thoughts.local", "capacity": 100},
    {"host": "node3.thoughts.local", "capacity": 100}
  ],
  "scheduling": {
    "strategy": "least_loaded",
    "health_check_interval": 30,
    "failover": true
  },
  "shared_services": {
    "vector_db": {"type": "qdrant", "url": "http://qdrant.thoughts.local:6333"},
    "graph_db": {"type": "neo4j", "url": "bolt://neo4j.thoughts.local:7687"},
    "message_queue": {"type": "redis", "url": "redis://redis.thoughts.local:6379"}
  }
}
```

### Workspace Node Configuration
```json
{
  "name": "WorkspaceNode",
  "mode": "worker", 
  "controller": "http://controller.thoughts.local:8080",
  "capacity": {
    "max_workspaces": 50,
    "max_memory": "8GB",
    "max_cpu_cores": 4
  },
  "local_memory": {
    "cache_size": "1GB",
    "persistence": "local"
  }
}
```

## Monitoring and Observability

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'thoughts'
    static_configs:
      - targets: ['thoughts:8000']
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'thoughts-nodes'
    consul_sd_configs:
      - server: 'consul:8500'
        services: ['thoughts-node']
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Thoughts Framework",
    "panels": [
      {
        "title": "Active Workspaces",
        "type": "stat",
        "targets": [{"expr": "thoughts_active_workspaces"}]
      },
      {
        "title": "Request Rate", 
        "type": "graph",
        "targets": [{"expr": "rate(thoughts_requests_total[5m])"}]
      },
      {
        "title": "Memory Usage",
        "type": "graph", 
        "targets": [{"expr": "thoughts_memory_usage_bytes"}]
      }
    ]
  }
}
```

### Logging Configuration
```json
{
  "logging": {
    "version": 1,
    "formatters": {
      "json": {
        "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
      }
    },
    "handlers": {
      "file": {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": "/app/logs/thoughts.log",
        "maxBytes": 104857600,
        "backupCount": 10,
        "formatter": "json"
      },
      "elasticsearch": {
        "class": "thoughts.logging.ElasticsearchHandler",
        "hosts": ["elasticsearch:9200"],
        "index": "thoughts-logs"
      }
    },
    "loggers": {
      "thoughts": {"level": "INFO", "handlers": ["file", "elasticsearch"]}
    }
  }
}
```

## Security Considerations

### Network Security
```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: thoughts-network-policy
  namespace: thoughts
spec:
  podSelector:
    matchLabels:
      app: thoughts
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
```

### Secret Management
```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: thoughts-secrets
  namespace: thoughts
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
  database-password: <base64-encoded-password>
  session-encryption-key: <base64-encoded-key>
```

### RBAC Configuration
```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: thoughts-service-account
  namespace: thoughts

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: thoughts-role
  namespace: thoughts
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: thoughts-rolebinding
  namespace: thoughts
subjects:
- kind: ServiceAccount
  name: thoughts-service-account
  namespace: thoughts
roleRef:
  kind: Role
  name: thoughts-role
  apiGroup: rbac.authorization.k8s.io
```

## Backup and Disaster Recovery

### Backup Strategy
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup configuration
tar -czf $BACKUP_DIR/configs.tar.gz /opt/thoughts/configs/

# Backup data directory
tar -czf $BACKUP_DIR/data.tar.gz /opt/thoughts/data/

# Backup memory systems
pg_dump thoughts > $BACKUP_DIR/postgres.sql
redis-cli --rdb $BACKUP_DIR/redis.rdb

# Upload to cloud storage
aws s3 sync $BACKUP_DIR s3://thoughts-backups/$(basename $BACKUP_DIR)/

# Cleanup old local backups
find /backups -type d -mtime +7 -exec rm -rf {} \;
```

### Recovery Procedure
```bash
#!/bin/bash
# restore.sh

BACKUP_DATE=$1
BACKUP_DIR="/backups/$BACKUP_DATE"

# Stop services
systemctl stop thoughts

# Restore configuration
tar -xzf $BACKUP_DIR/configs.tar.gz -C /

# Restore data
tar -xzf $BACKUP_DIR/data.tar.gz -C /

# Restore databases
psql thoughts < $BACKUP_DIR/postgres.sql
redis-cli --rdb $BACKUP_DIR/redis.rdb

# Start services
systemctl start thoughts

# Verify recovery
python -c "from thoughts.health import verify_recovery; verify_recovery()"
```

This deployment guide provides comprehensive coverage of deployment patterns from development to production, including containerization, Kubernetes orchestration, monitoring, security, and disaster recovery procedures.