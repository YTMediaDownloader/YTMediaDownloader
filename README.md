# YT Media Downloader 🚀

A modern, standalone desktop application for downloading high-quality audio and video from YouTube. Built with a sleek dark-mode UI, multi-threading for flawless performance, and an open-source backbone that guarantees zero ads, zero trackers, and zero sketchy web conversions.

## ✨ Key Features

- **Pristine Audio Quality**: Directly extracts YouTube's native high-quality audio streams (AAC/Opus) without forcing destructive MP3 compression, ensuring you get the absolute best 1:1 audio quality possible.
- **Universal Support**: Paste a link to a single video, or paste a link to a massive 500-video playlist. The engine automatically detects it and handles the rest.
- **Lossless & Lossy Formats**: Choose between M4A, MP3, OPUS, FLAC, and WAV.
- **Auto-Metadata Tagging**: Automatically parses YouTube titles (e.g., `Artist - Song`) and embeds the Artist and Title perfectly into the file's ID3 metadata for flawless syncing to Spotify Local Files and Apple Music.
- **Album Art Embedding**: With a single toggle, the app will grab the high-resolution YouTube video thumbnail and permanently embed it as the track's official cover art.
- **Background Auto-Retry**: Built-in network resilience. If a fragment drops or YouTube temporarily throttles your connection, the app automatically waits and retries without failing the download.
- **Speed Limiter**: Built-in throttle control so you can download massive playlists in the background without lagging your games or streams.

## 🛠️ The Tech Stack

This app was built using the following open-source technologies:

- **`customtkinter`**: Powers the gorgeous, modern Windows 11-style dark mode GUI.
- **`yt-dlp`**: The gold-standard backend engine for extracting media from YouTube.
- **`ffmpeg`**: The heavy-lifting background processor used to cleanly convert audio streams and embed album artwork.
- **`mutagen`**: A specialized Python library used to safely inject metadata tags and album art into audio files without corrupting them.
- **`PyInstaller`**: Used to compile the entire project (and its 200MB of dependencies) into a single, portable `.exe` file that works on any PC out of the box.

## 🎮 How to Use It

1. **Launch the App**: Run `YT_Media_Downloader.exe`.
2. **Paste your Link**: Drop any YouTube URL (video or playlist) into the top bar.
3. **Select your Settings**:
   - Pick Audio or Video.
   - Choose your format (M4A is highly recommended for standard listening).
   - Toggle Album Art and Auto-Metadata on/off.
4. **Download**: Hit the massive `START DOWNLOAD` button and watch the progress bar do its thing. The app uses multi-threading, meaning the UI stays perfectly smooth while the engine churns in the background!

---

_Built transparently, locally, and safely._
