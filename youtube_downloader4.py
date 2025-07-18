import sys
import io
import os
import argparse
import json
import yt_dlp
import datetime
from youtube_transcript_api import YouTubeTranscriptApi

def check_already_downloaded(log_file, video_id, media_type, language=None):
    """
    Check if a file has already been downloaded based on the log
    
    Args:
        log_file (str): Path to the log file
        video_id (str): YouTube video ID
        media_type (str): Type of download ('audio', 'video', or 'caption')
        language (str, optional): Language code for captions
        
    Returns:
        bool: True if already downloaded, False otherwise
        str: File path if found, None otherwise
    """
    if not os.path.exists(log_file):
        return False, None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get('video_id') == video_id and entry.get('type') == media_type:
                    # For captions, also check language match
                    if media_type == "caption" and language:
                        if entry.get('language') != language:
                            continue
                    
                    # Check if the file still exists
                    file_path = entry.get('file_path')
                    if file_path and os.path.exists(file_path):
                        print(f"Found existing {media_type} in log: {file_path}")
                        return True, file_path
                    elif file_path:
                        print(f"Found entry in log but file doesn't exist: {file_path}")
                        
                        # Try to find file with video ID in the directory
                        dir_path = os.path.dirname(file_path)
                        if os.path.exists(dir_path):
                            # Look for files with the video ID as the filename
                            for file in os.listdir(dir_path):
                                if file.startswith(f"{video_id}.") or file == video_id:
                                    if (media_type == "audio" and file.endswith('.wav')) or \
                                       (media_type == "video" and any(file.endswith(ext) for ext in ['.mp4', '.webm', '.mkv'])) or \
                                       (media_type == "caption" and file.endswith('.txt')):
                                        new_path = os.path.join(dir_path, file)
                                        print(f"Found file with matching ID: {new_path}")
                                        return True, new_path
            except Exception as e:
                print(f"Error parsing log entry: {e}")
                continue
    
    # If we get here, we haven't found a match in the log
    # Try to find a file with the video ID in the output directory
    if os.path.exists(os.path.dirname(log_file)):
        output_dir = os.path.dirname(log_file)
        for file in os.listdir(output_dir):
            if file.startswith(f"{video_id}."):
                if (media_type == "audio" and file.endswith('.wav')) or \
                   (media_type == "video" and any(file.endswith(ext) for ext in ['.mp4', '.webm', '.mkv'])) or \
                   (media_type == "caption" and file.endswith('.txt')):
                    path = os.path.join(output_dir, file)
                    print(f"Found matching file in directory: {path}")
                    return True, path
    
    return False, None

# Setup logging
def log_download(log_file, video_id, title, media_type, language=None, file_path=None):
    """
    Log a download to a file
    
    Args:
        log_file (str): Path to the log file
        video_id (str): YouTube video ID
        title (str): Video title
        media_type (str): Type of download ('audio', 'video', or 'caption')
        language (str, optional): Language code for captions
        file_path (str, optional): Path to the downloaded file
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log entry
    log_entry = {
        "timestamp": timestamp,
        "video_id": video_id,
        "title": title,
        "type": media_type,
        "file_path": file_path
    }
    
    if language and media_type == "caption":
        log_entry["language"] = language
    
    # Write to log file
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + "\n")

def extract_video_id(url):
    """
    Extract the video ID from a YouTube URL
    
    Args:
        url (str): YouTube URL
        
    Returns:
        str: Video ID
    """
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0].split('&')[0]
    elif 'youtube.com/watch' in url:
        if 'v=' in url:
            return url.split('v=')[1].split('&')[0]
    elif 'youtube.com/playlist' in url:
        return None  # This is a playlist URL
    return url  # Assume it's already a video ID

def format_timestamp(seconds):
    """
    Format seconds into HH:MM:SS format
    
    Args:
        seconds (float): Time in seconds
        
    Returns:
        str: Formatted timestamp
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def download_caption(video_id, output_path, title, language=None, log_file=None, caption_type='any'):
    """
    Download caption for a YouTube video
    
    Args:
        video_id (str): YouTube video ID
        output_path (str): Path to save the caption
        title (str): Video title for the caption file header
        language (str): Language code for captions (e.g., 'en', 'es', 'fr')
        log_file (str): Path to the log file
        caption_type (str): Type of caption to prefer ('manual', 'auto', 'translate', 'any')
        
    Returns:
        str: Path to the saved caption file or None if not available
    """
    try:
        # Setup language selection
        languages = [language] if language else ['en']
        
        # Check log file if this caption has already been downloaded
        if log_file:
            already_downloaded, file_path = check_already_downloaded(
                log_file, video_id, "caption", language=languages[0]
            )
            if already_downloaded:
                print(f"Caption already downloaded: {file_path}")
                return file_path
        
        # Create filename with just the ID
        safe_filename = video_id
        
        # Get available transcript languages
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Variable to store our fetched transcript
        fetched_transcript = None
        
        # Try to get transcript based on caption_type preference
        if caption_type in ['manual', 'any']:
            # Try to get user-created transcript in requested language
            try:
                print(f"Searching for manual transcript in {languages[0] if languages[0] else 'default'} language...")
                fetched_transcript = transcript_list.find_transcript(languages)
                print(f"Found manual transcript in {fetched_transcript.language_code} language")
            except Exception as e:
                print(f"No manual transcript found: {e}")
        
        # If manual not found or not requested, try auto-generated (if allowed)
        if not fetched_transcript and caption_type in ['auto', 'any']:
            try:
                print(f"Searching for auto-generated transcript in {languages[0] if languages[0] else 'default'} language...")
                fetched_transcript = transcript_list.find_generated_transcript(languages)
                print(f"Found auto-generated transcript in {fetched_transcript.language_code} language")
            except Exception as e:
                print(f"No auto-generated transcript found: {e}")
        
        # If still not found and translation is allowed, try translation
        if not fetched_transcript and caption_type in ['translate', 'any']:
            try:
                # Get any available transcript
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    any_transcript = available_transcripts[0]
                    print(f"Found transcript in {any_transcript.language_code}, attempting to translate to {languages[0]}")
                    
                    # Translate to requested language
                    translated_transcript = any_transcript.translate(languages[0])
                    fetched_transcript = translated_transcript
                    print(f"Successfully translated to {languages[0]}")
            except Exception as e:
                print(f"Translation failed: {e}")
        
        # If we still don't have a transcript, list available ones and exit
        if not fetched_transcript:
            print(f"No {caption_type} transcript found for requested language.")
            try:
                available_languages = [
                    f"{tr.language_code} ({tr.language})" 
                    for tr in transcript_list
                ]
                if available_languages:
                    print(f"Available languages: {', '.join(available_languages)}")
            except:
                pass
            return None
                
        # Fetch the transcript data
        transcript_data = fetched_transcript.fetch()
        
        # Update the path with the actual language code that was fetched
        lang_suffix = f".{fetched_transcript.language_code}" if fetched_transcript.language_code else ""
        caption_path = os.path.join(output_path, f"{safe_filename}{lang_suffix}.txt")
        
        # Format transcript with timestamps (like YouTube)
        formatted_lines = []
        for snippet in transcript_data:
            start_time = format_timestamp(snippet.start)
            text = snippet.text.replace('\n', ' ')
            formatted_lines.append(f"[{start_time}] {text}")
                    
        formatted_transcript = '\n'.join(formatted_lines)
        
        # Write transcript to file
        with open(caption_path, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write(f"Video ID: {video_id}\n")
            f.write(f"Language: {fetched_transcript.language} ({fetched_transcript.language_code})\n")
            
            # Add info if auto-generated or translated
            is_generated = getattr(fetched_transcript, 'is_generated', False)
            is_translating = getattr(fetched_transcript, 'is_translating', False)
            f.write(f"Generated: {'Yes' if is_generated else 'No'}\n")
            f.write(f"Translated: {'Yes' if is_translating else 'No'}\n\n")
            
            f.write(formatted_transcript)
        
        # Log the download
        if log_file:
            log_download(
                log_file, video_id, title, "caption",
                language=fetched_transcript.language_code,
                file_path=caption_path
            )
            
        print(f"Caption saved to: {caption_path}")
        return caption_path
        
    except Exception as e:
        print(f"Failed to download caption: {e}")
        return None

def download_video_or_audio(url, output_path, audio_only=False, log_file=None, cookies=None, browser=None, video_format="mp4"):
    """
    Download a YouTube video or its audio with yt-dlp
    
    Args:
        url (str): YouTube video URL
        output_path (str): Directory to save the downloaded files
        audio_only (bool): If True, download only audio
        log_file (str): Path to the log file
        cookies (str): Path to cookies file
        browser (str): Browser name to extract cookies from
        video_format (str): Preferred video format (mp4, webm, mkv, etc.)
        
    Returns:
        tuple: (media_path, video_id, title)
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    # Extract video ID and basic info
    try:
        # Setup basic options for getting video info
        info_opts = {
            'quiet': True,
            'ignoreerrors': True,
        }
        
        # Add authentication if provided
        if browser:
            info_opts['cookiesfrombrowser'] = (browser, None, None, None)
        elif cookies:
            info_opts['cookiefile'] = cookies
            
        # Try to get info without downloading
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id')
            title = info.get('title')
            
            # Check if already downloaded
            media_type = "audio" if audio_only else "video"
            if log_file and video_id:
                already_downloaded, file_path = check_already_downloaded(log_file, video_id, media_type)
                if already_downloaded and os.path.exists(file_path):
                    print(f"{media_type.capitalize()} already downloaded: {file_path}")
                    return file_path, video_id, title
    except Exception as e:
        print(f"Error getting video info: {e}")
        # Try to get the video ID at least
        video_id = extract_video_id(url)
        title = f"video_{video_id}"
    
    # Create a filename using only the video ID
    safe_filename = video_id
    
    # For audio-only downloads, we use a simpler approach
    if audio_only:
        return download_audio_only(url, output_path, safe_filename, video_id, title, log_file, cookies, browser)
    else:
        # For video, we try a more careful approach to avoid black screens
        return download_video(url, output_path, safe_filename, video_id, title, log_file, cookies, browser, video_format)


def download_audio_only(url, output_path, safe_filename, video_id, title, log_file, cookies, browser):
    """Handle audio-only downloads"""
    # Check if already exists
    expected_path = os.path.join(output_path, f"{safe_filename}.wav")
    if os.path.exists(expected_path):
        print(f"Audio file already exists: {expected_path}")
        if log_file:
            log_download(log_file, video_id, title, "audio", file_path=expected_path)
        return expected_path, video_id, title
    
    # Audio-only download options
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, safe_filename),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'keepvideo': False,
    }
    
    # Add authentication if provided
    if browser:
        ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
    elif cookies:
        ydl_opts['cookiefile'] = cookies
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Check for the output file
        audio_path = os.path.join(output_path, f"{safe_filename}.wav")
        if os.path.exists(audio_path):
            # Success!
            if log_file:
                log_download(log_file, video_id, title, "audio", file_path=audio_path)
            return audio_path, video_id, title
            
    except Exception as e:
        print(f"Error downloading audio: {e}")
    
    # If we got here, try one more time with simpler options
    try:
        print("Trying alternate audio download method...")
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(output_path, f"{safe_filename}.%(ext)s"),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
        }
        
        # Add authentication if provided
        if browser:
            ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
        elif cookies:
            ydl_opts['cookiefile'] = cookies
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Check for the output file
        audio_path = os.path.join(output_path, f"{safe_filename}.wav")
        if os.path.exists(audio_path):
            # Success!
            if log_file:
                log_download(log_file, video_id, title, "audio", file_path=audio_path)
            return audio_path, video_id, title
            
    except Exception as e:
        print(f"Error with alternate audio download: {e}")
        raise  # Re-raise the error after all attempts failed


def download_video(url, output_path, safe_filename, video_id, title, log_file, cookies, browser, video_format):
    """Download video at best available quality using the simplest possible approach that ensures compatibility"""
    # Check if already exists
    expected_path = os.path.join(output_path, f"{safe_filename}.{video_format}")
    if os.path.exists(expected_path):
        print(f"Video file already exists: {expected_path}")
        if log_file:
            log_download(log_file, video_id, title, "video", file_path=expected_path)
        return expected_path, video_id, title
    
    # Use a more specific approach to ensure codec compatibility
    if video_format == "mp4":
        # For MP4, specify compatible codecs (h264 video, aac audio)
        format_option = "bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    elif video_format == "webm":
        # For WEBM, specify VP9/VP8 video and Opus/Vorbis audio
        format_option = "bestvideo[ext=webm][vcodec^=vp9]+bestaudio[ext=webm]/best[ext=webm]/best"
    else:
        # For other formats, use best quality but still try to get a compatible combination
        format_option = f"bestvideo+bestaudio/best[ext={video_format}]/best"
    
    print(f"Using format option: {format_option}")
    
    # Setup download options
    ydl_opts = {
        'format': format_option,
        'outtmpl': os.path.join(output_path, f"{safe_filename}.%(ext)s"),
        'restrictfilenames': True,
        'noplaylist': True,
        'quiet': False,
    }
    
    # Add authentication if provided
    if browser:
        ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
    elif cookies:
        ydl_opts['cookiefile'] = cookies
    
    # Set merge format if specified
    if video_format in ['mp4', 'webm', 'mkv']:
        ydl_opts['merge_output_format'] = video_format
    
    # Instead of copying the video stream as is, let ffmpeg transcode to ensure compatibility
    # Remove the copy directive to allow ffmpeg to transcode if needed
    
    try:
        # Attempt download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Check which file was actually created
        for ext in [video_format, 'mp4', 'webm', 'mkv']:
            test_path = os.path.join(output_path, f"{safe_filename}.{ext}")
            if os.path.exists(test_path):
                # Success!
                if log_file:
                    log_download(log_file, video_id, title, "video", file_path=test_path)
                return test_path, video_id, title
                
    except Exception as e:
        print(f"Error downloading video: {e}")
        
        # Try with format 22 (standard high quality MP4) or format 18 (medium quality MP4)
        try:
            print("Trying with specific YouTube formats (22/18)...")
            ydl_opts = {
                'format': '22/18/best',
                'outtmpl': os.path.join(output_path, f"{safe_filename}.%(ext)s"),
            }
            
            # Add authentication if provided
            if browser:
                ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
            elif cookies:
                ydl_opts['cookiefile'] = cookies
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Check for created file
            for ext in ['mp4', 'webm', 'mkv']:
                test_path = os.path.join(output_path, f"{safe_filename}.{ext}")
                if os.path.exists(test_path):
                    # Success!
                    if log_file:
                        log_download(log_file, video_id, title, "video", file_path=test_path)
                    return test_path, video_id, title
                    
        except Exception as e:
            print(f"Error with fallback formats: {e}")
            raise  # Re-raise the error after all attempts failed
            
    # If we got here without returning, we failed to find the downloaded file
    raise FileNotFoundError(f"Failed to find downloaded video file for {url}")

def process_video(video_url, output_path, audio_only=False, language=None, log_file=None, skip_captions=False, cookies=None, browser=None, video_format="mp4", caption_type="any"):
    """
    Process a single YouTube video: download media and caption
    
    Args:
        video_url (str): YouTube video URL
        output_path (str): Directory to save files
        audio_only (bool): If True, download only audio
        language (str): Language code for captions
        log_file (str): Path to the log file
        skip_captions (bool): If True, skip downloading captions
        cookies (str): Path to cookies file
        browser (str): Browser name to extract cookies from
        video_format (str): Preferred video format (mp4, webm, mkv, etc.)
        caption_type (str): Type of caption to prefer ('manual', 'auto', 'translate', 'any')
    """
    try:
        media_type = "audio" if audio_only else "video"
        print(f"Processing: {video_url}")
        
        # Download media
        media_path, video_id, title = download_video_or_audio(
            video_url, output_path, audio_only, log_file, cookies, browser, video_format
        )
        print(f"{media_type.capitalize()} path: {media_path}")
        
        # Download caption if not skipped
        caption_path = None
        if not skip_captions:
            caption_path = download_caption(video_id, output_path, title, language, log_file, caption_type)
        else:
            print("Skipping captions as requested")
            
        # Log the caption status to the log file
        if log_file:
            caption_status = {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "video_id": video_id,
                "title": title,
                "type": "caption_status",
                "has_caption": caption_path is not None,
                "reason": "skipped" if skip_captions else ("not_found" if caption_path is None else "downloaded"),
                "language": language,
                "caption_type": caption_type
            }
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(caption_status) + "\n")
        
    except Exception as e:
        print(f"Error processing video: {e}")


def process_playlist(playlist_url, output_path, audio_only=False, language=None, log_file=None, skip_captions=False, cookies=None, browser=None, video_format="mp4", caption_type="any"):
    """
    Process all videos in a YouTube playlist
    
    Args:
        playlist_url (str): YouTube playlist URL
        output_path (str): Base directory to save files
        audio_only (bool): If True, download only audio
        language (str): Language code for captions
        log_file (str): Path to the log file
        skip_captions (bool): If True, skip downloading captions
        cookies (str): Path to cookies file
        browser (str): Browser name to extract cookies from
        video_format (str): Preferred video format (mp4, webm, mkv, etc.)
        caption_type (str): Type of caption to prefer ('manual', 'auto', 'translate', 'any')
    """
    # Setup yt-dlp options to extract playlist info
    ydl_opts = {
        'extract_flat': True,  # Don't download, just get info
        'quiet': True,
        'dump_single_json': True,
    }
    
    # Add cookies options if provided
    if cookies:
        ydl_opts['cookiefile'] = cookies
    if browser:
        ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
    
    try:
        # Get playlist information
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            
            # Create a folder for the playlist
            playlist_title = playlist_info.get('title', 'YouTube_Playlist')
            safe_title = "".join([c if c.isalnum() or c in " -_" else "_" for c in playlist_title])
            playlist_dir = os.path.join(output_path, safe_title)
            
            if not os.path.exists(playlist_dir):
                os.makedirs(playlist_dir)
                
            print(f"Playlist: {playlist_title}")
            print(f"Number of videos: {len(playlist_info.get('entries', []))}")
            
            # Setup log file for this playlist if not provided
            playlist_log_file = log_file
            if not playlist_log_file:
                playlist_log_file = os.path.join(playlist_dir, "download_log.jsonl")
            
            # Process each video in the playlist
            for index, entry in enumerate(playlist_info.get('entries', [])):
                if entry:
                    video_id = entry['id']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Track progress
                    print(f"\nProcessing {index+1} of {len(playlist_info.get('entries', []))}")
                    
                    # Process the video
                    process_video(
                        video_url, playlist_dir, 
                        audio_only, language, playlist_log_file, 
                        skip_captions, cookies, browser, video_format, caption_type
                    )
    
    except Exception as e:
        print(f"Error processing playlist: {e}")


def main():
    parser = argparse.ArgumentParser(description='Download YouTube videos/audio with captions')
    parser.add_argument('-p', '--playlist', help='YouTube playlist URL to download')
    parser.add_argument('-v', '--video', help='YouTube video URL to download')
    parser.add_argument('-o', '--output', default='downloads', 
                        help='Output directory where files will be saved (default: downloads)')
    parser.add_argument('-a', '--audio', action='store_true', 
                        help='Download audio only in WAV format instead of video')
    parser.add_argument('-l', '--language', 
                        help='Language code for captions (e.g., en, es, fr, de)')
    parser.add_argument('--log', default=None, 
                        help='Path to log file (default: [output_dir]/download_log.jsonl)')
    parser.add_argument('--no-captions', action='store_true', 
                        help='Skip downloading captions entirely')
    parser.add_argument('--cookies', 
                        help='Path to cookies file for authentication')
    parser.add_argument('--browser', choices=['chrome', 'firefox', 'opera', 'edge', 'safari', 'brave', 'chromium'],
                        help='Browser to extract cookies from (chrome, firefox, opera, edge, safari, brave, chromium)')
    parser.add_argument('--format', default='mp4', choices=['mp4', 'webm', 'mkv', 'flv', 'avi'],
                        help='Preferred video format (default: mp4)')
    parser.add_argument('--caption-type', default='any', choices=['manual', 'auto', 'translate', 'any'],
                        help='Type of caption to prefer: manual, auto-generated, translation, or any (default: any)')
    
    args = parser.parse_args()
    
    if not args.playlist and not args.video:
        parser.error("Please provide either a playlist URL (-p) or a video URL (-v)")
    
    # Setup log file if not specified
    log_file = args.log
    if not log_file:
        log_file = os.path.join(args.output, "download_log.jsonl")
        
    if args.playlist:
        process_playlist(
            args.playlist, args.output, args.audio, args.language, 
            log_file, args.no_captions, args.cookies, args.browser, args.format, args.caption_type
        )
    
    if args.video:
        process_video(
            args.video, args.output, args.audio, args.language,
            log_file, args.no_captions, args.cookies, args.browser, args.format, args.caption_type
        )


if __name__ == "__main__":
    main()