import yt_dlp
from PySide6.QtCore import Signal, QThread

class DownloadThread(QThread):
    progress_signal = Signal(str)

    def __init__(self, url, options):
        super().__init__()
        self.url = url
        self.options = options

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)

            if total > 0:
                percent = (downloaded / total) * 100
                self.progress_signal.emit(str(percent))

    def run(self):
        try:
            self.options['progress_hooks'] = [self.progress_hook]
            with yt_dlp.YoutubeDL(self.options) as ydl:
                ydl.download([self.url])
        except Exception as e:
            print(f"Lỗi: {str(e)}")
    
    