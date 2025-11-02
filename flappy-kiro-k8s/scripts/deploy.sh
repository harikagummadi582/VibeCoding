#!/bin/bash

set -e

# Configuration
AWS_PROFILE="kiro-eks-workshop"
CLUSTER_NAME="eks-kiro-demo"
AWS_REGION="us-west-2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check if kubectl is configured
log "Checking kubectl configuration..."
if ! kubectl cluster-info >/dev/null 2>&1; then
    warning "kubectl not configured. Updating kubeconfig..."
    aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME --profile $AWS_PROFILE
    success "Updated kubeconfig"
else
    success "kubectl is configured"
fi

# Check if AWS Load Balancer Controller is installed
log "Checking AWS Load Balancer Controller..."
if ! kubectl get deployment -n kube-system aws-load-balancer-controller >/dev/null 2>&1; then
    warning "AWS Load Balancer Controller not found. Installing..."
    
    # Install cert-manager (required for ALB controller)
    kubectl apply --validate=false -f https://github.com/jetstack/cert-manager/releases/download/v1.5.4/cert-manager.yaml
    
    # Wait for cert-manager to be ready
    kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
    
    # Install AWS Load Balancer Controller
    kubectl apply -k "github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master"
    
    success "Installed AWS Load Balancer Controller prerequisites"
else
    success "AWS Load Balancer Controller is installed"
fi

# Deploy the application
log "Deploying Flappy Kiro to Kubernetes..."

# Apply manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/persistent-volume.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
kubectl apply -f k8s/ingress.yaml

success "Applied Kubernetes manifests"

# Wait for deployments to be ready
log "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/flappy-kiro-backend -n flappy-kiro
kubectl wait --for=condition=available --timeout=300s deployment/flappy-kiro-frontend -n flappy-kiro

success "Deployments are ready"

# Get deployment status
log "Checking deployment status..."
echo ""
kubectl get pods -n flappy-kiro
echo ""
kubectl get services -n flappy-kiro
echo ""

# Wait for ingress to get an address
log "Waiting for ALB to be provisioned (this may take a few minutes)..."
for i in {1..30}; do
    ALB_URL=$(kubectl get ingress flappy-kiro-ingress -n flappy-kiro -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "")
    if [ ! -z "$ALB_URL" ]; then
        break
    fi
    echo -n "."
    sleep 10
done

echo ""

if [ ! -z "$ALB_URL" ]; then
    success "ALB provisioned successfully!"
    echo ""
    echo -e "${GREEN}🎮 Flappy Kiro is now available at:${NC}"
    echo -e "${YELLOW}http://$ALB_URL${NC}"
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo "View pods:     kubectl get pods -n flappy-kiro"
    echo "View services: kubectl get services -n flappy-kiro"
    echo "View ingress:  kubectl get ingress -n flappy-kiro"
    echo "View logs:     kubectl logs -f deployment/flappy-kiro-backend -n flappy-kiro"
    echo "Scale backend: kubectl scale deployment flappy-kiro-backend --replicas=3 -n flappy-kiro"
else
    warning "ALB is still being provisioned. Check status with:"
    echo "kubectl get ingress flappy-kiro-ingress -n flappy-kiro"
fi

echo ""
success "Deployment completed!"