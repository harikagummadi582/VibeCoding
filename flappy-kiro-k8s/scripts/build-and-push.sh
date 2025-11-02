#!/bin/bash

set -e

# Configuration
AWS_REGION="us-west-2"
AWS_PROFILE="kiro-eks-workshop"
ECR_REGISTRY=""
FRONTEND_REPO="flappy-kiro-frontend"
BACKEND_REPO="flappy-kiro-backend"

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

# Get AWS Account ID
log "Getting AWS Account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    error "Failed to get AWS Account ID. Check your AWS profile: $AWS_PROFILE"
fi
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
success "AWS Account ID: $AWS_ACCOUNT_ID"

# Login to ECR
log "Logging into Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $ECR_REGISTRY
success "Logged into ECR"

# Create ECR repositories if they don't exist
create_ecr_repo() {
    local repo_name=$1
    log "Checking if ECR repository '$repo_name' exists..."
    
    if aws ecr describe-repositories --repository-names $repo_name --region $AWS_REGION --profile $AWS_PROFILE >/dev/null 2>&1; then
        success "Repository '$repo_name' already exists"
    else
        log "Creating ECR repository '$repo_name'..."
        aws ecr create-repository \
            --repository-name $repo_name \
            --region $AWS_REGION \
            --profile $AWS_PROFILE \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256 >/dev/null
        success "Created repository '$repo_name'"
    fi
}

create_ecr_repo $FRONTEND_REPO
create_ecr_repo $BACKEND_REPO

# Build and push frontend
log "Building frontend Docker image..."
cd frontend
docker build -t $FRONTEND_REPO:latest .
docker tag $FRONTEND_REPO:latest $ECR_REGISTRY/$FRONTEND_REPO:latest
success "Built frontend image"

log "Pushing frontend image to ECR..."
docker push $ECR_REGISTRY/$FRONTEND_REPO:latest
success "Pushed frontend image"

# Build and push backend
log "Building backend Docker image..."
cd ../backend
docker build -t $BACKEND_REPO:latest .
docker tag $BACKEND_REPO:latest $ECR_REGISTRY/$BACKEND_REPO:latest
success "Built backend image"

log "Pushing backend image to ECR..."
docker push $ECR_REGISTRY/$BACKEND_REPO:latest
success "Pushed backend image"

cd ..

# Update Kubernetes manifests with correct image URIs
log "Updating Kubernetes manifests with ECR image URIs..."

# Update backend deployment
sed -i.bak "s|ACCOUNT_ID|$AWS_ACCOUNT_ID|g" k8s/backend-deployment.yaml
sed -i.bak "s|ACCOUNT_ID|$AWS_ACCOUNT_ID|g" k8s/frontend-deployment.yaml

# Clean up backup files
rm -f k8s/*.bak

success "Updated Kubernetes manifests"

# Display next steps
echo ""
log "🎉 Build and push completed successfully!"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Install AWS Load Balancer Controller (if not already installed):"
echo "   kubectl apply -k \"github.com/aws/eks-charts/stable/aws-load-balancer-controller//crds?ref=master\""
echo ""
echo "2. Deploy the application:"
echo "   kubectl apply -f k8s/"
echo ""
echo "3. Check deployment status:"
echo "   kubectl get pods -n flappy-kiro"
echo ""
echo "4. Get the ALB URL:"
echo "   kubectl get ingress flappy-kiro-ingress -n flappy-kiro"
echo ""
echo -e "${GREEN}Images pushed:${NC}"
echo "Frontend: $ECR_REGISTRY/$FRONTEND_REPO:latest"
echo "Backend:  $ECR_REGISTRY/$BACKEND_REPO:latest"