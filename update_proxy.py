import requests
import os
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_proxy(ip, port, api_url_template):
    api_url = api_url_template.format(ip=ip, port=port)
    try:
        response = requests.get(api_url, timeout=180)
        response.raise_for_status()
        data = response.json()

        status = data.get("status", "").strip().upper()

        if status == "ACTIVE ✅":
            print(f"{ip}:{port} is ALIVE")
            return f"{ip},{port}", None
        else:
            print(f"{ip}:{port} is DEAD")
            return None, f"{ip}:{port}"
    except requests.exceptions.RequestException as e:
        print(f"Error checking {ip}:{port}: {e}")
        return None, f"{ip}:{port}"

def main():
    input_file = os.getenv('IP_FILE', 'proxyip.txt')  # File input
    update_file = 'update_proxyip.txt'  # Proxy aktif
    error_file = 'error.txt'  # Proxy mati / error
    api_url_template = os.getenv('API_URL', 'https://api.bmkg.xyz/check?ip={ip}:{port}')

    alive_proxies = []
    error_proxies = []

    try:
        with open(input_file, "r") as f:
            reader = csv.reader(f)
            proxies = [row for row in reader if len(row) >= 2]
    except FileNotFoundError:
        print(f"File {input_file} tidak ditemukan.")
        return

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_proxy, row[0].strip(), row[1].strip(), api_url_template): row for row in proxies}

        for future in as_completed(futures):
            alive, error = future.result()
            if alive:
                alive_proxies.append(alive)
            if error:
                error_proxies.append(error)

    # Simpan proxy yang aktif
    with open(update_file, "w") as f:
        for proxy in alive_proxies:
            f.write(proxy + "\n")
        print(f"Proxy aktif disimpan di {update_file}.")

    # Simpan proxy yang error
    with open(error_file, "w") as f:
        for proxy in error_proxies:
            f.write(proxy + "\n")
        print(f"Proxy mati/error disimpan di {error_file}.")

if __name__ == "__main__":
    main()
