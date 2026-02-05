import streamlit as st
import pandas as pd
import time
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="GMap Lead Scout", page_icon="📡", layout="wide")

# --- CUSTOM CSS FOR SLEEK UI ---
st.markdown("""
    <style>
    /* FIX: Mengurangi padding atas agar konten naik ke atas (Compact Mode) */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    
    /* Global Theme */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    
    /* Button Styling (Cyber Style) */
    .stButton>button {
        width: 100%;
        border-radius: 4px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        background-color: #238636; 
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }

    /* Expander Styling */
    .stExpander {
        border: 1px solid #30363D;
        border-radius: 6px;
        background-color: #161B22;
    }
    
    /* Dataframe Styling */
    .stDataFrame {
        border: 1px solid #30363D;
    }
    </style>
""", unsafe_allow_html=True)

# --- MAIN HEADER ---
st.title("📡 GMap Lead Scout // Pro Edition")
st.markdown("**Automated Business Intelligence & Contact Extraction Tool.** Harvest URLs securely, then extract detailed metadata.")
st.markdown("---") # Garis pemisah tipis

# --- SIDEBAR: MISSION CONTROL ---
with st.sidebar:
    st.header("⚙️ Mission Control")
    st.markdown("---")
    
    # Input Section
    kata_kunci = st.text_input("Target Query", value="Pabrik di Cikarang", help="Enter specific location or niche. E.g., 'Textile Factory in Bandung'")
    jumlah_target = st.slider("Extraction Limit", min_value=10, max_value=200, value=20, step=10, help="Maximum number of leads to extract.")
    
    st.markdown("### Advanced Parameters")
    mode_hantu = st.checkbox("Stealth Mode (Headless)", value=False, help="Run browser in background without UI rendering.")
    
    st.markdown("---")
    tombol_mulai = st.button("INITIATE SEQUENCE", type="primary")
    
    # Indikator status minimalis
    if mode_hantu:
        st.caption("🟢 System Status: **Stealth Mode Active**")
    else:
        st.caption("🔵 System Status: **GUI Mode Active**")

# --- CORE SCRAPER LOGIC ---
def run_scraper(keyword, limit, headless):
    data_hasil = []
    
    # Dashboard Layout (Lebih Rapi)
    col1, col2 = st.columns([3, 1])
    with col1:
        progress_bar = st.progress(0)
        status_text = st.empty()
    with col2:
        counter_text = st.empty()

    log_box = st.expander("System Logs (Live Stream)", expanded=True)
    
    def log(msg, type="info"):
        with log_box:
            timestamp = time.strftime("%H:%M:%S")
            if type == "info": st.markdown(f"`[{timestamp}] INFO` : {msg}")
            elif type == "success": st.success(f"[{timestamp}] SUCCESS : {msg}")
            elif type == "warning": st.warning(f"[{timestamp}] WARNING : {msg}")
            elif type == "error": st.error(f"[{timestamp}] ERROR : {msg}")

    # WebDriver Setup
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    if headless:
        options.add_argument("--headless=new")

    driver = None
    try:
        log("Initializing WebDriver kernel...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 20)
        
        # 1. Navigation phase
        driver.get("https://www.google.com/maps?hl=en") # Force English for consistency
        time.sleep(3)
        
        log(f"Acquiring target: **{keyword}**...")
        try:
            box = None
            try: box = driver.find_element(By.ID, "searchboxinput")
            except: pass
            
            if not box: box = driver.find_element(By.NAME, "q")
            
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

        # 2. Harvesting Phase
        log("Harvesting endpoints (Scrolling)...")
        time.sleep(3)
        
        scroll_div = None
        try:
            scroll_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
        except:
            time.sleep(3)
            try: scroll_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
            except: pass

        if not scroll_div:
            log("Feed container unavailable.", "error")
            return []

        count_found = 0
        max_scroll_attempts = 5 
        no_new_data = 0
        
        while count_found < limit:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_div)
            time.sleep(2.5)
            
            elements = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
            current_count = len(elements)
            
            status_text.markdown(f"**Phase 1/2: Harvesting Endpoints...**")
            counter_text.markdown(f"### `{current_count}/{limit}`")
            
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
        
        # --- STORAGE PHASE ---
        log("Indexing gathered URLs...", "info")
        elements = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
        list_urls = []
        for el in elements[:limit]:
            url = el.get_attribute("href")
            if url:
                list_urls.append(url)
        
        log(f"Index secured: {len(list_urls)} endpoints ready. Commencing direct extraction...", "success")
        
        # 3. Extraction Phase (Direct Visit)
        total_items = len(list_urls)
        
        for i, url in enumerate(list_urls):
            try:
                # Update Status
                progress_val = (i) / total_items
                progress_bar.progress(progress_val)
                status_text.markdown(f"**Phase 2/2: Extracting Intelligence...**")
                counter_text.markdown(f"### `{i+1}/{total_items}`")
                
                driver.get(url)
                
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                except:
                    time.sleep(2) 
                
                # --- DATA MINING ---
                # Name
                nama_bisnis = "N/A"
                try:
                    nama_bisnis = driver.find_element(By.TAG_NAME, "h1").text
                except: pass

                # Phone
                no_telp = "-"
                try:
                    btns = driver.find_elements(By.XPATH, '//button[contains(@data-item-id, "phone:tel:")]')
                    if btns:
                        txt = btns[0].get_attribute("aria-label") or ""
                        no_telp = txt.replace("Telepon: ", "").replace("Phone: ", "").strip()
                    else:
                        no_telp = "Not Available"
                except: pass

                # Website
                website = "-"
                try:
                    web_btns = driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
                    if web_btns:
                        website = web_btns[0].get_attribute("href")
                except: pass

                # Address
                alamat = "-"
                try:
                    addr_btns = driver.find_elements(By.XPATH, '//button[contains(@data-item-id, "address")]')
                    if addr_btns:
                        txt = addr_btns[0].get_attribute("aria-label") or ""
                        alamat = txt.replace("Alamat: ", "").replace("Address: ", "").strip()
                except: pass
                
                # Append to dataset
                data_hasil.append({
                    "Entity Name": nama_bisnis,
                    "Contact Number": no_telp,
                    "Website URL": website,
                    "Address": alamat,
                    "Search Query": keyword,
                    "Status": "Pending Review"
                })
                
            except Exception as e:
                log(f"Extraction failed for index {i+1}: {e}", "warning")
                continue

        progress_bar.progress(1.0)
        status_text.text("Operation Complete.")
        log("Sequence finished. Shutting down WebDriver.", "success")
        return data_hasil

    except Exception as e:
        log(f"Critical System Failure: {e}", "error")
        return []
    finally:
        if driver:
            driver.quit()

# --- EXECUTION LOGIC ---
if tombol_mulai:
    if not kata_kunci:
        st.warning("⚠️ Input Error: Target Query is required.")
    else:
        with st.spinner('Initializing GMap Scout Protocol...'):
            hasil_scraping = run_scraper(kata_kunci, jumlah_target, mode_hantu)
            
        if hasil_scraping:
            st.success(f"✅ Operation Successful. Extracted {len(hasil_scraping)} entities.")
            
            # Display Data
            st.subheader("Extracted Intelligence")
            df = pd.DataFrame(hasil_scraping)
            st.dataframe(df, use_container_width=True)
            
            # Export
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Leads')
                
            nama_file = f"Leads_{kata_kunci.replace(' ', '_')}.xlsx"
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.download_button(
                    label="📥 EXPORT DATASET (.XLSX)",
                    data=buffer.getvalue(),
                    file_name=nama_file,
                    mime="application/vnd.ms-excel",
                    type="primary"
                )
        else:
            st.error("❌ Operation Failed. No data retrieved. Verify connection or query parameters.")