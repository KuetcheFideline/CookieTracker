import re
import urllib.parse

from treatement.helpers import (
    detect_suspicious_tokens,
    get_variants_for_key,
    get_compiled_pattern,
    deduplicate_matches,
    calculate_match_confidence,
    is_technical_context
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
        
        # Pattern exact avec cache
        if isinstance(value, list):
            for v in value:
                if v and str(v).strip():
                    pattern_str = rf'\b{re.escape(str(v))}\b'
                    data_patterns[key]['exact'].append(get_compiled_pattern(pattern_str))
        else:
            if value and str(value).strip():
                val_str = str(value)
                pattern_str = rf'\b{re.escape(val_str)}\b'
                
                # Logique stricte pour les codes courts (pays, langue)
                flags = re.IGNORECASE
                if key in ['country', 'code_pays', 'language', 'lang'] and len(val_str) == 2:
                    common_words = {'us', 'it', 'at', 'in', 'to', 'do', 'is', 'an', 'or', 'if', 'my', 'me', 'we', 'he', 'be', 'by', 'on', 'go', 'up', 'no', 'as', 'of'}
                    if val_str.lower() in common_words:
                        flags = 0 # Case sensitive
                        
                data_patterns[key]['exact'].append(get_compiled_pattern(pattern_str, flags))
        
        # Patterns variants avec cache
        for variant in variants:
            if len(variant) >= 3:
                pattern_str = rf'\b{re.escape(variant)}\b'
                data_patterns[key]['variants'].append(get_compiled_pattern(pattern_str))
            # Exception pour les codes de 2 lettres (pays/langue) qui sont pertinents
            elif len(variant) == 2 and key in ['country', 'code_pays', 'language', 'lang']:
                pattern_str = rf'\b{re.escape(variant)}\b'
                
                # Même logique stricte pour les variants
                flags = re.IGNORECASE
                common_words = {'us', 'it', 'at', 'in', 'to', 'do', 'is', 'an', 'or', 'if', 'my', 'me', 'we', 'he', 'be', 'by', 'on', 'go', 'up', 'no', 'as', 'of'}
                if variant.lower() in common_words:
                    flags = 0 # Case sensitive
                    
                data_patterns[key]['variants'].append(get_compiled_pattern(pattern_str, flags))
    
    result = {}
    
    for host, cookie_dict in cookies_by_host.items():
        # Nouvelle structure avec sections séparées
        host_info = {
            'personal_information': {},
            'decoded_tokens': {
                'count': 0,
                'items': []
            },
            'detected_emails': {
                'count': 0,
                'unique_emails': []
            },
            'suspicious_tokens': {
                'count': 0,
                'high_risk': 0,
                'medium_risk': 0,
                'low_risk': 0,
                'items': []
            }
        }
        
        # Initialisation pour données personnelles
        for key in personal_info.keys():
            host_info['personal_information'][key] = {
                'exact': 0,
                'variants': 0,
                'matches': []  
            }
        
        for cookie_idx, (cookie_name, cookie_value) in enumerate(cookie_dict.items()):
            # Normaliser les valeurs
            val = urllib.parse.unquote_plus(urllib.parse.unquote(str(cookie_value)))
            val_clean = re.sub(r'[^\w\s@.-]', ' ', val)
            cookie_name_str = str(cookie_name)
            
            # 1. Recherche données personnelles
            for key, patterns in data_patterns.items():
                is_exact = False
                # Recherche exacte dans valeur ET nom du cookie
                for pattern in patterns['exact']:
                    matches_val = list(pattern.finditer(val))
                    matches_name = list(pattern.finditer(cookie_name_str))
                    
                    for match in matches_val + matches_name:
                        # Vérifier le contexte technique
                        source = val if match in matches_val else cookie_name_str
                        if is_technical_context(source, match.start(), match.end()):
                            continue
                        
                        is_exact = True
                        confidence = calculate_match_confidence('exact', match.group(), cookie_name_str, key)
                        
                        host_info['personal_information'][key]['exact'] += 1
                        host_info['personal_information'][key]['matches'].append({
                            'type': 'exact',
                            'matched_text': match.group(),
                            'cookie_name': cookie_name_str,
                            'cookie_value': source,  # Valeur complète du DOM/cookie
                            'cookie_index': cookie_idx,
                            'match_position': {'start': match.start(), 'end': match.end()},
                            'confidence': confidence
                        })
                
                if not is_exact:

                    # Recherche variants
                    for pattern in patterns['variants']:
                        matches_val = list(pattern.finditer(val_clean))
                        matches_name = list(pattern.finditer(cookie_name_str))
                        
                        for match in matches_val + matches_name:
                            # Vérifier le contexte technique
                            source = val_clean if match in matches_val else cookie_name_str
                            if is_technical_context(source, match.start(), match.end()):
                                continue
                            
                            confidence = calculate_match_confidence('variant', match.group(), cookie_name_str, key)
                            
                            host_info['personal_information'][key]['variants'] += 1
                            host_info['personal_information'][key]['matches'].append({
                                'type': 'variant',
                                'matched_text': match.group(),
                                'cookie_name': cookie_name_str,
                                'cookie_value': source,  # Valeur complète du DOM/cookie
                                'cookie_index': cookie_idx,
                                'match_position': {'start': match.start(), 'end': match.end()},
                                'confidence': confidence
                            })
            
            # 2. Détection tokens suspects
            suspicious_items = detect_suspicious_tokens(val, cookie_name_str, personal_info=personal_info)
            for item in suspicious_items:
                item.update({
                    'cookie_index': cookie_idx,
                })
                
                # Séparer les tokens décodés, emails détectés et autres tokens suspects
                if item.get('category') == 'email_detection':
                    # C'est un email détecté
                    email = item.get('email')
                    if email and email not in host_info['detected_emails']['unique_emails']:
                        host_info['detected_emails']['unique_emails'].append(email)
                        host_info['detected_emails']['count'] += 1
                elif item.get('subtype') in ['jwt_token', 'base64_data'] and item.get('decoded_value'):
                    # C'est un token décodé
                    host_info['decoded_tokens']['count'] += 1
                    host_info['decoded_tokens']['items'].append(item)
                else:
                    # Autres tokens suspects
                    host_info['suspicious_tokens']['count'] += 1
                    host_info['suspicious_tokens']['items'].append(item)
        
        # Dédupliquer les matches pour chaque clé d'information personnelle
        for key in personal_info.keys():
            if host_info['personal_information'][key]['matches']:
                host_info['personal_information'][key]['matches'] = deduplicate_matches(host_info['personal_information'][key]['matches'])
                host_info['personal_information'][key]['unique_count'] = len(host_info['personal_information'][key]['matches'])
        
        result[host] = host_info
    
    return result