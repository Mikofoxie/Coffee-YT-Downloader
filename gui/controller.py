from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QFileDialog, QMessageBox, QApplication
from downloader.downloader import download_video
from config.settings import load_config, update_config
from config.languages import get_text, set_language
import os
import glob
import shutil


class DownloadThread(QThread):
    finished = Signal(str, list)
    error = Signal(str)
    progress = Signal(int)
    cancelled = Signal(list)
    log = Signal(str)
    
    def __init__(self, url, format_choice, custom_name, download_folder, temp_folder, use_sponsorblock, skip_no_music, cancel_check=None):
        super().__init__()
        self.url = url
        self.format_choice = format_choice
        self.custom_name = custom_name
        self.download_folder = download_folder
        self.temp_folder = temp_folder
        self.use_sponsorblock = use_sponsorblock
        self.skip_no_music = skip_no_music
        self._is_cancelled = False
        self.cancel_check = cancel_check
        self.initial_files = set(os.listdir(temp_folder)) if os.path.exists(temp_folder) else set()
        self.max_percent = 0

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            current_download_file = os.path.join(self.temp_folder, "current_download.txt")
            with open(current_download_file, "w", encoding="utf-8") as f:
                f.write(self.url)
            self.log.emit(f"Starting download for URL: {self.url}\nIf it's a playlist or YouTube channel, please wait...\nCancellation will take time. Consider closing the program")

            def progress_callback(percent):
                if percent < self.max_percent - 50 and percent >= 0:
                    self.max_percent = percent
                if percent >= 0 and percent <= 100:
                    if percent > self.max_percent:
                        self.max_percent = percent
                        self.progress.emit(self.max_percent)

            def log_callback(message):
                self.log.emit(message)

            download_video(
                url=self.url,
                format_choice=self.format_choice,
                custom_name=self.custom_name,
                download_folder=self.download_folder,
                temp_folder=self.temp_folder,
                progress_callback=progress_callback,
                use_sponsorblock=self.use_sponsorblock,
                skip_no_music=self.skip_no_music,
                cancel_check=lambda: self._is_cancelled or (self.cancel_check and self.cancel_check()),
                log_callback=log_callback
            )

            temp_files = [f for f in os.listdir(self.temp_folder) if f.endswith(('.mp3', '.mp4', '.webm')) and not f.startswith('current_download')]
            if not temp_files:
                raise Exception("No completed files found in temp folder after download")

            final_filepaths = []
            for temp_filename in temp_files:
                temp_filepath = os.path.join(self.temp_folder, temp_filename)
                final_filepath = os.path.join(self.download_folder, temp_filename)
                if os.path.exists(temp_filepath):
                    self.log.emit(f"Moving file: {temp_filepath} to {final_filepath}")
                    shutil.move(temp_filepath, final_filepath)
                    final_filepaths.append(final_filepath)
                else:
                    self.log.emit(f"Warning: File {temp_filepath} not found during move")

            if os.path.exists(current_download_file):
                os.remove(current_download_file)
                self.log.emit(f"Deleted current_download.txt: {current_download_file}")

            if os.path.exists(self.temp_folder) and not os.listdir(self.temp_folder):
                shutil.rmtree(self.temp_folder)
                self.log.emit(f"Deleted empty temp folder: {self.temp_folder}")

            self.finished.emit(get_text("success_download"), final_filepaths)

        except Exception as e:
            if str(e) == "Download cancelled by user":
                current_files = set(os.listdir(self.temp_folder)) if os.path.exists(self.temp_folder) else set()
                new_files = current_files - self.initial_files
                temp_files = {os.path.join(self.temp_folder, f) for f in new_files}
                temp_files.update(set(glob.glob(os.path.join(self.temp_folder, "*.part"))))
                temp_files.update(set(glob.glob(os.path.join(self.temp_folder, "*.part-Frag*"))))
                temp_files.update(set(glob.glob(os.path.join(self.temp_folder, "*.ytdl"))))
                self.cancelled.emit(list(temp_files))
                self.log.emit("Download cancelled by user")
            else:
                self.error.emit(f"{get_text('error_title')}: {str(e)}")
                self.log.emit(f"Error: {str(e)}")


class Controller:
    def __init__(self, window):
        self.window = window
        self.config = load_config()
        self.setup_language()
        self.connect_signals()
        self.apply_stylesheet()

    def setup_language(self):
        lang_display = self.config.get("language", "English")
        index = self.window.language_select.findText(lang_display)
        if index >= 0:
            self.window.language_select.setCurrentIndex(index)
        else:
            self.window.language_select.setCurrentText("English")
        set_language({"english": "en", "tiếng việt": "vi", "日本語": "jp", "en": "en", "vi": "vi", "jp": "jp"}.get(lang_display.lower(), "en"))
        self.update_ui_texts()
        self.window.folder_label.setText(f"{get_text('current_folder')}: {self.config['download_folder']}")
        format_map = {"best": "Best video (recommended)", "mp4": "MP4", "mp3": "MP3", "webm": "WebM"}
        self.window.format_select.setCurrentText(format_map.get(self.config["format_choice"].lower(), "Best video"))

    def connect_signals(self):
        self.window.download_btn.clicked.connect(self.download_video)
        self.window.cancel_btn.clicked.connect(self.cancel_download)
        self.window.folder_btn.clicked.connect(self.select_folder)
        self.window.language_select.currentIndexChanged.connect(self.change_language)
        self.window.format_select.currentTextChanged.connect(self.save_format_choice)

    def apply_stylesheet(self):
        try:
            stylesheet_paths = [
                "gui/styles.qss", "./gui/styles.qss", "../gui/styles.qss",
                os.path.join(os.path.dirname(__file__), "styles.qss")
            ]
            stylesheet = ""
            for path in stylesheet_paths:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        stylesheet = f.read()
                        break
                except FileNotFoundError:
                    continue
            if stylesheet:
                self.window.setStyleSheet(stylesheet)
            else:
                self.window.setStyleSheet("""
                    QMainWindow, QWidget { background-color: #F5F5DC; }
                    QPushButton { background-color: #8B4513; color: white; padding: 5px; }
                    QLineEdit, QComboBox { background-color: #FFFACD; border: 1px solid #8B4513; padding: 5px; }
                    QPlainTextEdit { background-color: #FFFACD; border: 1px solid #8B4513; padding: 5px; }
                """)
        except Exception:
            pass

    def update_ui_texts(self):
        self.window.setWindowTitle(get_text("app_title"))
        self.window.widgets["lang_label"].setText(get_text("language_label"))
        self.window.widgets["header"].setText(get_text("app_title"))
        self.window.widgets["url_group"].setTitle(get_text("url_group"))
        self.window.url_input.setPlaceholderText(get_text("url_placeholder"))
        self.window.widgets["options_group"].setTitle(get_text("options_group"))
        self.window.widgets["format_label"].setText(get_text("format_label"))
        self.window.widgets["name_label"].setText(get_text("filename_label"))
        self.window.filename_input.setPlaceholderText(get_text("filename_placeholder"))
        self.window.widgets["folder_label"].setText(get_text("folder_label"))
        self.window.folder_btn.setText(get_text("select_folder"))
        self.window.folder_label.setText(f"{get_text('current_folder')}: {self.config['download_folder']}")
        self.window.sponsorblock_checkbox.setText(get_text("sponsorblock_label"))
        self.window.skip_no_music_checkbox.setText(get_text("skip_no_music_label"))
        self.window.widgets["progress_group"].setTitle(get_text("progress_group"))
        self.window.status_label.setText(get_text("status_ready"))
        self.window.download_btn.setText(get_text("download_btn"))
        self.window.cancel_btn.setText(get_text("cancel_btn"))

    def cancel_download(self):
        if hasattr(self, 'thread') and self.thread and self.thread.isRunning():
            self.window._is_cancelled = True
            self.thread.cancel()
            self.window.status_label.setText(f"{get_text('status_label')}: {get_text('canceling')}")
            self.window.cancel_btn.setEnabled(False)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self.window, get_text("select_folder"))
        if folder:
            self.window.folder_label.setText(f"{get_text('current_folder')}: {folder}")
            self.config["download_folder"] = folder
            update_config(self.config)

    def change_language(self):
        lang_map = {"English": "en", "Tiếng Việt": "vi", "日本語": "jp"}
        lang_display = self.window.language_select.currentText()
        lang = lang_map.get(lang_display, "en")
        set_language(lang)
        self.update_ui_texts()
        QApplication.processEvents()
        self.window.repaint()
        self.config["language"] = lang_display
        update_config(self.config)

    def save_format_choice(self, text):
        format_map = {"Best video (recommended)": "best", "MP4": "mp4", "MP3": "mp3", "WebM": "webm"}
        format_choice = format_map.get(text, "best")
        self.config["format_choice"] = format_choice
        update_config(self.config)

    def download_video(self):
        self.window._is_cancelled = False
        url = self.window.url_input.text().strip()
        format_choice = self.window.format_select.currentText().lower()
        format_map = {"best video (recommended)": "best", "mp4": "mp4", "mp3": "mp3", "webm": "webm"}
        format_choice = format_map.get(format_choice, "best")
        custom_name = self.window.filename_input.text().strip()
        download_folder = self.config["download_folder"]

        temp_folder = os.path.join(download_folder, "temp")
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        temp_files = []
        temp_files.extend(glob.glob(os.path.join(temp_folder, "*.part")))
        temp_files.extend(glob.glob(os.path.join(temp_folder, "*.part-Frag*")))
        temp_files.extend(glob.glob(os.path.join(temp_folder, "*.ytdl")))
        current_download_file = os.path.join(temp_folder, "current_download.txt")

        previous_url = None
        if os.path.exists(current_download_file):
            with open(current_download_file, "r", encoding="utf-8") as f:
                previous_url = f.read().strip()

        use_sponsorblock = self.window.sponsorblock_checkbox.isChecked()
        skip_no_music = self.window.skip_no_music_checkbox.isChecked()

        if not url:
            QMessageBox.warning(self.window, get_text("error_title"), get_text("error_url_empty"))
            return
        if not download_folder:
            QMessageBox.warning(self.window, get_text("error_title"), get_text("error_folder_empty"))
            return

        if temp_files:
            if previous_url == url:
                self.window.status_label.setText(f"{get_text('status_label')}: {get_text('resuming_download')}")
            else:
                try:
                    shutil.rmtree(temp_folder)
                    os.makedirs(temp_folder)
                except Exception:
                    pass
                self.window.status_label.setText(f"{get_text('status_downloading')}...")
        else:
            self.window.status_label.setText(f"{get_text('status_downloading')}...")

        self.window.download_btn.setEnabled(False)
        self.window.cancel_btn.setEnabled(True)
        self.window.progress_bar.setValue(0)
        self.window.log_area.clear()

        self.thread = DownloadThread(url, format_choice, custom_name, download_folder, temp_folder,
                                    use_sponsorblock, skip_no_music, cancel_check=lambda: self.window._is_cancelled)
        self.thread.finished.connect(self.on_download_finished)
        self.thread.error.connect(self.on_download_error)
        self.thread.progress.connect(self.on_progress_update)
        self.thread.cancelled.connect(self.on_download_cancelled)
        self.thread.log.connect(self.update_log)
        self.thread.start()

    def on_progress_update(self, percent):
        self.window.progress_bar.setValue(percent)

    def update_log(self, message):
        self.window.log_area.appendPlainText(message)

    def on_download_cancelled(self, temp_files=None):
        self.window.status_label.setText(f"{get_text('status_label')}: {get_text('cancelled_message')}")
        self.window.download_btn.setEnabled(True)
        self.window.cancel_btn.setEnabled(False)
        self.window.progress_bar.setValue(0)
        self.window._is_cancelled = False

    def on_download_finished(self, message, final_filepaths):
        self.window.status_label.setText(f"{get_text('status_label')}: {message}")
        self.window.download_btn.setEnabled(True)
        self.window.cancel_btn.setEnabled(False)
        self.window.progress_bar.setValue(100)
        num_files = len(final_filepaths)
        download_folder = self.config["download_folder"]
        self.window.log_area.appendPlainText(f"Download completed. {num_files} file(s) saved to {download_folder}")
        QMessageBox.information(self.window, get_text("success_title"), f"{message}\n{num_files} file(s) saved to:\n{download_folder}")

    def on_download_error(self, message):
        self.window.status_label.setText(f"{get_text('status_label')}: {get_text('status_error')}")
        self.window.download_btn.setEnabled(True)
        self.window.cancel_btn.setEnabled(False)
        self.window.progress_bar.setValue(0)
        QMessageBox.critical(self.window, get_text("error_title"), message)