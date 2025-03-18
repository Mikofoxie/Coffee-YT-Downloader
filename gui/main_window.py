from PySide6.QtCore import Qt, QPropertyAnimation
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QLineEdit, QVBoxLayout, QWidget,
    QComboBox, QLabel, QProgressBar, QCheckBox, QHBoxLayout,
    QGroupBox, QScrollArea, QSizePolicy, QPlainTextEdit
)
import os
import ctypes


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
    def __init__(self, get_text):
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

        self.widgets = {}
        self.init_ui(get_text)

    def init_ui(self, get_text):
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
        self.language_select = QComboBox()
        self.language_select.setMinimumWidth(100)
        self.language_select.addItems(["English", "Tiếng Việt", "日本語"])
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
        self.folder_btn.setMinimumWidth(150)
        folder_layout.addWidget(self.folder_btn)
        options_layout.addLayout(folder_layout)

        self.folder_label = QLabel(f"{get_text('current_folder')}: ")
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
        content_layout.addWidget(self.download_btn)

        self.cancel_btn = QPushButton(get_text("cancel_btn"))
        self.cancel_btn.setObjectName("cancel_btn")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.setEnabled(False)
        content_layout.addWidget(self.cancel_btn)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self.setCentralWidget(main_container)