# SquishFile Distribution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable users to install SquishFile via `pip install squishfile` or by downloading a standalone `.exe` from GitHub Releases.

**Architecture:** A GitHub Actions workflow triggers on version tags (`v*`). It builds a Windows `.exe` with PyInstaller, publishes the Python package to PyPI, and creates a GitHub Release with the `.exe` attached.

**Tech Stack:** PyInstaller, GitHub Actions, twine, setuptools

---

### Task 1: Create PyInstaller Spec File

**Files:**
- Create: `squishfile.spec`

**Step 1: Create the PyInstaller spec file**

Create `squishfile.spec` in the repo root:

```python
# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Paths relative to spec file location
ROOT = os.path.abspath('.')

a = Analysis(
    ['squishfile/cli.py'],
    pathex=[ROOT],
    binaries=[],
    datas=[
        ('squishfile/frontend/dist', 'squishfile/frontend/dist'),
        ('squishfile/models', 'squishfile/models'),
    ],
    hiddenimports=[
        'squishfile',
        'squishfile.main',
        'squishfile.cli',
        'squishfile.detector',
        'squishfile.routes.upload',
        'squishfile.routes.compress',
        'squishfile.compressor.engine',
        'squishfile.compressor.image',
        'squishfile.compressor.pdf',
        'squishfile.compressor.video',
        'squishfile.compressor.audio',
        'squishfile.compressor.ffmpeg_utils',
        'squishfile.compressor.predictor',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'sklearn',
        'sklearn.tree',
        'sklearn.ensemble',
        'PIL',
        'fitz',
        'magic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SquishFile',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon=None,
)
```

**Step 2: Add PyInstaller to dev dependencies and `.gitignore` entries**

Add to `.gitignore`:
```
build/
dist/
*.spec.bak
```

**Step 3: Commit**

```bash
git add squishfile.spec .gitignore
git commit -m "feat: add PyInstaller spec for standalone exe build"
```

---

### Task 2: Create GitHub Actions Release Workflow

**Files:**
- Create: `.github/workflows/release.yml`

**Step 1: Create the workflow directory**

```bash
mkdir -p .github/workflows
```

**Step 2: Create the release workflow**

Create `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  build-exe:
    name: Build Windows EXE
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Python dependencies
        run: |
          pip install -e .
          pip install pyinstaller

      - name: Build frontend
        working-directory: frontend
        run: |
          npm ci
          npm run build

      - name: Build EXE with PyInstaller
        run: pyinstaller squishfile.spec --noconfirm

      - name: Upload EXE artifact
        uses: actions/upload-artifact@v4
        with:
          name: SquishFile-windows
          path: dist/SquishFile.exe

  publish-pypi:
    name: Publish to PyPI
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Build frontend
        working-directory: frontend
        run: |
          npm ci
          npm run build

      - name: Build package
        run: |
          pip install build twine
          python -m build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*

  create-release:
    name: Create GitHub Release
    needs: build-exe
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Download EXE artifact
        uses: actions/download-artifact@v4
        with:
          name: SquishFile-windows
          path: ./release

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: ./release/SquishFile.exe
          generate_release_notes: true
```

**Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "ci: add release workflow for PyPI and GitHub Releases"
```

---

### Task 3: Update README with Installation Instructions

**Files:**
- Modify: `README.md`

**Step 1: Update the README**

Replace the current "Quick Start" and "Installation" sections with:

```markdown
## Installation

### Option A: pip install (Python users)

```bash
pip install squishfile
squishfile
```

### Option B: Download EXE (Windows)

1. Go to [Releases](https://github.com/WinnerWang971119/filecompresser/releases)
2. Download `SquishFile.exe`
3. Double-click to run — opens your browser automatically
```

Keep the rest of the README (Architecture, API Reference, Development Setup, etc.) as-is.

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README with pip and exe install instructions"
```

---

### Task 4: Verify PyInstaller Build Locally (Manual)

**Step 1: Install PyInstaller**

```bash
pip install pyinstaller
```

**Step 2: Build the frontend**

```bash
cd frontend && npm run build && cd ..
```

**Step 3: Run PyInstaller**

```bash
pyinstaller squishfile.spec --noconfirm
```

**Step 4: Verify the EXE exists**

```bash
ls dist/SquishFile.exe
```

Expected: File exists at `dist/SquishFile.exe`

**Step 5: Test the EXE runs**

```bash
dist/SquishFile.exe
```

Expected: Browser opens, app is functional at `http://127.0.0.1:800x`

---

### Task 5: Set Up PyPI Token (Manual - Diego)

This is a manual step for Diego:

1. Go to https://pypi.org/manage/account/token/
2. Create an API token scoped to the `squishfile` project (or all projects for first upload)
3. In your GitHub repo, go to Settings → Secrets → Actions
4. Add secret `PYPI_API_TOKEN` with the token value

---

### Task 6: Tag and Release

**Step 1: Update version in `pyproject.toml`**

Ensure `version` in `pyproject.toml` matches the tag you're about to create.

**Step 2: Create and push a tag**

```bash
git tag v0.1.0
git push origin v0.1.0
```

**Step 3: Verify the workflow**

Go to GitHub → Actions tab → verify the "Release" workflow runs successfully:
- EXE is built and uploaded
- Package is published to PyPI
- GitHub Release is created with `.exe` attached
