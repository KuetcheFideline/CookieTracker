from chrome.helpers import get_cookies, filters_cookies
from chrome.storage import read_storage ,transform ,third 
from treatement.cookie_treatment import search_personal_info_robust
from treatement.dom_treatment import search_personal_info_in_dict   
from colorama import Fore, Style, init


def main_linux(user,browser,date):
    
    statistiques = []

    try:
        for b in browser:
                print(Fore.GREEN + f"Processing Cookies for {b}" + Style.RESET_ALL)
                cookies = get_cookies(b,date)
                print(Fore.GREEN + f"Processing Dom for {b}" + Style.RESET_ALL)
                DomStorage = read_storage(b)



                print(Fore.GREEN + f"Processing Personal info for cookies {b}" + Style.RESET_ALL)
                stats= search_personal_info_robust(cookies,user)
                print(Fore.GREEN + f"Processing Personal info for dom {b}" + Style.RESET_ALL)
                
                dom =search_personal_info_in_dict(DomStorage,user)
                print(Fore.GREEN + f"Processing Stats {b}" + Style.RESET_ALL)
                statistiques.append({b:{"cookies":stats,"dom":dom}})   
        return statistiques
        
    except Exception as e:
         print(f"Erreur lors du traitement de {b}: {e}")                         
                     




    

    


    
   