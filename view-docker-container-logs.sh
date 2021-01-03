#!/bin/sh
docker logs -f `docker ps | grep "ikea-homelight-api-server" | awk '{ print $1 }'`