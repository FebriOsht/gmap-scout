import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import datetime # Tambahan untuk penamaan file unik jika error

# --- KONFIGURASI PENCARIAN ---
KATA_KUNCI = "Pabrik di Cikarang"
TARGET_JUMLAH_DATA = 20  # Ubah ke 100 jika ingin lebih banyak
NAMA_FILE_HASIL = "Data_Mentah_Andre.xlsx"

def jalankan_scraper():
    print("=== MEMULAI ROBOT SCRAPER (VERSI FINAL - ANTI GAGAL SIMPAN) ===")
    print("1. Membuka Browser Chrome...")

    # Setup Chrome Driver otomatis
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-blink-features=AutomationControlled") 
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20) 

    try:
        # 1. Buka Google Maps
        driver.get("https://www.google.com/maps")
        time.sleep(5)
        
        # 2. Cari Kotak Pencarian
        print(f"2. Mencari kotak pencarian untuk: '{KATA_KUNCI}'...")
        
        search_box = None
        try:
            search_box = driver.find_element(By.ID, "searchboxinput")
        except:
            pass

        if not search_box:
            try:
                search_box = driver.find_element(By.NAME, "q")
            except:
                pass

        if not search_box:
            try:
                search_box = driver.find_element(By.CSS_SELECTOR, "input#searchboxinput")
            except:
                pass
        
        if search_box:
            print("   -> Kotak pencarian ditemukan!")
            search_box.click()
            time.sleep(1)
            search_box.clear()
            search_box.send_keys(KATA_KUNCI)
            time.sleep(1)
            search_box.send_keys(Keys.ENTER)
        else:
            raise Exception("Gagal menemukan kotak pencarian.")

        print("   -> Berhasil mengetik. Menunggu hasil muncul...")

        # 3. Proses Scrolling
        try:
            scrollable_div = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]')))
        except:
            print("   -> Panel hasil standar belum muncul, menunggu sebentar...")
            time.sleep(5)
            scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')

        print("3. Sedang memuat daftar (Scrolling)...")
        
        items_found = 0
        consecutive_no_new_data = 0
        
        while items_found < TARGET_JUMLAH_DATA:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(3) 
            
            elements = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
            new_count = len(elements)
            
            print(f"   -> Data termuat: {new_count} dari target {TARGET_JUMLAH_DATA}")
            
            if new_count == items_found:
                consecutive_no_new_data += 1
                if consecutive_no_new_data >= 3:
                    print("   -> Tidak ada data baru setelah 3x scroll. Berhenti.")
                    break
            else:
                consecutive_no_new_data = 0
                
            items_found = new_count
            
            if items_found >= TARGET_JUMLAH_DATA:
                break

        # 4. Ekstraksi Data
        print("4. Mulai mengambil detail data...")
        
        hasil_data = []
        element_list = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")
        limit = min(len(element_list), TARGET_JUMLAH_DATA)
        
        for i in range(limit):
            item = element_list[i]
            try:
                # FIX UTAMA: Ambil nama dari list item langsung
                nama_pabrik = item.get_attribute("aria-label")
                if not nama_pabrik:
                    nama_pabrik = "Tanpa Nama"

                # Scroll dan Klik untuk detail
                driver.execute_script("arguments[0].scrollIntoView();", item)
                item.click()
                time.sleep(2) 

                # Ambil No Telp
                try:
                    phone_elements = driver.find_elements(By.XPATH, '//button[contains(@data-item-id, "phone:tel:")]')
                    if len(phone_elements) > 0:
                        no_telp = phone_elements[0].get_attribute("aria-label")
                        no_telp = no_telp.replace("Telepon: ", "").strip()
                    else:
                        no_telp = "Tidak Ada Nomor"
                except:
                    no_telp = "-"

                # Ambil Alamat
                try:
                    address_elements = driver.find_elements(By.XPATH, '//button[contains(@data-item-id, "address")]')
                    if len(address_elements) > 0:
                        alamat = address_elements[0].get_attribute("aria-label")
                        alamat = alamat.replace("Alamat: ", "").strip()
                    else:
                        alamat = "-"
                except:
                    alamat = "-"

                print(f"   [{i+1}] {nama_pabrik} | {no_telp}")

                hasil_data.append({
                    "Nama Pabrik": nama_pabrik,
                    "Nomor Telepon": no_telp,
                    "Alamat": alamat,
                    "Status Follow Up": "Belum"
                })

            except Exception as e:
                print(f"   [Skip item {i+1}]: {str(e)}")
                continue

        # 5. Simpan ke Excel (Dengan Penanganan Error jika File Terbuka)
        if len(hasil_data) > 0:
            print(f"5. Menyimpan {len(hasil_data)} data ke {NAMA_FILE_HASIL}...")
            df = pd.DataFrame(hasil_data)
            
            try:
                df.to_excel(NAMA_FILE_HASIL, index=False)
                print("=== SELESAI! Data siap ===")
            except PermissionError:
                # Jika file sedang dibuka, simpan dengan nama beda
                waktu_sekarang = datetime.datetime.now().strftime("%H%M%S")
                nama_baru = f"Data_Mentah_Andre_{waktu_sekarang}.xlsx"
                print(f"\n[PERINGATAN] File '{NAMA_FILE_HASIL}' sedang terbuka/dikunci.")
                print(f"-> Menyimpan ke file alternatif: {nama_baru}")
                df.to_excel(nama_baru, index=False)
                print(f"=== SELESAI! Data tersimpan di {nama_baru} ===")
                
        else:
            print("=== SELESAI TAPI KOSONG (Tidak ada data yang terambil) ===")

    except Exception as e:
        print(f"TERJADI ERROR UTAMA: {e}")
        driver.save_screenshot("error_screenshot.png")
        print("   -> Screenshot error disimpan.")
        
    finally:
        print("Menutup browser dalam 5 detik...")
        time.sleep(5)
        driver.quit()

if __name__ == "__main__":
    jalankan_scraper()