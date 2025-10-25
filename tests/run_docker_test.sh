#!/bin/bash

set -e

# Build the executable
conda run -n ocr-my-mess python ../scripts/build.py

# Build the docker image
docker build -t ocr-my-mess-test -f Dockerfile ..

# Run the test inside the docker container
docker run ocr-my-mess-test
