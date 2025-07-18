import os
import subprocess
import json
import glob
import argparse
import math

def get_video_info_ffprobe(folder_path, show_duration=True, recursive=False, debug=False):
    """
    Get video info using ffprobe with duration in frames
    """
    extensions = [
        '*.mp4', '*.avi', '*.mkv', '*.mov', '*.wmv', '*.flv', '*.webm', '*.m4v', '*.3gp',
        '*.mpg', '*.mpeg', '*.m2v', '*.ts', '*.m2ts', '*.mts', '*.vob',
        '*.ogv', '*.ogg', '*.rm', '*.rmvb', '*.divx', '*.f4v', '*.3g2', '*.asf',
        '*.mxf', '*.dv', '*.nut', '*.nsv', '*.roq', '*.svi', '*.amv', '*.mtv',
        '*.yuv', '*.h264', '*.h265', '*.hevc'
    ]
    
    if debug:
        debug_folder_contents(folder_path)
    
    print(f"Scanning folder: {folder_path}")
    if recursive:
        print("(Recursive mode enabled)")
    
    # Normalize path
    folder_path = os.path.abspath(folder_path)
    
    header = f"{'Filename':<40} {'Resolution':<15} {'Aspect Ratio':<12}"
    separator = "-" * 80
    
    if show_duration:
        header += f" {'Frames':<12} {'FPS':<8}"
        separator = "-" * 105
    
    print(separator)
    print(header)
    print(separator)
    
    video_files = []
    
    # File detection logic (ugyanaz mint előtte)
    if recursive:
        for ext in extensions:
            pattern = os.path.join(folder_path, "**", ext)
            files = glob.glob(pattern, recursive=True)
            video_files.extend(files)
            pattern_upper = os.path.join(folder_path, "**", ext.upper())
            files_upper = glob.glob(pattern_upper, recursive=True)
            video_files.extend(files_upper)
    else:
        for ext in extensions:
            pattern = os.path.join(folder_path, ext)
            files = glob.glob(pattern)
            video_files.extend(files)
            pattern_upper = os.path.join(folder_path, ext.upper())
            files_upper = glob.glob(pattern_upper)
            video_files.extend(files_upper)
    
    # Alternative manual scan if glob fails
    if not video_files:
        try:
            if recursive:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if any(file.lower().endswith(ext[1:]) for ext in extensions):
                            video_files.append(os.path.join(root, file))
            else:
                for file in os.listdir(folder_path):
                    if os.path.isfile(os.path.join(folder_path, file)):
                        if any(file.lower().endswith(ext[1:]) for ext in extensions):
                            video_files.append(os.path.join(folder_path, file))
        except Exception as e:
            if debug:
                print(f"Error during manual scan: {e}")
    
    if not video_files:
        print("No video files found in the folder.")
        print("Supported extensions:", ", ".join([ext[2:] for ext in extensions]))
        return
    
    # Remove duplicates and sort
    video_files = sorted(list(set(video_files)))
    
    total_files = len(video_files)
    processed = 0
    
    for file_path in video_files:
        processed += 1
        try:
            # Get detailed stream info including frame count
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', '-count_frames', file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                raise Exception(f"ffprobe failed: {result.stderr}")
            
            data = json.loads(result.stdout)
            
            # Find video stream
            video_stream = next((s for s in data['streams'] if s['codec_type'] == 'video'), None)
            
            if video_stream:
                width = video_stream['width']
                height = video_stream['height']
                aspect_ratio = round(width / height, 2)
                
                if recursive:
                    filename = os.path.relpath(file_path, folder_path)
                else:
                    filename = os.path.basename(file_path)
                
                if len(filename) > 38:
                    filename = filename[:35] + "..."
                
                output = f"{filename:<40} {width}x{height:<10} {aspect_ratio:<12}"
                
                if show_duration:
                    # Try to get frame count from different sources
                    frame_count = "N/A"
                    fps = "N/A"
                    
                    # Method 1: Direct frame count (if available)
                    if 'nb_frames' in video_stream:
                        frame_count = video_stream['nb_frames']
                    
                    # Method 2: Calculate from duration and fps
                    elif 'duration' in video_stream and 'avg_frame_rate' in video_stream:
                        try:
                            duration_sec = float(video_stream['duration'])
                            fps_fraction = video_stream['avg_frame_rate']
                            if fps_fraction and fps_fraction != '0/0':
                                fps_parts = fps_fraction.split('/')
                                if len(fps_parts) == 2:
                                    fps_val = float(fps_parts[0]) / float(fps_parts[1])
                                    frame_count = int(duration_sec * fps_val)
                                    fps = f"{fps_val:.2f}"
                        except:
                            pass
                    
                    # Method 3: Try format duration if stream duration not available
                    elif 'duration' in data.get('format', {}) and 'avg_frame_rate' in video_stream:
                        try:
                            duration_sec = float(data['format']['duration'])
                            fps_fraction = video_stream['avg_frame_rate']
                            if fps_fraction and fps_fraction != '0/0':
                                fps_parts = fps_fraction.split('/')
                                if len(fps_parts) == 2:
                                    fps_val = float(fps_parts[0]) / float(fps_parts[1])
                                    frame_count = int(duration_sec * fps_val)
                                    fps = f"{fps_val:.2f}"
                        except:
                            pass
                    
                    # Get FPS if not already calculated
                    if fps == "N/A" and 'avg_frame_rate' in video_stream:
                        try:
                            fps_fraction = video_stream['avg_frame_rate']
                            if fps_fraction and fps_fraction != '0/0':
                                fps_parts = fps_fraction.split('/')
                                if len(fps_parts) == 2:
                                    fps_val = float(fps_parts[0]) / float(fps_parts[1])
                                    fps = f"{fps_val:.2f}"
                        except:
                            pass
                    
                    output += f" {str(frame_count):<12} {fps:<8}"
                
                print(output)
            else:
                print(f"{'No video stream found':<40} {'N/A':<15} {'N/A':<12}")
                
        except subprocess.TimeoutExpired:
            filename = os.path.basename(file_path)
            if len(filename) > 38:
                filename = filename[:35] + "..."
            error_output = f"{filename:<40} {'Timeout':<15} {'N/A':<12}"
            if show_duration:
                error_output += f" {'N/A':<12} {'N/A':<8}"
            print(error_output)
            
        except Exception as e:
            filename = os.path.basename(file_path)
            if len(filename) > 38:
                filename = filename[:35] + "..."
            
            error_output = f"{filename:<40} {'Error':<15} {'N/A':<12}"
            if show_duration:
                error_output += f" {'N/A':<12} {'N/A':<8}"
            
            print(error_output)
            if debug:
                print(f"    Error details: {str(e)}")
    
    print(separator)
    print(f"Total files processed: {processed}")

def debug_folder_contents(folder_path):
    """
    Debug function to show what's actually in the folder
    """
    print(f"\n=== DEBUGGING FOLDER CONTENTS ===")
    print(f"Folder path: {folder_path}")
    print(f"Folder exists: {os.path.exists(folder_path)}")
    print(f"Is directory: {os.path.isdir(folder_path)}")
    print(f"Absolute path: {os.path.abspath(folder_path)}")
    
    if os.path.exists(folder_path):
        print(f"\nAll files in folder:")
        try:
            all_files = os.listdir(folder_path)
            if not all_files:
                print("  (Folder is empty)")
            else:
                for i, file in enumerate(all_files[:20]):
                    print(f"  {i+1}. {file}")
                if len(all_files) > 20:
                    print(f"  ... and {len(all_files) - 20} more files")
        except PermissionError:
            print("  Permission denied to read folder")
    
    print(f"=== END DEBUGGING ===\n")

def main():
    parser = argparse.ArgumentParser(description='Get resolution and aspect ratio of video files using ffprobe')
    parser.add_argument('folder', help='Input folder path')
    parser.add_argument('-r', '--recursive', action='store_true', 
                       help='Search recursively in subdirectories')
    parser.add_argument('--no-duration', action='store_true', 
                       help='Skip duration information')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug output')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.folder):
        print(f"Error: Folder '{args.folder}' does not exist.")
        return
    
    if not os.path.isdir(args.folder):
        print(f"Error: '{args.folder}' is not a directory.")
        return
    
    show_duration = not args.no_duration
    get_video_info_ffprobe(args.folder, show_duration, args.recursive, args.debug)

if __name__ == "__main__":
    main()