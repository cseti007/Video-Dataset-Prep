#!/bin/bash

# Check if the correct number of arguments is passed
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <input_dir_or_video> <output_dir> <speed_factor>"
    exit 1
fi

# Assign the command-line arguments to variables
input="$1"
output_dir="$2"
speed_factor="$3"

# Create output directory if it doesn't exist
mkdir -p "$output_dir"

# If the input is a directory, process all .mp4 files in it
if [ -d "$input" ]; then
    # Loop through all .mp4 files in the input directory
    for video in "$input"/*.mp4; do
        # Get the filename without the extension
        filename=$(basename "$video" .mp4)
        
        # Apply video speed-up (setpts)
        video_filter="setpts=1/${speed_factor}*PTS"

        # Apply audio speed-up (atempo)
        if (( $(echo "$speed_factor > 2.0" | bc -l) )); then
            atempo_filters="atempo=2.0,atempo=$(echo "$speed_factor/2.0" | bc -l)"
        else
            atempo_filters="atempo=${speed_factor}"
        fi
        
        # Apply speed-up effect (video and audio)
        ffmpeg -i "$video" -filter:v "$video_filter" -filter:a "$atempo_filters" "$output_dir/${filename}_sped_up.mp4"
    done
# If the input is a file, process that single video
elif [ -f "$input" ]; then
    # Get the filename without the extension
    filename=$(basename "$input" .mp4)
    
    # Apply video speed-up (setpts)
    video_filter="setpts=1/${speed_factor}*PTS"

    # Apply audio speed-up (atempo)
    if (( $(echo "$speed_factor > 2.0" | bc -l) )); then
        atempo_filters="atempo=2.0,atempo=$(echo "$speed_factor/2.0" | bc -l)"
    else
        atempo_filters="atempo=${speed_factor}"
    fi
    
    # Apply speed-up effect (video and audio)
    ffmpeg -i "$input" -filter:v "$video_filter" -filter:a "$atempo_filters" "$output_dir/${filename}_sped_up.mp4"
else
    echo "Error: Input is neither a directory nor a file"
    exit 1
fi

echo "Processing completed."

