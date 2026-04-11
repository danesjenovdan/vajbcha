#!/usr/bin/env bash

# exit immediately if a command exits with a non-zero status
set -e

# check if mypy is installed
if ! command -v mypy &> /dev/null
then
    echo "mypy could not be found, please install it to check types"
    exit 1
fi

# change directory to the app directory
cd ./vajbcha

# run mypy
echo "Checking types..."
mypy .
