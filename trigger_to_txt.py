#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def generate_txt_files(folder_path, trigger_word):
    """
    Creates a txt file for each mp4 file with the specified trigger word
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"Error: The folder '{folder_path}' does not exist!")
        return
    
    # Find all mp4 files
    mp4_files = list(folder.glob("*.mp4"))
    
    if not mp4_files:
        print(f"No mp4 files found in '{folder_path}' folder.")
        return
    
    print(f"Found {len(mp4_files)} mp4 files...")
    
    for mp4_file in mp4_files:
        # txt file name: same as mp4 but with txt extension
        txt_file = mp4_file.with_suffix('.txt')
        
        # Create txt file with the trigger word
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(trigger_word)
        
        print(f"Created: {txt_file.name}")
    
    print(f"\nDone! {len(mp4_files)} txt files created.")

def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <folder_path> <trigger_word>")
        print("Example: python script.py /home/user/videos 'my trigger word'")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    trigger_word = sys.argv[2]
    
    generate_txt_files(folder_path, trigger_word)

if __name__ == "__main__":
    main()