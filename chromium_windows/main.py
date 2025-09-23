import json
import os
from chromium_windows.cookies_decrypter import get_cookies
from chromium_windows.dom_storage import get_dom_storage_data
from chromium_windows.personal_info_finder import search_personal_info
import uuid

from treatement.dom_treatment import search_personal_info_in_dict
from treatement.cookie_treatment import search_personal_info_robust

# Function to build paths based on browser
def get_paths(browser, username):
    base_paths = {
        "chrome": "Google/Chrome",
        "edge": "Microsoft/Edge",
        "brave": "BraveSoftware/Brave-Browser",
        "opera": "Opera Software/Opera Stable",  # Opera est dans AppData/Roaming
        "vivaldi": "Vivaldi",
        "yandex": "Yandex/YandexBrowser",
        "chromium": "Chromium",
    }

    if browser.lower() not in base_paths:
        return None, None, None  # cookies, local_state, dom_storage

    base = base_paths[browser.lower()]
    appdata = "Roaming" if "opera" in browser.lower() else "Local"

    base_dir = f"C:/Users/{username}/AppData/{appdata}/{base}/User Data/Default"

    cookies_path = os.path.join(base_dir, "Network/Cookies")
    local_state_path = f"C:/Users/{username}/AppData/{appdata}/{base}/User Data/Local State"
    dom_storage_path = os.path.join(base_dir, "Local Storage/leveldb")

    return cookies_path, local_state_path, dom_storage_path


def main_chromium(user_info, date, browser):
    # init()
    session_id = uuid.uuid4()

    # Get the current username
    username = os.getlogin()

    # Get paths based on the provided browser
    path_cookies, path_local_state, path_dom_storage = get_paths(browser, username)
    print(f'le chemin des cookies est : {path_cookies}')
    print(f'le chemin du local state est : {path_local_state}')
    print(f'le chemin du dom storage est : {path_dom_storage}')
    if not path_cookies or not path_local_state:
        print(f"Unsupported browser: {browser}")
        return

    # Check if the paths exist
    if not os.path.exists(path_cookies):
        print(f"Cookies file not found at {path_cookies}")
        return

    if not os.path.exists(path_local_state):
        print(f"Local State file not found at {path_local_state}")
        return
    if not os.path.exists(path_dom_storage):
        print(f"DOM Storage path not found at {path_dom_storage}")
        return  
    

    local_storage_data = get_dom_storage_data(path_dom_storage)



    # Add further code here to decrypt and process the cookies...
    json_filepath = get_cookies(
        session_id=session_id,
        browser_name=browser,
        path_local_state=path_local_state,
        path_cookies_db=path_cookies,
    )

    # The cookies_data should be the result of your previously generated cookies.json
    with open(json_filepath, "r") as f:
        cookies_data = json.load(f)
    
    with open(local_storage_data, "r") as f:
        dom_data = json.load(f) 

    # Search for personal info in the cookies
    cookies_stats= search_personal_info_robust(cookies_data, user_info)
    dom_stats = search_personal_info_in_dict(dom_data, user_info)

    return {browser: {"cookies": cookies_stats, "dom": dom_stats}}


