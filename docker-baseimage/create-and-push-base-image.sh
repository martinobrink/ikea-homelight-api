#!/bin/sh

# Stop on errors
set -e

DOCKERFILE="Dockerfile"
DOCKER_IMAGE_NAME="ikea-homelight-baseimage"
DOCKER_REPO_NAME="martinobrink" #replace with your own repo name if necessary to create own base image
OSX_TZ=$(ls -la /etc/localtime | cut -d/ -f8-9)
MACHINE=$(uname -m)
PWD=$(pwd)

docker build -t $DOCKER_IMAGE_NAME -f "$PWD/$DOCKERFILE" .

docker run \
  --net=host \
  --env "TZ=$OSX_TZ" \
  --volume `pwd`:/usr/src/app \
  --rm \
  $DOCKER_IMAGE_NAME

docker tag $DOCKER_IMAGE_NAME $DOCKER_REPO_NAME/$DOCKER_IMAGE_NAME

# Ensure you have run 'docker login' in your terminal before you can 
# successfully complete command below 
docker push $DOCKER_REPO_NAME/$DOCKER_IMAGE_NAME