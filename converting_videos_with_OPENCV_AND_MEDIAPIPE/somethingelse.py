import time
import json
import re
import asyncio
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

BRAVE_PATH = "C:/Users/tumom/AppData/Local/BraveSoftware/Brave-Browser/Application/brave.exe"
WEBSITE_URL = "https://learnsasl.com/"

def create_driver():
    options = uc.ChromeOptions()
    options.binary_location = BRAVE_PATH
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--remote-debugging-port=9222")
    return uc.Chrome(options=options)

# =================================== MAIN ===================================
if __name__ == "__main__":
    driver = create_driver()
    
    # Enable CDP network tracking
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd("Network.setRequestInterception", {
        "patterns": [{"urlPattern": "*"}]
    })

    # Store all intercepted data
    intercepted = []

    # Listen to WebSocket frames via CDP
    driver.execute_cdp_cmd("Network.enable", {})

    print("Loading website...")
    driver.get(WEBSITE_URL)
    time.sleep(3)

    # Click letter A to trigger data load
    print("Clicking letter A to trigger Firebase query...")
    try:
        driver.execute_script("""
            // Try to find and click the A button
            let elements = document.querySelectorAll('flt-semantics');
            for(let el of elements) {
                if(el.getAttribute('aria-label') === 'A') {
                    el.click();
                    break;
                }
            }
        """)
    except:
        pass
    
    time.sleep(5)

    # Get all network logs via CDP
    print("\nCapturing all network activity...")
    logs = driver.execute_script("""
        return window.performance.getEntriesByType('resource').map(r => ({
            name: r.name,
            type: r.initiatorType,
            duration: r.duration
        }));
    """)

    print("\n=== All Network Resources ===")
    for log in logs:
        print(f"  {log['type']:15} | {log['name']}")

    # Check page source for any embedded data
    print("\n=== Scanning Page for Vimeo IDs ===")
    source = driver.page_source
    vimeo_ids = re.findall(r'(?:vimeo\.com/(?:video/)?|vimeoId["\s:]+)(\d{7,12})', source)
    print(f"Found: {set(vimeo_ids)}")

    # Try accessing Firebase via JS directly in the browser context
    print("\n=== Trying Firebase JS SDK in browser ===")
    result = driver.execute_script("""
        try {
            // Check if Firebase is initialized
            if (typeof firebase !== 'undefined') {
                return 'Firebase found: ' + JSON.stringify(Object.keys(firebase));
            }
            // Check for Firestore
            if (window._firebase) return 'window._firebase found';
            return 'Firebase not found in window scope';
        } catch(e) {
            return 'Error: ' + e.message;
        }
    """)
    print(result)

    # Try to extract data from Flutter's internal state
    print("\n=== Flutter Internal State ===")
    result = driver.execute_script("""
        try {
            let keys = Object.keys(window);
            return keys.filter(k => 
                k.includes('flutter') || 
                k.includes('firebase') || 
                k.includes('firestore') ||
                k.includes('_')
            ).slice(0, 30);
        } catch(e) {
            return 'Error: ' + e.message;
        }
    """)
    print(result)

    input("\nPress Enter to quit...")
    driver.quit()