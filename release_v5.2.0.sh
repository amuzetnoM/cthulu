#!/bin/bash
# Release Script for v5.2.0
# This script pushes the tag and triggers the release workflow

set -e

echo "=== Cthulu v5.2.0 Release Script ==="
echo ""
echo "This script will:"
echo "1. Push the v5.2.0 tag to GitHub"
echo "2. Trigger the Docker build and publish workflow"
echo "3. Create the GitHub release automatically"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "Error: Must be run from the repository root"
    exit 1
fi

# Check if tag exists locally
if ! git tag -l | grep -q "^v5.2.0$"; then
    echo "Error: Tag v5.2.0 not found locally"
    exit 1
fi

echo "Pushing tag v5.2.0 to origin..."
git push origin v5.2.0

echo ""
echo "✅ Tag pushed successfully!"
echo ""
echo "The following will happen automatically:"
echo "1. GitHub Actions workflow 'docker-publish.yml' will be triggered"
echo "2. Docker image will be built for linux/amd64 and linux/arm64"
echo "3. Image will be pushed to ghcr.io/amuzetnoM/cthulu:v5.2.0"
echo "4. Image will also be tagged as ghcr.io/amuzetnoM/cthulu:5.2"
echo "5. GitHub release will be created with release notes"
echo ""
echo "Monitor the workflow at:"
echo "https://github.com/amuzetnoM/cthulu/actions/workflows/docker-publish.yml"
echo ""
echo "Once complete, the release will be available at:"
echo "https://github.com/amuzetnoM/cthulu/releases/tag/v5.2.0"
echo ""
echo "Docker image will be available at:"
echo "docker pull ghcr.io/amuzetnoM/cthulu:v5.2.0"
echo "docker pull ghcr.io/amuzetnoM/cthulu:5.2"
