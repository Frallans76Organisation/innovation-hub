#!/bin/bash
# Innovation Hub - OpenShift Setup Script
# This script helps configure the OpenShift deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Innovation Hub - OpenShift Setup Script   ║${NC}"
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo ""

# Check if oc is installed
if ! command -v oc &> /dev/null; then
    echo -e "${RED}Error: OpenShift CLI (oc) is not installed${NC}"
    echo "Please install it from: https://mirror.openshift.com/pub/openshift-v4/clients/ocp/"
    exit 1
fi

# Prompt for configuration
echo -e "${YELLOW}Please provide the following information:${NC}"
echo ""

read -p "GitLab Group/Username: " GITLAB_GROUP
read -p "GitLab Project Name [innovation-hub]: " GITLAB_PROJECT
GITLAB_PROJECT=${GITLAB_PROJECT:-innovation-hub}

read -p "OpenShift Cluster API URL: " OPENSHIFT_SERVER
read -sp "OpenShift Token: " OPENSHIFT_TOKEN
echo ""

read -p "GitLab Username: " GITLAB_USERNAME
read -sp "GitLab Token (with read_registry scope): " GITLAB_TOKEN
echo ""

read -sp "OpenRouter API Key: " OPENROUTER_KEY
echo ""
read -sp "OpenAI API Key: " OPENAI_KEY
echo ""

read -p "Application Domain [innovation-hub.apps.example.com]: " APP_DOMAIN
APP_DOMAIN=${APP_DOMAIN:-innovation-hub.apps.example.com}

read -p "Namespace [innovation-hub]: " NAMESPACE
NAMESPACE=${NAMESPACE:-innovation-hub}

echo ""
echo -e "${GREEN}Configuration summary:${NC}"
echo "  GitLab Repo: ${GITLAB_GROUP}/${GITLAB_PROJECT}"
echo "  OpenShift Server: ${OPENSHIFT_SERVER}"
echo "  Namespace: ${NAMESPACE}"
echo "  App Domain: ${APP_DOMAIN}"
echo ""
read -p "Continue with setup? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled"
    exit 1
fi

# Login to OpenShift
echo -e "${GREEN}1. Logging into OpenShift...${NC}"
oc login --token="${OPENSHIFT_TOKEN}" --server="${OPENSHIFT_SERVER}" --insecure-skip-tls-verify=true

# Create namespace
echo -e "${GREEN}2. Creating namespace...${NC}"
oc create namespace ${NAMESPACE} 2>/dev/null || echo "Namespace already exists"
oc project ${NAMESPACE}

# Create registry secret
echo -e "${GREEN}3. Creating GitLab registry credentials...${NC}"
oc delete secret gitlab-registry -n ${NAMESPACE} 2>/dev/null || true
oc create secret docker-registry gitlab-registry \
  --docker-server=registry.gitlab.com \
  --docker-username="${GITLAB_USERNAME}" \
  --docker-password="${GITLAB_TOKEN}" \
  --docker-email="${GITLAB_USERNAME}@gitlab.com" \
  -n ${NAMESPACE}

# Link secret to service account
oc secrets link default gitlab-registry --for=pull -n ${NAMESPACE}

# Create application secrets
echo -e "${GREEN}4. Creating application secrets...${NC}"
oc delete secret innovation-hub-secrets -n ${NAMESPACE} 2>/dev/null || true
oc create secret generic innovation-hub-secrets \
  --from-literal=OPENROUTER_API_KEY="${OPENROUTER_KEY}" \
  --from-literal=OPENAI_API_KEY="${OPENAI_KEY}" \
  -n ${NAMESPACE}

# Update configuration files
echo -e "${GREEN}5. Updating configuration files...${NC}"

# Update kustomization.yaml
sed -i "s|registry.gitlab.com/your-group/innovation-hub|registry.gitlab.com/${GITLAB_GROUP}/${GITLAB_PROJECT}|g" k8s/kustomization.yaml

# Update deployment.yaml
sed -i "s|registry.gitlab.com/your-group/innovation-hub|registry.gitlab.com/${GITLAB_GROUP}/${GITLAB_PROJECT}|g" k8s/deployment.yaml

# Update route.yaml
sed -i "s|innovation-hub.apps.your-cluster.example.com|${APP_DOMAIN}|g" k8s/route.yaml

# Update ArgoCD application
sed -i "s|https://gitlab.com/your-group/innovation-hub.git|https://gitlab.com/${GITLAB_GROUP}/${GITLAB_PROJECT}.git|g" argocd/application.yaml

# Update GitLab CI
sed -i "s|registry.gitlab.com/your-group/innovation-hub|registry.gitlab.com/${GITLAB_GROUP}/${GITLAB_PROJECT}|g" .gitlab-ci.yml
sed -i "s|innovation-hub.apps.your-cluster.example.com|${APP_DOMAIN}|g" .gitlab-ci.yml

# Create service account for GitLab CI
echo -e "${GREEN}6. Creating service account for GitLab CI...${NC}"
oc create serviceaccount gitlab-ci -n ${NAMESPACE} 2>/dev/null || echo "Service account already exists"
oc policy add-role-to-user admin system:serviceaccount:${NAMESPACE}:gitlab-ci -n ${NAMESPACE}

# Get service account token
SA_TOKEN=$(oc create token gitlab-ci -n ${NAMESPACE} --duration=8760h)

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Setup Complete!                   ║${NC}"
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Add these CI/CD variables to GitLab (Settings → CI/CD → Variables):"
echo ""
echo "   OPENSHIFT_SERVER: ${OPENSHIFT_SERVER}"
echo "   OPENSHIFT_TOKEN: ${SA_TOKEN}"
echo "   GITLAB_PUSH_TOKEN: <create a GitLab personal access token>"
echo ""
echo "2. Commit and push changes:"
echo "   git add ."
echo "   git commit -m 'Configure OpenShift deployment'"
echo "   git push origin main"
echo ""
echo "3. Deploy application:"
echo "   oc apply -k k8s/"
echo ""
echo "4. (Optional) Setup ArgoCD:"
echo "   oc apply -f argocd/application.yaml"
echo ""
echo "5. Access your application:"
echo "   https://${APP_DOMAIN}"
echo ""
echo -e "${GREEN}Deployment files have been updated in:${NC}"
echo "  - k8s/"
echo "  - argocd/"
echo "  - .gitlab-ci.yml"
echo ""
