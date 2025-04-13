#!/usr/bin/env python3
import os
import sys
import shutil
import argparse
import cv2
from pathlib import Path


def get_frame_count(video_path):
    """Get the total number of frames in an MP4 file using OpenCV."""
    try:
        video = cv2.VideoCapture(str(video_path))
        if not video.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return None
            
        # Get frame count
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        video.release()
        return frame_count
    except Exception as e:
        print(f"Error processing {video_path}: {e}")
        return None


def find_closest_smaller_bucket(frame_count, buckets):
    """Find the closest bucket that is smaller than or equal to the frame count."""
    valid_buckets = [b for b in buckets if b <= frame_count]
    if not valid_buckets:
        return None
    return max(valid_buckets)


def organize_videos_by_frame_count(input_folder, buckets, output_folder=None):
    """
    Organize MP4 files into buckets based on frame count.
    
    Args:
        input_folder: Path to folder containing MP4 files
        buckets: List of frame count buckets
        output_folder: Base output folder (defaults to input_folder if not specified)
    """
    input_path = Path(input_folder)
    
    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Input folder '{input_folder}' does not exist or is not a directory")
        return
    
    # Sort buckets in ascending order
    buckets = sorted(buckets)
    print(f"Using buckets: {buckets}")
    
    # If output folder not specified, use input folder
    if output_folder is None:
        output_path = input_path
    else:
        output_path = Path(output_folder)
        os.makedirs(output_path, exist_ok=True)
    
    # Will create bucket folders only when needed
    bucket_folders = {}
    # Map which files go to which bucket first without creating folders
    bucket_assignments = {}
    
    # Find all MP4 files
    mp4_files = list(input_path.glob("**/*.mp4"))
    total_files = len(mp4_files)
    print(f"Found {total_files} MP4 files")
    
    # Process each file
    processed = 0
    skipped = 0
    
    for video_file in mp4_files:
        processed += 1
        print(f"Processing {processed}/{total_files}: {video_file.name}", end="")
        
        # Get frame count
        frame_count = get_frame_count(video_file)
        if frame_count is None:
            print(" - SKIPPED (could not determine frame count)")
            skipped += 1
            continue
            
        print(f" - {frame_count} frames", end="")
        
        # Find appropriate bucket
        bucket = find_closest_smaller_bucket(frame_count, buckets)
        if bucket is None:
            print(f" - SKIPPED (no suitable bucket)")
            skipped += 1
            continue
            
        # Add to bucket assignments
        if bucket not in bucket_assignments:
            bucket_assignments[bucket] = []
        
        bucket_assignments[bucket].append(video_file)
        print(f" - assigned to bucket_{bucket}_frames")
    
    # Now create only the folders we need and copy files
    print("\nCreating bucket folders and copying files...")
    
    for bucket, files in bucket_assignments.items():
        if not files:  # Skip empty buckets
            continue
            
        # Create bucket folder
        bucket_folder = output_path / f"bucket_{bucket}_frames"
        os.makedirs(bucket_folder, exist_ok=True)
        print(f"Created {bucket_folder} for {len(files)} files")
        
        # Copy files to bucket folder
        copied = 0
        for video_file in files:
            dest_file = bucket_folder / video_file.name
            
            # Check if file already exists at destination
            if dest_file.exists():
                print(f"  Skipped {video_file.name} (already exists in bucket)")
                skipped += 1
                continue
                
            try:
                shutil.copy2(video_file, bucket_folder)
                copied += 1
            except Exception as e:
                print(f"  Error copying {video_file.name}: {str(e)}")
                skipped += 1
                
        print(f"  Copied {copied} files to bucket_{bucket}_frames")
    
    print(f"\nSummary:")
    print(f"  Total MP4 files: {total_files}")
    print(f"  Successfully processed: {total_files - skipped}")
    print(f"  Skipped: {skipped}")
    print(f"  Number of buckets created: {len(bucket_assignments)}")


def main():
    parser = argparse.ArgumentParser(description="Organize MP4 files into buckets based on frame count")
    parser.add_argument("input_folder", help="Folder containing MP4 files to analyze")
    parser.add_argument("--buckets", "-b", required=True, type=str, 
                        help="Frame count buckets, comma-separated (e.g., '30,60,120,300')")
    parser.add_argument("--output", "-o", help="Base output folder (defaults to input folder if not specified)")
    
    args = parser.parse_args()
    
    # Parse buckets
    try:
        buckets = [int(b.strip()) for b in args.buckets.split(",")]
    except ValueError:
        print("Error: Buckets must be comma-separated integers")
        sys.exit(1)
    
    organize_videos_by_frame_count(args.input_folder, buckets, args.output)


if __name__ == "__main__":
    main()