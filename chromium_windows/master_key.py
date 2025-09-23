import base64
from ctypes import *
from ctypes.wintypes import BYTE, DWORD, LPVOID
import re
import sys

# Load the Crypt32 library
crypt32 = windll.crypt32
kernel32 = windll.kernel32

class DATA_BLOB(Structure):
    _fields_ = [("cbData", DWORD), ("pbData", LPVOID)]  # Correctly define pbData as LPVOID.

# Regular expression to match valid Base64 characters
base64_pattern = re.compile(r'[^A-Za-z0-9+/=]')

def clean_base64_string(b64_string):
    return base64_pattern.sub('', b64_string)

import json
import base64
import ctypes
from ctypes import wintypes

def find_master_key(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
    encrypted_key = base64.b64decode(encrypted_key_b64)[5:]  # retire le préfixe DPAPI

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]
    blob_in = DATA_BLOB(len(encrypted_key), ctypes.cast(ctypes.create_string_buffer(encrypted_key), ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()
    crypt32 = ctypes.windll.crypt32
    if crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        pointer = ctypes.cast(blob_out.pbData, ctypes.POINTER(ctypes.c_char * blob_out.cbData))
        master_key = pointer.contents.raw
        ctypes.windll.kernel32.LocalFree(blob_out.pbData)
        return master_key
    else:
        raise Exception("Failed to decrypt master key")