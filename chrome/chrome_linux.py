from chrome.helpers import get_cookies, filters_cookies
from chrome.storage import read_storage ,transform ,third 
from treatement.cookie_treatment import search_personal_info_robust
from treatement.dom_treatment import search_personal_info_in_dict   

def main_linux(user,browser,date):
    print("Linux/Ubuntu OS detected")
    
    statistiques = []
    for b in browser:
        if b =="mozilla" or b=="firefox":
            pass
           
        else:
             cookies = get_cookies(b,date)
             DomStorage = read_storage(b)



             if(cookies ==0):
                 print(f"Le navigateur {b} n'est pas pris en compte sur Linux/Ubuntu .")
             else:
                 stats= search_personal_info_robust(cookies,user)
                 dom =search_personal_info_in_dict(DomStorage,user)
                 statistiques.append({b:{"cookies":stats,"dom":dom}})                          
                     
    return statistiques




    

    


    
   