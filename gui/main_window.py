"""
███╗   ███╗ █████╗ ██╗███╗   ██╗    ██╗   ██╗██╗       
████╗ ████║██╔══██╗██║████╗  ██║    ██║   ██║██║       
██╔████╔██║███████║██║██╔██╗ ██║    ██║   ██║██║       
██║╚██╔╝██║██╔══██║██║██║╚██╗██║    ██║   ██║██║       
██║ ╚═╝ ██║██║  ██║██║██║ ╚████║    ╚██████╔╝██║       
╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝     ╚═════╝ ╚═╝       
An elegant, efficient YouTube video downloader with a clean GUI
"""

import os, glob, shutil, ctypes

from downloader.downloader import download_video; from config.settings import load_config, update_config; from config.languages import get_text, set_language;
from PySide6.QtCore import QThread, Signal, Qt, QPropertyAnimation; from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget,
    QComboBox, QFileDialog, QLabel, QMessageBox, QProgressBar, QCheckBox,
    QHBoxLayout, QGroupBox, QApplication, QScrollArea, QSizePolicy, QPlainTextEdit)


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
        self.initial_files = set(os.listdir(temp_folder))
        self.max_percent = 0

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            current_download_file = os.path.join(self.temp_folder, "current_download.txt")
            with open(current_download_file, "w", encoding="utf-8") as f:
                f.write(self.url)
            self.log.emit(f"Starting download for URL: {self.url}\nIf it's a playlist or youtube channel, please wait...\nCancellation will take time. Consider closing the program")

            def progress_callback(percent):
                if percent < self.max_percent - 50 and percent >= 0:
                    self.max_percent = percent
                if percent >= 0 and percent <= 100:
                    if percent > self.max_percent:
                        self.max_percent = percent
                        self.progress.emit(self.max_percent)

            download_video(
                url=self.url,
                format_choice=self.format_choice,
                custom_name=self.custom_name,
                download_folder=self.download_folder,
                temp_folder=self.temp_folder,
                progress_callback=progress_callback,
                use_sponsorblock=self.use_sponsorblock,
                skip_no_music=self.skip_no_music,
                cancel_check=lambda: self._is_cancelled or (self.cancel_check and self.cancel_check())
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

            if os.path.exists(self.temp_folder):
                remaining_files = os.listdir(self.temp_folder)
                if not remaining_files:
                    shutil.rmtree(self.temp_folder)
                    self.log.emit(f"Deleted empty temp folder: {self.temp_folder}")
                else:
                    self.log.emit(f"Temp folder {self.temp_folder} still contains files: {remaining_files}")

            self.finished.emit(get_text("success_download"), final_filepaths)

        except Exception as e:
            if str(e) == "Download cancelled by user":
                current_files = set(os.listdir(self.temp_folder))
                new_files = current_files - self.initial_files
                temp_files = set()
                for new_file in new_files:
                    temp_files.add(os.path.join(self.temp_folder, new_file))
                temp_files.update(glob.glob(os.path.join(self.temp_folder, "*.part")))
                temp_files.update(glob.glob(os.path.join(self.temp_folder, "*.part-Frag*")))
                temp_files.update(glob.glob(os.path.join(self.temp_folder, "*.ytdl")))
                self.cancelled.emit(list(temp_files))
                self.log.emit("Download cancelled by user")
            else:
                self.error.emit(f"{get_text('error_title')}: {str(e)}")
                self.log.emit(f"Error: {str(e)}")

class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.delta_y = 0  
        self.animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.animation.setDuration(100)  

    def wheelEvent(self, event):
        self.delta_y += event.angleDelta().y()
        current_pos = self.verticalScrollBar().value()
        target_pos = current_pos - self.delta_y     
        target_pos = max(self.verticalScrollBar().minimum(),
                         min(self.verticalScrollBar().maximum(), target_pos))
                
        self.animation.stop()  
        self.animation.setStartValue(current_pos)
        self.animation.setEndValue(target_pos)
        self.animation.start()      
        self.delta_y = 0
        event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._is_cancelled = False
        self.setWindowTitle(get_text("app_title"))

        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, 'icon', 'coffee.ico')
        self.setWindowIcon(QIcon(icon_path))
        myappid = "Mikofoxie.Coffee YT Downloader.Ver 0.1"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        self.setGeometry(100, 100, 550, 450)
        self.setMinimumSize(600, 620)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint)
        
        self.config = load_config()

        self.language_map = {"en": "English", "vi": "Tiếng Việt", "jp": "日本語"}
        self.language_code_map = {
            "english": "en", "tiếng việt": "vi", "日本語": "jp",
            "en": "en", "vi": "vi", "jp": "jp"
        }
        self.language_select = QComboBox()
        self.language_select.addItems(["English", "Tiếng Việt", "日本語"])
        
        lang_display = self.config.get("language", "English")
        index = self.language_select.findText(lang_display)
        if index >= 0:
            self.language_select.setCurrentIndex(index)
        else:
            self.language_select.setCurrentText("English")
            
        set_language(self.language_code_map.get(lang_display.lower(), "en"))

        self.widgets = {}
        self.init_ui()
        self.update_ui_texts()

        try:
            stylesheet_paths = [
                "gui/styles.qss", "./gui/styles.qss", "../gui/styles.qss",
                os.path.join(os.path.dirname(__file__), "styles.qss"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.qss")
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
                self.setStyleSheet(stylesheet)
            else:
                self.setStyleSheet("""
                    QMainWindow, QWidget { background-color: #F5F5DC; }
                    QPushButton { background-color: #8B4513; color: white; padding: 5px; }
                    QLineEdit, QComboBox { background-color: #FFFACD; border: 1px solid #8B4513; padding: 5px; }
                    QPlainTextEdit { background-color: #FFFACD; border: 1px solid #8B4513; padding: 5px; }
                """)
        except Exception:
            pass
    
    def init_ui(self):
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(20, 20, 20, 20)
       
        scroll_area = SmoothScrollArea(self)    
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(10)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        self.widgets["header"] = QLabel(get_text("app_title"))
        self.widgets["header"].setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.widgets["header"].setFont(font)
        content_layout.addWidget(self.widgets["header"])
        
        lang_layout = QHBoxLayout()
        self.widgets["lang_label"] = QLabel(get_text("language_label"))
        lang_layout.addWidget(self.widgets["lang_label"])
        self.language_select.setMinimumWidth(100)  
        lang_layout.addWidget(self.language_select)
        content_layout.addLayout(lang_layout)
        
        self.widgets["url_group"] = QGroupBox(get_text("url_group"))
        self.widgets["url_group"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        url_layout = QVBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(get_text("url_placeholder"))
        self.url_input.setMinimumHeight(30)
        url_layout.addWidget(self.url_input)
        self.widgets["url_group"].setLayout(url_layout)
        content_layout.addWidget(self.widgets["url_group"])
        
        self.widgets["options_group"] = QGroupBox(get_text("options_group"))
        self.widgets["options_group"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        options_layout = QVBoxLayout()
        
        format_layout = QHBoxLayout()
        self.widgets["format_label"] = QLabel(get_text("format_label"))
        format_layout.addWidget(self.widgets["format_label"])
        self.format_select = QComboBox()
        self.format_select.addItems(["MP4", "MP3", "WebM", "Best video (recommended)"])
        format_map = {
            "best": "Best video (recommended)",
            "mp4": "MP4",
            "mp3": "MP3",
            "webm": "WebM"
        }
        format_display = format_map.get(self.config["format_choice"].lower(), "Best video")
        self.format_select.setCurrentText(format_display)
        self.format_select.currentTextChanged.connect(self.save_format_choice)
        self.format_select.setMinimumWidth(100)
        format_layout.addWidget(self.format_select)
        options_layout.addLayout(format_layout)
        
        name_layout = QHBoxLayout()
        self.widgets["name_label"] = QLabel(get_text("filename_label"))
        name_layout.addWidget(self.widgets["name_label"])
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText(get_text("filename_placeholder"))
        self.filename_input.setMinimumHeight(30)
        name_layout.addWidget(self.filename_input)
        options_layout.addLayout(name_layout)
        
        folder_layout = QHBoxLayout()
        self.widgets["folder_label"] = QLabel(get_text("folder_label"))
        folder_layout.addWidget(self.widgets["folder_label"])
        self.folder_btn = QPushButton(get_text("select_folder"))
        self.folder_btn.clicked.connect(self.select_folder)
        self.folder_btn.setMinimumWidth(150)
        folder_layout.addWidget(self.folder_btn)
        options_layout.addLayout(folder_layout)
        
        self.folder_label = QLabel(f"{get_text('current_folder')}: {self.config['download_folder']}")
        self.folder_label.setWordWrap(True)  
        options_layout.addWidget(self.folder_label)
        
        checkbox_layout = QVBoxLayout()
        self.sponsorblock_checkbox = QCheckBox(get_text("sponsorblock_label"))
        self.skip_no_music_checkbox = QCheckBox(get_text("skip_no_music_label"))
        checkbox_layout.addWidget(self.sponsorblock_checkbox)
        checkbox_layout.addWidget(self.skip_no_music_checkbox)
        options_layout.addLayout(checkbox_layout)
        
        self.widgets["options_group"].setLayout(options_layout)
        content_layout.addWidget(self.widgets["options_group"])
        
        self.widgets["progress_group"] = QGroupBox(get_text("progress_group"))
        self.widgets["progress_group"].setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        progress_layout = QVBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setMinimumHeight(20)
        progress_layout.addWidget(self.progress_bar)
        self.status_label = QLabel(get_text("status_ready"))
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)
        self.widgets["progress_group"].setLayout(progress_layout)
        content_layout.addWidget(self.widgets["progress_group"])
        
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        content_layout.addWidget(self.log_area)
        
        self.download_btn = QPushButton(get_text("download_btn"))
        self.download_btn.setObjectName("download_btn")
        self.download_btn.setMinimumHeight(40)
        self.download_btn.clicked.connect(self.download_video)
        content_layout.addWidget(self.download_btn)

        self.cancel_btn = QPushButton(get_text("cancel_btn"))
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.cancel_btn.setEnabled(False)
        content_layout.addWidget(self.cancel_btn)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self.language_select.currentIndexChanged.connect(self.change_language)
        self.setCentralWidget(main_container)

    def cancel_download(self):
        if hasattr(self, 'thread') and self.thread and self.thread.isRunning():
            self._is_cancelled = True
            self.thread.cancel()
            self.status_label.setText(f"{get_text('status_label')}: {get_text('canceling')}")
            self.cancel_btn.setEnabled(False)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, get_text("select_folder"))
        if folder:
            self.folder_label.setText(f"{get_text('current_folder')}: {folder}")
            self.config["download_folder"] = folder
            update_config(self.config)

    def change_language(self):
        lang_map = {
            "English": "en",
            "Tiếng Việt": "vi",
            "日本語": "jp"
        }
        lang_display = self.language_select.currentText()
        lang = lang_map.get(lang_display, "en")
        set_language(lang)
        self.update_ui_texts()
        QApplication.processEvents()
        self.repaint()
        self.config["language"] = lang_display
        update_config(self.config)

    def update_ui_texts(self):
        self.setWindowTitle(get_text("app_title"))
        self.widgets["lang_label"].setText(get_text("language_label"))
        self.widgets["header"].setText(get_text("app_title"))
        self.widgets["url_group"].setTitle(get_text("url_group"))
        self.url_input.setPlaceholderText(get_text("url_placeholder"))
        self.widgets["options_group"].setTitle(get_text("options_group"))
        self.widgets["format_label"].setText(get_text("format_label"))
        self.widgets["name_label"].setText(get_text("filename_label"))
        self.filename_input.setPlaceholderText(get_text("filename_placeholder"))
        self.widgets["folder_label"].setText(get_text("folder_label"))
        self.folder_btn.setText(get_text("select_folder"))
        self.folder_label.setText(f"{get_text('current_folder')}: {self.config['download_folder']}")
        self.sponsorblock_checkbox.setText(get_text("sponsorblock_label"))
        self.skip_no_music_checkbox.setText(get_text("skip_no_music_label"))
        self.widgets["progress_group"].setTitle(get_text("progress_group"))
        self.status_label.setText(get_text("status_ready"))
        self.download_btn.setText(get_text("download_btn"))
        self.cancel_btn.setText(get_text("cancel_btn"))

    def save_format_choice(self, text):
        format_map = {
            "Best video": "best",
            "MP4": "mp4",
            "MP3": "mp3",
            "WebM": "webm"
        }
        format_choice = format_map.get(text, "best")
        self.config["format_choice"] = format_choice
        update_config(self.config)

    def download_video(self):
        self._is_cancelled = False  
        url = self.url_input.text().strip()
        format_choice = self.format_select.currentText().lower()
        format_map = {
            "best video": "best",
            "mp4": "mp4",
            "mp3": "mp3",
            "webm": "webm"
        }
        format_choice = format_map.get(format_choice, "best")
        custom_name = self.filename_input.text().strip()
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

        use_sponsorblock = self.sponsorblock_checkbox.isChecked()
        skip_no_music = self.skip_no_music_checkbox.isChecked()

        if not url:
            QMessageBox.warning(self, get_text("error_title"), get_text("error_url_empty"))
            return
        if not download_folder:
            QMessageBox.warning(self, get_text("error_title"), get_text("error_folder_empty"))
            return

        if temp_files:
            if previous_url == url:
                self.status_label.setText(f"{get_text('status_label')}: {get_text('resuming_download')}")
            else:
                try:
                    shutil.rmtree(temp_folder)
                    os.makedirs(temp_folder)
                except Exception:
                    pass
                self.status_label.setText(f"{get_text('status_downloading')}...")
        else:
            self.status_label.setText(f"{get_text('status_downloading')}...")

        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_area.clear()

        self.thread = DownloadThread(url, format_choice, custom_name, download_folder, temp_folder,
                                    use_sponsorblock, skip_no_music, cancel_check=lambda: self._is_cancelled)
        self.thread.finished.connect(self.on_download_finished)
        self.thread.error.connect(self.on_download_error)
        self.thread.progress.connect(self.on_progress_update)
        self.thread.cancelled.connect(self.on_download_cancelled)
        self.thread.log.connect(self.update_log)
        self.thread.start()

    def on_progress_update(self, percent):
        self.progress_bar.setValue(percent)

    def update_log(self, message):
        self.log_area.appendPlainText(message)

    def on_download_cancelled(self, temp_files=None):
        self.status_label.setText(f"{get_text('status_label')}: {get_text('cancelled_message')}")
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self._is_cancelled = False

    def on_download_finished(self, message, final_filepaths):
        self.status_label.setText(f"{get_text('status_label')}: {message}")
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        num_files = len(final_filepaths)
        download_folder = self.config["download_folder"]
        self.log_area.appendPlainText(f"Download completed. {num_files} file(s) saved to {download_folder}")
        QMessageBox.information(self, get_text("success_title"), f"{message}\n{num_files} file(s) saved to:\n{download_folder}")

    def on_download_error(self, message):
        self.status_label.setText(f"{get_text('status_label')}: {get_text('status_error')}")
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        QMessageBox.critical(self, get_text("error_title"), message)