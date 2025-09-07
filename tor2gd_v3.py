# ============================================================
# Advanced Async Torrent Downloader for Google Colab
# Features:
# ✅ Async + ThreadPoolExecutor
# ✅ Per-torrent speed limits
# ✅ Global download/upload throttle
# ✅ Auto Drive mount check
# ✅ Interactive single-cell run
# ✅ Clickable folder link
# Developed by RJ Sheesh + Assistant
# ============================================================

import asyncio
import libtorrent as lt
import time
from tqdm import tqdm
from colorama import Fore, Style, init as colorama_init
from IPython.display import display, HTML
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import os

colorama_init(autoreset=True)

# ---------------- Config ----------------
SAVE_PATH = Path("/content/drive/My Drive/Torrents")
MAX_CONCURRENT = 3           # concurrent torrents
POLL_INTERVAL = 1.0          # status update interval (seconds)
PER_TORRENT_DL_LIMIT = 200 * 1024   # bytes/sec (200 KB/s per torrent, 0 = unlimited)
PER_TORRENT_UL_LIMIT = 50 * 1024    # bytes/sec (50 KB/s per torrent, 0 = unlimited)
GLOBAL_DL_LIMIT = 0          # bytes/sec (0 = unlimited)
GLOBAL_UL_LIMIT = 0          # bytes/sec (0 = unlimited)
# ----------------------------------------

def check_drive_mount():
    from google.colab import drive
    if not Path('/content/drive').exists():
        print(Fore.YELLOW + "[*] Mounting Google Drive..." + Style.RESET_ALL)
        drive.mount('/content/drive')
    SAVE_PATH.mkdir(parents=True, exist_ok=True)
    print(Fore.GREEN + f"[✔] Torrents will be saved at: {SAVE_PATH}" + Style.RESET_ALL)

def start_session():
    ses = lt.session()
    ses.listen_on(6881, 6891)
    try:
        ses.start_dht()
    except Exception:
        pass
    # apply global rate limits
    ses.set_download_rate_limit(GLOBAL_DL_LIMIT)
    ses.set_upload_rate_limit(GLOBAL_UL_LIMIT)
    return ses

def add_torrent(ses, link_or_path, save_path):
    params = {
        'save_path': str(save_path),
        'storage_mode': lt.storage_mode_t.storage_mode_sparse
    }
    if link_or_path.startswith("magnet:"):
        handle = lt.add_magnet_uri(ses, link_or_path, params)
    else:
        info = lt.torrent_info(link_or_path)
        handle = ses.add_torrent({'ti': info, 'save_path': str(save_path)})
    # per-torrent rate limits
    if PER_TORRENT_DL_LIMIT:
        handle.set_download_limit(PER_TORRENT_DL_LIMIT)
    if PER_TORRENT_UL_LIMIT:
        handle.set_upload_limit(PER_TORRENT_UL_LIMIT)
    return handle

def format_eta(seconds):
    if not seconds or seconds == float('inf'):
        return "∞"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h: return f"{h}h {m}m {s}s"
    if m: return f"{m}m {s}s"
    return f"{s}s"

async def download_worker(handle, sem):
    async with sem:
        # wait for metadata
        while not handle.has_metadata():
            await asyncio.sleep(POLL_INTERVAL)
        info = handle.get_torrent_info()
        total = info.total_size()
        pbar = tqdm(total=total, unit="B", unit_scale=True, unit_divisor=1024,
                    desc=handle.name()[:40])
        last_done = 0
        while True:
            status = handle.status()
            done = status.total_done
            delta = done - last_done
            if delta > 0:
                pbar.update(delta)
                last_done = done

            down_kb = status.download_rate / 1024
            up_kb = status.upload_rate / 1024
            seeds = status.num_seeds
            peers = status.num_peers
            remaining = status.total_wanted - status.total_done
            eta = format_eta(remaining / status.download_rate) if status.download_rate > 0 else "∞"

            pbar.set_postfix({"Down": f"{down_kb:.1f} KB/s",
                              "Up": f"{up_kb:.1f} KB/s",
                              "Seeds": seeds,
                              "Peers": peers,
                              "ETA": eta})
            
            if status.is_seeding or (status.total_wanted == status.total_done and status.total_wanted>0):
                pbar.close()
                print(Fore.GREEN + f"[✔] {handle.name()} COMPLETED!" + Style.RESET_ALL)
                saved_location = SAVE_PATH / handle.name()
                if not saved_location.exists():
                    saved_location = SAVE_PATH
                print(Fore.YELLOW + f"📂 Saved at: {saved_location}" + Style.RESET_ALL)
                return str(saved_location)
            await asyncio.sleep(POLL_INTERVAL)

async def torrent_downloader_async(links):
    loop = asyncio.get_running_loop()
    executor = ThreadPoolExecutor(max_workers=min(8, MAX_CONCURRENT*2))
    ses = start_session()
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    # add torrents
    add_tasks = [loop.run_in_executor(executor, add_torrent, ses, l.strip(), SAVE_PATH)
                 for l in links if l.strip()]
    handles = await asyncio.gather(*add_tasks)

    # download tasks
    tasks = [asyncio.create_task(download_worker(h, sem)) for h in handles]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # clickable folder link
    display(HTML(f"""
        <h3 style="color:green;">✅ All tasks finished</h3>
        <p>📂 Open folder: <a href="file://{SAVE_PATH}" target="_blank">{SAVE_PATH}</a></p>
    """))
    executor.shutdown(wait=False)
    return results

def run_downloader():
    check_drive_mount()
    print(Fore.YELLOW + "Enter magnet links or .torrent paths (comma separated):" + Style.RESET_ALL)
    raw = input("➡️  ")
    links = [l.strip() for l in raw.split(",") if l.strip()]
    if not links:
        print("No links provided. Exiting.")
        return
    print(Fore.CYAN + f"Starting async download for {len(links)} torrent(s)..." + Style.RESET_ALL)
    asyncio.run(torrent_downloader_async(links))

# ---------------- Run Everything ----------------
run_downloader()
