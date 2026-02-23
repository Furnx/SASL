import os
import re
import time
import requests
import yt_dlp
import undetected_chromedriver as uc
from urllib.parse import urlparse, parse_qs
from selenium.webdriver.common.by import By

# =================================== CONFIG ===================================
URL_FILE = "urls.txt"
OUTPUT_FOLDER = "Downloaded_videos"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

BRAVE_PATH = "C:/Users/tumom/AppData/Local/BraveSoftware/Brave-Browser/Application/brave.exe"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.realsasl.com/",
}

def create_driver():
    options = uc.ChromeOptions()
    options.binary_location = BRAVE_PATH
    options.add_argument("--no-sandbox")
    return uc.Chrome(options=options)

def extract_video_id(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if "vid" in params:
        return params["vid"][0]
    if "id" in params:
        return params["id"][0]
    return None

def is_direct_video(url):
    return urlparse(url).path.endswith(".mp4")

def is_vimeo(url):
    return "vimeo.com" in url

def download_vimeo(url, index):
    """Download Vimeo video using yt-dlp."""
    print(f"    Vimeo video detected — using yt-dlp")

    # First extract the title
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        full_title = info.get('title', f'video_{index}')
        # Get just the first word before "from"
        short_title = full_title.split(" from ")[0].strip()

    print(f"    Title: {short_title}")

    ydl_opts = {
        'outtmpl': f'{OUTPUT_FOLDER}/{short_title}.%(ext)s',
        'format': 'best',
        'quiet': False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print(f"[✓] Saved: {short_title}.mp4")

def download_direct(url, filename):
    """Download a direct .mp4 URL."""
    print(f"    Direct download...")
    response = requests.get(url, stream=True, headers=HEADERS, timeout=60)
    response.raise_for_status()
    save_path = os.path.join(OUTPUT_FOLDER, filename)
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"[✓] Saved: {filename}")

def get_video_url_via_browser(driver, video_id):
    """Navigate to realsasl player page and extract video URL."""
    player_url = f"https://www.realsasl.com/index.php?option=com_yendifvideoshare&view=player&id={video_id}&format=raw"
    print(f"    Opening player: {player_url}")
    driver.get(player_url)
    time.sleep(4)

    page_source = driver.page_source

    try:
        source = driver.find_element(By.TAG_NAME, "source")
        src = source.get_attribute("src")
        if src:
            return src
    except:
        pass

    try:
        video = driver.find_element(By.TAG_NAME, "video")
        src = video.get_attribute("src")
        if src:
            return src
    except:
        pass

    match = re.search(r'file["\s]*:["\s]*["\']([^"\']+\.mp4)["\']', page_source)
    if match:
        return match.group(1)

    print("    [DEBUG] Page snippet:")
    print(page_source[:1000])
    return None

def download_via_browser(driver, video_url, filename):
    cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
    response = requests.get(video_url, stream=True, headers=HEADERS, cookies=cookies, timeout=60)
    response.raise_for_status()
    save_path = os.path.join(OUTPUT_FOLDER, filename)
    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"[✓] Saved: {filename}")

# =================================== MAIN ===================================
if __name__ == "__main__":
    with open(URL_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Found {len(urls)} URLs to process...\n")

    driver = create_driver()
    print("Establishing session on realsasl.com...")
    driver.get("https://www.realsasl.com")
    time.sleep(3)
    print("[✓] Session established\n")

    for index, url in enumerate(urls, start=1):
        print(f"Processing: {url}")
        try:
            # Case 1: Vimeo URL
            if is_vimeo(url):
                download_vimeo(url, index)

            # Case 2: Direct .mp4 URL
            elif is_direct_video(url):
                filename = os.path.basename(urlparse(url).path) or f"video_{index}.mp4"
                download_direct(url, filename)

            # Case 3: realsasl player page
            else:
                video_id = extract_video_id(url)
                if not video_id:
                    print(f"[✗] Could not extract video ID from: {url}")
                    continue

                print(f"    Video ID: {video_id}")
                video_url = get_video_url_via_browser(driver, video_id)

                if video_url:
                    print(f"    Found URL: {video_url}")
                    download_via_browser(driver, video_url, f"video_{video_id}.mp4")
                else:
                    print(f"[✗] Could not find .mp4 for ID {video_id}")

        except Exception as e:
            print(f"[✗] Failed for {url}: {e}")

        print()

    driver.quit()
    print("All downloads completed.")