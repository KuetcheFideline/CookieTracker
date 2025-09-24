def check_browser_installed(browser_name):
    """Vérifie si un navigateur est installé sur Windows"""
    browser_paths = {
        'firefox': [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Mozilla Firefox\firefox.exe")
        ],
        'chrome': [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ],
    }

    exe_names = {
        'firefox': 'firefox.exe',
        'chrome': 'chrome.exe',
    }

    browser_key = browser_name.lower()

    if browser_key not in browser_paths:
        print(f"✗ Navigateur {browser_name} non reconnu.")
        return False

    # Vérifie chemins classiques
    for path in browser_paths[browser_key]:
        if os.path.exists(path):
            print(f"✓ {browser_name} trouvé: {path}")
            return True

    # Vérifie dans le registre (HKCU + HKLM)
    reg_path = get_browser_path_from_registry(exe_names[browser_key])
    if reg_path:
        print(f"✓ {browser_name} trouvé via registre: {reg_path}")
        return True

    print(f"✗ {browser_name} non installé.")
    return False
