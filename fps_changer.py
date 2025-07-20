import os
import subprocess
import argparse
def get_video_fps(input_path):
    """
    Get the FPS of a video file using ffprobe.
    
    Args:
        input_path (str): Path to the video file
    
    Returns:
        float: FPS of the video, or 30.0 as default if detection fails
    """
    try:
        command = [
            'ffprobe',
            '-v', 'quiet',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=r_frame_rate',
            '-of', 'csv=p=0',
            input_path
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        fps_fraction = result.stdout.strip()
        
        # Parse fraction (e.g., "30/1" or "2997/100")
        if '/' in fps_fraction:
            num, den = fps_fraction.split('/')
            fps = float(num) / float(den)
        else:
            fps = float(fps_fraction)
        
        return fps
    except:
        # Default to 30 FPS if detection fails
        return 30.0


def change_video_fps(input_path, output_path, target_fps, duration_mode='preserve'):
    """
    Change the FPS of a video file using FFmpeg.
    
    Args:
        input_path (str): Path to the input video file
        output_path (str): Path to save the output video file
        target_fps (float): Target frames per second
        duration_mode (str): 'preserve' to keep original duration, 'change' to alter duration
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create the FFmpeg command based on duration mode
        if duration_mode == 'preserve':
            # Use fps filter to maintain original duration (drops/duplicates frames)
            command = [
                'ffmpeg',
                '-i', input_path,
                '-filter:v', f'fps={target_fps}',
                '-c:v', 'libx264',  # Use H.264 codec for video
                '-c:a', 'copy',     # Copy audio without re-encoding
                '-preset', 'medium', # Balance between encoding speed and quality
                output_path
            ]
        elif duration_mode == 'change':
            # Get original FPS to calculate proper itsscale
            original_fps = get_video_fps(input_path)
            itsscale_value = original_fps / target_fps
            
            # Use itsscale to change duration - this changes timestamps
            command = [
                'ffmpeg',
                '-itsscale', str(itsscale_value),
                '-i', input_path,
                '-c:v', 'copy',     # Copy video without re-encoding
                '-c:a', 'copy',     # Copy audio without re-encoding  
                '-avoid_negative_ts', 'make_zero',
                output_path
            ]
        else:
            raise ValueError(f"Invalid duration_mode: {duration_mode}. Use 'preserve' or 'change'.")
        
        # Run the command
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print(f"Successfully converted: {os.path.basename(input_path)}")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"Error converting {input_path}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error with {input_path}: {e}")
        return False


def process_folder(input_folder, output_folder, target_fps, duration_mode='preserve'):
    """
    Process all video files in the input folder and save to output folder.
    
    Args:
        input_folder (str): Path to the folder containing input videos
        output_folder (str): Path to save the converted videos
        target_fps (float): Target frames per second
        duration_mode (str): 'preserve' to keep original duration, 'change' to alter duration
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Common video file extensions
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
    
    # Process each file in the input folder
    successful = 0
    failed = 0
    
    for filename in os.listdir(input_folder):
        input_path = os.path.join(input_folder, filename)
        
        # Skip directories and non-video files
        if os.path.isdir(input_path):
            continue
            
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in video_extensions:
            continue
        
        # Create output path with fps in filename
        filename_no_ext = os.path.splitext(filename)[0]
        file_ext = os.path.splitext(filename)[1]
        output_filename = f"{filename_no_ext}_fps{int(target_fps)}{file_ext}"
        output_path = os.path.join(output_folder, output_filename)
        
        # Convert the video
        if change_video_fps(input_path, output_path, target_fps, duration_mode):
            successful += 1
        else:
            failed += 1
    
    print(f"\nConversion completed: {successful} videos successfully converted, {failed} failed.")


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Change FPS of videos in a folder')
    parser.add_argument('--input', '-i', required=True, help='Input folder containing videos')
    parser.add_argument('--output', '-o', required=True, help='Output folder for converted videos')
    parser.add_argument('--fps', '-f', type=float, default=30, help='Target FPS (default: 30)')
    parser.add_argument('--duration', '-d', choices=['preserve', 'change'], default='preserve', 
                       help='Duration mode: "preserve" keeps original duration (default), "change" alters duration')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate input folder exists
    if not os.path.exists(args.input) or not os.path.isdir(args.input):
        print(f"Error: Input folder '{args.input}' does not exist or is not a directory")
        return
    
    # Validate input and output paths are different
    if os.path.abspath(args.input) == os.path.abspath(args.output):
        print("Error: Input and output folders must be different")
        return
    
    # Process all videos in the folder
    process_folder(args.input, args.output, args.fps, args.duration)


if __name__ == "__main__":
    main()