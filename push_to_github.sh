#!/bin/bash

# Simple Git push helper script for SeedVr2Test

cd ~/Desktop/SeedVr2Test

# Add all changes
git add -A

# Commit with a message (use first argument or default message)
if [ -z "$1" ]; then
    COMMIT_MSG="Update from helper script $(date '+%Y-%m-%d %H:%M:%S')"
else
    COMMIT_MSG="$1"
fi

git commit -m "$COMMIT_MSG"

# Push to origin
git push origin main

echo "Push completed!"
