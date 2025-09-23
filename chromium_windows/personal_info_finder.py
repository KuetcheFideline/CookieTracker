import datetime
import json
import csv
import re 
import urllib.parse

def search_personal_info(user_info, cookies_data):
    data_regex= {}

    for key in user_info:
        value = user_info[key]
        if isinstance(value, list):
            data_regex[key] = []
            for v in value:
                data_regex[key].append(re.compile(rf'{re.escape(v)}', re.IGNORECASE))
        else:
            data_regex[key] = re.compile(rf'{re.escape(value)}', re.IGNORECASE)

    result = {}

    for host, cookies in cookies_data.items():
        host_info = {
            key: 0 for key in user_info.keys()
        }  # Initialize counts for each type of personal info

        for cookie in cookies:
            decrypted_value = cookie.get("decrypted_value", "")
            decoded_value = urllib.parse.unquote(
                decrypted_value
            )  # Decode URL-encoded values

            for key, regex_list in data_regex.items():

                if isinstance(regex_list, list):
                    for regex in regex_list:
                        match = regex.search(re.escape(urllib.parse.unquote(decrypted_value).lower()))
                        if match:
                         host_info[key] += 1
                         break
                else:
                     match = regex_list.search(re.escape(urllib.parse.unquote(decrypted_value).lower()))
                     if match:
                         host_info[key] += 1
                         break
        result[host] = host_info
  

    return result
