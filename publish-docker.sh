#!/bin/bash
# Script to build and publish Docker image to Docker Hub
# Usage: ./publish-docker.sh [version]

set -e

# Configuration
IMAGE_NAME="xtamtamx/pickaxe-rcon"  # Change to your Docker Hub username
VERSION="${1:-latest}"

echo "⛏️  Building and Publishing Pickaxe RCON"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Build for multiple platforms
echo "📦 Building multi-platform image..."
echo "Platforms: linux/amd64, linux/arm64"
echo ""

# Create buildx builder if it doesn't exist
if ! docker buildx ls | grep -q "multiplatform"; then
    echo "Creating buildx builder..."
    docker buildx create --name multiplatform --use
fi

# Build and push
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag "${IMAGE_NAME}:${VERSION}" \
    --tag "${IMAGE_NAME}:latest" \
    --push \
    .

echo ""
echo "✅ Successfully published!"
echo ""
echo "Image: ${IMAGE_NAME}:${VERSION}"
echo "Latest: ${IMAGE_NAME}:latest"
echo ""
echo "Users can now pull with:"
echo "  docker pull ${IMAGE_NAME}:latest"
echo ""
echo "📝 Don't forget to:"
echo "  1. Update README.md with the correct image name"
echo "  2. Create a GitHub release with tag v${VERSION}"
echo "  3. Update CHANGELOG.md"
echo ""
