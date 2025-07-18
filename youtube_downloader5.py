import sys
import io
import os
import argparse
import json
import yt_dlp
import datetime
from youtube_transcript_api import YouTubeTranscriptApi

def check_file_exists(output_path, video_id, media_type="video", video_format="mp4"):
    """
    Check if a file for the given video ID already exists on disk without checking the log
    
    Args:
        output_path (str): Path to check for existing files
        video_id (str): YouTube video ID
        media_type (str): Type of file ('audio', 'video', or 'caption')
        video_format (str): Video format for video files
        
    Returns:
        bool: True if file exists, False otherwise
        str: File path if found, None otherwise
    """
    if not os.path.exists(output_path):
        return False, None
        
    # Check for matching files
    for file in os.listdir(output_path):
        if file.startswith(f"{video_id}.") or file == video_id:
            if (media_type == "audio" and file.endswith('.wav')) or \
               (media_type == "video" and any(file.endswith(ext) for ext in ['.mp4', '.webm', '.mkv', video_format])) or \
               (media_type == "caption" and file.endswith('.txt')):
                path = os.path.join(output_path, file)
                print(f"Found existing {media_type} file: {path}")
                return True, path
    
    return False, None

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

def log_skipped(log_file, video_id, url, reason):
    """
    Log a skipped video
    
    Args:
        log_file (str): Path to the log file
        video_id (str): YouTube video ID
        url (str): Video URL
        reason (str): Reason for skipping
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Create log directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log entry
    skip_entry = {
        "timestamp": timestamp,
        "video_id": video_id,
        "url": url,
        "type": "skipped",
        "reason": reason
    }
    
    # Write to log file
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(skip_entry) + "\n")

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

def is_livestream(video_id):
    """
    Check if a video is a livestream
    
    Args:
        video_id (str): YouTube video ID
        
    Returns:
        bool: True if livestream, False otherwise
    """
    try:
        # Setup yt-dlp options to check for livestream
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            
            # Check if it's a live stream
            is_live = info.get('is_live', False)
            if is_live:
                print(f"Video {video_id} is a livestream. Skipping.")
                return True
                
            # Check for "premiere" which is like a scheduled livestream
            is_premiere = info.get('premiere_timestamp') is not None
            if is_premiere:
                print(f"Video {video_id} is a premiere. Skipping.")
                return True
                
            # Check for other livestream indicators
            if info.get('live_status') in ['is_live', 'is_upcoming', 'post_live']:
                print(f"Video {video_id} has live status: {info.get('live_status')}. Skipping.")
                return True
                
            return False
    except Exception as e:
        print(f"Error checking if livestream: {e}")
        # If we can't determine, assume it's not a livestream
        return False

def check_if_hungarian_content(video_id):
    """
    Check if a video has Hungarian content either in title, description or captions
    
    Args:
        video_id (str): YouTube video ID
        
    Returns:
        tuple: (is_hungarian, reason)
    """
    try:
        # Get video info using yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            
            # Check if title or description contains Hungarian patterns
            title = info.get('title', '')
            description = info.get('description', '')
            
            # Common Hungarian characters that are specific to the language
            hungarian_chars = ['ő', 'ű', 'ó', 'ú', 'é', 'á', 'í', 'ü', 'ö']
            hungarian_words = ['és', 'vagy', 'nem', 'igen', 'hogy', 'magyar', 'magyarország', 'köszönöm']
            
            # Check title and description for Hungarian characters and words
            for char in hungarian_chars:
                if char in title.lower() or char in description.lower():
                    return True, f"Found Hungarian character '{char}' in title/description"
            
            for word in hungarian_words:
                if f" {word} " in f" {title.lower()} " or f" {word} " in f" {description.lower()} ":
                    return True, f"Found Hungarian word '{word}' in title/description"
            
            # Check for Hungarian in language or country metadata
            if info.get('language') == 'hu' or info.get('country') == 'HU':
                return True, "Metadata indicates Hungarian content"
                
            # Check if video has Hungarian captions
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                for transcript in transcript_list:
                    if transcript.language_code == 'hu':
                        return True, "Has Hungarian captions"
            except Exception as e:
                # If no captions are available, continue with other checks
                pass
                
            # Check channel info for Hungarian indicators
            channel_name = info.get('channel', '')
            if any(char in channel_name.lower() for char in hungarian_chars) or \
               any(word in f" {channel_name.lower()} " for word in hungarian_words):
                return True, "Channel name indicates Hungarian content"
                
            # If nothing matched, it's likely not Hungarian
            return False, "No Hungarian indicators found"
            
    except Exception as e:
        print(f"Error checking if Hungarian content: {e}")
        return False, f"Error: {e}"

def download_caption(video_id, output_path, title, language='hu', log_file=None, caption_type='any'):
    """
    Download caption for a YouTube video, prioritizing Hungarian
    
    Args:
        video_id (str): YouTube video ID
        output_path (str): Path to save the caption
        title (str): Video title for the caption file header
        language (str): Language code for captions (default: 'hu' for Hungarian)
        log_file (str): Path to the log file
        caption_type (str): Type of caption to prefer ('manual', 'auto', 'translate', 'any')
        
    Returns:
        str: Path to the saved caption file or None if not available
    """
    try:
        # Setup language selection - prioritize Hungarian, but fall back to English if needed
        languages = [language]  # Primary language (Hungarian)
        if language != 'en':
            languages.append('en')  # Secondary fallback
        
        # First check if the file exists directly on disk
        file_exists, file_path = check_file_exists(output_path, video_id, "caption")
        if file_exists:
            print(f"Caption already exists on disk: {file_path}")
            # Update log if it doesn't have this entry
            if log_file:
                log_download(log_file, video_id, title or video_id, "caption", language=language, file_path=file_path)
            return file_path
        
        # Then check log file if this caption has already been downloaded
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
                print(f"Searching for manual transcript in {languages[0]} language...")
                fetched_transcript = transcript_list.find_transcript(languages)
                print(f"Found manual transcript in {fetched_transcript.language_code} language")
            except Exception as e:
                print(f"No manual transcript found: {e}")
        
        # If manual not found or not requested, try auto-generated (if allowed)
        if not fetched_transcript and caption_type in ['auto', 'any']:
            try:
                print(f"Searching for auto-generated transcript in {languages[0]} language...")
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
    
    # Extract video ID
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    # First check if file already exists directly on disk
    media_type = "audio" if audio_only else "video"
    file_exists, file_path = check_file_exists(
        output_path, video_id, media_type, video_format
    )
    if file_exists:
        print(f"{media_type.capitalize()} already exists on disk: {file_path}")
        # Get title for the log if we don't have it
        try:
            ydl_opts = {'quiet': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', f"video_{video_id}")
        except:
            title = f"video_{video_id}"
            
        # Update log if it doesn't have this entry
        if log_file:
            log_download(log_file, video_id, title, media_type, file_path=file_path)
        return file_path, video_id, title
        
    # Check if it's a livestream - if so, skip it
    if is_livestream(video_id):
        if log_file:
            log_skipped(log_file, video_id, url, "Livestream - skipped")
        raise ValueError(f"Video {video_id} is a livestream, skipping")
    
    # Extract basic info
    try:
        # Setup basic options for getting video info
        info_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'skip_download': True,
        }
        
        # Add authentication if provided, but handle errors gracefully
        if browser:
            try:
                info_opts['cookiesfrombrowser'] = (browser, None, None, None)
            except Exception as e:
                print(f"Warning: Could not extract cookies from {browser}: {e}")
        elif cookies:
            if os.path.exists(cookies):
                info_opts['cookiefile'] = cookies
            else:
                print(f"Warning: Cookies file not found: {cookies}")
            
        # Try to get info without downloading
        with yt_dlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise ValueError(f"Could not get video info for {url}")
                
            video_id = info.get('id')
            title = info.get('title')
            
            # Check if already downloaded in the log
            if log_file and video_id:
                already_downloaded, file_path = check_already_downloaded(log_file, video_id, media_type)
                if already_downloaded and os.path.exists(file_path):
                    print(f"{media_type.capitalize()} already downloaded: {file_path}")
                    return file_path, video_id, title
    except Exception as e:
        print(f"Error getting video info: {e}")
        # Since we already checked for video ID above, we can at least use that
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
        'ignoreerrors': True,
    }
    
    # Add authentication if provided, but handle errors gracefully
    if browser:
        try:
            ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
        except Exception as e:
            print(f"Warning: Could not extract cookies from {browser}: {e}")
    elif cookies:
        if os.path.exists(cookies):
            ydl_opts['cookiefile'] = cookies
        else:
            print(f"Warning: Cookies file not found: {cookies}")
    
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
            'ignoreerrors': True,
        }
        
        # Add authentication if provided, but handle errors gracefully
        if browser:
            try:
                ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
            except Exception as e:
                print(f"Warning: Could not extract cookies from {browser}: {e}")
        elif cookies:
            if os.path.exists(cookies):
                ydl_opts['cookiefile'] = cookies
            else:
                print(f"Warning: Cookies file not found: {cookies}")
            
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
        'ignoreerrors': True,
    }
    
    # Add authentication if provided, but handle errors gracefully
    if browser:
        try:
            ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
        except Exception as e:
            print(f"Warning: Could not extract cookies from {browser}: {e}")
    elif cookies:
        if os.path.exists(cookies):
            ydl_opts['cookiefile'] = cookies
        else:
            print(f"Warning: Cookies file not found: {cookies}")
    
    # Set merge format if specified
    if video_format in ['mp4', 'webm', 'mkv']:
        ydl_opts['merge_output_format'] = video_format
    
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
                'ignoreerrors': True,
            }
            
            # Add authentication if provided, but handle errors gracefully
            if browser:
                try:
                    ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
                except Exception as e:
                    print(f"Warning: Could not extract cookies from {browser}: {e}")
            elif cookies:
                if os.path.exists(cookies):
                    ydl_opts['cookiefile'] = cookies
                else:
                    print(f"Warning: Cookies file not found: {cookies}")
                
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

def process_video(video_url, output_path, audio_only=False, language='hu', log_file=None, skip_captions=False, cookies=None, browser=None, video_format="mp4", caption_type="any", hungarian_only=True, skip_livestreams=True):
    """
    Process a single YouTube video: download media and caption if it's Hungarian content
    
    Args:
        video_url (str): YouTube video URL
        output_path (str): Directory to save files
        audio_only (bool): If True, download only audio
        language (str): Language code for captions (default: hu)
        log_file (str): Path to the log file
        skip_captions (bool): If True, skip downloading captions
        cookies (str): Path to cookies file
        browser (str): Browser name to extract cookies from
        video_format (str): Preferred video format (mp4, webm, mkv, etc.)
        caption_type (str): Type of caption to prefer ('manual', 'auto', 'translate', 'any')
        hungarian_only (bool): If True, only process Hungarian content
        skip_livestreams (bool): If True, skip livestreams
    """
    try:
        media_type = "audio" if audio_only else "video"
        print(f"Processing: {video_url}")
        
        # Extract video ID
        video_id = extract_video_id(video_url)
        if not video_id:
            print(f"Could not extract video ID from URL: {video_url}")
            return
        
        # First check if the file already exists (both on disk and in logs)
        file_exists, file_path = check_file_exists(output_path, video_id, media_type, video_format)
        if file_exists:
            print(f"File already exists for {video_id}, skipping content check")
            # Try to get title for logging
            try:
                ydl_opts = {'quiet': True, 'skip_download': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    title = info.get('title', f"video_{video_id}")
            except:
                title = f"video_{video_id}"
                
            # Update log if it doesn't have this entry
            if log_file:
                log_download(log_file, video_id, title, media_type, file_path=file_path)
                
            # Download caption if not skipped and not already exists
            if not skip_captions:
                caption_exists, caption_path = check_file_exists(output_path, video_id, "caption")
                if not caption_exists:
                    caption_path = download_caption(video_id, output_path, title, language, log_file, caption_type)
            
            return
            
        # Check in log file too
        if log_file:
            already_downloaded, log_path = check_already_downloaded(log_file, video_id, media_type)
            if already_downloaded:
                print(f"File already logged for {video_id}, skipping content check")
                
                # Download caption if not skipped and not already exists
                if not skip_captions:
                    caption_exists, caption_path = check_file_exists(output_path, video_id, "caption")
                    if not caption_exists:
                        # Try to get title for caption
                        try:
                            ydl_opts = {'quiet': True, 'skip_download': True}
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                info = ydl.extract_info(video_url, download=False)
                                title = info.get('title', f"video_{video_id}")
                        except:
                            title = f"video_{video_id}"
                            
                        caption_path = download_caption(video_id, output_path, title, language, log_file, caption_type)
                
                return
        
        # Check if it's a livestream and skip if required
        if skip_livestreams and is_livestream(video_id):
            print(f"Skipping livestream: {video_url}")
            if log_file:
                log_skipped(log_file, video_id, video_url, "Livestream - skipped")
            return
            
        # Now check if this is Hungarian content (only if we need to download)
        if hungarian_only:
            is_hungarian, reason = check_if_hungarian_content(video_id)
            if not is_hungarian:
                print(f"Skipping non-Hungarian content: {reason}")
                
                # Log skipped video
                if log_file:
                    log_skipped(log_file, video_id, video_url, reason)
                return
            else:
                print(f"Hungarian content detected: {reason}")
        
        # Download media
        try:
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
            if "livestream" in str(e).lower():
                print(f"Skipping livestream: {video_url}")
                if log_file:
                    log_skipped(log_file, video_id, video_url, "Livestream detected during download")
            else:
                print(f"Error downloading media: {e}")
        
    except Exception as e:
        print(f"Error processing video: {e}")

def search_hungarian_videos(query, max_results=10, force_hungarian=True):
    """
    Search for Hungarian videos on YouTube
    
    Args:
        query (str): Search query
        max_results (int): Maximum number of results to return
        force_hungarian (bool): If True, add Hungarian terms to query
        
    Returns:
        list: List of video IDs
    """
    original_query = query
    
    # Define Hungarian search terms to add to the query
    if force_hungarian:
        hungarian_terms = ["magyar", "magyarország"]
        
        # Add Hungarian terms to query if not already present
        for term in hungarian_terms:
            if term not in query.lower():
                query = f"{query} {term}"
    
    print(f"Searching for: '{original_query}'" + 
          (f" with Hungarian terms: '{query}'" if force_hungarian and query != original_query else ""))
    
    # Setup yt-dlp search options
    ydl_opts = {
        'extract_flat': True,  # Don't download, just get info
        'quiet': True,
        'max_downloads': max_results,
        'skip_download': True,
        'ignoreerrors': True,
    }
    
    video_ids = []
    try:
        # Use ytsearch prefix to search YouTube
        search_url = f"ytsearch{max_results}:{query}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_url, download=False)
            
            # Extract video IDs from search results
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        video_id = entry.get('id')
                        if video_id:
                            video_ids.append(video_id)
        
        print(f"Found {len(video_ids)} videos for query: {query}")
        return video_ids
    except Exception as e:
        print(f"Error searching for videos: {e}")
        return []

def process_hungarian_search(search_query, output_path, audio_only=False, language='hu', log_file=None, 
                            skip_captions=False, cookies=None, browser=None, video_format="mp4", 
                            caption_type="any", max_results=20, skip_livestreams=True, pure_search=False):
    """
    Search for Hungarian videos and download them
    
    Args:
        search_query (str): Search query
        output_path (str): Directory to save files
        audio_only (bool): If True, download only audio
        language (str): Language code for captions (default: hu)
        log_file (str): Path to the log file
        skip_captions (bool): If True, skip downloading captions
        cookies (str): Path to cookies file
        browser (str): Browser name to extract cookies from
        video_format (str): Preferred video format (mp4, webm, mkv, etc.)
        caption_type (str): Type of caption to prefer ('manual', 'auto', 'translate', 'any')
        max_results (int): Maximum number of search results to process
        skip_livestreams (bool): If True, skip livestreams
        pure_search (bool): If True, don't add Hungarian terms to search
    """
    # Create a subfolder for the search results
    folder_name = f"search_{search_query.replace(' ', '_')}"
    if pure_search:
        folder_name += "_exact"
        
    search_folder = os.path.join(output_path, folder_name)
    if not os.path.exists(search_folder):
        os.makedirs(search_folder)
    
    # Setup search-specific log file if not provided
    search_log_file = log_file
    if not search_log_file:
        search_log_file = os.path.join(search_folder, "download_log.jsonl")
    
    # Search for videos (with or without Hungarian terms)
    video_ids = search_hungarian_videos(search_query, max_results, force_hungarian=not pure_search)
    
    # Process each video
    for i, video_id in enumerate(video_ids):
        print(f"\nProcessing search result {i+1}/{len(video_ids)}")
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        # Process the video (only Hungarian content will be downloaded if hungarian_only is True)
        process_video(
            video_url, search_folder, audio_only, language, 
            search_log_file, skip_captions, cookies, browser, 
            video_format, caption_type, hungarian_only=not pure_search, 
            skip_livestreams=skip_livestreams
        )

def process_playlist(playlist_url, output_path, audio_only=False, language='hu', log_file=None, 
                     skip_captions=False, cookies=None, browser=None, video_format="mp4", 
                     caption_type="any", hungarian_only=True, skip_livestreams=True):
    """
    Process all videos in a YouTube playlist, filtering for Hungarian content
    
    Args:
        playlist_url (str): YouTube playlist URL
        output_path (str): Base directory to save files
        audio_only (bool): If True, download only audio
        language (str): Language code for captions (default: hu)
        log_file (str): Path to the log file
        skip_captions (bool): If True, skip downloading captions
        cookies (str): Path to cookies file
        browser (str): Browser name to extract cookies from
        video_format (str): Preferred video format (mp4, webm, mkv, etc.)
        caption_type (str): Type of caption to prefer ('manual', 'auto', 'translate', 'any')
        hungarian_only (bool): If True, only process Hungarian content
        skip_livestreams (bool): If True, skip livestreams
    """
    # Setup yt-dlp options to extract playlist info
    ydl_opts = {
        'extract_flat': True,  # Don't download, just get info
        'quiet': True,
        'dump_single_json': True,
        'ignoreerrors': True,
    }
    
    # Add cookies options if provided
    if cookies and os.path.exists(cookies):
        ydl_opts['cookiefile'] = cookies
    elif browser:
        try:
            ydl_opts['cookiesfrombrowser'] = (browser, None, None, None)
        except Exception as e:
            print(f"Warning: Could not extract cookies from {browser}: {e}")
    
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
                        skip_captions, cookies, browser, video_format, caption_type,
                        hungarian_only=hungarian_only, skip_livestreams=skip_livestreams
                    )
    
    except Exception as e:
        print(f"Error processing playlist: {e}")

def main():
    parser = argparse.ArgumentParser(description='Download Hungarian YouTube videos/audio with captions (Optimized File Checking)')
    parser.add_argument('-p', '--playlist', help='YouTube playlist URL to download')
    parser.add_argument('-v', '--video', help='YouTube video URL to download')
    parser.add_argument('-s', '--search', help='Search for Hungarian videos with the given query')
    parser.add_argument('-o', '--output', default='hungarian_downloads', 
                        help='Output directory where files will be saved (default: hungarian_downloads)')
    parser.add_argument('-a', '--audio', action='store_true', 
                        help='Download audio only in WAV format instead of video')
    parser.add_argument('-l', '--language', default='hu',
                        help='Language code for captions (default: hu for Hungarian)')
    parser.add_argument('--log', default=None, 
                        help='Path to log file (default: [output_dir]/download_log.jsonl)')
    parser.add_argument('--no-captions', action='store_true', 
                        help='Skip downloading captions entirely')
    parser.add_argument('--all-videos', action='store_true',
                        help='Download all videos, not just Hungarian ones')
    parser.add_argument('--include-livestreams', action='store_true',
                        help='Include livestreams in downloads (not recommended)')
    parser.add_argument('--cookies', 
                        help='Path to cookies file for authentication')
    parser.add_argument('--browser', choices=['chrome', 'firefox', 'opera', 'edge', 'safari', 'brave', 'chromium'],
                        help='Browser to extract cookies from (chrome, firefox, opera, edge, safari, brave, chromium)')
    parser.add_argument('--format', default='mp4', choices=['mp4', 'webm', 'mkv', 'flv', 'avi'],
                        help='Preferred video format (default: mp4)')
    parser.add_argument('--caption-type', default='any', choices=['manual', 'auto', 'translate', 'any'],
                        help='Type of caption to prefer: manual, auto-generated, translation, or any (default: any)')
    parser.add_argument('--max-results', type=int, default=20,
                        help='Maximum number of search results to process (default: 20)')
    parser.add_argument('--pure-search', action='store_true',
                        help='Search using exactly the query provided without adding Hungarian terms')
    
    args = parser.parse_args()
    
    if not args.playlist and not args.video and not args.search:
        parser.error("Please provide either a playlist URL (-p), a video URL (-v), or a search query (-s)")
    
    # Setup log file if not specified
    log_file = args.log
    if not log_file:
        log_file = os.path.join(args.output, "download_log.jsonl")
    
    # Determine if we should filter for Hungarian only (not if pure search or all videos specified)
    hungarian_only = not (args.all_videos or (args.pure_search and args.search))
    
    # Determine if we should skip livestreams
    skip_livestreams = not args.include_livestreams
    
    if args.playlist:
        process_playlist(
            args.playlist, args.output, args.audio, args.language, 
            log_file, args.no_captions, args.cookies, args.browser, 
            args.format, args.caption_type, hungarian_only, skip_livestreams
        )
    
    if args.video:
        process_video(
            args.video, args.output, args.audio, args.language,
            log_file, args.no_captions, args.cookies, args.browser, 
            args.format, args.caption_type, hungarian_only, skip_livestreams
        )
        
    if args.search:
        process_hungarian_search(
            args.search, args.output, args.audio, args.language,
            log_file, args.no_captions, args.cookies, args.browser,
            args.format, args.caption_type, args.max_results, skip_livestreams,
            args.pure_search
        )


if __name__ == "__main__":
    main()