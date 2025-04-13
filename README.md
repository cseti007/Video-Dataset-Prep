# Video Dataset Preparation utilities

## Bucketeer script
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