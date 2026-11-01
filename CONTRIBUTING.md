# Contributing to VirtueMotif

Thank you for helping improve VirtueMotif, an audio-reactive lyric-video and motion-typography pipeline. This guide describes the expected workflow for changes to the Python pipeline and the Remotion application.

## Before you start

- Check existing issues and pull requests to avoid duplicating work.
- For substantial changes, open an issue first to agree on the approach.
- Keep changes focused and explain the problem they solve.
- Never commit API keys, credentials, private media, personal data, or generated output containing material you do not have permission to share.
- For suspected security vulnerabilities, follow [SECURITY.md](SECURITY.md). Do not report vulnerabilities in public issues or pull requests.

## Development setup

### Python pipeline

Use Python 3.11 and install the development dependencies:

```bash
python -m venv .venv
# Activate the environment for your platform, then:
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

The pipeline and CI use FFmpeg/ffprobe for media processing. Install FFmpeg for your operating system and verify that both commands are available.

### Remotion application

Use Node.js 24 (the same major version as CI) and npm. From the repository root, install the locked dependencies:

```bash
cd film
node --version
npm ci
```

The Node version check in CI deliberately fails if the runtime is not Node.js 24, so local and CI environments stay aligned.

## Validate your changes

Run the checks relevant to your changes before opening a pull request.

### Python

From the repository root:

```bash
python -m pytest -q
python -m compileall -q tools tests
ruff check tools/make_video.py tools/make_tapsync.py tools/utils.py tools/effects tests/test_ci_smoke.py
```

If you change documentation-generation inputs, validate the maintained API docs too:

```bash
python -m pdoc -o site tools.make_video tools.make_tapsync tools.utils tools.effects
```

### Remotion / TypeScript

From the `film/` directory:

```bash
node --version
npm ci
npx tsc --noEmit
npx remotion browser ensure
npx remotion compositions src/index.ts
```

CI runs Python quality checks and Remotion validation for pull requests targeting `main`. Do not commit generated build artifacts unless a change specifically requires them.

## Code and content expectations

- Prefer small, readable changes that fit the existing architecture and naming conventions.
- Add or update tests when behavior changes or a bug is fixed.
- Keep configuration and defaults explicit; document new options and expected values.
- Preserve reproducibility where practical. Avoid introducing network calls or environment-specific absolute paths into routine pipeline execution.
- Handle missing files, invalid configuration, and subprocess failures with actionable error messages.
- For visual effects, consider frame boundaries, image dimensions, alpha/transparency, color behavior, and deterministic output.
- For lyric, audio, font, image, and video assets, ensure you have the necessary rights to use and redistribute them. Do not add copyrighted material unless its inclusion is authorized and compatible with the repository's license.

## Pull request checklist

A good pull request should:

1. Explain the problem and why the proposed change is appropriate.
2. Summarize user-visible behavior changes and note any trade-offs.
3. Link related issues where applicable.
4. Include tests or explain why testing is not practical.
5. Include screenshots or appropriately licensed sample output for visual changes when useful.
6. Update relevant documentation and configuration examples.
7. Confirm that secrets, private data, and unrelated generated files are not included.

Keep pull requests focused and use a descriptive title, such as `Fix tap-sync path resolution` or `Add waveform-reactive transition`.

## Review and release

Maintainers may request changes or clarification before merging. Keep discussion constructive and respond to review feedback with follow-up commits. Merging does not guarantee an immediate release; release timing is determined by the maintainers.
