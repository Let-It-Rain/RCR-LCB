import os
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox
import requests
import time
import webbrowser


# ----- Токен с гитхаба чтоб не добавлять руками -----

CLIENT_ID = "Ov23libxwWDK2iVhx2Zg"
TOKEN_FILE = ".token_do_not_share"
SCOPE = "repo"

def get_github_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            token = f.read().strip()
            if token:
                return token

    resp = requests.post(
        "https://github.com/login/device/code",
        data={"client_id": CLIENT_ID, "scope": SCOPE},
        headers={"Accept": "application/json"}
    )
    resp.raise_for_status()
    data = resp.json()
    user_code = data["user_code"]
    verification_uri = data["verification_uri"]
    device_code = data["device_code"]
    expires_in = data["expires_in"]
    interval = data["interval"]

    webbrowser.open(verification_uri)
    
    messagebox.showinfo("Логин", f"Чтобы запушить релиз нужен токен.\nСайт попросит ввести код: {user_code}")
    

    token = None
    start_time = time.time()
    while time.time() - start_time < expires_in:
        time.sleep(interval)
        resp = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
            },
            headers={"Accept": "application/json"}
        )
        resp.raise_for_status()
        res = resp.json()
        if "access_token" in res:
            token = res["access_token"]
            break
        elif res.get("error") == "authorization_pending":
            continue
        else:
            raise Exception(res.get("error_description", "Unknown error"))

    if token:
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        return token
    else:
        raise Exception("Чето сломалось.")

token = get_github_token()

# ----- Запарсить нынешнюю версию -----

current_ver = "Ошибка =("
url = "https://api.github.com/repos/enqenqenqenqenq/RCR/releases/latest"
url2 ="https://api.github.com/repos/enqenqenqenqenq/RCR/releases"
url3 = "https://github.com/enqenqenqenqenq/RCR/releases/latest"

response = requests.get(url)

if response.status_code == 200:
        data = response.json()
        current_ver = data.get("tag_name")


# ----- Сам релиз -----
import os
import shutil
import subprocess
from tkinter import messagebox

# ----- Сам релиз -----
def build_archive():
    version = version_entry.get().strip()
    description = description_entry.get().strip()

    if not version:
        messagebox.showerror("ЭЭЭЭ КУДААА", "Версию напиши")
        return

    src_localize = './localize'
    dst_rcr = './dist/RCR'
    dst = './dist/'
    submodule_path = './localize/StoryData'
    dst_storydata = os.path.join(dst_rcr, 'StoryData')

    archive_name = os.path.join(dst, f'v{version}')

    try:
        # Clean destination
        if os.path.exists(dst_rcr):
            shutil.rmtree(dst_rcr)

        # Ensure the submodule is initialized and updated
        subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'], check=True)

        # Copy main localize folder first, ignoring StoryData
        shutil.copytree(src_localize, dst_rcr, dirs_exist_ok=True, ignore=shutil.ignore_patterns('StoryData'))

        # Copy StoryData submodule into the destination
        if os.path.exists(dst_storydata):
            shutil.rmtree(dst_storydata)
        shutil.copytree(submodule_path, dst_storydata, dirs_exist_ok=True)

        # Make zip archive of the release
        shutil.make_archive(archive_name, 'zip', dst_rcr)

        # Push to GitHub
        push_to_github(version, description, f"{archive_name}.zip")

        messagebox.showinfo("Заебок", f"Релиз создан: {archive_name}")

    except Exception as e:
        messagebox.showerror("Ашыбка, кинь скрин", str(e))
        
# ----- Сразу пушит в гитхаб

def push_to_github(version, description, archive_path):
    headers = {"Authorization": f"token {token}"}
    data = {
        "tag_name": f"v{version}",
        "name": f"v{version}",
        "body": description,
        "draft": False,
        "prerelease": False
    }
    response = requests.post(url2, json=data, headers=headers)
    response.raise_for_status()
    release = response.json()
    upload_url = release["upload_url"].split("{")[0]


    archive_name = os.path.basename(archive_path)
    with open(archive_path, "rb") as f:
        headers.update({"Content-Type": "application/zip"})
        upload_response = requests.post(
            f"{upload_url}?name={archive_name}",
            headers=headers,
            data=f
        )
    upload_response.raise_for_status()
    webbrowser.open(url3)
    

# ----- GUI -----
root = tk.Tk()
root.title("Ура релиз")

tk.Label(root, text=f"Версия без v (Сейчас: {current_ver})").grid(row=0, column=0, padx=5, pady=5, sticky="e")
version_entry = tk.Entry(root)
version_entry.grid(row=1, column=0, padx=5, pady=5)

tk.Label(root, text="Ссылка на сообщение в дс с изменениями").grid(row=2, column=0, padx=5, pady=5, sticky="e")
description_entry = tk.Entry(root)
description_entry.grid(row=3, column=0, padx=5, pady=5)

build_btn = tk.Button(root, text="ЗАЕБАШИТЬ РЕЛИЗ", command=build_archive)
build_btn.grid(row=4, column=0, columnspan=2, pady=10)

root.mainloop()

