# ================================================
# 🚀 Google Colab Auto Installer for Python 3.10
# By RJ Sheesh
# ================================================

import os
from google.colab import drive

print("🔄 Step 1: Updating and installing dependencies...")
!apt update -y && apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget -y

print("🔄 Step 2: Mounting Google Drive...")
drive.mount('/content/drive')

# Create Torrents folder if not exists
TORRENTS_DIR = "/content/drive/MyDrive/Torrents"
if not os.path.exists(TORRENTS_DIR):
    print(f"📁 Creating folder: {TORRENTS_DIR}")
    os.makedirs(TORRENTS_DIR)
else:
    print(f"✅ Folder exists: {TORRENTS_DIR}")

# Change working directory
%cd $TORRENTS_DIR

PYTHON_TGZ = "Python-3.10.0.tgz"
PYTHON_SRC = os.path.join(TORRENTS_DIR, "Python-3.10.0")
PYTHON_URL = "https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz"

print("🔄 Step 3: Checking Python-3.10.0.tgz...")
if not os.path.exists(os.path.join(TORRENTS_DIR, PYTHON_TGZ)):
    print("⬇️ Downloading Python-3.10.0.tgz ...")
    !wget $PYTHON_URL -O $PYTHON_TGZ
else:
    print("✅ Python-3.10.0.tgz already exists, skipping download.")

# Extract Python source if not extracted already
if not os.path.exists(PYTHON_SRC):
    print("📦 Extracting Python-3.10.0...")
    !tar -xf $PYTHON_TGZ
else:
    print("✅ Python source folder already exists, skipping extraction.")

# Change directory to Python source
%cd $PYTHON_SRC

print("⚙️ Step 4: Configuring Python 3.10 build...")
!chmod +x configure
!./configure --enable-optimizations --with-ensurepip=install

print("🛠️ Step 5: Compiling Python 3.10 (this may take a while)...")
!make -j $(nproc)

print("📥 Step 6: Installing Python 3.10...")
!sudo make altinstall

print("📦 Step 7: Installing required Python packages...")
!python3.10 -m pip install --upgrade pip
!python3.10 -m pip install libtorrent tqdm colorama

print("✅ Step 8: Setup Completed Successfully!")
%cd $TORRENTS_DIR

