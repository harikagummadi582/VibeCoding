# Flappy Kiro Kubernetes Microservices

A containerized microservices deployment of Flappy Kiro on Amazon EKS with OpenTelemetry logging.

## Architecture

```
User → ALB (Ingress) → Frontend Service → Frontend Pod → Backend Service → Backend Pod → JSON Storage
                                                                                    ↓
                                                                            ADOT Collector → CloudWatch/X-Ray
```

## Components

- **Frontend**: Nginx serving HTML/JS game (2 replicas)
- **Backend**: Python Flask API with leaderboard storage (2 replicas)
- **Storage**: Persistent Volume with JSON file-based leaderboard
- **Monitoring**: OpenTelemetry with AWS Distro for OpenTelemetry (ADOT)
- **Load Balancer**: AWS Application Load Balancer via Ingress

## Prerequisites

1. **EKS Cluster**: Running eks-kiro-demo cluster
2. **AWS CLI**: Configured with kiro-eks-workshop profile
3. **Docker**: For building container images
4. **kubectl**: Configured for your EKS cluster

## Quick Deploy

```bash
# 1. Build and push container images to ECR
./scripts/build-and-push.sh

# 2. Deploy to Kubernetes
./scripts/deploy.sh

# 3. Get the game URL
kubectl get ingress flappy-kiro-ingress -n flappy-kiro
```

## Manual Deployment Steps

### Step 1: Build and Push Images

```bash
cd flappy-kiro-k8s
./scripts/build-and-push.sh
```

### Step 2: Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n flappy-kiro
kubectl get services -n flappy-kiro
kubectl get ingress -n flappy-kiro
```

### Step 3: Access the Game

```bash
# Get ALB URL (may take 5-10 minutes to provision)
kubectl get ingress flappy-kiro-ingress -n flappy-kiro -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

## Services Architecture

### Frontend Service

- **Type**: NodePort (exposed via ALB Ingress)
- **Replicas**: 2
- **Container**: Nginx serving static files
- **Health Check**: `/health` endpoint
- **Resources**: 64Mi RAM, 50m CPU

### Backend Service

- **Type**: ClusterIP (internal only)
- **Replicas**: 2
- **Container**: Python Flask API
- **Health Check**: `/health` endpoint
- **Resources**: 128Mi RAM, 100m CPU
- **Storage**: 1Gi Persistent Volume for JSON data

### Traffic Flow

1. User accesses ALB URL
2. ALB routes to Frontend Service (NodePort)
3. Frontend serves game files
4. Game makes API calls to `/api/*`
5. Nginx proxies API calls to Backend Service (ClusterIP)
6. Backend processes requests and stores data in PV

## OpenTelemetry Monitoring

### Components

- **ADOT Collector**: Collects traces and logs
- **AWS X-Ray**: Distributed tracing
- **CloudWatch Logs**: Centralized logging
- **Structured Logging**: JSON format throughout

### Monitoring Commands

```bash
# View application logs
kubectl logs -f deployment/flappy-kiro-backend -n flappy-kiro
kubectl logs -f deployment/flappy-kiro-frontend -n flappy-kiro

# View ADOT collector logs
kubectl logs -f deployment/adot-collector -n flappy-kiro
```

## Scaling

```bash
# Scale backend replicas
kubectl scale deployment flappy-kiro-backend --replicas=3 -n flappy-kiro

# Scale frontend replicas
kubectl scale deployment flappy-kiro-frontend --replicas=3 -n flappy-kiro
```

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -n flappy-kiro
kubectl describe pod <pod-name> -n flappy-kiro
```

### Check Service Connectivity

```bash
# Test backend service from frontend pod
kubectl exec -it deployment/flappy-kiro-frontend -n flappy-kiro -- curl http://flappy-kiro-backend-service:5000/health
```

### Check ALB Status

```bash
kubectl describe ingress flappy-kiro-ingress -n flappy-kiro
```

### View Events

```bash
kubectl get events -n flappy-kiro --sort-by='.lastTimestamp'
```

## Cleanup

```bash
# Delete the application
kubectl delete namespace flappy-kiro

# Delete ECR repositories (optional)
aws ecr delete-repository --repository-name flappy-kiro-frontend --force --profile kiro-eks-workshop
aws ecr delete-repository --repository-name flappy-kiro-backend --force --profile kiro-eks-workshop
```
