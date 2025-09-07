# ============================================================
# ⚡ One-Click Colab Torrent Downloader (Multithreaded)
# Developed by RJ Sheesh 😎
# ============================================================

import libtorrent as lt
import time
from tqdm import tqdm
from colorama import Fore, Style
from IPython.display import HTML, display
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# --- Step 1: Setup Torrent Session ---
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

# --- Step 2: Download Worker (per torrent) ---
def download_worker(handle, pbar):
    while not handle.has_metadata():
        time.sleep(1)

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
    return handle.name()

# --- Step 3: Main Downloader Function ---
def torrent_downloader():
    ses = start_session()
    save_path = "/content/drive/My Drive/Torrents"
    os.makedirs(save_path, exist_ok=True)

    print(Fore.YELLOW + "\n[+] Enter Magnet Links or Torrent File Paths (comma separated)" + Style.RESET_ALL)
    links = input("➡️  ").split(",")

    handles = []
    for link in links:
        link = link.strip()
        if not link:
            continue
        print(Fore.CYAN + f"[*] Adding torrent: {link}" + Style.RESET_ALL)
        handle = add_torrent(ses, link, save_path)
        handles.append(handle)

    # Create progress bars for all torrents
    progress_bars = {
        handle: tqdm(
            total=handle.get_torrent_info().total_size(),
            unit="B", unit_scale=True, unit_divisor=1024,
            desc=handle.name()[:25]
        ) for handle in handles
    }

    # --- Step 4: Use ThreadPoolExecutor ---
    completed = []
    with ThreadPoolExecutor(max_workers=min(5, len(handles))) as executor:
        futures = [executor.submit(download_worker, handle, progress_bars[handle]) for handle in handles]
        for future in as_completed(futures):
            name = future.result()
            print(Fore.GREEN + f"\n[✔] {name} COMPLETED!" + Style.RESET_ALL)
            completed.append(name)

    # Final success message with clickable path
    display(HTML(f"""
        <h3 style="color:green;">✅ All torrents downloaded successfully!</h3>
        <p>📂 Saved at: <a href="file://{save_path}" target="_blank" style="color:blue;">{save_path}</a></p>
    """))

# --- Step 5: Run Downloader ---
torrent_downloader()
