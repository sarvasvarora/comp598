#!/bin/bash

# stop all running containers
echo '####################################################'
echo 'Stopping running containers (if available)...'
echo '####################################################'
docker stop $(docker ps -aq)

# remove all stopped containers
echo '####################################################'
echo 'Removing containers ..'
echo '####################################################'
docker rm $(docker ps -aq)

echo '####################################################'
echo 'Cleaning jobs folder ..'
echo '####################################################'
rm -rf jobs
mkdir jobs
chmod -R 777 jobs