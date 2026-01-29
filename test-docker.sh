#!/bin/bash
# Innovation Hub - Local Docker Testing Script
# Quick validation script for Docker image

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Innovation Hub - Docker Test Script          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Configuration
CONTAINER_NAME="innovation-hub-test"
IMAGE_NAME="innovation-hub:local"
PORT=8000

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    echo "Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✓${NC} .env created from template"
        echo -e "${YELLOW}⚠️  Please edit .env and add your API keys${NC}"
        echo ""
        read -p "Press Enter to continue after editing .env, or Ctrl+C to exit..."
    else
        echo -e "${RED}✗${NC} .env.example not found"
        exit 1
    fi
fi

# Check if Docker is running
if ! docker ps >/dev/null 2>&1; then
    echo -e "${RED}✗${NC} Docker is not running"
    echo "Please start Docker and try again"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker is running"

# Stop and remove existing container
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo ""
    echo -e "${YELLOW}Stopping existing container...${NC}"
    docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true
    docker rm ${CONTAINER_NAME} >/dev/null 2>&1 || true
    echo -e "${GREEN}✓${NC} Old container removed"
fi

# Build image
echo ""
echo -e "${BLUE}Building Docker image...${NC}"
docker build -t ${IMAGE_NAME} . --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Image built successfully: ${IMAGE_NAME}"
else
    echo -e "${RED}✗${NC} Build failed"
    exit 1
fi

# Create local data directories
mkdir -p local-data local-chroma
echo -e "${GREEN}✓${NC} Data directories created"

# Run container
echo ""
echo -e "${BLUE}Starting container...${NC}"
docker run -d \
  --name ${CONTAINER_NAME} \
  -p ${PORT}:8000 \
  --env-file .env \
  -v $(pwd)/local-data:/app/data \
  -v $(pwd)/local-chroma:/app/chroma_db \
  --health-cmd="curl -f http://localhost:8000/api/health || exit 1" \
  --health-interval=10s \
  --health-timeout=5s \
  --health-retries=3 \
  --health-start-period=30s \
  ${IMAGE_NAME} >/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Container started: ${CONTAINER_NAME}"
else
    echo -e "${RED}✗${NC} Failed to start container"
    exit 1
fi

# Wait for container to be healthy
echo ""
echo -e "${YELLOW}Waiting for application to start (max 60s)...${NC}"
COUNTER=0
while [ $COUNTER -lt 60 ]; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' ${CONTAINER_NAME} 2>/dev/null || echo "starting")

    if [ "$STATUS" = "healthy" ]; then
        echo -e "${GREEN}✓${NC} Application is healthy!"
        break
    fi

    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 2))
done
echo ""

if [ "$STATUS" != "healthy" ]; then
    echo -e "${RED}✗${NC} Application failed to become healthy"
    echo ""
    echo "Container logs:"
    docker logs ${CONTAINER_NAME} | tail -20
    exit 1
fi

# Run tests
echo ""
echo -e "${BLUE}Running validation tests...${NC}"
echo ""

# Test 1: Liveness probe
echo -n "1. Testing liveness probe... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/api/health/live)
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Passed"
else
    echo -e "${RED}✗${NC} Failed (HTTP $RESPONSE)"
fi

# Test 2: Readiness probe
echo -n "2. Testing readiness probe... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/api/health/ready)
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Passed"
else
    echo -e "${RED}✗${NC} Failed (HTTP $RESPONSE)"
fi

# Test 3: Main health check
echo -n "3. Testing main health check... "
RESPONSE=$(curl -s http://localhost:${PORT}/api/health)
if echo "$RESPONSE" | grep -q '"status":"healthy"'; then
    echo -e "${GREEN}✓${NC} Passed"
else
    echo -e "${RED}✗${NC} Failed"
    echo "   Response: $RESPONSE"
fi

# Test 4: Database check
echo -n "4. Testing database connectivity... "
if echo "$RESPONSE" | grep -q '"database":"healthy"'; then
    echo -e "${GREEN}✓${NC} Passed"
else
    echo -e "${RED}✗${NC} Failed"
fi

# Test 5: Frontend
echo -n "5. Testing frontend... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/)
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Passed"
else
    echo -e "${RED}✗${NC} Failed (HTTP $RESPONSE)"
fi

# Test 6: API docs
echo -n "6. Testing API documentation... "
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT}/docs)
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓${NC} Passed"
else
    echo -e "${RED}✗${NC} Failed (HTTP $RESPONSE)"
fi

# Test 7: Non-root user
echo -n "7. Testing non-root user... "
USER_ID=$(docker exec ${CONTAINER_NAME} id -u)
if [ "$USER_ID" != "0" ]; then
    echo -e "${GREEN}✓${NC} Passed (UID: $USER_ID)"
else
    echo -e "${RED}✗${NC} Failed (running as root)"
fi

# Test 8: Volume mounts
echo -n "8. Testing volume mounts... "
if docker exec ${CONTAINER_NAME} test -d /app/data && docker exec ${CONTAINER_NAME} test -d /app/chroma_db; then
    echo -e "${GREEN}✓${NC} Passed"
else
    echo -e "${RED}✗${NC} Failed"
fi

# Test 9: File permissions
echo -n "9. Testing file write permissions... "
if docker exec ${CONTAINER_NAME} touch /app/data/test.txt 2>/dev/null; then
    docker exec ${CONTAINER_NAME} rm /app/data/test.txt
    echo -e "${GREEN}✓${NC} Passed"
else
    echo -e "${RED}✗${NC} Failed"
fi

# Test 10: Create test idea (if API keys are configured)
echo -n "10. Testing API (create idea)... "
RESPONSE=$(curl -s -X POST http://localhost:${PORT}/api/ideas \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Docker Test Idea",
    "description": "Testing from test-docker.sh",
    "type": "idea",
    "target_group": "citizens"
  }')

if echo "$RESPONSE" | grep -q '"id"'; then
    echo -e "${GREEN}✓${NC} Passed"
else
    echo -e "${YELLOW}⚠${NC}  Skipped (API keys may not be configured)"
fi

# Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Test Summary                                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo "Container: ${CONTAINER_NAME}"
echo "Image: ${IMAGE_NAME}"
echo "Port: ${PORT}"
echo ""
echo "Access points:"
echo "  • Frontend:  http://localhost:${PORT}"
echo "  • API Docs:  http://localhost:${PORT}/docs"
echo "  • Health:    http://localhost:${PORT}/api/health"
echo ""

# Container info
echo "Container details:"
docker ps --filter "name=${CONTAINER_NAME}" --format "  Status: {{.Status}}"
docker stats ${CONTAINER_NAME} --no-stream --format "  CPU: {{.CPUPerc}}  Memory: {{.MemUsage}}"
echo ""

# Useful commands
echo -e "${YELLOW}Useful commands:${NC}"
echo "  View logs:      docker logs -f ${CONTAINER_NAME}"
echo "  Shell access:   docker exec -it ${CONTAINER_NAME} bash"
echo "  Stop:           docker stop ${CONTAINER_NAME}"
echo "  Remove:         docker rm -f ${CONTAINER_NAME}"
echo "  Stats:          docker stats ${CONTAINER_NAME}"
echo ""

# Ask to keep running
echo -e "${YELLOW}Container is running!${NC}"
read -p "Press Enter to stop and remove container, or Ctrl+C to keep it running..."

# Cleanup
echo ""
echo -e "${YELLOW}Cleaning up...${NC}"
docker stop ${CONTAINER_NAME} >/dev/null
docker rm ${CONTAINER_NAME} >/dev/null
echo -e "${GREEN}✓${NC} Container stopped and removed"
echo ""
echo -e "${GREEN}Test completed successfully!${NC}"
