#!/bin/sh

# Execution Flow:
#   Parse Token from package.json
#   Derive variables
#   IF `docker` arg is supplied, build using docker
#     Check for docker executable
#     Delete old `deimosc2_vue` images
#     Delete old frontend files from Go Server and local `dist` directory
#     Build `deimosc2_vue` Docker Image
#     Start `deimosc2_vue` container
#     Copy frontend build from container
#     Kill container
#     Copy frontend file from `dist` directory to Deimos Go Server
#   ELSE build with NPM
#     Check for NPM executable
#     execute `npm run build`
#     Delete old frontend files from Go Server and local `dist` directory
#     Copy frontend file from `dist` directory to Deimos Go Server


DELETE_FRONTEND () {
  echo "** Deleting old files..."
  rm -rf ./resources/frontend/static/*
  rm -rf ./frontend/dist/*
}

COPY_FRONTEND () {
  echo "Copying Frontend to Deimos Server..."
  cp -r ./frontend/dist/* ../../resources/frontend/static/
}

# Extract version number
VERSION=$(grep \"version\" ./frontend/package.json | grep -o '[0-9]\.[0-9]\.[0-9]')
IMAGE=deimosc2_vue:$VERSION
NAME=deimos-build

if [ "$1" = "docker" ]
  then
    echo "** Docker Building Version $VERSION"

    #Checking for Docker executable
    if ! command -v docker > /dev/null
      then
          echo "Docker could not be found"
          exit 1
    fi

    #Deleting old Docker Images
    echo "** Notice: Deleting old images"
    for i in $(docker images --format "{{.ID}}" "$IMAGE")
      do
        docker rmi "$i"
    done

    DELETE_FRONTEND

    echo "** Building $NAME from $IMAGE..."
    docker build -t "$IMAGE" -f ./DockerFrontend .

    echo "** Starting container $NAME..."
    docker run --rm --detach --name $NAME "$IMAGE"

    echo "** Copying from container $NAME..."
    docker cp $NAME:/app/dist .

    echo "** Killing container $NAME..."
    docker kill "$NAME"

    COPY_FRONTEND

else
  echo "** NPM Building Version $VERSION"

  #Checking for Docker executable
  if ! command -v npm > /dev/null
    then
        echo "NPM could not be found"
        exit 1
  fi

  npm run build
  DELETE_FRONTEND
  COPY_FRONTEND
fi

