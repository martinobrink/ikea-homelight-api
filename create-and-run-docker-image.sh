#!/bin/sh

# Stop on errors
set -e

DOCKERFILE="Dockerfile"
DOCKER_IMAGE_NAME="ikea-homelight-api-server"
OSX_TZ=$(ls -la /etc/localtime | cut -d/ -f8-9)
MACHINE=$(uname -m)
PWD=$(pwd)
DOCKER_RUNNING_CONTAINER_ID=$(docker ps | grep "ikea-homelight-api-server" | awk '{ print $1 }')

#removes currently running docker container in order to release currently used port
docker rm -f $DOCKER_RUNNING_CONTAINER_ID || true 

docker build -t $DOCKER_IMAGE_NAME -f "$PWD/$DOCKERFILE" .

docker run -d -p 5000:5000 --env "TZ=$OSX_TZ" --rm $DOCKER_IMAGE_NAME
