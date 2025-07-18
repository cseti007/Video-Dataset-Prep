#!/bin/bash

# Usage: ./crop_and_split.sh input_video output_directory crop_top crop_bottom split_flag
# ./video_halfer_crop.sh e-DRtSV_OTA.mp4 cropped 100 100 yes

# Parameters
INPUT_VIDEO=$1
OUTPUT_DIR=$2
CROP_TOP=$3
CROP_BOTTOM=$4
SPLIT=$5

# Extract the base name (without extension) of the input video
BASE_NAME=$(basename "$INPUT_VIDEO" .mp4)

# Create output file names based on the original file name and the output directory
OUTPUT_FILE="${OUTPUT_DIR}/${BASE_NAME}_cropped.mp4"

# Get video dimensions (width and height)
VIDEO_DIMENSIONS=$(ffmpeg -i "$INPUT_VIDEO" 2>&1 | grep -oP 'Stream #0:0.*Video:.*\s(\d+)x(\d+)' | sed -E 's/.* ([0-9]+)x([0-9]+).*/\1 \2/')
WIDTH=$(echo $VIDEO_DIMENSIONS | cut -d ' ' -f 1)
HEIGHT=$(echo $VIDEO_DIMENSIONS | cut -d ' ' -f 2)

# Calculate the total height adjustment (from top and bottom)
CROP_HEIGHT=$((CROP_TOP + CROP_BOTTOM))

# If we need to split the video
if [[ "$SPLIT" == "yes" ]]; then
  # Split the width in half
  HALF_WIDTH=$((WIDTH / 2))

  # Create output names for the split video
  OUTPUT_LEFT="${OUTPUT_DIR}/${BASE_NAME}_left.mp4"
  OUTPUT_RIGHT="${OUTPUT_DIR}/${BASE_NAME}_right.mp4"

  # Crop both left and right halves, cropping specified pixels from top and bottom
  ffmpeg -i "$INPUT_VIDEO" -filter_complex \
  "[0]crop=$HALF_WIDTH:ih-$CROP_HEIGHT:0:$CROP_TOP[left];[0]crop=$HALF_WIDTH:ih-$CROP_HEIGHT:$HALF_WIDTH:$CROP_TOP[right]" \
  -map "[left]" "$OUTPUT_LEFT" -map "[right]" "$OUTPUT_RIGHT"

  echo "Left and Right videos created in $OUTPUT_DIR: $OUTPUT_LEFT, $OUTPUT_RIGHT"
else
  # Crop the video without splitting
  ffmpeg -i "$INPUT_VIDEO" -vf "crop=iw:ih-$CROP_HEIGHT:0:$CROP_TOP" "$OUTPUT_FILE"
  echo "Cropped video created: $OUTPUT_FILE"
fi

