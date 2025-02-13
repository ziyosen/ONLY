import requests
import os
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_proxy(ip, port, api_url_template):
    """ Mengecek status proxy melalui API """
    api_url = api_url_template.format(ip=ip, port=port)
    try:
        print(f"Checking: {ip}:{port} -> {api_url}")  # Debugging URL API
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"Response JSON: {data}")  # Debugging respons API

        # Cek apakah proxy dianggap aktif
        if str(data.get("proxyip", "")).strip().lower() == "true":
            print(f"{ip}:{port} is ALIVE")
            return f"{ip},{port}\n", None
        else:
            print(f"{ip}:{port} is DEAD")
            return None, None
    except requests.exceptions.RequestException as e:
        error_msg = f"{ip}:{port} - {e}"
        print(error_msg)
        return None, error_msg
    except ValueError as ve:
        error_msg = f"{ip}:{port} - JSON Error: {ve}"
        print(error_msg)
        return None, error_msg

def main():
    input_file = os.getenv('IP_FILE', 'proxyip.txt')
    update_file = 'update_proxyip.txt'
    error_file = 'error.txt'
    api_url_template = os.getenv('API_URL', 'https://api.bmkg.xyz/check?ip={ip}:{port}')

    if not os.path.exists(input_file):
        print(f"File {input_file} tidak ditemukan.")
        return

    # Membaca proxy dari file
    with open(input_file, "r") as f:
        rows = [line.strip().split(",") for line in f if line.strip()]

    if not rows:
        print(f"Tidak ada proxy yang ditemukan di {input_file}.")
        return

    print(f"Total proxies found: {len(rows)}")

    alive_proxies = []
    error_logs = []

    # Mengecek proxy secara paralel
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_proxy, row[0], row[1], api_url_template): row for row in rows if len(row) >= 2}

        for future in as_completed(futures):
            alive, error = future.result()
            if alive:
                alive_proxies.append(alive)
            if error:
                error_logs.append(error)

    # Menyimpan proxy aktif ke file
    with open(update_file, "w") as f:
        f.writelines(alive_proxies)

    if alive_proxies:
        print(f"Proxy yang ALIVE disimpan ke {update_file}.")
    else:
        print(f"Tidak ada proxy yang aktif.")

    # Menyimpan log error jika ada
    if error_logs:
        with open(error_file, "w") as f:
            f.writelines("\n".join(error_logs) + "\n")
        print(f"Error dicatat di {error_file}.")

if __name__ == "__main__":
    main()
