import re
import urllib.parse

from treatement.helpers import (
    detect_suspicious_tokens,
    get_variants_for_key
)




def search_personal_info_in_dict(cookies_by_host, personal_info):
    """
    Recherche robuste d'informations personnelles dans un format dict avec variants et tokens.
    cookies_by_host = { host: {cookie_key: cookie_value, ...}, ... }
    Retourne un dict {host: {clé_info: {'exact': nb, 'variants': nb, 'matches': [...]}, 'suspicious_tokens': {...}}}
    """
    
    # Préparation des patterns pour chaque info
    data_patterns = {}
    for key, value in personal_info.items():
        variants = get_variants_for_key(key, value)
        data_patterns[key] = {
            'exact': [],
            'variants': []
        }
        
        # Pattern exact
        if isinstance(value, list):
            for v in value:
                data_patterns[key]['exact'].append(re.compile(rf'\b{re.escape(str(v))}\b', re.IGNORECASE))
        else:
            data_patterns[key]['exact'].append(re.compile(rf'\b{re.escape(str(value))}\b', re.IGNORECASE))
        
        # Patterns variants
        for variant in variants:
            if len(variant) >= 3:
                data_patterns[key]['variants'].append(re.compile(rf'\b{re.escape(variant)}\b', re.IGNORECASE))
    
    result = {}
    
    for host, cookie_dict in cookies_by_host.items():
        host_info = {}
        
        # Initialisation pour données personnelles
        for key in personal_info.keys():
            host_info[key] = {
                'exact': 0,
                'variants': 0,
                'matches': []  
            }
        
        # Initialisation pour tokens suspects
        host_info['suspicious_tokens'] = {
            'count': 0,
            'high_risk': 0,
            'medium_risk': 0,
            'low_risk': 0,
            'items': []
        }
        
        for cookie_idx, (cookie_name, cookie_value) in enumerate(cookie_dict.items()):
            # Normaliser les valeurs
            val = urllib.parse.unquote_plus(urllib.parse.unquote(str(cookie_value)))
            val_clean = re.sub(r'[^\w\s@.-]', ' ', val)
            cookie_name_str = str(cookie_name)
            
            # 1. Recherche données personnelles
            for key, patterns in data_patterns.items():
                # Recherche exacte dans valeur ET nom du cookie
                for pattern in patterns['exact']:
                    matches_val = list(pattern.finditer(val))
                    matches_name = list(pattern.finditer(cookie_name_str))
                    
                    for match in matches_val + matches_name:
                        host_info[key]['exact'] += 1
                        host_info[key]['matches'].append({
                            'type': 'exact',
                            'matched_text': match.group(),
                            'cookie_name': cookie_name_str,
                            'cookie_index': cookie_idx,
                            'match_position': {'start': match.start(), 'end': match.end()},
                        })
                
                # Recherche variants
                for pattern in patterns['variants']:
                    matches_val = list(pattern.finditer(val_clean))
                    matches_name = list(pattern.finditer(cookie_name_str))
                    
                    for match in matches_val + matches_name:
                        is_exact = any(exact_p.search(match.group()) for exact_p in patterns['exact'])
                        if not is_exact:
                            host_info[key]['variants'] += 1
                            host_info[key]['matches'].append({
                                'type': 'variant',
                                'matched_text': match.group(),
                                'cookie_name': cookie_name_str,
                                'cookie_index': cookie_idx,
                                'match_position': {'start': match.start(), 'end': match.end()},
                            })
            
            # 2. Détection tokens suspects
            suspicious_items = detect_suspicious_tokens(val, cookie_name_str)
            for item in suspicious_items:
                item.update({
                    'cookie_index': cookie_idx,
                })
                host_info['suspicious_tokens']['count'] += 1
                host_info['suspicious_tokens']['items'].append(item)
                
                if item['risk_score'] >= 8:
                    host_info['suspicious_tokens']['high_risk'] += 1
                elif item['risk_score'] >= 6:
                    host_info['suspicious_tokens']['medium_risk'] += 1
                else:
                    host_info['suspicious_tokens']['low_risk'] += 1
        
        result[host] = host_info
    
    return result
