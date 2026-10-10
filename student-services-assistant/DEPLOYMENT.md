# Deployment Guide

This guide covers deploying the Student Services Assistant to production.

## Deployment Options

1. **Docker Compose** (Recommended for single-server deployment)
2. **Kubernetes** (For scalable, multi-server deployment)
3. **Manual Deployment** (Development or small-scale use)

## Option 1: Docker Compose Deployment

### Prerequisites

- Docker and Docker Compose installed
- Ollama running on host or accessible endpoint
- Sufficient disk space for vector store and database

### Steps

1. **Clone and Configure**

```bash
git clone <repository>
cd student-services-assistant

# Copy and edit environment
cp .env.example .env
vim .env  # Update for production
```

2. **Production Environment Variables**

```env
# .env
LLM_PROVIDER=ollama
LLM_MODEL=qwen2.5:7b-instruct
OLLAMA_HOST=http://host.docker.internal:11434
EMBED_MODEL=BAAI/bge-small-en-v1.5
STORE_DIR=/app/store
API_HOST=0.0.0.0
API_PORT=8000
ADMIN_TOKEN=<secure-random-token>
```

3. **Build and Start Services**

```bash
# Pull Ollama model first
ollama pull qwen2.5:7b-instruct

# Start services
docker-compose up -d --build

# Check logs
docker-compose logs -f
```

4. **Load Initial Data**

```bash
# Generate sample data (or use real data)
docker-compose exec api python scripts/generate_data.py
docker-compose exec api python scripts/load_students.py --dir data/test_students/

# Ingest documents
docker-compose exec api python scripts/ingest_seed.py
```

5. **Verify Deployment**

```bash
curl http://localhost:8000/health
```

### Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Backup and Restore

**Backup:**
```bash
# Backup database and vector store
tar -czf backup-$(date +%Y%m%d).tar.gz store/

# Or use Docker volumes
docker run --rm -v student-services-assistant_ollama:/data -v $(pwd):/backup ubuntu tar czf /backup/ollama-backup.tar.gz /data
```

**Restore:**
```bash
# Restore from backup
tar -xzf backup-20241010.tar.gz
```

## Option 2: Kubernetes Deployment

### Prerequisites

- Kubernetes cluster
- kubectl configured
- Persistent volume support
- Load balancer or Ingress controller

### Kubernetes Manifests

**namespace.yaml:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: student-services
```

**configmap.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: student-services
data:
  LLM_PROVIDER: "ollama"
  LLM_MODEL: "qwen2.5:7b-instruct"
  OLLAMA_HOST: "http://ollama:11434"
  EMBED_MODEL: "BAAI/bge-small-en-v1.5"
  STORE_DIR: "/app/store"
```

**pvc.yaml:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: store-pvc
  namespace: student-services
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

**deployment-api.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: student-services
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: student-services-api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: app-config
        volumeMounts:
        - name: store
          mountPath: /app/store
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: store
        persistentVolumeClaim:
          claimName: store-pvc
```

**service-api.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: student-services
spec:
  selector:
    app: api
  ports:
  - port: 8000
    targetPort: 8000
  type: LoadBalancer
```

**Deploy:**
```bash
kubectl apply -f k8s/
```

## Option 3: Manual Deployment

### On Ubuntu Server

1. **Install Dependencies**

```bash
# System packages
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip
sudo apt-get install -y tesseract-ocr poppler-utils

# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b-instruct
```

2. **Setup Application**

```bash
# Create user
sudo useradd -m -s /bin/bash studentservices
sudo su - studentservices

# Clone and setup
git clone <repository>
cd student-services-assistant
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Create Systemd Service**

**/etc/systemd/system/student-services-api.service:**
```ini
[Unit]
Description=Student Services API
After=network.target

[Service]
Type=simple
User=studentservices
WorkingDirectory=/home/studentservices/student-services-assistant
Environment="PATH=/home/studentservices/student-services-assistant/venv/bin"
ExecStart=/home/studentservices/student-services-assistant/venv/bin/uvicorn src.api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable student-services-api
sudo systemctl start student-services-api
```

4. **Setup Nginx Reverse Proxy**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Production Considerations

### Security

1. **API Authentication**
   - Add authentication middleware
   - Use API keys or OAuth
   - Validate X-Student-Id header

2. **HTTPS**
   - Use Let's Encrypt for SSL certificates
   - Configure TLS in nginx or ingress

3. **Secrets Management**
   - Use environment variables, not .env files
   - Consider using Vault or AWS Secrets Manager

4. **Rate Limiting**
   - Add rate limiting to prevent abuse
   - Use nginx or API middleware

### Performance

1. **Database Optimization**
   - Add indexes for common queries
   - Consider PostgreSQL for production instead of SQLite
   - Use connection pooling

2. **Caching**
   - Cache common queries
   - Use Redis for session storage
   - Cache embeddings for repeated documents

3. **Load Balancing**
   - Use multiple API instances
   - Add load balancer (nginx, HAProxy, AWS ALB)
   - Scale based on CPU/memory usage

4. **Ollama Optimization**
   - Use GPU if available
   - Consider multiple Ollama instances
   - Monitor model memory usage

### Monitoring

1. **Application Metrics**
   - Add Prometheus metrics
   - Track request latency
   - Monitor error rates

2. **Logs**
   - Centralized logging (ELK, CloudWatch)
   - Structure logs as JSON
   - Log trace_ids for debugging

3. **Alerts**
   - Set up alerts for errors
   - Monitor disk space (vector store grows)
   - Alert on high latency

### Backup Strategy

1. **Database Backups**
   - Daily full backup
   - Point-in-time recovery capability
   - Test restore procedures

2. **Vector Store Backups**
   - Weekly full backup
   - Incremental daily backups
   - Version control for source_register.csv

3. **Document Archive**
   - Keep original PDFs
   - Version control for regulations
   - Audit trail for document changes

## Scaling

### Horizontal Scaling

- API: Stateless, can scale horizontally
- UI: Can run multiple replicas
- Database: Read replicas for query scaling
- Vector Store: Consider managed ChromaDB or Pinecone

### Vertical Scaling

- Increase memory for embedding model
- Add GPU for faster LLM inference
- Increase disk for growing vector store

## Troubleshooting Production Issues

### High Latency

1. Check Ollama response time
2. Review database query performance
3. Monitor vector store query time
4. Check network latency

### Out of Memory

1. Reduce batch sizes
2. Limit concurrent requests
3. Optimize chunk sizes
4. Use smaller models

### Disk Full

1. Rotate logs
2. Clean up old audit records
3. Archive old documents
4. Monitor vector store growth

## Rollback Procedure

1. Stop services: `docker-compose down`
2. Restore from backup
3. Start services: `docker-compose up -d`
4. Verify health: `curl http://localhost:8000/health`

## Maintenance Windows

Schedule regular maintenance for:
- Database vacuuming
- Vector store optimization
- Log rotation
- Security updates

Recommended: Weekly maintenance window during low-traffic hours.
