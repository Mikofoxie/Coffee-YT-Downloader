import yt_dlp
import glob
import os


def download_video(url, format_choice, custom_name, download_folder, temp_folder, progress_callback, use_sponsorblock, skip_no_music, cancel_check=None, log_callback=None):
    initial_files = set(os.listdir(temp_folder)) if os.path.exists(temp_folder) else set()
    temp_files = set()

    def progress_hook(d):
        if cancel_check and cancel_check():
            raise Exception("Download cancelled by user")

        if d['status'] == 'downloading':
            if 'filename' in d:
                temp_file = d['filename']
                if temp_file:
                    temp_files.add(temp_file)
                    if not temp_file.endswith('.part'):
                        part_file = temp_file + '.part'
                        if os.path.exists(part_file):
                            temp_files.add(part_file)
                    base_name = os.path.splitext(temp_file)[0]
                    related_files = glob.glob(f"{base_name}*")
                    for related_file in related_files:
                        if os.path.exists(related_file):
                            temp_files.add(related_file)

            try:
                downloaded = float(d.get('downloaded_bytes', 0))
                total = float(d.get('total_bytes') or d.get('total_bytes_estimate', 1) or 1)
                percent = min(int((downloaded / total) * 100), 100)
                if progress_callback:
                    progress_callback(percent)
            except Exception as e:
                if log_callback:
                    log_callback(f"Error calculating progress: {str(e)}")

    format_map = {
        'mp4': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'mp3': 'bestaudio/best',
        'webm': 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]',
        'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
    }

    ydl_opts = {
        'format': format_map.get(format_choice),
        'outtmpl': os.path.join(temp_folder, f"{custom_name or '%(title)s'}.%(ext)s"),
        'noplaylist': False,
        'progress_hooks': [progress_hook],
        'postprocessors': [],
        'verbose': False,
        'continuedl': True,
        'quiet': True,
        'no_warnings': True,
    }

    if format_choice == 'webm':
        ydl_opts['merge_output_format'] = 'webm'
    elif format_choice in ['mp4', 'best']:
        ydl_opts['merge_output_format'] = 'mp4'

    if format_choice == 'mp3':
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        })

    if use_sponsorblock or skip_no_music:
        sponsor_categories = []
        if use_sponsorblock:
            sponsor_categories.extend(['sponsor', 'intro', 'outro', 'selfpromo', 'interaction'])
        if skip_no_music:
            sponsor_categories.append('filler')

        ydl_opts['postprocessors'].append({
            'key': 'SponsorBlock',
            'categories': sponsor_categories,
            'when': 'after_filter'
        })

        ydl_opts['postprocessors'].append({
            'key': 'ModifyChapters',
            'remove_sponsor_segments': sponsor_categories,
            'force_keyframes': False,
            'sponsorblock_chapter_title': '[SponsorBlock]: %(category_names)s',
            'when': 'post_process'
        })

        ydl_opts['postprocessors'].append({
            'key': 'FFmpegMetadata',
            'add_chapters': True,
            'add_metadata': False,
            'when': 'post_process'
        })

    class CustomLogger:
        def __init__(self, log_callback):
            self.log_callback = log_callback

        def debug(self, msg):
            if "[download]" not in msg and self.log_callback:
                self.log_callback(msg)

        def warning(self, msg):
            if self.log_callback:
                self.log_callback(f"Warning: {msg}")

        def error(self, msg):
            if self.log_callback:
                self.log_callback(f"Error: {msg}")

    ydl_opts['logger'] = CustomLogger(log_callback)

    try:
        if cancel_check and cancel_check():
            raise Exception("Download cancelled by user")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            temp_filename = ydl.prepare_filename(info)
            temp_files.add(temp_filename)

            if custom_name:
                custom_base_name = os.path.join(temp_folder, custom_name)
                related_files = glob.glob(f"{custom_base_name}*")
                for related_file in related_files:
                    if os.path.exists(related_file):
                        temp_files.add(related_file)

            ydl.download([url])

    except Exception as e:
        if str(e) == "Download cancelled by user":
            current_files = set(os.listdir(temp_folder)) if os.path.exists(temp_folder) else set()
            new_files = current_files - initial_files
            for new_file in new_files:
                full_path = os.path.join(temp_folder, new_file)
                temp_files.add(full_path)
            temp_files.update(glob.glob(os.path.join(temp_folder, "*.part")))
            temp_files.update(glob.glob(os.path.join(temp_folder, "*.part-Frag*")))
            temp_files.update(glob.glob(os.path.join(temp_folder, "*.ytdl")))
            if log_callback:
                log_callback(f"Cancellation temporary files: {temp_files}")
            raise Exception("Download cancelled by user") from e
        else:
            if log_callback:
                log_callback(f"Error downloading video: {str(e)}")
            raise

    return []