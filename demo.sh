#!/bin/bash
echo "start deployment..."
PROJECT_NAME1=$3
if [ -z "PROJECT_NAME1" ]; then
echo "error, folder not found"
echo "use: ./deploy.sh <project_name>"
exit 1
fi
mkdir "PROJECT_NAME1"
STATUS=$?
if [ $STATUS -ne 0 ]; then
echo "Error: failed to create to directory: $PROJECT_NAME1"
exit 1
fi
echo "success: $PROJECT_NAME1"
exit 0