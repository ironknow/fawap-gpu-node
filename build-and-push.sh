#!/bin/bash
# Build and push GPU Node Docker image to Docker Hub with versioning
#
# Usage: ./build-and-push.sh [VERSION]
#   - If VERSION is provided, uses that version
#   - If VERSION is not provided, reads from VERSION file
#   - If VERSION file doesn't exist, prompts for version
#
# Example: ./build-and-push.sh 1.0.0
# Example: ./build-and-push.sh  (reads from VERSION file)
#
# Creates tags: latest, v1.0.0, 1.0.0
# Pushes to: YOUR_DOCKERHUB_USERNAME/fawap-gpu-node

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="fawap-gpu-node"
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-YOUR_DOCKERHUB_USERNAME}"

# Check if Docker Hub username is set
if [ "$DOCKERHUB_USERNAME" = "YOUR_DOCKERHUB_USERNAME" ]; then
    echo -e "${RED}Error: DOCKERHUB_USERNAME not set${NC}"
    echo "Please set it as an environment variable:"
    echo "  export DOCKERHUB_USERNAME=your-username"
    echo "Or edit this script and replace YOUR_DOCKERHUB_USERNAME"
    exit 1
fi

# Get version from argument, VERSION file, or prompt
if [ -n "$1" ]; then
    # Version provided as argument (override)
    VERSION="$1"
    VERSION_SOURCE="command line argument"
elif [ -f "VERSION" ]; then
    # Read version from VERSION file
    VERSION=$(cat VERSION | tr -d '[:space:]')
    VERSION_SOURCE="VERSION file"
    if [ -z "$VERSION" ]; then
        echo -e "${RED}Error: VERSION file is empty${NC}"
        exit 1
    fi
    echo -e "${GREEN}Using version from VERSION file: ${VERSION}${NC}"
else
    # No VERSION file, prompt user
    echo -e "${YELLOW}No version specified and VERSION file not found.${NC}"
    read -p "Enter version number (e.g., 1.0.0): " VERSION
    if [ -z "$VERSION" ]; then
        echo -e "${RED}Error: Version is required${NC}"
        exit 1
    fi
    VERSION_SOURCE="user input"
fi

# Validate version format (semantic versioning: X.Y.Z)
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo -e "${YELLOW}Warning: Version '$VERSION' doesn't match semantic versioning (X.Y.Z)${NC}"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Full image name
FULL_IMAGE_NAME="${DOCKERHUB_USERNAME}/${IMAGE_NAME}"

echo -e "${GREEN}Building and pushing ${FULL_IMAGE_NAME}${NC}"
echo -e "Version: ${VERSION} (from ${VERSION_SOURCE})"
echo ""

# Check if logged in to Docker Hub
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}Not logged in to Docker Hub. Attempting login...${NC}"
    docker login
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Docker login failed${NC}"
        exit 1
    fi
fi

# Build the image
echo -e "${GREEN}Step 1: Building Docker image...${NC}"
docker build -t "${FULL_IMAGE_NAME}:latest" \
             -t "${FULL_IMAGE_NAME}:v${VERSION}" \
             -t "${FULL_IMAGE_NAME}:${VERSION}" \
             .

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker build failed${NC}"
    exit 1
fi

echo -e "${GREEN}Build successful!${NC}"
echo ""

# Show tags
echo -e "${GREEN}Step 2: Image tagged as:${NC}"
echo "  - ${FULL_IMAGE_NAME}:latest"
echo "  - ${FULL_IMAGE_NAME}:v${VERSION}"
echo "  - ${FULL_IMAGE_NAME}:${VERSION}"
echo ""

# Confirm before pushing
read -p "Push to Docker Hub? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Push cancelled. Image built locally with tags.${NC}"
    exit 0
fi

# Push all tags
echo -e "${GREEN}Step 3: Pushing to Docker Hub...${NC}"
docker push "${FULL_IMAGE_NAME}:latest"
docker push "${FULL_IMAGE_NAME}:v${VERSION}"
docker push "${FULL_IMAGE_NAME}:${VERSION}"

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Docker push failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Successfully pushed to Docker Hub!${NC}"
echo ""
echo "Image available at:"
echo "  https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${IMAGE_NAME}"
echo ""
echo "Pull commands:"
echo "  docker pull ${FULL_IMAGE_NAME}:latest"
echo "  docker pull ${FULL_IMAGE_NAME}:v${VERSION}"
echo "  docker pull ${FULL_IMAGE_NAME}:${VERSION}"

