# Video Dataset Preparation utilities

## Frame_Bucketeer
A Python utility that analyzes MP4 files by frame count and organizes them into appropriate buckets.

### Key Features

- Analyzes MP4 files to determine their exact frame count using OpenCV
- Organizes videos into user-defined frame count buckets (e.g., 30, 60, 120 frames)
- Creates only the bucket folders that will actually contain files
- Places each video in the bucket with the closest smaller-or-equal frame count
- Provides detailed progress feedback and summary statistics

### Requirements

- Python 3.6+
- OpenCV (pip install opencv-python)

### Usage
```
python bucketeer.py /path/to/videos --buckets 30,60,120,300
```

## FPS changer
A simple Python script to change the FPS (frames per second) of all videos in a folder.

### Key Features

- This tool changes the frame rate but keeps the same video duration
- It processes all videos in the input folder and saves them to the output folder
- Original videos are left untouched
- Audio is preserved without re-encoding

### Requirements

- Python 3.6 or higher
- FFmpeg (must be installed separately and available in your PATH)

### Usage
```
python fps-changer.py --input /path/to/videos --output /path/to/output --fps 16
```

## Video resoultion and fps analyzer
A simple Python script to analyze video files and display their resolution, aspect ratio, frame count, and FPS information.

### Key Features
Analyzes all video files in a folder and displays comprehensive information
Shows resolution, aspect ratio, total frame count, and FPS for each video
Supports recursive scanning of subdirectories
Works with a wide range of video formats (MP4, AVI, MKV, MOV, and many more)
Fast processing using FFprobe
Debug mode for troubleshooting file detection issues

### Requirements

- Python 3.6 or higher
- FFmpeg with FFprobe (must be installed separately and available in your PATH)

### Installation

Install FFmpeg:

- Windows: Download from https://ffmpeg.org/download.html
- macOS: brew install ffmpeg
- Linux: sudo apt install ffmpeg (Ubuntu/Debian) or sudo yum install ffmpeg (CentOS/RHEL)


Verify FFprobe is working:
```ffprobe -version```

### Usage

Basic usage:
```
python video_info.py /path/to/videos
```

#### Command Line Options

- ```folder``` - Input folder path (required)
- ```-r, --recursive``` - Search recursively in subdirectories
- ```--no-duration``` - Skip frame count and FPS information for faster processing
- ```--debug``` - Enable debug output to troubleshoot file detection issues
- ```-h, --help``` - Show help message