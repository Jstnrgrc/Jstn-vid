import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp
import os
import sys
import threading
import subprocess
from pathlib import Path
import urllib.request
import zipfile
import shutil

# Determine download folder
if getattr(sys, 'frozen', False):
    DOWNLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'Downloads', 'jstndownloader')
else:
    DOWNLOAD_FOLDER = "downloads"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# FFmpeg installation folder
FFMPEG_FOLDER = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'jstndownloader', 'ffmpeg')
FFMPEG_CONFIG = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'jstndownloader', 'ffmpeg_path.txt')

def get_ffmpeg_path():
    """Get FFmpeg path from config or check system"""
    # Check config file first
    if os.path.exists(FFMPEG_CONFIG):
        try:
            with open(FFMPEG_CONFIG, 'r') as f:
                stored_path = f.read().strip()
                if os.path.exists(stored_path):
                    return stored_path
        except:
            pass
    
    # Check default installation location
    default_bin = os.path.join(FFMPEG_FOLDER, 'bin', 'ffmpeg.exe')
    if os.path.exists(default_bin):
        save_ffmpeg_path(default_bin)
        return default_bin
    
    # Check system PATH
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return 'ffmpeg'  # Available in PATH
    except:
        pass
    
    return None

def save_ffmpeg_path(path):
    """Save FFmpeg path to config file"""
    try:
        config_dir = os.path.dirname(FFMPEG_CONFIG)
        os.makedirs(config_dir, exist_ok=True)
        with open(FFMPEG_CONFIG, 'w') as f:
            f.write(path)
    except:
        pass

def check_ffmpeg():
    """Check if FFmpeg is installed or available"""
    return get_ffmpeg_path() is not None

def install_ffmpeg_auto():
    """Automatically download and install FFmpeg"""
    try:
        # Show progress window for download
        progress_window = tk.Toplevel()
        progress_window.title("Downloading FFmpeg")
        progress_window.geometry("400x150")
        progress_window.configure(bg='#0d1117')
        progress_window.resizable(False, False)
        
        tk.Label(progress_window, text="Downloading FFmpeg...", font=('Segoe UI', 11), 
                bg='#0d1117', fg='#c9d1d9').pack(pady=10)
        
        progress = ttk.Progressbar(progress_window, length=350, mode='indeterminate')
        progress.pack(pady=10, padx=25)
        progress.start()
        
        status_label = tk.Label(progress_window, text="", font=('Segoe UI', 9), 
                               bg='#0d1117', fg='#8b949e')
        status_label.pack(pady=5)
        
        progress_window.update()
        
        # FFmpeg download URL (latest build from BtbN)
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        
        temp_folder = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'jstndownloader', 'temp')
        os.makedirs(temp_folder, exist_ok=True)
        zip_path = os.path.join(temp_folder, 'ffmpeg.zip')
        
        # Download FFmpeg
        status_label.config(text="Downloading... (this may take a minute)")
        progress_window.update()
        
        def download_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 // total_size, 100)
            status_label.config(text=f"Downloaded: {percent}%")
            progress_window.update()
        
        urllib.request.urlretrieve(ffmpeg_url, zip_path, download_progress)
        progress_window.destroy()
        
        # ===== ASK USER WHERE TO INSTALL =====
        install_dialog = messagebox.askyesno(
            "Install FFmpeg",
            "FFmpeg downloaded successfully!\n\n"
            "Where would you like to install FFmpeg?\n\n"
            "YES → Choose a custom location\n"
            "NO → Install to default location\n"
            f"    (AppData\\Local\\jstndownloader\\ffmpeg)"
        )
        
        if install_dialog:
            # Let user choose folder
            install_location = filedialog.askdirectory(
                title="Select FFmpeg Installation Folder",
                initialdir=os.path.expanduser('~'),
                mustexist=True
            )
            
            if not install_location:
                # User cancelled
                os.remove(zip_path)
                messagebox.showinfo("Cancelled", "FFmpeg installation cancelled.")
                return False
            
            install_folder = os.path.join(install_location, 'ffmpeg')
        else:
            # Use default location
            install_folder = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'jstndownloader', 'ffmpeg')
        
        # Show extraction progress
        progress_window = tk.Toplevel()
        progress_window.title("Installing FFmpeg")
        progress_window.geometry("400x150")
        progress_window.configure(bg='#0d1117')
        progress_window.resizable(False, False)
        
        tk.Label(progress_window, text="Installing FFmpeg...", font=('Segoe UI', 11), 
                bg='#0d1117', fg='#c9d1d9').pack(pady=10)
        
        progress = ttk.Progressbar(progress_window, length=350, mode='indeterminate')
        progress.pack(pady=10, padx=25)
        progress.start()
        
        status_label = tk.Label(progress_window, text="Extracting files...", font=('Segoe UI', 9), 
                               bg='#0d1117', fg='#8b949e')
        status_label.pack(pady=5)
        
        progress_window.update()
        
        # Extract FFmpeg
        os.makedirs(install_folder, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(install_folder)
        
        # Find ffmpeg.exe and move to bin folder
        ffmpeg_exe = None
        for root, dirs, files in os.walk(install_folder):
            if 'ffmpeg.exe' in files:
                ffmpeg_exe = os.path.join(root, 'ffmpeg.exe')
                break
        
        if ffmpeg_exe:
            # Copy to bin folder for easy access
            bin_folder = os.path.join(install_folder, 'bin')
            os.makedirs(bin_folder, exist_ok=True)
            shutil.copy(ffmpeg_exe, bin_folder)
            
            # Add to PATH for current session
            path_env = os.environ.get('PATH', '')
            if bin_folder not in path_env:
                os.environ['PATH'] = bin_folder + os.pathsep + path_env
            
            # Clean up zip and temp folder
            try:
                os.remove(zip_path)
                if not os.listdir(temp_folder):
                    os.rmdir(temp_folder)
            except:
                pass
            
            # Verify installation
            status_label.config(text="Verifying installation...")
            progress_window.update()
            
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5, 
                             env=os.environ)
                # Save FFmpeg path for future use
                ffmpeg_bin = os.path.join(bin_folder, 'ffmpeg.exe')
                save_ffmpeg_path(ffmpeg_bin)
                progress_window.destroy()
                messagebox.showinfo("Success", f"FFmpeg installed successfully!\n\nLocation: {bin_folder}\n\nRestart the app or try download again for best quality.")
                return True
            except:
                pass
        
        progress_window.destroy()
        messagebox.showerror("Installation Failed", "Could not install FFmpeg. Please visit:\nhttps://ffmpeg.org/download.html")
        return False
        
    except Exception as e:
        try:
            progress_window.destroy()
        except:
            pass
        messagebox.showerror("Download Failed", f"Could not download FFmpeg:\n{str(e)}\n\nVisit: https://ffmpeg.org/download.html")
        return False

class JstnDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("jstndownloader")
        self.root.geometry("800x800")
        self.root.configure(bg='#0d1117')
        self.root.minsize(700, 700)
        
        # Configure style
        self.setup_styles()
        
        self.downloading = False
        self.create_widgets()
        
    def setup_styles(self):
        """Setup modern styling"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure progressbar
        style.configure(
            'Accent.Horizontal.TProgressbar',
            background='#1f6feb',
            troughcolor='#30363d',
            bordercolor='#30363d',
            lightcolor='#1f6feb',
            darkcolor='#1f6feb'
        )
    
    def create_widgets(self):
        """Create the UI elements with modern professional design"""
        
        # Header with gradient effect
        header_frame = tk.Frame(self.root, bg='#161b22', height=110)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Add a colored accent bar
        accent_bar = tk.Frame(header_frame, bg='#1f6feb', height=4)
        accent_bar.pack(fill=tk.X)
        
        inner_header = tk.Frame(header_frame, bg='#161b22')
        inner_header.pack(fill=tk.BOTH, expand=True, padx=24, pady=14)
        
        tk.Label(
            inner_header,
            text="jstndownloader",
            font=('Segoe UI', 26, 'bold'),
            bg='#161b22',
            fg='#ffffff'
        ).pack(anchor=tk.W)
        
        tk.Label(
            inner_header,
            text="Fast & Reliable • 1000+ Sites • Simple to Use",
            font=('Segoe UI', 9),
            bg='#161b22',
            fg='#8b949e'
        ).pack(anchor=tk.W, pady=(4, 0))
        
        # Main content frame with padding
        main_frame = tk.Frame(self.root, bg='#0d1117')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)
        
        # URL input section
        url_label = tk.Label(main_frame, text="Enter Video URL", font=('Segoe UI', 10, 'bold'), bg='#0d1117', fg='#c9d1d9')
        url_label.pack(anchor=tk.W, pady=(0, 6))
        
        url_input_frame = tk.Frame(main_frame, bg='#161b22', highlightbackground='#30363d', highlightthickness=1)
        url_input_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 16))
        
        self.url_entry = tk.Entry(
            url_input_frame,
            font=('Segoe UI', 10),
            bg='#0d1117',
            fg='#c9d1d9',
            insertbackground='#1f6feb',
            border=0
        )
        self.url_entry.pack(fill=tk.BOTH, expand=True, padx=12, pady=11)
        self.url_entry.insert(0, "Paste video URL here...")
        self.url_entry.bind("<FocusIn>", self.on_focus_in)
        self.url_entry.bind("<FocusOut>", self.on_focus_out)
        
        # Quality selection section
        quality_label = tk.Label(main_frame, text="Select Quality", font=('Segoe UI', 10, 'bold'), bg='#0d1117', fg='#c9d1d9')
        quality_label.pack(anchor=tk.W, pady=(0, 8))
        
        self.quality_var = tk.StringVar(value="best")
        quality_frame = tk.Frame(main_frame, bg='#0d1117')
        quality_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 20))
        
        qualities = [
            ("Best Quality - Video + Audio (Recommended)", "best"),
            ("1080p HD - High Quality", "1080"),
            ("720p - Fast Download", "720"),
            ("Audio Only - MP3 Format", "audio")
        ]
        
        for text, value in qualities:
            rb = tk.Radiobutton(
                quality_frame,
                text=text,
                variable=self.quality_var,
                value=value,
                font=('Segoe UI', 9),
                bg='#0d1117',
                fg='#c9d1d9',
                activebackground='#0d1117',
                activeforeground='#1f6feb',
                selectcolor='#0d1117',
                highlightthickness=0
            )
            rb.pack(anchor=tk.W, pady=5)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg='#0d1117')
        button_frame.pack(fill=tk.X, pady=(0, 18))
        
        self.download_btn = tk.Button(
            button_frame,
            text="⬇  Download",
            command=self.on_download,
            font=('Segoe UI', 10, 'bold'),
            bg='#1f6feb',
            fg='white',
            activebackground='#388bfd',
            activeforeground='white',
            border=0,
            padx=28,
            pady=9,
            cursor='hand2'
        )
        self.download_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        folder_btn = tk.Button(
            button_frame,
            text="📁 Folder",
            command=self.open_folder,
            font=('Segoe UI', 10),
            bg='#30363d',
            fg='#c9d1d9',
            activebackground='#3d444d',
            activeforeground='#1f6feb',
            border=0,
            padx=28,
            pady=9,
            cursor='hand2'
        )
        folder_btn.pack(side=tk.LEFT)
        
        # Progress bar with label
        progress_container = tk.Frame(main_frame, bg='#0d1117')
        progress_container.pack(fill=tk.X, pady=(0, 12))
        
        progress_label = tk.Label(progress_container, text="Download Progress", font=('Segoe UI', 9, 'bold'), bg='#0d1117', fg='#8b949e')
        progress_label.pack(anchor=tk.W)
        
        self.progress = ttk.Progressbar(
            progress_container,
            length=650,
            mode='determinate',
            maximum=100,
            style='Accent.Horizontal.TProgressbar'
        )
        self.progress.pack(fill=tk.X, pady=(4, 0))
        
        # Download stats label
        self.stats_label = tk.Label(progress_container, text="", font=('Segoe UI', 8), bg='#0d1117', fg='#8b949e')
        self.stats_label.pack(anchor=tk.W, pady=(2, 0))
        
        # Status/Activity log
        status_label = tk.Label(main_frame, text="Activity Log", font=('Segoe UI', 10, 'bold'), bg='#0d1117', fg='#c9d1d9')
        status_label.pack(anchor=tk.W, pady=(0, 6))
        
        # Log area with better styling
        log_frame = tk.Frame(main_frame, bg='#161b22', highlightbackground='#30363d', highlightthickness=1)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output_text = tk.Text(
            log_frame,
            font=('Courier New', 8),
            height=12,
            bg='#0d1117',
            fg='#00d936',
            insertbackground='#1f6feb',
            border=0,
            relief=tk.FLAT,
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=self.output_text.yview)
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        self.output_text.config(state=tk.DISABLED)
        
        # Initial messages
        self.log("✓ jstndownloader ready")
        self.log("→ Paste a video URL and select quality")
        self.log("→ Click Download to start")
        self.log("")
    
    def on_focus_in(self, event):
        """Clear placeholder on focus"""
        if self.url_entry.get() == "Paste video URL here...":
            self.url_entry.delete(0, tk.END)
            self.url_entry.config(fg='#c9d1d9')
    
    def on_focus_out(self, event):
        """Show placeholder if empty"""
        if self.url_entry.get() == "":
            self.url_entry.insert(0, "Paste video URL here...")
            self.url_entry.config(fg='#8b949e')
    
    def log(self, message, color='#00d936', clear=False):
        """Log message to output"""
        self.output_text.config(state=tk.NORMAL)
        if clear:
            self.output_text.delete(1.0, tk.END)
        
        self.output_text.insert(tk.END, message + "\n", color)
        self.output_text.tag_config(color, foreground=color)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.root.update()
    
    def on_download(self):
        """Handle download button click"""
        if self.downloading:
            messagebox.showwarning("Already Downloading", "Please wait for current download to finish")
            return
        
        url = self.url_entry.get().strip()
        
        if not url or url == "Paste video URL here...":
            messagebox.showerror("Error", "Please enter a video URL")
            return
        
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
        self.downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.progress['value'] = 0
        self.stats_label.config(text="")
        
        # Run download in separate thread
        thread = threading.Thread(target=self.download_video, args=(url,), daemon=True)
        thread.start()
    
    def update_progress_stats(self, downloaded_bytes, total_bytes, speed_bps, eta_seconds):
        """Update progress display with detailed stats"""
        try:
            # Convert bytes to GB
            downloaded_gb = downloaded_bytes / (1024**3)
            total_gb = total_bytes / (1024**3)
            percent = int((downloaded_bytes / total_bytes * 100)) if total_bytes > 0 else 0
            
            # Convert speed
            if speed_bps > 0:
                speed_mbps = speed_bps / (1024**2)
                speed_str = f"{speed_mbps:.1f} MB/s"
            else:
                speed_str = "calculating..."
            
            # Convert ETA
            if eta_seconds > 0:
                minutes = int(eta_seconds // 60)
                seconds = int(eta_seconds % 60)
                eta_str = f"{minutes}m {seconds}s"
            else:
                eta_str = "calculating..."
            
            # Update progress bar
            self.progress['value'] = percent
            
            # Update stats label
            stats_text = f"↓ {downloaded_gb:.2f}GB / {total_gb:.2f}GB  •  {speed_str}  •  ETA: {eta_str}"
            self.stats_label.config(text=stats_text)
            
            self.root.update()
        except:
            pass
    
    def download_video(self, url):
        """Download video from any site - universal compatibility"""
        try:
            quality = self.quality_var.get()
            
            self.log("→ Analyzing video...", '#00d936')
            self.progress['value'] = 10
            self.root.update()
            
            # Get FFmpeg path if available
            ffmpeg_path = get_ffmpeg_path()
            
            # Create progress hook
            def progress_hook(d):
                if d['status'] == 'downloading':
                    try:
                        downloaded_bytes = d.get('downloaded_bytes', 0)
                        total_bytes = d.get('total_bytes', 0)
                        speed_bps = d.get('speed', 0)
                        eta_seconds = d.get('eta', 0)
                        
                        if total_bytes > 0:
                            self.update_progress_stats(downloaded_bytes, total_bytes, speed_bps, eta_seconds)
                    except:
                        pass
            
            ydl_opts_base = {
                'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
                'quiet': False,
                'no_warnings': False,
                'ignoreerrors': False,
                'no_check_certificate': True,
                'progress_hooks': [progress_hook],
            }
            
            # Add FFmpeg path if found
            if ffmpeg_path:
                ydl_opts_base['ffmpeg_location'] = ffmpeg_path
            
            title = None
            download_success = False
            ffmpeg_failed = False
            
            # ===== STAGE 1: Try with FFmpeg (best quality + audio) =====
            if quality != 'audio':  # For video downloads, try FFmpeg-based merge first
                if quality == 'best':
                    ffmpeg_format = 'bestvideo+bestaudio/best'
                elif quality == '1080':
                    ffmpeg_format = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
                elif quality == '720':
                    ffmpeg_format = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
                
                # Only try FFmpeg merge if FFmpeg is available
                if ffmpeg_path:
                    try:
                        self.log("→ Starting best quality download (merging video+audio)...", '#00d936')
                        self.progress['value'] = 20
                        self.root.update()
                        
                        ydl_opts = ydl_opts_base.copy()
                        ydl_opts['format'] = ffmpeg_format
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegConcat',
                            'only_multi_video': False,
                        }]
                        
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            title = info.get('title', 'video')
                        
                        download_success = True
                        self.progress['value'] = 100
                        self.log(f"✓ Successfully downloaded with best quality: {title}", '#51cf66')
                        self.log(f"✓ Saved to: {DOWNLOAD_FOLDER}", '#51cf66')
                        messagebox.showinfo("Success", f"Best Quality Download Complete!\n\n{title}\n\nSaved to downloads folder")
                        return
                        
                    except Exception as e:
                        error_str = str(e).lower()
                        if 'ffmpeg' in error_str:
                            ffmpeg_failed = True
                            self.log("⚠ FFmpeg error - falling back to audio-compatible format", '#ffd700')
                        else:
                            raise
                else:
                    # FFmpeg not available - offer to install
                    ffmpeg_failed = True
                    self.log("⚠ FFmpeg not installed - attempting auto-install...", '#ffd700')
                    
                    # Ask user if they want to auto-install FFmpeg
                    response = messagebox.askyesno(
                        "Install FFmpeg?",
                        "For BEST QUALITY + AUDIO merging, FFmpeg is required.\n\n"
                        "Without it, videos download with lower quality but still have audio.\n\n"
                        "Download and install FFmpeg automatically now?\n\n"
                        "This will download ~150MB (~2-5 minutes)\n\n"
                        "Click NO to continue with lower quality version."
                    )
                    if response:
                        self.log("→ Downloading FFmpeg (this takes a few minutes)...", '#ffd700')
                        self.downloading = False  # Allow window to update during download
                        
                        # Run install in separate thread
                        install_thread = threading.Thread(target=lambda: self._install_and_retry(url), daemon=True)
                        install_thread.start()
                        return
            
            # ===== STAGE 2: Fallback to pre-muxed formats (has audio, lower quality) =====
            if quality == 'best':
                format_strategies = [
                    'best[ext=mp4]',  # Pre-muxed MP4 (good quality + audio)
                    'best',  # Pre-muxed any container with audio
                ]
            elif quality == '1080':
                format_strategies = [
                    'best[height<=1080][ext=mp4]',  # Pre-muxed with height limit
                    'best[height<=1080]',  # Any container with height limit
                    'best',  # Last resort
                ]
            elif quality == '720':
                format_strategies = [
                    'best[height<=720][ext=mp4]',  # Pre-muxed with height limit
                    'best[height<=720]',  # Any container with height limit
                    'best',  # Last resort
                ]
            else:  # audio
                format_strategies = ['bestaudio[ext=m4a]/bestaudio', 'best']
            
            # Try fallback formats
            for attempt, fmt in enumerate(format_strategies, 1):
                try:
                    msg = "audio-compatible" if ffmpeg_failed else "standard"
                    self.log(f"→ Trying {msg} format ({attempt}/{len(format_strategies)})...", '#00d936')
                    self.progress['value'] = 25 + (attempt * 15)
                    self.root.update()
                    
                    ydl_opts = ydl_opts_base.copy()
                    ydl_opts['format'] = fmt
                    
                    # Add audio extraction for audio-only mode
                    if quality == 'audio' and attempt == 1:
                        ydl_opts['postprocessors'] = [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192',
                        }]
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        title = info.get('title', 'video')
                    
                    download_success = True
                    break
                    
                except Exception as e:
                    if attempt < len(format_strategies):
                        continue
                    else:
                        raise
            
            if download_success and title:
                self.progress['value'] = 100
                msg = "downloaded with audio" if ffmpeg_failed else "successfully downloaded"
                self.log(f"✓ Video {msg}: {title}", '#51cf66')
                self.log(f"✓ Saved to: {DOWNLOAD_FOLDER}", '#51cf66')
                if ffmpeg_failed and quality != 'audio':
                    self.log("💡 Tip: Install FFmpeg for BEST quality video + audio merge", '#8b949e')
                messagebox.showinfo("Success", f"Download completed!\n\n{title}\n\nSaved to downloads folder")
        
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            self.log("✗ Download error - Check URL or try another video", '#ff6b6b')
            self.log(f"→ Error details: {error_msg[:80]}", '#ff6b6b')
            messagebox.showerror("Download Failed", f"URL not supported or video not available.\n\n{error_msg[:150]}")
        
        except Exception as e:
            error_msg = str(e)
            
            # Specific error handling
            if 'Connection' in error_msg or 'timeout' in error_msg.lower() or 'network' in error_msg.lower():
                self.log("✗ Network error - Check your internet connection", '#ff6b6b')
                messagebox.showerror("Connection Error", "Check your internet connection and try again.")
            elif 'Unsupported' in error_msg or 'not supported' in error_msg.lower():
                self.log("✗ Site not supported - Try another link", '#ff6b6b')
                messagebox.showerror("Unsupported Site", "This website is not supported.\nTry another video link.")
            elif 'Permission' in error_msg or 'private' in error_msg.lower() or 'age' in error_msg.lower():
                self.log("✗ Video is private or restricted", '#ff6b6b')
                messagebox.showerror("Restricted", "This video is private, restricted, or age-gated.")
            else:
                self.log(f"✗ Error: {error_msg[:80]}", '#ff6b6b')
                messagebox.showerror("Download Failed", f"Error:\n{error_msg[:200]}")
        
        finally:
            self.downloading = False
            self.download_btn.config(state=tk.NORMAL)
            self.progress['value'] = 0
    
    def _install_and_retry(self, url):
        """Install FFmpeg and retry download"""
        if install_ffmpeg_auto():
            self.log("✓ FFmpeg installed successfully!", '#51cf66')
            self.log("→ Retrying download with best quality...", '#00d936')
            self.downloading = True
            # Retry the download
            self.download_video(url)
        else:
            self.log("→ FFmpeg installation failed - falling back to lower quality", '#ffd700')
            self.downloading = True
            self.download_video(url)
    
    def open_folder(self):
        """Open downloads folder using native file explorer"""
        try:
            # Create folder if it doesn't exist
            os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
            
            # Use subprocess with explicit explorer command on Windows
            if sys.platform == 'win32':
                # Windows - use explorer.exe directly
                subprocess.Popen(f'explorer "{os.path.abspath(DOWNLOAD_FOLDER)}"')
            elif sys.platform == 'darwin':
                # macOS - use open command
                subprocess.Popen(['open', DOWNLOAD_FOLDER])
            else:
                # Linux - use xdg-open
                subprocess.Popen(['xdg-open', DOWNLOAD_FOLDER])
            
            self.log("📂 Opening folder...", '#51cf66')
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder: {str(e)}\n\nFolder path: {DOWNLOAD_FOLDER}")
            self.log(f"❌ Could not open folder: {str(e)}", '#ff6b6b')

if __name__ == '__main__':
    root = tk.Tk()
    app = JstnDownloader(root)
    root.mainloop()
