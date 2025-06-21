#!/bin/bash
# Upload a sample video for demo purposes

echo "Creating sample video with ffmpeg..."
ffmpeg -f lavfi -i testsrc=duration=5:size=640x480:rate=30 -c:v libx264 sample_input.mp4 -y

echo "Creating upscaled demo output..."
ffmpeg -i sample_input.mp4 -vf scale=1280:720 -c:v libx264 -crf 18 sample_output.mp4 -y

echo "Uploading to GCS..."
gsutil cp sample_output.mp4 gs://seedvr2-videos/samples/demo_output.mp4
gsutil acl ch -u AllUsers:R gs://seedvr2-videos/samples/demo_output.mp4

echo "Demo video uploaded!"
echo "URL: https://storage.googleapis.com/seedvr2-videos/samples/demo_output.mp4"

# Cleanup
rm -f sample_input.mp4 sample_output.mp4