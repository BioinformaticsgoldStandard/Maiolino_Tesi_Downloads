#!/usr/bin/env bash
set -Eeuo pipefail

IMAGE="ghcr.io/bioinformaticsgoldstandard/maiolino_tesi_downloads:latest"

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker is not installed or is not in PATH." >&2
    exit 1
fi

read -r -p "Enter the host directory to use for downloaded datasets [$(pwd)]: " BASE_DIR
BASE_DIR="${BASE_DIR:-$(pwd)}"

# Expand a leading ~/ and create the directory if necessary.
if [[ "$BASE_DIR" == "~/"* ]]; then
    BASE_DIR="${HOME}/${BASE_DIR#~/}"
elif [[ "$BASE_DIR" == "~" ]]; then
    BASE_DIR="$HOME"
fi

mkdir -p -- "$BASE_DIR"
BASE_DIR="$(cd -- "$BASE_DIR" && pwd -P)"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "Error: Docker image '$IMAGE' was not found."
    echo "Build it first with: docker build -t $IMAGE ."
    exit 1
fi

CONTAINER_NAME="tesi-geo-download-$(date +%Y%m%d-%H%M%S)"

echo "Host directory: $BASE_DIR"
echo "Starting container: $CONTAINER_NAME"

docker run -d \
    --name "$CONTAINER_NAME" \
    --mount "type=bind,source=$BASE_DIR,target=/data" \
    --workdir /data \
    "$IMAGE"

echo
echo "Container started in detached mode."
echo "Follow its output with:"
echo "  docker logs -f $CONTAINER_NAME"
echo
echo "Check its status with:"
echo "  docker ps -a --filter name=$CONTAINER_NAME"
echo
echo "Stop it with:"
echo "  docker stop $CONTAINER_NAME"
