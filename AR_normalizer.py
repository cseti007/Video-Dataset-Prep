#!/usr/bin/env python3
"""
Video Aspect Ratio Normalizer
Converts all videos in a folder to a target aspect ratio without deformation
Uses letterboxing/pillarboxing to maintain original proportions
"""

import os
import subprocess
import argparse
import shutil
from pathlib import Path

def get_video_info(video_path):
    """Get video dimensions using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams',
            '-select_streams', 'v:0', str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        import json
        data = json.loads(result.stdout)
        
        if 'streams' in data and len(data['streams']) > 0:
            stream = data['streams'][0]
            width = int(stream['width'])
            height = int(stream['height'])
            return width, height
        return None, None
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
        return None, None

def calculate_output_dimensions(input_width, input_height, target_width, target_height):
    """Calculate crop dimensions from original video size"""
    input_ar = input_width / input_height
    target_ar = target_width / target_height
    
    if input_ar > target_ar:
        # Input is wider - crop width, keep height
        crop_width = int(input_height * target_ar)
        crop_height = input_height
        # Ensure even width
        crop_width = crop_width - (crop_width % 2)
    else:
        # Input is taller - crop height, keep width  
        crop_width = input_width
        crop_height = int(input_width / target_ar)
        # Ensure even height
        crop_height = crop_height - (crop_height % 2)
    
    return crop_width, crop_height

def normalize_video(input_path, output_path, target_width, target_height, target_aspect_ratio=None):
    """Normalize a single video to target aspect ratio using crop method"""
    
    # Get input video dimensions
    input_width, input_height = get_video_info(input_path)
    if not input_width or not input_height:
        print(f"Error: Could not get dimensions for {input_path}")
        return False
    
    # Calculate input aspect ratio
    input_aspect_ratio = input_width / input_height
    
    # Determine target aspect ratio
    if target_aspect_ratio is None and target_width and target_height:
        target_aspect_ratio = target_width / target_height
    elif target_aspect_ratio is None:
        print(f"Error: No target dimensions or aspect ratio specified")
        return False
    
    # Check if input already matches target aspect ratio (within tolerance)
    aspect_ratio_tolerance = 0.01
    if abs(input_aspect_ratio - target_aspect_ratio) < aspect_ratio_tolerance:
        print(f"Copying: {input_path.name} (already correct AR: {input_aspect_ratio:.2f})")
        try:
            shutil.copy2(input_path, output_path)
            print(f"  ✓ Success: {output_path.name}")
            return True
        except Exception as e:
            print(f"  ✗ Error copying {input_path.name}: {e}")
            return False
    
    # If target dimensions are None, calculate from input dimensions and aspect ratio
    if target_width is None and target_height is None:
        # Use the larger dimension as reference to maintain quality
        if input_width >= input_height:
            target_width = input_width
            target_height = int(input_width / target_aspect_ratio)
        else:
            target_height = input_height
            target_width = int(input_height * target_aspect_ratio)
        
        # Ensure even dimensions for video encoding
        target_width = target_width - (target_width % 2)
        target_height = target_height - (target_height % 2)
    
    # Calculate crop dimensions
    crop_width, crop_height = calculate_output_dimensions(
        input_width, input_height, target_width, target_height
    )
    
    # Build FFmpeg command - crop from center, then scale to target size
    # Use copy streams when possible to preserve original quality
    video_filter = f'crop={crop_width}:{crop_height},scale={target_width}:{target_height}'
    
    cmd = [
        'ffmpeg', '-i', str(input_path),
        '-vf', video_filter,
        '-c:v', 'libx264',
        '-crf', '18',  # High quality
        '-preset', 'slow',  # Better compression
        '-c:a', 'copy',  # Copy audio without re-encoding
        '-y',  # Overwrite output file if it exists
        str(output_path)
    ]
    
    print(f"Processing: {input_path.name}")
    print(f"  Input: {input_width}x{input_height} (AR: {input_width/input_height:.2f})")
    
    # Calculate what gets cropped
    input_ar = input_width / input_height
    target_ar = target_width / target_height
    
    if input_ar > target_ar:
        print(f"  Crop: {crop_width}x{crop_height} (cropping {input_width - crop_width}px from width)")
    else:
        print(f"  Crop: {crop_width}x{crop_height} (cropping {input_height - crop_height}px from height)")
    
    print(f"  Final: {target_width}x{target_height} (AR: {target_width/target_height:.2f})")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"  ✓ Success: {output_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Error processing {input_path.name}: {e}")
        print(f"  FFmpeg error: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Normalize video aspect ratios using crop method')
    parser.add_argument('input_folder', help='Input folder containing videos')
    parser.add_argument('output_folder', help='Output folder for normalized videos')
    parser.add_argument('--aspect-ratio', type=float, default=1.78, help='Target aspect ratio (default: 1.78 for 16:9)')
    parser.add_argument('--width', type=int, help='Target width (optional, calculated from input if not specified)')
    parser.add_argument('--height', type=int, help='Target height (optional, calculated from input if not specified)')
    
    args = parser.parse_args()
    
    # Validate dimension arguments
    if args.width and args.height:
        print("Error: Specify either --width or --height, not both")
        return
    
    # Calculate target dimensions from aspect ratio if needed
    target_width = None
    target_height = None
    
    if args.width:
        target_width = args.width
        target_height = int(args.width / args.aspect_ratio)
        # Ensure even height for video encoding
        target_height = target_height - (target_height % 2)
    elif args.height:
        target_height = args.height
        target_width = int(args.height * args.aspect_ratio)
        # Ensure even width for video encoding
        target_width = target_width - (target_width % 2)
    # If neither width nor height specified, they remain None and will be calculated per video
    
    input_folder = Path(args.input_folder)
    output_folder = Path(args.output_folder)
    
    # Validate input folder
    if not input_folder.exists():
        print(f"Error: Input folder '{input_folder}' does not exist")
        return
    
    # Create output folder
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # Find video files - common video extensions
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.m4v', '.wmv', '.flv', '.webm']
    video_files = []
    for ext in video_extensions:
        video_files.extend(input_folder.glob(f'*{ext}'))
        video_files.extend(input_folder.glob(f'*{ext.upper()}'))
    
    if not video_files:
        print(f"No video files found in '{input_folder}'")
        return
    
    print(f"Found {len(video_files)} video files")
    if target_width and target_height:
        print(f"Target resolution: {target_width}x{target_height} (AR: {target_width/target_height:.2f})")
    else:
        print(f"Target aspect ratio: {args.aspect_ratio:.2f} (resolution calculated per video)")
    print(f"Method: crop (content may be lost from edges)")
    print(f"Quality: highest (original quality preserved when possible)")
    print("=" * 60)
    
    # Process each video
    success_count = 0
    for video_file in video_files:
        output_file = output_folder / f"{video_file.stem}_normalized{video_file.suffix}"
        
        if normalize_video(video_file, output_file, target_width, target_height, args.aspect_ratio):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"Processed {success_count}/{len(video_files)} videos successfully")

if __name__ == '__main__':
    main()