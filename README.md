# Video Dataset Preparation utilities

## Frame_Bucketeer.py
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

## FPS_changer.py
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

## video_res_fps_analyzer.py
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
python video_res_fps_analyzer.py /path/to/videos
```

#### Command Line Options

- ```folder``` - Input folder path (required)
- ```-r, --recursive``` - Search recursively in subdirectories
- ```--no-duration``` - Skip frame count and FPS information for faster processing
- ```--debug``` - Enable debug output to troubleshoot file detection issues
- ```-h, --help``` - Show help message

## ar_normalizer.py
A Python utility that normalizes video aspect ratios using intelligent cropping while preserving maximum quality.

### Key Features

- Normalizes all videos in a folder to a target aspect ratio (default 16:9)
- Uses intelligent cropping to maintain content without black bars or distortion
- Preserves original quality when videos already have the correct aspect ratio (simple copy)
- Maintains highest possible quality for processed videos (CRF 18, audio copy)
- Automatically calculates optimal output dimensions based on input video resolution
- Supports all common video formats (MP4, MOV, AVI, MKV, M4V, WMV, FLV, WebM)

### Requirements

- Python 3.6+
- FFmpeg (must be installed and available in PATH)
- FFprobe (usually included with FFmpeg)

### Usage

**Basic usage (16:9 aspect ratio):**
```bash
python ar_normalizer.py /path/to/input /path/to/output
```

**Custom aspect ratio:**
```bash
python ar_normalizer.py /path/to/input /path/to/output --aspect-ratio 1.33
```

**Fixed width or height:**
```bash
# All videos will have 1920px width, height calculated from aspect ratio
python ar_normalizer.py /path/to/input /path/to/output --aspect-ratio 1.78 --width 1920

# All videos will have 1080px height, width calculated from aspect ratio  
python ar_normalizer.py /path/to/input /path/to/output --aspect-ratio 1.78 --height 1080
```

### How It Works

**Smart Processing:**
- Videos with correct aspect ratio (±0.01 tolerance) are simply copied without re-encoding
- Videos needing correction are cropped from the center and scaled to target dimensions
- Audio is always preserved without re-encoding to maintain quality

**Cropping Logic:**
- **Square videos (1:1) → 16:9**: Crops top and bottom, maintains width
- **Portrait videos (9:16) → 16:9**: Crops top and bottom significantly  
- **Wide videos (2:1) → 16:9**: Crops left and right sides
- Always crops from the center to preserve the most important content

### Common Aspect Ratios

- **1.78** (16:9) - Standard widescreen, YouTube, most displays
- **1.33** (4:3) - Classic TV, older content
- **1.0** (1:1) - Square format, Instagram posts
- **0.56** (9:16) - Vertical format, TikTok, Instagram Stories
- **2.35** (21:9) - Cinematic widescreen