import os
import re
import time
import requests
import base64
import undetected_chromedriver as uc
from urllib.parse import urlparse, parse_qs, urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# =================================== CONFIG ===================================
URL_FILE = "urls.txt"
OUTPUT_FOLDER = "Downloaded_videos"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Update this path to your Brave/Chrome executable
BRAVE_PATH = "C:/Users/tumom/AppData/Local/BraveSoftware/Brave-Browser/Application/brave.exe"

def create_driver():
    options = uc.ChromeOptions()
    if os.path.exists(BRAVE_PATH):
        options.binary_location = BRAVE_PATH
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return uc.Chrome(options=options)

def sanitize_filename(filename):
    """Remove characters that aren't allowed in filenames."""
    if not filename:
        return ""
    # Remove HTML/metadata leftovers and illegal Windows characters
    clean = re.sub(r'[\\/*?:"<>|]', "", filename).strip()
    # Remove site branding from the title
    clean = clean.replace("Real South African Sign Language", "").replace("- Real SASL", "").strip()
    # Remove trailing/leading dots or spaces
    clean = clean.strip(". ")
    return clean[:100] if clean else ""

def extract_video_id(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if "vid" in params:
        return params["vid"][0]
    if "id" in params:
        return params["id"][0]
    return None

def get_video_data(driver, url):
    """
    Navigates to the URL and extracts both the Title and the Video Source URL.
    """
    print(f"    Navigating to: {url}")
    driver.get(url)
    
    # Wait for the video element or a reasonable timeout
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )
    except:
        time.sleep(3)

    title = ""
    video_src = None

    # 1. Improved Title Extraction
    try:
        # Check for H1 (Standard video pages)
        h1_elements = driver.find_elements(By.TAG_NAME, "h1")
        if h1_elements:
            title = sanitize_filename(h1_elements[0].text.split('\n')[0])
        
        # If no H1, check document.title (Raw player pages)
        if not title:
            raw_title = driver.title
            # Often looks like "HELLO | Real South African Sign Language"
            title = sanitize_filename(raw_title.split('|')[0].split('-')[0].strip())
            
        # Last resort: look for any breadcrumb or specific class
        if not title:
            bread = driver.find_elements(By.CLASS_NAME, "breadcrumb-item")
            if bread:
                title = sanitize_filename(bread[-1].text)
    except:
        pass

    # 2. Extract Video Source
    try:
        sources = driver.find_elements(By.TAG_NAME, "source")
        for s in sources:
            src = s.get_attribute("src")
            if src and ".mp4" in src:
                video_src = src
                break
        
        if not video_src:
            videos = driver.find_elements(By.TAG_NAME, "video")
            for v in videos:
                src = v.get_attribute("src")
                if src and ".mp4" in src:
                    video_src = src
                    break
    except:
        pass

    # Regex fallback
    if not video_src:
        page_source = driver.page_source
        match = re.search(r'file["\s]*:["\s]*["\']([^"\']+\.mp4)["\']', page_source)
        if match:
            video_src = match.group(1)

    # Clean the video URL string
    if video_src:
        if video_src.startswith("//"):
            video_src = "https:" + video_src
        elif not video_src.startswith("http"):
            video_src = urljoin("https://www.realsasl.com", video_src)
            
        p = urlparse(video_src)
        clean_path = re.sub(r'/{2,}', '/', p.path)
        video_src = f"{p.scheme}://{p.netloc}{clean_path}"
        if p.query:
            video_src += f"?{p.query}"

    return title, video_src

def download_file_via_js(driver, video_url, filename):
    """
    Bypasses 403 by downloading the file using the browser's own fetch API.
    """
    print(f"    Initiating browser-side download for: {filename}")
    save_path = os.path.join(OUTPUT_FOLDER, filename)
    
    js_script = """
    var callback = arguments[arguments.length - 1];
    fetch(arguments[0])
        .then(response => {
            if (!response.ok) throw new Error('HTTP error, status = ' + response.status);
            return response.blob();
        })
        .then(blob => {
            var reader = new FileReader();
            reader.onloadend = function() {
                callback({success: true, data: reader.result.split(',')[1]});
            };
            reader.readAsDataURL(blob);
        })
        .catch(err => {
            callback({success: false, error: err.message});
        });
    """
    
    try:
        result = driver.execute_async_script(js_script, video_url)
        
        if result.get('success'):
            video_data = base64.b64decode(result['data'])
            with open(save_path, "wb") as f:
                f.write(video_data)
            print(f"    [✓] Successfully saved as: {filename}")
            return True
        else:
            print(f"    [✗] Browser Fetch Error: {result.get('error')}")
            return False
    except Exception as e:
        print(f"    [✗] Script execution failed: {e}")
        return False

# =================================== MAIN ===================================
if __name__ == "__main__":
    if not os.path.exists(URL_FILE):
        print(f"Error: {URL_FILE} not found.")
        exit()

    with open(URL_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        print("No URLs to process.")
        exit()

    driver = create_driver()
    driver.set_script_timeout(300)

    try:
        print("Starting session. PLEASE LOG IN if required.")
        driver.get("https://www.realsasl.com/index.php?option=com_users&view=login")
        
        input("\n>>> Please LOG IN manually in the browser, then press ENTER here to start...\n")

        for index, url in enumerate(urls, start=1):
            print(f"[{index}/{len(urls)}] Processing: {url}")
            
            try:
                vid_id = extract_video_id(url)
                title, video_url = get_video_data(driver, url)
                
                # Naming Priority: Website Title -> URL Parameter ID -> Index Fallback
                name_base = title if title else (vid_id if vid_id else f"video_{index}")
                final_filename = f"{name_base}.mp4"

                if not video_url:
                    print(f"    [✗] No video source found for {final_filename}.")
                    continue

                success = download_file_via_js(driver, video_url, final_filename)

            except Exception as e:
                print(f"    [✗] Error during processing: {e}")
            print("-" * 30)

    finally:
        try:
            driver.quit()
        except:
            pass
        print("\nAll tasks completed.")