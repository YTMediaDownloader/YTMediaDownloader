import yt_dlp
import sys
import os
import glob
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.console import Console

console = Console()

# ============================================================
#                   YT Media Downloader
# ============================================================

DEFAULT_URL = "https://www.youtube.com/playlist?list=PLNyPiL5e4F2bo2ruSM_ivlbH5xrXMSF7f"

AUDIO_FORMATS = {
    "1": {"name": "M4A (AAC)",       "codec": "m4a",  "lossy": True,  "qualities": ["64", "128", "192", "256"]},
    "2": {"name": "MP3",             "codec": "mp3",  "lossy": True,  "qualities": ["128", "192", "256", "320"]},
    "3": {"name": "OPUS",            "codec": "opus", "lossy": True,  "qualities": ["64", "128", "160", "192", "256"]},
    "4": {"name": "FLAC (Lossless)", "codec": "flac", "lossy": False, "qualities": []},
    "5": {"name": "WAV (Lossless)",  "codec": "wav",  "lossy": False, "qualities": []},
}

def build_ydl_options(output_dir, media_type, audio_format_key=None, quality=None, embed_thumbnail=False, speed_limit=None, auto_metadata=False):
    ydl_opts = {
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'ignoreerrors': True,
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        'retries': 3,
        'fragment_retries': 3,
        'allow_playlist_files': False,
    }

    if speed_limit:
        ydl_opts['ratelimit'] = speed_limit

    postprocessors = []

    if media_type == "video":
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        if embed_thumbnail:
            ydl_opts['writethumbnail'] = True
            postprocessors.append({'key': 'EmbedThumbnail'})
    else:
        ydl_opts['format'] = 'bestaudio/best'
        fmt = AUDIO_FORMATS.get(audio_format_key, AUDIO_FORMATS["1"])

        extract_audio_pp = {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': fmt["codec"],
        }
        if fmt["lossy"] and quality:
            extract_audio_pp['preferredquality'] = quality

        postprocessors.append(extract_audio_pp)

        if embed_thumbnail:
            ydl_opts['writethumbnail'] = True
            postprocessors.append({'key': 'EmbedThumbnail'})

    if auto_metadata:
        ydl_opts['parse_metadata'] = ['title:%(artist)s - %(title)s']
        postprocessors.append({'key': 'FFmpegMetadata'})

    if postprocessors:
        ydl_opts['postprocessors'] = postprocessors

    return ydl_opts

def download_media(url, ydl_opts):
    console.print(f"\n[bold green]Starting Download[/bold green]")
    console.print(f"Target URL: [blue]{url}[/blue]")
    console.print(f"Destination: [blue]{os.path.abspath(ydl_opts['outtmpl'].rsplit(os.sep, 1)[0])}[/blue]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        transient=False,
    ) as progress:
        task_id = progress.add_task("Initializing...", total=None)

        def my_hook(d):
            if d['status'] == 'downloading':
                filename = os.path.basename(d.get('filename', 'Unknown'))
                if len(filename) > 35:
                    filename = filename[:32] + "..."
                
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                
                progress.update(task_id, description=filename, completed=downloaded, total=total if total > 0 else None)
            elif d['status'] == 'finished':
                progress.update(task_id, description="Processing / Converting...", total=100, completed=100)
            elif d['status'] == 'error':
                progress.update(task_id, description="[red]Error downloading file.[/red]")

        ydl_opts['progress_hooks'] = [my_hook]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([url])
                console.print("\n[bold green]Download Process Completed![/bold green]")
            except Exception as e:
                console.print(f"\n[bold red]A fatal error occurred: {e}[/bold red]")

def prompt_url():
    console.print("\n[bold]--- Step 1: URL ---[/bold]")
    url = input(f"Enter Playlist/Video URL (Press Enter for default playlist):\n> ").strip()
    if not url:
        url = DEFAULT_URL
        console.print("   [dim]Using default playlist.[/dim]")
    return url

def prompt_media_type():
    console.print("\n[bold]--- Step 2: Media Type ---[/bold]")
    print("1 - Audio Only")
    print("2 - Video (MP4)")
    choice = input("> ").strip()
    if choice == "2":
        return "video"
    return "audio"

def prompt_audio_format():
    console.print("\n[bold]--- Step 3: Audio Format ---[/bold]")
    for key, fmt in AUDIO_FORMATS.items():
        print(f"{key} - {fmt['name']}")
    choice = input("> ").strip()
    if choice not in AUDIO_FORMATS:
        console.print("   [dim]Invalid choice. Defaulting to M4A.[/dim]")
        choice = "1"
    fmt = AUDIO_FORMATS[choice]
    console.print(f"   [dim]Selected: {fmt['name']}[/dim]")
    return choice

def prompt_quality(audio_format_key):
    fmt = AUDIO_FORMATS[audio_format_key]
    if not fmt["lossy"]:
        console.print(f"\n[bold]--- Step 4: Quality ---[/bold]")
        console.print(f"   [dim]{fmt['name']} is lossless. Quality selection is not applicable.[/dim]")
        return None

    console.print(f"\n[bold]--- Step 4: Quality ---[/bold]")
    print(f"Available bitrates for {fmt['name']}:")
    for i, q in enumerate(fmt["qualities"]):
        print(f"  {i + 1} - {q} kbps")
    print(f"  Press Enter for original stream quality (recommended)")
    choice = input("> ").strip()

    if not choice:
        console.print("   [dim]Using original stream quality.[/dim]")
        return None

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(fmt["qualities"]):
            selected = fmt["qualities"][idx]
            console.print(f"   [dim]Selected: {selected} kbps[/dim]")
            return selected
    except ValueError:
        pass

    console.print("   [dim]Invalid choice. Using original stream quality.[/dim]")
    return None

def prompt_thumbnail():
    console.print("\n[bold]--- Step 5: Album Art ---[/bold]")
    choice = input("Embed video thumbnail as album art? (Y/n): ").strip().lower()
    embed = choice != "n"
    console.print(f"   [dim]Album art: {'Enabled' if embed else 'Disabled'}[/dim]")
    return embed

def prompt_speed_limit():
    console.print("\n[bold]--- Step 6: Speed Limit ---[/bold]")
    limit = input("Enter max speed (e.g. '5M' for 5MB/s) or press Enter for unlimited:\n> ").strip().upper()
    if not limit:
        return None
    try:
        if limit.endswith('M'):
            val = int(float(limit[:-1]) * 1024 * 1024)
        elif limit.endswith('K'):
            val = int(float(limit[:-1]) * 1024)
        else:
            val = int(limit)
        console.print(f"   [dim]Speed limited to {limit}[/dim]")
        return val
    except ValueError:
        console.print("   [dim]Invalid format. Defaulting to unlimited.[/dim]")
        return None

def prompt_metadata():
    console.print("\n[bold]--- Step 7: Auto-Metadata ---[/bold]")
    choice = input("Enable Auto-Metadata Tagging (Artist/Title extraction)? (Y/n): ").strip().lower()
    auto_meta = choice != "n"
    console.print(f"   [dim]Metadata Tagging: {'Enabled' if auto_meta else 'Disabled'}[/dim]")
    return auto_meta

def prompt_output_dir():
    console.print("\n[bold]--- Step 8: Output Folder ---[/bold]")
    out_dir = input("Enter output folder name (Press Enter for 'downloads'):\n> ").strip()
    if not out_dir:
        out_dir = "downloads"
    console.print(f"   [dim]Saving to: {os.path.abspath(out_dir)}[/dim]")
    return out_dir

def print_summary(url, media_type, audio_format_key, quality, embed_thumb, speed_limit, auto_metadata, output_dir):
    console.print("\n[bold]=" * 50)
    console.print("          [magenta]DOWNLOAD SUMMARY[/magenta]")
    console.print("=" * 50 + "[/bold]")
    print(f"  URL:         {url[:60]}{'...' if len(url) > 60 else ''}")
    print(f"  Media Type:  {'Video (MP4)' if media_type == 'video' else 'Audio Only'}")
    if media_type == "audio":
        fmt = AUDIO_FORMATS.get(audio_format_key, AUDIO_FORMATS["1"])
        print(f"  Format:      {fmt['name']}")
        if quality:
            print(f"  Quality:     {quality} kbps")
        else:
            q_label = "Lossless" if not fmt["lossy"] else "Original Stream"
            print(f"  Quality:     {q_label}")
    print(f"  Album Art:   {'Yes' if embed_thumb else 'No'}")
    print(f"  Speed Limit: {'Unlimited' if not speed_limit else str(speed_limit) + ' bytes/s'}")
    print(f"  Auto-Meta:   {'Yes' if auto_metadata else 'No'}")
    print(f"  Output:      {os.path.abspath(output_dir)}")
    console.print("[bold]=" * 50 + "[/bold]")

    confirm = input("\nProceed with download? (Y/n): ").strip().lower()
    return confirm != "n"

def run_interactive_menu():
    console.print("\n[bold cyan]========================================[/bold cyan]")
    console.print("[bold cyan]    YT Media Downloader - Interactive   [/bold cyan]")
    console.print("[bold cyan]========================================[/bold cyan]")

    url = prompt_url()
    media_type = prompt_media_type()

    audio_format_key = None
    quality = None

    if media_type == "audio":
        audio_format_key = prompt_audio_format()
        quality = prompt_quality(audio_format_key)

    embed_thumb = prompt_thumbnail()
    speed_limit = prompt_speed_limit()
    auto_meta = prompt_metadata()
    output_dir = prompt_output_dir()

    if print_summary(url, media_type, audio_format_key, quality, embed_thumb, speed_limit, auto_meta, output_dir):
        ydl_opts = build_ydl_options(output_dir, media_type, audio_format_key, quality, embed_thumb, speed_limit, auto_meta)
        download_media(url, ydl_opts)
    else:
        console.print("[yellow]Download cancelled.[/yellow]")

def run_legacy_mode(url=None, out_dir="downloads"):
    console.print("\n[bold yellow]--- Running in Legacy Mode (Quick M4A) ---[/bold yellow]")
    if not url:
        url = DEFAULT_URL
    ydl_opts = build_ydl_options(out_dir, "audio", audio_format_key="1", quality=None, embed_thumbnail=False, speed_limit=None, auto_metadata=False)
    download_media(url, ydl_opts)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--legacy":
            run_legacy_mode()
        else:
            url = sys.argv[1]
            out_dir = sys.argv[2] if len(sys.argv) > 2 else "downloads"
            run_legacy_mode(url, out_dir)
    else:
        console.print("[bold cyan]========================================[/bold cyan]")
        console.print("[bold cyan]         YT Media Downloader            [/bold cyan]")
        console.print("[bold cyan]========================================[/bold cyan]")
        print("1. Interactive Menu (Full Settings)")
        print("2. Legacy Mode (Quick M4A Download)")
        choice = input("\nSelect an option (1 or 2) [Press Enter for 1]: ").strip()

        if choice == "2":
            run_legacy_mode()
        else:
            run_interactive_menu()
