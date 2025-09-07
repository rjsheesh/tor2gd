# ============================================================
# One-Click Colab Torrent Downloader Setup 🚀 (Multithreaded)
# Developed by RJ Sheesh 😎 | Optimized by GPT-5
# ============================================================
# --- Mount Google Drive ---
from google.colab import drive
drive.mount('/content/drive')

import libtorrent as lt
import time
import datetime
from tqdm import tqdm
from colorama import Fore, Style
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# --- Setup Torrent Session ---
def start_session():
    ses = lt.session()
    ses.listen_on(6881, 6891)
    ses.start_dht()
    return ses

def add_torrent(ses, link_or_path, save_path):
    params = {
        'save_path': save_path,
        'storage_mode': lt.storage_mode_t.storage_mode_sparse
    }
    if link_or_path.startswith("magnet:"):
        handle = lt.add_magnet_uri(ses, link_or_path, params)
    else:
        info = lt.torrent_info(link_or_path)
        handle = ses.add_torrent({'ti': info, 'save_path': save_path})
    return handle

def format_eta(seconds):
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"

# --- Core Download Function ---
def download_single_torrent(ses, link, save_path):
    link = link.strip()
    if not link:
        return None

    print(Fore.CYAN + f"[*] Adding torrent: {link}" + Style.RESET_ALL)
    handle = add_torrent(ses, link, save_path)

    # Wait for metadata
    while not handle.has_metadata():
        time.sleep(1)

    print(Fore.GREEN + f"[+] Metadata fetched: {handle.name()}" + Style.RESET_ALL)

    # Setup progress bar
    total_size = handle.get_torrent_info().total_size()
    pbar = tqdm(
        total=total_size,
        unit="B", unit_scale=True, unit_divisor=1024,
        desc=handle.name()[:25]
    )

    # Download loop
    while not handle.status().is_seeding:
        status = handle.status()
        pbar.update(status.total_done - pbar.n)

        download_speed = status.download_rate / 1024
        upload_speed = status.upload_rate / 1024
        seeders = status.num_seeds
        peers = status.num_peers
        remaining = status.total_wanted - status.total_done
        eta = format_eta(remaining / status.download_rate) if status.download_rate > 0 else "∞"

        pbar.set_postfix({
            "Down": f"{download_speed:.1f} KB/s",
            "Up": f"{upload_speed:.1f} KB/s",
            "Seeds": seeders,
            "Peers": peers,
            "ETA": eta
        })
        time.sleep(1)

    pbar.close()
    print(Fore.GREEN + f"\n[✔] {handle.name()} COMPLETED!" + Style.RESET_ALL)
    print(Fore.YELLOW + f"📂 Saved at: {os.path.join(save_path, handle.name())}" + Style.RESET_ALL)

# --- Main Downloader ---
def torrent_downloader():
    ses = start_session()
    save_path = "/content/drive/My Drive/Torrents"

    print(Fore.YELLOW + "\n[+] Enter Magnet Links or Torrent File Paths (comma separated)" + Style.RESET_ALL)
    links = input("➡️  ").split(",")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(download_single_torrent, ses, link, save_path) for link in links]
        for future in as_completed(futures):
            future.result()

    print(Fore.MAGENTA + "\n[+] All torrents downloaded successfully!" + Style.RESET_ALL)
    print(Fore.YELLOW + f"📂 Saved at: {save_path}" + Style.RESET_ALL)

# --- Run Downloader ---
torrent_downloader()
