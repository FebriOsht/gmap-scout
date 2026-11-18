"""GMaps Scout core: the scraping logic shared by the Streamlit app (app_scraper.py) and the command line (cli.py)."""
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

COLUMNS = ["Entity Name", "Contact Number", "Email Address", "Website URL", "Address", "Search Query", "Status"]


def get_driver_service():
    """Linux/cloud: the system chromedriver (from packages.txt). Windows/macOS: ChromeDriverManager."""
    system_path = "/usr/bin/chromedriver"
    if os.path.exists(system_path):
        return Service(system_path)
    return Service(ChromeDriverManager().install())


def _noop(*args, **kwargs):
    pass


def _read_place(driver, keyword):
    nama_bisnis = "N/A"
    try:
        nama_bisnis = driver.find_element(By.TAG_NAME, "h1").text
    except Exception:
        pass

    no_telp = "-"
    try:
        btns = driver.find_elements(By.XPATH, '//button[contains(@data-item-id, "phone:tel:")]')
        if btns:
            txt = btns[0].get_attribute("aria-label") or ""
            no_telp = txt.replace("Telepon: ", "").replace("Phone: ", "").strip()
        else:
            no_telp = "Not Available"
    except Exception:
        pass

    website = "-"
    try:
        web_btns = driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
        if web_btns:
            website = web_btns[0].get_attribute("href")
    except Exception:
        pass

    email_addr = "-"
    try:
        email_btns = driver.find_elements(By.XPATH, '//button[contains(@data-item-id, "email")]')
        if email_btns:
            txt = email_btns[0].get_attribute("aria-label") or ""
            email_addr = txt.replace("Email: ", "").strip()
    except Exception:
        pass

    alamat = "-"
    try:
        addr_btns = driver.find_elements(By.XPATH, '//button[contains(@data-item-id, "address")]')
        if addr_btns:
            txt = addr_btns[0].get_attribute("aria-label") or ""
            alamat = txt.replace("Alamat: ", "").replace("Address: ", "").strip()
    except Exception:
        pass

    return {
        "Entity Name": nama_bisnis,
        "Contact Number": no_telp,
        "Email Address": email_addr,
        "Website URL": website,
        "Address": alamat,
        "Search Query": keyword,
        "Status": "Pending Review",
    }


def scrape(keyword, limit, headless=True, log=None, on_progress=None):
    """Search Google Maps for `keyword` and return up to `limit` rows with COLUMNS.
    Optional callbacks: log(msg, type) and on_progress(phase, current, total), phase = harvest | extract | done."""
    log = log or _noop
    on_progress = on_progress or _noop
    data = []

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Required on Streamlit Cloud / Docker
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    if headless:
        options.add_argument("--headless=new")

    driver = None
    try:
        log("Initializing WebDriver kernel...")
        driver = webdriver.Chrome(service=get_driver_service(), options=options)
        wait = WebDriverWait(driver, 20)

        # 1. Navigation
        driver.get("https://www.google.com/maps?hl=en")
        time.sleep(3)

        log(f"Acquiring target: **{keyword}**...")
        try:
            box = None
            try:
                box = driver.find_element(By.ID, "searchboxinput")
            except Exception:
                pass
            if not box:
                box = driver.find_element(By.NAME, "q")

            if box:
                box.clear()
                box.send_keys(keyword)
                time.sleep(1)
                box.send_keys(Keys.ENTER)
            else:
                log("Search interface not detected.", "error")
                return []
        except Exception as e:
            log(f"Search execution failed: {e}", "error")
            return []

        # 2. Collect place links (scrolling)
        log("Harvesting endpoints (Scrolling)...")
        time.sleep(3)

        scroll_div = None
        try:
            scroll_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
        except Exception:
            time.sleep(3)
            try:
                scroll_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            except Exception:
                pass

        if not scroll_div:
            log("Feed container unavailable.", "error")
            return []

        count_found = 0
        max_scroll_attempts = 5
        no_new_data = 0
        while count_found < limit:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_div)
            time.sleep(2.5)
            current_count = len(driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc"))
            on_progress("harvest", current_count, limit)
            if current_count == count_found:
                no_new_data += 1
                if no_new_data >= max_scroll_attempts:
                    log("End of list reached. Halting harvest.", "warning")
                    break
            else:
                no_new_data = 0
            count_found = current_count
            if count_found >= limit:
                break

        log("Indexing gathered URLs...", "info")
        list_urls = []
        for el in driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")[:limit]:
            url = el.get_attribute("href")
            if url:
                list_urls.append(url)
        log(f"Index secured: {len(list_urls)} endpoints ready. Commencing extraction...", "success")

        # 3. Read each place
        total = len(list_urls)
        for i, url in enumerate(list_urls):
            try:
                on_progress("extract", i + 1, total)
                driver.get(url)
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                except Exception:
                    time.sleep(2)
                data.append(_read_place(driver, keyword))
            except Exception as e:
                log(f"Extraction failed for index {i+1}: {e}", "warning")
                continue

        on_progress("done", total, total)
        log("Sequence finished.", "success")
        return data

    except Exception as e:
        log(f"Critical System Failure: {e}", "error")
        return []
    finally:
        if driver:
            driver.quit()
