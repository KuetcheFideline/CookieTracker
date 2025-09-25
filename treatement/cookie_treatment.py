import re
import urllib.parse

from treatement.helpers import (
    detect_suspicious_tokens,
    get_variants_for_key
)







def search_personal_info_robust(cookies_by_host, personal_info):
    """
    Recherche robuste d'informations personnelles dans les cookies, tous navigateurs confondus.
    Retourne un dict {host: {clé_info: nb_matchs, ...}} avec traçabilité complète
    """



    
    # AJOUT: Filtrer les valeurs vides au début
    filtered_personal_info = {}
    for key, value in personal_info.items():
        if value is None:
            continue
            
        # Si c'est une liste, filtrer les éléments vides
        if isinstance(value, list):
            non_empty_values = [v for v in value if v and str(v).strip()]
            if non_empty_values:
                filtered_personal_info[key] = non_empty_values
        # Si c'est une chaîne ou autre, vérifier qu'elle n'est pas vide
        elif str(value).strip():
            filtered_personal_info[key] = value
    account_keys = ['account', 'account_number', 'compte', 'rib', 'iban']
    for key in account_keys:
        if key not in filtered_personal_info:
            filtered_personal_info[key] = ""  

    
    # Si aucune donnée personnelle valide, retourner un résultat vide mais structuré
    if not filtered_personal_info:
        result = {}
        for host in cookies_by_host.keys():
            result[host] = {
                'suspicious_tokens': {
                    'count': 0,
                    'high_risk': 0,
                    'medium_risk': 0,
                    'low_risk': 0,
                    'items': []
                }
            }
        return result

    data_patterns = {}
    for key, value in filtered_personal_info.items():  # Utiliser les données filtrées
        variants = get_variants_for_key(key, value)
        data_patterns[key] = {
            'exact': [],
            'variants': []
        }
        
        if isinstance(value, list):
            for v in value:
                if v and str(v).strip():  # AJOUT: Vérification supplémentaire
                    data_patterns[key]['exact'].append(re.compile(rf'\b{re.escape(str(v))}\b', re.IGNORECASE))
        else:
            if value and str(value).strip():  # AJOUT: Vérification supplémentaire
                data_patterns[key]['exact'].append(re.compile(rf'\b{re.escape(str(value))}\b', re.IGNORECASE))
        
        for variant in variants:
            if len(variant) >= 3:  # Cette condition existe déjà, c'est bien
                data_patterns[key]['variants'].append(re.compile(rf'\b{re.escape(variant)}\b', re.IGNORECASE))
    



    result = {}
    for host, cookies in cookies_by_host.items():
        host_info = {}
        
        # AJOUT: Initialiser seulement pour les clés qui ont des valeurs valides
        for key in filtered_personal_info.keys():
            host_info[key] = {
                'exact': 0,
                'variants': 0,
                'matches': []
            }
        
        host_info['suspicious_tokens'] = {
            'count': 0,
            'high_risk': 0,
            'medium_risk': 0,
            'low_risk': 0,
            'items': []
        }
        
        for cookie_idx, cookie in enumerate(cookies):
            # Valeur à analyser
            val = cookie.get("decrypted_value") or cookie.get("value") or ""
            val_decoded = urllib.parse.unquote_plus(urllib.parse.unquote(str(val)))
            val_clean = re.sub(r'[^\w\s@.-]', ' ', val_decoded)
            cookie_name = cookie.get("name", "")
            
            # 1. Recherche données personnelles AVEC TRAÇABILITÉ
            for key, patterns in data_patterns.items():
                is_exact = False
                # Recherche exacte
                for pattern in patterns['exact']:
                    matches = pattern.finditer(val_decoded)
                    for match in matches:
                        is_exact = True
                        host_info[key]['exact'] += 1
                        host_info[key]['matches'].append({
                            'type': 'exact',
                            'matched_text': match.group(),
                            'cookie_name': cookie_name,
                            'cookie_index': cookie_idx,
                            'match_position': {'start': match.start(), 'end': match.end()},
                        })
                
                # Recherche variants
                if not is_exact:

                    for pattern in patterns['variants']:
                        matches = pattern.finditer(val_clean)
                        for match in matches:
                                host_info[key]['variants'] += 1
                                host_info[key]['matches'].append({
                                    'type': 'variant',
                                    'matched_text': match.group(),
                                    'cookie_name': cookie_name,
                                    'cookie_index': cookie_idx,
                                    'match_position': {'start': match.start(), 'end': match.end()},
                                })
            
            # 2. Détection tokens/clés suspectes (inchangé car déjà robuste)
            suspicious_items = detect_suspicious_tokens(val_decoded, cookie_name)
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

