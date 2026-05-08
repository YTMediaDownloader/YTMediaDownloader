import customtkinter as ctk
from tkinter import filedialog, colorchooser
import threading
import yt_dlp
import os
import glob
import json
import urllib.request
import webbrowser
from packaging import version

try:
    from tkinterdnd2 import TkinterDnD, DND_TEXT, DND_ALL
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

VERSION = "2.0.0"
HISTORY_FILE = os.path.join(os.getcwd(), '.download_history.txt')
CONFIG_FILE = os.path.join(os.getcwd(), 'config.json')
REPO_URL = "https://api.github.com/repos/YTMediaDownloader/YTMediaDownloader/releases/latest"
RELEASES_PAGE = "https://github.com/YTMediaDownloader/YTMediaDownloader/releases"

COLOR_PRESETS = {
    "Blue": ("#3B8ED0", "#1F6AA5"),
    "Green": ("#2ECC71", "#27AE60"),
    "Purple": ("#9B59B6", "#8E44AD"),
    "Orange": ("#E67E22", "#D35400"),
    "Red": ("#E74C3C", "#C0392B"),
    "Pink": ("#E91E9C", "#C2185B"),
}

NAMING_TEMPLATES = {
    "Title Only": "%(title)s",
    "Uploader - Title": "%(uploader)s - %(title)s",
    "Numbered (01 Song)": "%(playlist_index)s - %(title)s",
}


class SettingsWindow(ctk.CTkToplevel):
    """A popup window for app personalization."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Settings")
        self.geometry("400x450")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.save_and_close)

        # ---- Appearance Section ----
        ctk.CTkLabel(self, text="Appearance", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        # Theme Toggle
        theme_frame = ctk.CTkFrame(self, fg_color="transparent")
        theme_frame.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left")
        self.theme_var = ctk.StringVar(value=parent.settings.get("theme", "Dark"))
        ctk.CTkOptionMenu(theme_frame, variable=self.theme_var,
                          values=["Dark", "Light", "System"],
                          command=self.on_theme_change).pack(side="right")

        # ---- Accent Color Section ----
        ctk.CTkLabel(self, text="Accent Color", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        # Color Preset Buttons
        self.color_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.color_frame.pack(pady=5, padx=20)

        col = 0
        for name, (fg, hover) in COLOR_PRESETS.items():
            btn = ctk.CTkButton(self.color_frame, text=name, width=100, height=35,
                                fg_color=fg, hover_color=hover,
                                command=lambda n=name: self.apply_preset(n))
            btn.grid(row=col // 3, column=col % 3, padx=5, pady=5)
            col += 1

        # Custom HEX
        hex_frame = ctk.CTkFrame(self, fg_color="transparent")
        hex_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(hex_frame, text="Custom HEX:").pack(side="left")
        self.hex_entry = ctk.CTkEntry(hex_frame, placeholder_text="#FF5733", width=120)
        self.hex_entry.pack(side="left", padx=10)
        ctk.CTkButton(hex_frame, text="Apply", width=70, command=self.apply_custom_hex).pack(side="left")
        ctk.CTkButton(hex_frame, text="Pick", width=60, command=self.pick_color).pack(side="left", padx=5)

        # ---- Save & Close ----
        ctk.CTkButton(self, text="Save & Close", height=40, font=ctk.CTkFont(weight="bold"),
                      command=self.save_and_close).pack(pady=20, padx=40, fill="x")

    def on_theme_change(self, value):
        ctk.set_appearance_mode(value)
        self.parent.settings["theme"] = value
        self.parent.save_settings()

    def apply_preset(self, name):
        fg, hover = COLOR_PRESETS[name]
        self.parent.settings["accent_color"] = name
        self.parent.settings["custom_hex"] = ""
        self.parent.apply_accent_color(fg, hover)
        self.parent.save_settings()

    def apply_custom_hex(self):
        hex_val = self.hex_entry.get().strip()
        if hex_val and hex_val.startswith("#"):
            self.parent.settings["accent_color"] = "Custom"
            self.parent.settings["custom_hex"] = hex_val
            self.parent.apply_accent_color(hex_val, hex_val)
            self.parent.save_settings()

    def pick_color(self):
        color = colorchooser.askcolor(title="Choose Accent Color")
        if color and color[1]:
            self.hex_entry.delete(0, "end")
            self.hex_entry.insert(0, color[1])
            self.apply_custom_hex()

    def save_and_close(self):
        self.parent.save_settings()
        self.destroy()


class App(ctk.CTk, TkinterDnD.DnDWrapper if DND_AVAILABLE else object):
    def __init__(self):
        super().__init__()
        if DND_AVAILABLE:
            self.TkdndVersion = TkinterDnD._require(self)

        self.title("YT Media Downloader")
        self.geometry("750x800")
        self.resizable(False, False)

        self.output_dir = os.path.join(os.getcwd(), "downloads")

        # Update state
        self.update_available = False
        self.latest_version = ""
        self.settings_window = None

        # Load settings before creating widgets
        self.load_settings()
        self.create_widgets()

        # Apply saved accent color
        accent = self.settings.get("accent_color", "Blue")
        if accent == "Custom" and self.settings.get("custom_hex"):
            self.apply_accent_color(self.settings["custom_hex"], self.settings["custom_hex"])
        elif accent in COLOR_PRESETS:
            fg, hover = COLOR_PRESETS[accent]
            self.apply_accent_color(fg, hover)

        # Apply initial UI state
        self.update_ui_state()

        # Start background update check
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    def load_settings(self):
        default = {
            "theme": "Dark", "accent_color": "Blue", "custom_hex": "",
            "output_dir": os.path.join(os.getcwd(), "downloads"),
            "naming_template": "Title Only", "custom_template": "%(title)s",
            "smart_skip": True, "metadata": True, "album_art": True,
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.settings = {**default, **json.load(f)}
            except Exception:
                self.settings = default
        else:
            self.settings = default

        self.output_dir = self.settings["output_dir"]
        ctk.set_appearance_mode(self.settings["theme"])

    def save_settings(self):
        self.settings["output_dir"] = self.output_dir
        self.settings["smart_skip"] = self.smart_skip_var.get()
        self.settings["metadata"] = self.metadata_var.get()
        self.settings["album_art"] = self.album_art_var.get()
        self.settings["naming_template"] = self.naming_var.get()
        self.settings["custom_template"] = self.custom_naming_entry.get()
        self.settings["theme"] = ctk.get_appearance_mode()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)

    # =============================================
    # UI CONSTRUCTION
    # =============================================
    def create_widgets(self):
        # Header Row
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(pady=(15, 0), padx=20, fill="x")

        self.header_label = ctk.CTkLabel(self.top_frame, text="YT Media Downloader",
                                         font=ctk.CTkFont(size=24, weight="bold"))
        self.header_label.pack(side="left", padx=(80, 0), expand=True)

        self.settings_button = ctk.CTkButton(self.top_frame, text="⚙", width=40, height=40,
                                             font=ctk.CTkFont(size=18),
                                             fg_color="gray30", hover_color="gray40",
                                             command=self.show_settings)
        self.settings_button.pack(side="right")

        self.version_label = ctk.CTkLabel(self, text=f"v{VERSION}", text_color="gray")
        self.version_label.pack(pady=(0, 5))

        # Update Notification (hidden by default)
        self.update_button = ctk.CTkButton(self, text="🚀 New Update Available!",
                                           fg_color="#2ecc71", hover_color="#27ae60",
                                           text_color="white", height=30, command=self.open_releases)

        # Batch URL Input
        self.url_label = ctk.CTkLabel(self, text="URL Queue  (one per line):",
                                      font=ctk.CTkFont(weight="bold"))
        self.url_label.pack(pady=(5, 0), padx=20, anchor="w")
        self.url_textbox = ctk.CTkTextbox(self, height=80, border_width=2)
        self.url_textbox.pack(pady=(3, 8), padx=20, fill="x")

        # Drag-and-drop support
        if DND_AVAILABLE:
            try:
                inner_text = self.url_textbox._textbox
                inner_text.drop_target_register(DND_ALL)
                inner_text.dnd_bind('<<Drop>>', self._on_drop)
            except Exception:
                pass

        # Main 2-Column Frame
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(pady=5, padx=20, fill="both", expand=True)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # ---- LEFT COLUMN: Core Settings ----
        self.left_frame = ctk.CTkFrame(self.main_frame)
        self.left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(self.left_frame, text="Core Settings",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        # Media Type
        self.media_var = ctk.StringVar(value="audio")
        self.radio_audio = ctk.CTkRadioButton(self.left_frame, text="Audio Only", variable=self.media_var,
                           value="audio", command=self.update_ui_state)
        self.radio_audio.pack(pady=4, padx=20, anchor="w")
        self.radio_video = ctk.CTkRadioButton(self.left_frame, text="Video (MP4)", variable=self.media_var,
                           value="video", command=self.update_ui_state)
        self.radio_video.pack(pady=4, padx=20, anchor="w")

        # Audio Format
        ctk.CTkLabel(self.left_frame, text="Audio Format:").pack(pady=(10, 0), padx=20, anchor="w")
        self.format_var = ctk.StringVar(value="M4A (AAC)")
        self.format_dropdown = ctk.CTkOptionMenu(self.left_frame, variable=self.format_var,
            values=["M4A (AAC)", "MP3", "OPUS", "FLAC (Lossless)", "WAV (Lossless)"],
            command=self.update_ui_state)
        self.format_dropdown.pack(pady=3, padx=20, fill="x")

        # Bitrate Quality
        ctk.CTkLabel(self.left_frame, text="Bitrate Quality:").pack(pady=(8, 0), padx=20, anchor="w")
        self.quality_var = ctk.StringVar(value="Original Stream")
        self.quality_dropdown = ctk.CTkOptionMenu(self.left_frame, variable=self.quality_var,
            values=["Original Stream", "320", "256", "192", "128"])
        self.quality_dropdown.pack(pady=3, padx=20, fill="x")

        # Video Resolution
        self.resolution_label = ctk.CTkLabel(self.left_frame, text="Video Resolution:")
        self.resolution_label.pack(pady=(8, 0), padx=20, anchor="w")
        self.resolution_var = ctk.StringVar(value="Best Available")
        self.resolution_dropdown = ctk.CTkOptionMenu(self.left_frame, variable=self.resolution_var,
            values=["Best Available", "4K (2160p)", "1440p", "1080p", "720p", "480p"])
        self.resolution_dropdown.pack(pady=3, padx=20, fill="x")

        # ---- RIGHT COLUMN: Advanced Features ----
        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(self.right_frame, text="Advanced Features",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(10, 10))

        # Toggles
        self.album_art_var = ctk.BooleanVar(value=self.settings.get("album_art", True))
        self.switch_art = ctk.CTkSwitch(self.right_frame, text="Embed Album Art",
                      variable=self.album_art_var)
        self.switch_art.pack(pady=6, padx=20, anchor="w")

        self.metadata_var = ctk.BooleanVar(value=self.settings.get("metadata", True))
        self.switch_meta = ctk.CTkSwitch(self.right_frame, text="Auto-Tag Metadata",
                      variable=self.metadata_var)
        self.switch_meta.pack(pady=6, padx=20, anchor="w")

        self.smart_skip_var = ctk.BooleanVar(value=self.settings.get("smart_skip", True))
        self.switch_skip = ctk.CTkSwitch(self.right_frame, text="Smart Skip (Skip Duplicates)",
                      variable=self.smart_skip_var)
        self.switch_skip.pack(pady=6, padx=20, anchor="w")

        # Filename Template
        ctk.CTkLabel(self.right_frame, text="Filename Template:").pack(pady=(10, 0), padx=20, anchor="w")
        self.naming_var = ctk.StringVar(value=self.settings.get("naming_template", "Title Only"))
        self.naming_dropdown = ctk.CTkOptionMenu(self.right_frame, variable=self.naming_var,
            values=["Title Only", "Uploader - Title", "Numbered (01 Song)", "Custom..."],
            command=self.update_ui_state)
        self.naming_dropdown.pack(pady=3, padx=20, fill="x")

        self.custom_naming_entry = ctk.CTkEntry(self.right_frame,
                                                placeholder_text="e.g. %(uploader)s - %(title)s")
        self.custom_naming_entry.insert(0, self.settings.get("custom_template", "%(title)s"))
        self.custom_naming_entry.pack(pady=3, padx=20, fill="x")

        # Speed Limit
        ctk.CTkLabel(self.right_frame, text="Speed Limit (e.g. 5M, 500K):").pack(pady=(10, 0), padx=20, anchor="w")
        self.speed_entry = ctk.CTkEntry(self.right_frame, placeholder_text="Leave blank for unlimited")
        self.speed_entry.pack(pady=3, padx=20, fill="x")

        # Output Folder
        self.folder_button = ctk.CTkButton(self.right_frame, text="Choose Output Folder",
                                           fg_color="transparent", border_width=2,
                                           text_color=("gray10", "#DCE4EE"),
                                           command=self.choose_folder)
        self.folder_button.pack(pady=(10, 3), padx=20, fill="x")
        self.folder_label = ctk.CTkLabel(self.right_frame,
                                         text=f".../{os.path.basename(self.output_dir)}",
                                         text_color="gray")
        self.folder_label.pack(pady=0, padx=20)

        # ---- BOTTOM: Action & Progress ----
        self.bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bottom_frame.pack(pady=8, padx=20, fill="x")

        self.status_label = ctk.CTkLabel(self.bottom_frame, text="Ready.", text_color="gray")
        self.status_label.pack(pady=(0, 2))

        self.progress_bar = ctk.CTkProgressBar(self.bottom_frame)
        self.progress_bar.pack(pady=(2, 8), fill="x")
        self.progress_bar.set(0)

        self.download_button = ctk.CTkButton(self.bottom_frame, text="START DOWNLOAD",
                                             height=50, font=ctk.CTkFont(size=16, weight="bold"),
                                             command=self.start_download_thread)
        self.download_button.pack(pady=5, fill="x")

    # =============================================
    # DRAG-AND-DROP HANDLER
    # =============================================
    def _on_drop(self, event):
        """Handle drag-and-drop data into the URL queue."""
        data = event.data.strip()
        # Strip curly braces that tkdnd sometimes wraps around paths/URLs
        if data.startswith('{') and data.endswith('}'):
            data = data[1:-1]
        # Ensure we start on a new line if there's existing text
        current = self.url_textbox.get("1.0", "end-1c")
        if current and not current.endswith('\n'):
            self.url_textbox.insert("end", "\n")
        self.url_textbox.insert("end", data)
        return event.action

    # =============================================
    # UI STATE MANAGEMENT
    # =============================================
    def update_ui_state(self, *args):
        is_video = self.media_var.get() == "video"
        # Audio vs Video controls
        self.format_dropdown.configure(state="disabled" if is_video else "normal")
        self.resolution_dropdown.configure(state="normal" if is_video else "disabled")
        self.resolution_label.configure(text_color=("white" if ctk.get_appearance_mode() == "Dark" else "black") if is_video else "gray40")

        if not is_video:
            fmt = self.format_var.get()
            self.quality_dropdown.configure(state="disabled" if "Lossless" in fmt else "normal")
        else:
            self.quality_dropdown.configure(state="disabled")

        # Custom naming entry
        is_custom = self.naming_var.get() == "Custom..."
        self.custom_naming_entry.configure(state="normal" if is_custom else "disabled")

    def apply_accent_color(self, fg_color, hover_color):
        """Apply the accent color to all interactive widgets across the app."""
        # Main action button & progress bar
        self.download_button.configure(fg_color=fg_color, hover_color=hover_color)
        self.progress_bar.configure(progress_color=fg_color)

        # Dropdowns
        for dropdown in [self.format_dropdown, self.quality_dropdown,
                         self.resolution_dropdown, self.naming_dropdown]:
            dropdown.configure(fg_color=fg_color, button_color=hover_color, button_hover_color=fg_color)

        # Switches
        for switch in [self.switch_art, self.switch_meta, self.switch_skip]:
            switch.configure(progress_color=fg_color, button_color=hover_color, button_hover_color=fg_color)

        # Radio buttons
        for radio in [self.radio_audio, self.radio_video]:
            radio.configure(fg_color=fg_color, hover_color=hover_color)

    def show_settings(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir)
        if folder:
            self.output_dir = folder
            self.folder_label.configure(text=f".../{os.path.basename(self.output_dir)}")

    # =============================================
    # DOWNLOAD ENGINE
    # =============================================
    def get_naming_template(self):
        """Return the yt-dlp outtmpl based on user's naming preference."""
        choice = self.naming_var.get()
        if choice == "Custom...":
            template = self.custom_naming_entry.get().strip()
            if not template:
                template = "%(title)s"
        else:
            template = NAMING_TEMPLATES.get(choice, "%(title)s")
        return os.path.join(self.output_dir, template + ".%(ext)s")

    def build_ydl_opts(self):
        import sys
        opts = {
            'outtmpl': self.get_naming_template(),
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'retries': 3,
            'fragment_retries': 3,
            'progress_hooks': [self.yt_dlp_hook],
            'allow_playlist_files': False,
        }

        # Smart Skip
        if self.smart_skip_var.get():
            opts['download_archive'] = HISTORY_FILE

        # FFmpeg location for PyInstaller builds
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
                pass

        postprocessors = []
        media = self.media_var.get()
        embed_art = self.album_art_var.get()
        auto_meta = self.metadata_var.get()

        if media == "video":
            res = self.resolution_var.get()
            res_map = {"4K (2160p)": 2160, "1440p": 1440, "1080p": 1080, "720p": 720, "480p": 480}
            if res in res_map:
                h = res_map[res]
                opts['format'] = f'bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/best[height<={h}][ext=mp4]/best[height<={h}]'
            else:
                opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            # Metadata MUST come before thumbnail embedding to prevent stripping
            if auto_meta:
                opts['parse_metadata'] = ['title:%(artist)s - %(title)s']
                postprocessors.append({'key': 'FFmpegMetadata'})
            if embed_art:
                opts['writethumbnail'] = True
                postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})
                postprocessors.append({'key': 'EmbedThumbnail'})
        else:
            opts['format'] = 'bestaudio/best'
            fmt_str = self.format_var.get()
            codec_map = {"M4A (AAC)": "m4a", "MP3": "mp3", "OPUS": "opus", "FLAC (Lossless)": "flac", "WAV (Lossless)": "wav"}
            codec = codec_map.get(fmt_str, "m4a")
            extract_pp = {'key': 'FFmpegExtractAudio', 'preferredcodec': codec}
            if "Lossless" not in fmt_str:
                q_str = self.quality_var.get()
                if q_str != "Original Stream":
                    extract_pp['preferredquality'] = q_str
            postprocessors.append(extract_pp)
            # Metadata MUST come before thumbnail embedding to prevent stripping
            if auto_meta:
                opts['parse_metadata'] = ['title:%(artist)s - %(title)s']
                postprocessors.append({'key': 'FFmpegMetadata'})
            if embed_art:
                opts['writethumbnail'] = True
                postprocessors.append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})
                postprocessors.append({'key': 'EmbedThumbnail'})

        if postprocessors:
            opts['postprocessors'] = postprocessors

        return opts

    def yt_dlp_hook(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)

            filename = os.path.basename(d.get('filename', 'Unknown File'))
            if len(filename) > 35:
                filename = filename[:32] + "..."

            percent = downloaded / total if total > 0 else 0

            speed = d.get('_speed_str', '').strip()
            eta = d.get('_eta_str', '').strip()

            info = d.get('info_dict', {})
            pl_index = info.get('playlist_index') or info.get('playlist_autonumber')
            n_entries = info.get('n_entries') or info.get('playlist_count')

            prefix = f"[{pl_index}/{n_entries}] " if pl_index and n_entries else ""
            # Prepend batch job info if available
            if hasattr(self, '_batch_prefix') and self._batch_prefix:
                prefix = self._batch_prefix + prefix

            status = f"{prefix}{filename}"
            details = []
            if speed and speed != 'Unknown':
                details.append(speed)
            if eta and eta != 'Unknown':
                details.append(f"ETA: {eta}")
            if details:
                status += f"  |  {' · '.join(details)}"

            self.after(0, self.update_progress, percent, status)

        elif d['status'] == 'finished':
            info = d.get('info_dict', {})
            pl_index = info.get('playlist_index') or info.get('playlist_autonumber')
            n_entries = info.get('n_entries') or info.get('playlist_count')
            prefix = f"[{pl_index}/{n_entries}] " if pl_index and n_entries else ""
            if hasattr(self, '_batch_prefix') and self._batch_prefix:
                prefix = self._batch_prefix + prefix
            self.after(0, self.update_progress, 1.0, f"{prefix}Converting & Embedding Metadata...")

        elif d['status'] == 'error':
            self.after(0, self.update_progress, 0.0, "Error occurred during download.")

    def update_progress(self, percent, text):
        self.progress_bar.set(percent)
        self.status_label.configure(text=text)

    def _snapshot_images(self):
        """Snapshot all image files currently in the output folder."""
        existing = set()
        for ext in ('*.jpg', '*.webp', '*.png'):
            for f in glob.glob(os.path.join(self.output_dir, ext)):
                existing.add(f)
        return existing

    def cleanup_stray_thumbnails(self, pre_existing):
        """Remove only NEW thumbnail files that yt-dlp created during download."""
        for ext in ('*.jpg', '*.webp', '*.png'):
            for f in glob.glob(os.path.join(self.output_dir, ext)):
                if f not in pre_existing:
                    try:
                        os.remove(f)
                    except OSError:
                        pass

    def download_thread(self, urls):
        """Process a list of URLs sequentially (batch queue)."""
        opts = self.build_ydl_opts()

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        total_jobs = len(urls)
        for i, url in enumerate(urls, 1):
            self._batch_prefix = f"[Job {i}/{total_jobs}] " if total_jobs > 1 else ""
            self.after(0, self.update_progress, 0.0,
                       f"{self._batch_prefix}Starting... → {self.output_dir}")
            try:
                pre_existing = self._snapshot_images()
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                self.cleanup_stray_thumbnails(pre_existing)
            except Exception as e:
                self.after(0, self.update_progress, 0.0,
                           f"{self._batch_prefix}Failed: {str(e)}")

        self._batch_prefix = ""
        self.after(0, self.finish_download,
                   f"✓ All {total_jobs} job(s) complete! Saved to: {self.output_dir}", "green")

    def start_download_thread(self):
        raw_text = self.url_textbox.get("1.0", "end").strip()
        urls = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not urls:
            self.status_label.configure(text="Paste at least one URL above.", text_color="red")
            return

        self.download_button.configure(state="disabled", text="DOWNLOADING...")
        self.progress_bar.set(0)
        self.status_label.configure(text="Initializing...")

        thread = threading.Thread(target=self.download_thread, args=(urls,))
        thread.daemon = True
        thread.start()

    def finish_download(self, message, color):
        self.download_button.configure(state="normal", text="START DOWNLOAD")
        self.status_label.configure(text=message, text_color=color)
        self.save_settings()

    # =============================================
    # UPDATE CHECKER
    # =============================================
    def open_releases(self):
        webbrowser.open(RELEASES_PAGE)

    def check_for_updates(self):
        try:
            headers = {'User-Agent': 'YT-Media-Downloader-App'}
            req = urllib.request.Request(REPO_URL, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_tag = data.get("tag_name", "").replace("v", "")
                if latest_tag and version.parse(latest_tag) > version.parse(VERSION):
                    self.latest_version = latest_tag
                    self.after(0, self.show_update_notification)
        except Exception as e:
            print(f"Update check failed: {e}")

    def show_update_notification(self):
        self.update_button.configure(text=f"🚀 Update to v{self.latest_version} Available!")
        self.update_button.pack(pady=(5, 5), before=self.url_label)


if __name__ == "__main__":
    app = App()
    app.mainloop()
