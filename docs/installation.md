# Installation Guide

## Prerequisites
- **Windows 10/11** (64‑bit)
- **Python 3.11** (recommended). Install from the official installer and ensure `python` is on your `PATH`.
- **Git** (optional, for cloning the repo).
- **Node.js 18+** (required for the Remotion video renderer).
- **FFmpeg** (for audio processing). Download the static build and add its `bin` folder to `PATH`.

## Setup Steps
1. **Clone the repository** (if you haven't already):
   ```powershell
   git clone https://github.com/your-user/lyrical-film.git
   cd lyrical-film
   ```
2. **Create a virtual environment** and activate it:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. **Install Python dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
4. **Install Node dependencies** for the Remotion front‑end:
   ```powershell
   cd film
   npm ci
   cd ..
   ```
5. **Verify the installation** by running a quick sanity check:
   ```powershell
   python -m tools.check_frames --help
   ```
   You should see the tool's usage output without errors.

## Optional GPU Acceleration
If you have an NVIDIA GPU and the appropriate CUDA toolkit installed, you can install `torch` with CUDA support:
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cu121
```
The rest of the pipeline will automatically use the GPU for any torch‑based processing.

---

**Next**: Follow the [Environment Variables guide](env.md) to configure any required settings.
