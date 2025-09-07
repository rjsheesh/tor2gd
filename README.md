# Google Colab Python 3.10 Auto Installer 🚀

Automatically installs Python 3.10 in Google Colab, sets up a custom folder for Torrents, and installs required Python packages.

## Features
- Auto installs Python 3.10 from source
- Installs required build dependencies
- Mounts Google Drive and creates a Torrents folder
- Installs Python packages: `libtorrent`, `tqdm`, `colorama`
- One-click setup in Colab

## Usage

1. Open Google Drive
2. Clone repo (optional) or copy `colab_py310_installer.py` cell
3. Run the script:
```python
from installer.colab_py310_installer import run_installer
run_installer()
