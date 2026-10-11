# youtubePlaylistDL

Download the videos in a YouTube playlist as progressive MP4 files and create
one MP3 audio file for each video. Downloads use numbered filenames so video
titles cannot break paths on Windows, macOS, or Linux.

## Requirements

- Python 3.10 or newer.
- FFmpeg and LAME available on `PATH`.
- The pinned Python dependency in `requirements.txt`.

Create and activate a virtual environment, then install the dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Install FFmpeg and LAME with your operating system's package manager. The
program checks for both before contacting YouTube and explains which one is
missing.

## Usage

```bash
python ytPlaylistDL.py 'https://www.youtube.com/playlist?list=PLAYLIST_ID'
python ytPlaylistDL.py 'https://www.youtube.com/playlist?list=PLAYLIST_ID' ~/Videos/my-playlist
```

If you omit the destination, files are written to the current directory. MP4
and MP3 files are named with the playlist order and video ID, for example
`0000-AbCdEfGh123.mp4`; this avoids unsafe titles and collisions between
playlists. Existing files are reused; incomplete audio conversion can be
retried by running the command again.

The script uses the playlist parser and stream downloader from
[`pytubefix`](https://github.com/JuanBindez/pytubefix), requests YouTube over
HTTPS, and applies a 30-second network timeout with up to three stream retries.
It downloads the highest available progressive MP4 stream, which contains both
video and audio.

## Usage and permissions

Download only content you are authorized to save. YouTube's terms restrict
downloading and other uses of content unless the service expressly allows it,
you have the required permission, or applicable law permits it. Review the
[YouTube Terms of Service](https://www.youtube.com/t/terms) before using this
tool.

## Static checks

```bash
python -m pip install -r requirements-dev.txt
python -m py_compile ytPlaylistDL.py
ruff check ytPlaylistDL.py
```

The CI workflow runs these checks. Automated tests are not included yet.
