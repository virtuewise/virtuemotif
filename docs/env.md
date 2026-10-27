# Environment Variables

This project relies on a few environment variables for optional features. Set them in your shell before running the scripts, or add them to a `.env` file and load it using `python-dotenv`.

| Variable | Description | Example |
|----------|-------------|---------|
| `PYTHONPATH` | Allows import of modules from the repository root when running scripts from subdirectories. | `PYTHONPATH=.` |
| `CUDA_VISIBLE_DEVICES` | Specifies which GPU(s) to use for torch‑based processing. Leave unset for CPU only. | `CUDA_VISIBLE_DEVICES=0` |
| `FFMPEG_PATH` | Path to a custom FFmpeg binary if not in `PATH`. | `FFMPEG_PATH=C:\ffmpeg\bin\ffmpeg.exe` |
| `RENDER_CONCURRENCY` | Number of concurrent workers for Remotion renders. Overrides the `--concurrency` flag. | `RENDER_CONCURRENCY=8` |
| `LOG_LEVEL` | Controls verbosity of the Python tools (`DEBUG`, `INFO`, `WARNING`, `ERROR`). | `LOG_LEVEL=INFO` |

You can export these in PowerShell, e.g.:
```powershell
$env:PYTHONPATH = '.'
$env:CUDA_VISIBLE_DEVICES = '0'
```

---

**Tip:** Keep a `.env.example` file in the repo root with the above variables commented out for newcomers.
