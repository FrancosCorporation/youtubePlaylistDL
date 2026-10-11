#!/usr/bin/env python3

"""Baixa vídeos progressivos de uma playlist e gera um MP3 por vídeo."""

import argparse
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from pytubefix import Playlist, YouTube

NETWORK_TIMEOUT_SECONDS = 30
CONVERSION_TIMEOUT_SECONDS = 60 * 60
MAX_DOWNLOAD_RETRIES = 3
ALLOWED_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


class ProgressBar:
    def __init__(self, bar_length=25):
        self.bar_length = bar_length
        self.longest = 0
        self.started_at = None

    def print_progress(self, stream, _chunk, bytes_remaining):
        total = stream.filesize or stream.filesize_approx or 0
        if total <= 0:
            return

        now = time.perf_counter()
        if self.started_at is None:
            self.started_at = now

        downloaded = max(total - bytes_remaining, 0)
        elapsed = max(now - self.started_at, 0.001)
        rate = max(downloaded / elapsed, 0.001)
        fraction = min(downloaded / total, 1)
        filled = int(fraction * self.bar_length)
        bar = f"\r[{'=' * filled}>{' ' * (self.bar_length - filled)}] "
        bar += f"{fraction:.0%} {bytestostr(rate)}/s "
        bar += f"{getHumanTime((total - downloaded) / rate)} left"
        self.longest = max(self.longest, len(bar))
        sys.stdout.write(bar.ljust(self.longest))
        sys.stdout.flush()

    def print_end(self):
        if self.longest:
            sys.stdout.write(f"\r{' ' * self.longest}\r")
            sys.stdout.flush()


def getHumanTime(seconds):
    seconds = max(int(seconds), 0)
    if seconds >= 3600:
        return f"{seconds // 3600} hour(s)"
    if seconds >= 60:
        return f"{seconds // 60} minute(s)"
    return f"{seconds} second(s)"


def bytestostr(byte_count):
    value = float(byte_count)
    units = (("Tb", 1024**4), ("Gb", 1024**3), ("Mb", 1024**2), ("Kb", 1024))
    for unit, threshold in units:
        if value >= threshold:
            return f"{value / threshold:.2f}{unit}"
    return f"{value:.2f}b"


def normalize_youtube_url(url):
    value = url.strip()
    if not value:
        raise ValueError("Playlist URL is required.")
    if "://" not in value:
        value = f"https://{value}"

    parsed = urlsplit(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValueError("Playlist URL must use HTTP or HTTPS.")
    if host not in ALLOWED_YOUTUBE_HOSTS or parsed.username or parsed.password:
        raise ValueError("URL must point to a YouTube playlist.")
    if parsed.port is not None:
        raise ValueError("A custom port is not allowed in a YouTube URL.")

    netloc = "www.youtube.com" if host == "youtube.com" else host
    return urlunsplit(("https", netloc, parsed.path, parsed.query, parsed.fragment))


def getPlaylistUrlID(url):
    normalized_url = normalize_youtube_url(url)
    playlist_id = parse_qs(urlsplit(normalized_url).query).get("list", [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]+", playlist_id):
        raise ValueError("URL does not contain a valid YouTube playlist ID.")
    return playlist_id


def getFinalVideoUrl(video_urls):
    final_urls = []
    for video_url in video_urls:
        parsed = urlsplit(normalize_youtube_url(video_url))
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
            raise ValueError("Playlist contains an invalid video URL.")
        final_urls.append(
            urlunsplit(
                ("https", "www.youtube.com", "/watch", urlencode({"v": video_id}), "")
            )
        )
    return list(dict.fromkeys(final_urls))


def getPlaylistVideoUrls(url):
    playlist_id = getPlaylistUrlID(url)
    normalized_url = normalize_youtube_url(url)

    try:
        playlist = Playlist(normalized_url)
        if playlist.playlist_id != playlist_id:
            raise ValueError("Playlist ID does not match the submitted URL.")
        video_urls = getFinalVideoUrl(playlist.video_urls)
    except Exception as error:
        raise RuntimeError(f"Could not read the YouTube playlist: {error}") from error

    if not video_urls:
        raise RuntimeError("No videos were found in this playlist.")

    print(f"Found {len(video_urls)} videos in playlist.")
    for video_url in video_urls:
        print(video_url)
    return video_urls


def require_external_tools():
    missing = [name for name in ("ffmpeg", "lame") if shutil.which(name) is None]
    if missing:
        joined = " and ".join(missing)
        raise RuntimeError(
            f"Missing required program(s): {joined}. Install them and try again."
        )


def convert_to_mp3(video_path, audio_path):
    wav_path = audio_path.with_suffix(".wav")
    wav_path.unlink(missing_ok=True)
    audio_path.unlink(missing_ok=True)

    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-n",
            "-i",
            str(video_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            str(wav_path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=CONVERSION_TIMEOUT_SECONDS,
    )
    subprocess.run(
        ["lame", "--silent", str(wav_path), str(audio_path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=CONVERSION_TIMEOUT_SECONDS,
    )
    wav_path.unlink(missing_ok=True)


def download_Video_Audio(destination, video_url, file_number):
    query = urlsplit(normalize_youtube_url(video_url)).query
    video_id = parse_qs(query).get("v", [""])[0]
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        print(f"Failed to process {video_url}: invalid video ID.")
        return False

    base_name = f"{file_number:04d}-{video_id}"
    video_path = destination / f"{base_name}.mp4"
    audio_path = destination / f"{base_name}.mp3"

    try:
        if not video_path.is_file():
            progress = ProgressBar()
            youtube = YouTube(video_url, on_progress_callback=progress.print_progress)
            stream = (
                youtube.streams.filter(progressive=True, file_extension="mp4")
                .order_by("resolution")
                .desc()
                .first()
            )
            if stream is None:
                raise RuntimeError(
                    "No progressive MP4 stream is available for this video."
                )

            print(f"Downloading {youtube.title}...")
            try:
                downloaded_path = stream.download(
                    output_path=str(destination),
                    filename=video_path.name,
                    skip_existing=True,
                    timeout=NETWORK_TIMEOUT_SECONDS,
                    max_retries=MAX_DOWNLOAD_RETRIES,
                )
            finally:
                progress.print_end()

            if downloaded_path:
                video_path = Path(downloaded_path)
            if not video_path.is_file():
                raise RuntimeError("The video download did not create an MP4 file.")
            print(f"Saved {video_path.name}.")
        else:
            print(f"Using existing {video_path.name}.")

        if audio_path.is_file():
            print(f"Using existing {audio_path.name}.")
            return True

        convert_to_mp3(video_path, audio_path)
        print(f"Created {audio_path.name}.")
        return True
    except Exception as error:
        print(f"Failed to process {video_url}: {error}")
        return False


def build_argument_parser():
    parser = argparse.ArgumentParser(
        description="Download YouTube playlist videos and create MP3 audio files."
    )
    parser.add_argument("playlist_url", help="YouTube playlist URL")
    parser.add_argument(
        "destination",
        nargs="?",
        default=str(Path.cwd()),
        help="Output folder (default: current directory)",
    )
    return parser


def main(argv=None):
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)

    try:
        playlist_url = normalize_youtube_url(arguments.playlist_url)
        getPlaylistUrlID(playlist_url)
        destination = Path(arguments.destination).expanduser().resolve()
        destination.mkdir(parents=True, exist_ok=True)
        require_external_tools()
        socket.setdefaulttimeout(NETWORK_TIMEOUT_SECONDS)
        video_urls = getPlaylistVideoUrls(playlist_url)
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")

    failures = 0
    for index, video_url in enumerate(video_urls):
        if not download_Video_Audio(destination, video_url, index):
            failures += 1
        if index < len(video_urls) - 1:
            time.sleep(1)

    succeeded = len(video_urls) - failures
    print(f"Finished: {succeeded} succeeded, {failures} failed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
