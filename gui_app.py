import customtkinter as ctk
from tkinter import filedialog
import threading
import yt_dlp
import os
import glob

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YT Media Downloader")
        self.geometry("700x550")
        self.resizable(False, False)

        # Output directory state
        self.output_dir = os.path.join(os.getcwd(), "downloads")

        self.create_widgets()

    def create_widgets(self):
        # Header
        self.header_label = ctk.CTkLabel(self, text="YT Media Downloader", font=ctk.CTkFont(size=24, weight="bold"))
        self.header_label.pack(pady=(20, 10))

        # URL Input
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Paste YouTube or Playlist URL here...", width=500, height=40)
        self.url_entry.pack(pady=10)

        # Main Content Frame (Settings + Toggles)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # ==========================================
        # LEFT COLUMN: Core Settings
        # ==========================================
        self.left_frame = ctk.CTkFrame(self.main_frame)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.settings_label = ctk.CTkLabel(self.left_frame, text="Core Settings", font=ctk.CTkFont(weight="bold"))
        self.settings_label.pack(pady=(10, 5))

        # Media Type
        self.media_var = ctk.StringVar(value="audio")
        self.media_audio_rb = ctk.CTkRadioButton(self.left_frame, text="Audio Only", variable=self.media_var, value="audio", command=self.update_ui_state)
        self.media_audio_rb.pack(pady=5, padx=20, anchor="w")
        self.media_video_rb = ctk.CTkRadioButton(self.left_frame, text="Video (MP4)", variable=self.media_var, value="video", command=self.update_ui_state)
        self.media_video_rb.pack(pady=5, padx=20, anchor="w")

        # Audio Format
        self.format_label = ctk.CTkLabel(self.left_frame, text="Audio Format:")
        self.format_label.pack(pady=(15, 0), padx=20, anchor="w")
        self.format_var = ctk.StringVar(value="M4A (AAC)")
        self.format_dropdown = ctk.CTkOptionMenu(self.left_frame, variable=self.format_var, values=["M4A (AAC)", "MP3", "OPUS", "FLAC (Lossless)", "WAV (Lossless)"], command=self.update_ui_state)
        self.format_dropdown.pack(pady=5, padx=20, fill="x")

        # Quality
        self.quality_label = ctk.CTkLabel(self.left_frame, text="Bitrate Quality:")
        self.quality_label.pack(pady=(10, 0), padx=20, anchor="w")
        self.quality_var = ctk.StringVar(value="Original Stream")
        self.quality_dropdown = ctk.CTkOptionMenu(self.left_frame, variable=self.quality_var, values=["Original Stream", "320", "256", "192", "128"])
        self.quality_dropdown.pack(pady=5, padx=20, fill="x")

        # ==========================================
        # RIGHT COLUMN: Advanced Toggles
        # ==========================================
        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.toggles_label = ctk.CTkLabel(self.right_frame, text="Advanced Features", font=ctk.CTkFont(weight="bold"))
        self.toggles_label.pack(pady=(10, 15))

        # Toggles
        self.album_art_var = ctk.BooleanVar(value=True)
        self.album_art_switch = ctk.CTkSwitch(self.right_frame, text="Embed Album Art", variable=self.album_art_var)
        self.album_art_switch.pack(pady=10, padx=20, anchor="w")

        self.metadata_var = ctk.BooleanVar(value=True)
        self.metadata_switch = ctk.CTkSwitch(self.right_frame, text="Auto-Tag Metadata", variable=self.metadata_var)
        self.metadata_switch.pack(pady=10, padx=20, anchor="w")

        # Speed Limit
        self.speed_label = ctk.CTkLabel(self.right_frame, text="Speed Limit (e.g. 5M, 500K):")
        self.speed_label.pack(pady=(15, 0), padx=20, anchor="w")
        self.speed_entry = ctk.CTkEntry(self.right_frame, placeholder_text="Leave blank for unlimited")
        self.speed_entry.pack(pady=5, padx=20, fill="x")

        # Output Folder
        self.folder_button = ctk.CTkButton(self.right_frame, text="Choose Output Folder", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.choose_folder)
        self.folder_button.pack(pady=(20, 5), padx=20, fill="x")
        self.folder_label = ctk.CTkLabel(self.right_frame, text=f".../{os.path.basename(self.output_dir)}", text_color="gray")
        self.folder_label.pack(pady=0, padx=20)

        # ==========================================
        # BOTTOM FRAME: Action & Progress
        # ==========================================
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(pady=10, padx=20, fill="x")

        self.download_button = ctk.CTkButton(self.bottom_frame, text="START DOWNLOAD", height=50, font=ctk.CTkFont(size=16, weight="bold"), command=self.start_download_thread)
        self.download_button.pack(pady=10, fill="x")

        self.progress_bar = ctk.CTkProgressBar(self.bottom_frame)
        self.progress_bar.pack(pady=(10, 5), fill="x")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.bottom_frame, text="Ready.", text_color="gray")
        self.status_label.pack()

    def update_ui_state(self, *args):
        # Disable audio-specific options if video is selected
        if self.media_var.get() == "video":
            self.format_dropdown.configure(state="disabled")
            self.quality_dropdown.configure(state="disabled")
        else:
            self.format_dropdown.configure(state="normal")
            fmt = self.format_var.get()
            if "Lossless" in fmt:
                self.quality_dropdown.configure(state="disabled")
            else:
                self.quality_dropdown.configure(state="normal")

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir)
        if folder:
            self.output_dir = folder
            self.folder_label.configure(text=f".../{os.path.basename(self.output_dir)}")

    def build_ydl_opts(self):
        import sys
        opts = {
            'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'noprogress': True,
            'retries': 3,
            'fragment_retries': 3,
            'progress_hooks': [self.yt_dlp_hook],
            'allow_playlist_files': False,
        }
        
        # When compiled to an EXE, PyInstaller extracts files to a temp _MEIPASS folder
        if getattr(sys, 'frozen', False):
            opts['ffmpeg_location'] = sys._MEIPASS
        else:
            opts['ffmpeg_location'] = os.getcwd()

        # Speed Limit
        speed_text = self.speed_entry.get().strip().upper()
        if speed_text:
            try:
                if speed_text.endswith('M'): val = int(float(speed_text[:-1]) * 1024 * 1024)
                elif speed_text.endswith('K'): val = int(float(speed_text[:-1]) * 1024)
                else: val = int(speed_text)
                opts['ratelimit'] = val
            except ValueError:
                pass # Ignore invalid speed limits

        postprocessors = []
        media = self.media_var.get()
        embed_art = self.album_art_var.get()
        auto_meta = self.metadata_var.get()

        if media == "video":
            opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            if embed_art:
                opts['writethumbnail'] = True
                postprocessors.append({'key': 'EmbedThumbnail'})
        else:
            opts['format'] = 'bestaudio/best'
            fmt_str = self.format_var.get()
            codec_map = {"M4A (AAC)": "m4a", "MP3": "mp3", "OPUS": "opus", "FLAC (Lossless)": "flac", "WAV (Lossless)": "wav"}
            codec = codec_map.get(fmt_str, "m4a")

            extract_pp = {'key': 'FFmpegExtractAudio', 'preferredcodec': codec}
            
            # Quality
            if "Lossless" not in fmt_str:
                q_str = self.quality_var.get()
                if q_str != "Original Stream":
                    extract_pp['preferredquality'] = q_str
            
            postprocessors.append(extract_pp)

            if embed_art:
                opts['writethumbnail'] = True
                postprocessors.append({'key': 'EmbedThumbnail'})

        if auto_meta:
            opts['parse_metadata'] = ['title:%(artist)s - %(title)s']
            postprocessors.append({'key': 'FFmpegMetadata'})

        if postprocessors:
            opts['postprocessors'] = postprocessors

        return opts

    def yt_dlp_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            
            filename = os.path.basename(d.get('filename', 'Unknown File'))
            if len(filename) > 40:
                filename = filename[:37] + "..."

            if total > 0:
                percent = downloaded / total
            else:
                percent = 0
            
            # Use app.after to safely update GUI from background thread
            self.after(0, self.update_progress, percent, f"Downloading: {filename}")

        elif d['status'] == 'finished':
            self.after(0, self.update_progress, 1.0, "Converting & Processing Metadata...")
        
        elif d['status'] == 'error':
            self.after(0, self.update_progress, 0.0, "Error occurred during download.")

    def update_progress(self, percent, text):
        self.progress_bar.set(percent)
        self.status_label.configure(text=text)

    def cleanup_stray_thumbnails(self):
        """Remove leftover thumbnail files that yt-dlp leaves behind.
        These can confuse media players into showing the playlist cover
        instead of the per-video embedded thumbnails."""
        for ext in ('*.jpg', '*.webp', '*.png'):
            for f in glob.glob(os.path.join(self.output_dir, ext)):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def download_thread(self, url):
        opts = self.build_ydl_opts()
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.cleanup_stray_thumbnails()
            self.after(0, self.finish_download, "Download Completed Successfully!", "green")
        except Exception as e:
            self.after(0, self.finish_download, f"Failed: {str(e)}", "red")

    def start_download_thread(self):
        url = self.url_entry.get().strip()
        if not url:
            # Fallback to default if empty
            url = "https://www.youtube.com/playlist?list=PLNyPiL5e4F2bo2ruSM_ivlbH5xrXMSF7f"

        self.download_button.configure(state="disabled", text="DOWNLOADING...")
        self.progress_bar.set(0)
        self.status_label.configure(text="Initializing...", text_color="white")

        # Start thread
        thread = threading.Thread(target=self.download_thread, args=(url,))
        thread.daemon = True
        thread.start()

    def finish_download(self, message, color):
        self.download_button.configure(state="normal", text="START DOWNLOAD")
        self.status_label.configure(text=message, text_color=color)

if __name__ == "__main__":
    app = App()
    app.mainloop()
