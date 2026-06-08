import streamlit as st
import pandas as pd
import time
import io
import os
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="GMap Lead Scout Pro", page_icon="📡", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS (MODERN UI / SILICON VALLEY STYLE) ---
st.markdown("""
    <style>
    /* Global Theme */
    .stApp {
        background-color: #0b0f19; /* Deep modern dark blue/gray */
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Layout Spacing */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.7) !important;
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Primary Button Styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 0.75rem 0;
        box-shadow: 0 4px 14px 0 rgba(59, 130, 246, 0.39);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.5);
        transform: translateY(-2px);
    }

    /* Input Fields */
    .stTextInput input, .stNumberInput input {
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background-color: rgba(30, 41, 59, 0.5);
        color: white;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 1px #3b82f6;
    }

    /* Expander (Log Box) */
    .stExpander {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        background-color: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(8px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }
    .stExpander summary {
        font-weight: 600;
        color: #94a3b8;
        padding: 0.5rem;
    }

    /* Dataframe Container */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    
    /* Metrics / Status Badges */
    .metric-box {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        backdrop-filter: blur(4px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Progress Bar custom accent */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #3b82f6, #8b5cf6);
    }
    </style>
""", unsafe_allow_html=True)

# --- MODERN HEADER DESIGN ---
st.markdown("""
    <div style="background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%); padding: 2.5rem 2rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 2.5rem; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);">
        <h1 style="margin: 0; padding: 0; font-size: 2.8rem; font-weight: 800; background: -webkit-linear-gradient(45deg, #60a5fa, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">📡 GMap Lead Scout</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; color: #94a3b8; font-weight: 400;">Automated Business Intelligence & Contact Extraction Tool <span style="background: rgba(59,130,246,0.2); color: #60a5fa; padding: 2px 8px; border-radius: 12px; font-size: 0.8rem; margin-left: 8px;">Cloud-Ready</span></p>
    </div>
""", unsafe_allow_html=True)


# --- SIDEBAR COMPONENT ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/854/854878.png", width=60) # Placeholder icon
    st.markdown("### ⚙️ Mission Control")
    st.markdown("---")
    
    kata_kunci = st.text_input("📍 Target Query", value="Pabrik di Cikarang", help="Enter specific location or niche (e.g. 'Coffee shop in Bali').")
    jumlah_target = st.slider("📊 Extraction Limit", min_value=10, max_value=200, value=20, step=10)
    
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🛠️ Advanced Parameters", expanded=False):
        # Di Cloud, Mode Hantu WAJIB aktif. Kita kunci saja jika terdeteksi Linux.
        is_cloud = os.name == 'posix' # Deteksi Linux
        default_headless = True if is_cloud else False
        mode_hantu = st.checkbox("Stealth Mode (Headless)", value=default_headless, help="Run browser invisibly in background.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    tombol_mulai = st.button("🚀 INITIATE SEQUENCE", type="primary")
    
    st.markdown("---")
    if is_cloud:
        st.info("☁️ **Cloud Environment Detected**\n\nOptimized for server execution.", icon="ℹ️")
    else:
        st.success("💻 **Local Machine Detected**\n\nUI mode is available.", icon="✅")

# --- SMART DRIVER SETUP ---
def get_driver_service():
    """
    Fungsi pintar untuk memilih Driver.
    - Jika di Cloud (Linux): Pakai /usr/bin/chromedriver (dari packages.txt)
    - Jika di Lokal (Windows): Pakai ChromeDriverManager
    """
    # Cek path driver sistem (biasanya di Linux/Streamlit Cloud)
    system_path = "/usr/bin/chromedriver"
    if os.path.exists(system_path):
        return Service(system_path)
    
    # Fallback untuk Windows/Mac (Local)
    return Service(ChromeDriverManager().install())

# --- CORE SCRAPER LOGIC ---
def run_scraper(keyword, limit, headless):
    data_hasil = []
    
    # Modern Layout Status Indicators
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("#### Operational Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
    with col2:
        counter_container = st.empty()

    log_box = st.expander("💻 System Logs (Live Stream)", expanded=True)
    
    def log(msg, type="info"):
        with log_box:
            timestamp = time.strftime("%H:%M:%S")
            if type == "info": st.markdown(f"<span style='color:#94a3b8;'>`[{timestamp}]`</span> **INFO** : {msg}", unsafe_allow_html=True)
            elif type == "success": st.markdown(f"<span style='color:#4ade80;'>`[{timestamp}]`</span> **SUCCESS** : {msg}", unsafe_allow_html=True)
            elif type == "warning": st.markdown(f"<span style='color:#fbbf24;'>`[{timestamp}]`</span> **WARNING** : {msg}", unsafe_allow_html=True)
            elif type == "error": st.markdown(f"<span style='color:#f87171;'>`[{timestamp}]`</span> **ERROR** : {msg}", unsafe_allow_html=True)

    def update_counter(current, maximum):
        counter_container.markdown(f"""
            <div class="metric-box">
                <div style="font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">Entities</div>
                <div class="metric-value">{current} <span style="font-size: 1.2rem; color: #64748b;">/ {maximum}</span></div>
            </div>
        """, unsafe_allow_html=True)

    # WebDriver Options (Critical for Cloud)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # WAJIB UNTUK STREAMLIT CLOUD / DOCKER
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    if headless:
        options.add_argument("--headless=new")

    driver = None
    try:
        log("Initializing WebDriver kernel...")
        
        # PANGGIL FUNGSI SMART DRIVER
        service = get_driver_service()
        driver = webdriver.Chrome(service=service, options=options)
        
        wait = WebDriverWait(driver, 20)
        
        # 1. Navigation
        driver.get("https://www.google.com/maps?hl=en")
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

        # 2. Harvesting
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
            
            status_text.markdown(f"**⏳ Phase 1/2: Harvesting Endpoints from Maps...**")
            update_counter(current_count, limit)
            
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
        
        log(f"Index secured: {len(list_urls)} endpoints ready. Commencing extraction...", "success")
        
        # 3. Extraction
        total_items = len(list_urls)
        
        for i, url in enumerate(list_urls):
            try:
                progress_val = (i) / total_items
                progress_bar.progress(progress_val)
                status_text.markdown(f"**🔍 Phase 2/2: Extracting Intelligence ( {i+1} / {total_items} )**")
                update_counter(i+1, total_items)
                
                driver.get(url)
                try:
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
                except:
                    time.sleep(2) 
                
                # Data Mining
                nama_bisnis = "N/A"
                try: nama_bisnis = driver.find_element(By.TAG_NAME, "h1").text
                except: pass

                no_telp = "-"
                try:
                    btns = driver.find_elements(By.XPATH, '//button[contains(@data-item-id, "phone:tel:")]')
                    if btns:
                        txt = btns[0].get_attribute("aria-label") or ""
                        no_telp = txt.replace("Telepon: ", "").replace("Phone: ", "").strip()
                    else:
                        no_telp = "Not Available"
                except: pass

                website = "-"
                try:
                    web_btns = driver.find_elements(By.CSS_SELECTOR, 'a[data-item-id="authority"]')
                    if web_btns: website = web_btns[0].get_attribute("href")
                except: pass
                
                # --- FITUR BARU: EMAIL SCRAPING ---
                email_addr = "-"
                try:
                    # Mencari tombol/elemen yang mengandung data email
                    email_btns = driver.find_elements(By.XPATH, '//button[contains(@data-item-id, "email")]')
                    if email_btns:
                        txt = email_btns[0].get_attribute("aria-label") or ""
                        email_addr = txt.replace("Email: ", "").strip()
                except: pass

                alamat = "-"
                try:
                    addr_btns = driver.find_elements(By.XPATH, '//button[contains(@data-item-id, "address")]')
                    if addr_btns:
                        txt = addr_btns[0].get_attribute("aria-label") or ""
                        alamat = txt.replace("Alamat: ", "").replace("Address: ", "").strip()
                except: pass
                
                data_hasil.append({
                    "Entity Name": nama_bisnis,
                    "Contact Number": no_telp,
                    "Email Address": email_addr, 
                    "Website URL": website,
                    "Address": alamat,
                    "Search Query": keyword,
                    "Status": "Pending Review"
                })
                
            except Exception as e:
                log(f"Extraction failed for index {i+1}: {e}", "warning")
                continue

        progress_bar.progress(1.0)
        status_text.markdown("**✅ Operation Complete.**")
        update_counter(total_items, total_items)
        log("Sequence finished.", "success")
        return data_hasil

    except Exception as e:
        log(f"Critical System Failure: {e}", "error")
        return []
    finally:
        if driver:
            driver.quit()

# --- EXECUTION ---
if tombol_mulai:
    if not kata_kunci:
        st.error("⚠️ Input Error: Target Query is required.")
    else:
        # PENTING: Jika di Cloud, PAKSA HEADLESS meskipun user lupa centang
        force_headless = True if is_cloud else mode_hantu
        
        with st.spinner('Initializing GMap Scout Protocol...'):
            hasil_scraping = run_scraper(kata_kunci, jumlah_target, force_headless)
            
        if hasil_scraping:
            st.markdown("---")
            st.markdown(f"### 📂 Extracted Intelligence")
            st.caption(f"Successfully collected **{len(hasil_scraping)}** data points for query: `{kata_kunci}`")
            
            df = pd.DataFrame(hasil_scraping)
            
            # Reorder columns to put Email next to Phone
            cols = ["Entity Name", "Contact Number", "Email Address", "Website URL", "Address", "Search Query", "Status"]
            df = df[cols]
            
            # Display DataFrame
            st.dataframe(df, use_container_width=True, height=400)
            
            # Excel Generation
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Leads')
                
                # Auto-adjust column widths
                worksheet = writer.sheets['Leads']
                for i, col in enumerate(df.columns):
                    column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, column_len)
                
            nama_file = f"Leads_{kata_kunci.replace(' ', '_')}.xlsx"
            
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.download_button(
                    label="📥 DOWNLOAD DATASET (.XLSX)",
                    data=buffer.getvalue(),
                    file_name=nama_file,
                    mime="application/vnd.ms-excel",
                    type="primary"
                )
        else:
            st.error("❌ Operation Failed. No data retrieved or connection interrupted.")
