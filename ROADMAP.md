# 🗺️ Development Roadmap

This document tracks the features developed for the **YT Media Downloader** across all versions.

> **Status**: This project has reached **feature-complete** status as of v2.0. All planned features have been implemented and tested. Community-driven feature requests are still welcome via [GitHub Issues](https://github.com/YTMediaDownloader/YTMediaDownloader/issues).

---

### ✅ Completed Features

- [x] **Core Download Engine** (v1.0.0)
  High-quality audio/video extraction with format selection, bitrate control, and multi-threading.

- [x] **Album Art & Metadata Embedding** (v1.0.0)
  Automatic thumbnail-to-JPEG conversion and ID3 metadata tagging.

- [x] **Per-Video Playlist Thumbnails** (v1.0.1)
  Fixed playlist cover art overriding individual track thumbnails.

- [x] **Live Progress Stats** (v1.1.0)
  Real-time download speed, ETA, and playlist counter in the status bar.

- [x] **M4A Thumbnail Support** (v1.1.0)
  Resolved thumbnail embedding failures for M4A/AAC containers.

- [x] **In-App Update Notifications** (v1.2.0)
  Background version check against GitHub Releases with one-click redirect.

- [x] **Smart Skip Database** (v1.3.0)
  Local download archive that automatically skips previously downloaded videos.

- [x] **Video Resolution Selector** (v1.3.0)
  Granular control over video quality (4K, 1440p, 1080p, 720p, 480p).

- [x] **Batch Queue System** (v2.0.0)
  Multi-line URL input for sequential processing of multiple links.

- [x] **Custom Filename Templates** (v2.0.0)
  Preset and user-defined naming patterns using yt-dlp output tags.

- [x] **Personalization Suite** (v2.0.0)
  Settings window with Dark/Light/System themes, accent color presets, custom HEX input, and a native color picker.

- [x] **Persistent Settings** (v2.0.0)
  All user preferences saved to `config.json` and restored on startup.

- [x] **Drag & Drop URL Input** (v2.0.0)
  Direct browser-to-app URL queueing for faster playlist management.

---

### 💡 Community Ideas (Not Planned)

The following features are **not currently planned** but could be revisited based on community interest:

- [ ] **Spotify Playlist Support**
  Map Spotify playlist metadata to YouTube audio queries for seamless downloading.

- [ ] **Download History Viewer**
  A built-in UI to browse and manage the Smart Skip database.

---

*Have a feature idea? [Open an Issue](https://github.com/YTMediaDownloader/YTMediaDownloader/issues) on GitHub!*
