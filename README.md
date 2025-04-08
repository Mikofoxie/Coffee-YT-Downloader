# Coffee YT Downloader  

A simple YouTube downloader that automatically checks and installs dependencies before running.
Graphical interface for the command line tool [yt-dlp](https://github.com/yt-dlp/yt-dlp)

![image](https://github.com/user-attachments/assets/41bdef65-2980-4806-9344-00388909cfe3)

## How to Use  

### 🔹 Automatic Setup  
1. Download [releases](https://github.com/Mikofoxie/Coffee-YT-Downloader/releases) and extract the folder.  
2. Run `run.bat` with Administartor.
3. The script will check and install `ffmpeg` & `yt-dlp` if missing.  
4. `CoffeeYTDownloaderSetup.exe` will launch automatically.
5. After installation, please close the application and reopen it.
6. Enjoy

### 🔹 Manual Setup  
If you prefer to install dependencies yourself:
1. Download and install:  
   - [ffmpeg](https://ffmpeg.org/download.html)  
   - [yt-dlp](https://github.com/yt-dlp/yt-dlp#installation)  
2. Add both to the system `PATH`.

```bash
git clone https://github.com/Mikofoxie/Coffee-YT-Downloader.git
pip install PySide6 yt_dlp
cd Coffee-YT-Downloader
python main.py
```
3. Enjoy


