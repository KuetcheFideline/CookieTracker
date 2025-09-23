
from Firefox.utils.utils import get_os_info
from Firefox.firefox  import Firefox
from Firefox.cookies_data import PersonalCookies, PersonalDOM
from treatement.cookie_treatment import search_personal_info_robust
from treatement.dom_treatment import search_personal_info_in_dict
def main_firefox(last_run,user) -> None:
    os_name = get_os_info()



    browser = Firefox(os_name=os_name)
    browser.print_os()
   
    cookies = PersonalCookies(browser.cookies_path,last_run)
    cookies_data = cookies.filter_data_by_date(user)
    stats = search_personal_info_robust(cookies_data,user)
    dom = PersonalDOM(browser.dom_path,last_run=last_run)

    dom_data = dom.filter_data_by_date(user=user)
    stats_dom = search_personal_info_in_dict(dom_data,user)


    return {"firefox": {"cookies": stats, "dom": stats_dom}}

   