# make_video.py

## Purpose
Main orchestration CLI to render end-to-end visual-lyric videos driven by song configuration files and the visual effects registry.

## Prerequisites
- Song configuration file under `songs/<song_id>.yaml`
- Base default configuration under `config/defaults.yaml`
- Audio file referenced in the song config
- `ffmpeg` installed and available in PATH

## Usage
```bash
python -m tools.make_video <song_id>
```

## Arguments
- `song_id`: The ID of the song corresponding to `songs/<song_id>.yaml`

## Pipeline Flow
1. Load configuration: Merges `config/defaults.yaml` with `songs/<song_id>.yaml`.
2. Audio Chunking: Reads audio into frame-sized audio chunks matching target FPS.
3. Frame Rendering: Iterates over audio chunks and passes them through registered `VisualEffect` plugins (e.g. `WaveformEffect`).
4. Video Encoding: Encodes output frames into an MP4 file with AAC audio muxed via `ffmpeg`.

## Output
- `out/<song_id>/frame_*.png`: Individual rendered frames.
- `out/<song_id>.mp4`: Final encoded video.
