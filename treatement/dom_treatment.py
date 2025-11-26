import re
import urllib.parse

from treatement.helpers import (
    detect_suspicious_tokens,
    get_variants_for_key
)

# Cache global pour les regex compilées (amélioration performance)
_regex_cache = {}

def get_compiled_pattern(pattern_str):
    """Cache les regex compilées pour éviter la recompilation."""
    if pattern_str not in _regex_cache:
        _regex_cache[pattern_str] = re.compile(pattern_str, re.IGNORECASE)
    return _regex_cache[pattern_str]

def deduplicate_matches(matches):
    """Groupe les matches identiques ensemble pour éviter la redondance."""
    if not matches:
        return []
    
    unique_matches = {}
    
    for match in matches:
        key = (match.get('matched_text', ''), match.get('type', ''))
        
        if key not in unique_matches:
            unique_matches[key] = {
                'matched_text': match.get('matched_text', ''),
                'type': match.get('type', ''),
                'occurrences': []
            }
        
        unique_matches[key]['occurrences'].append({
            'cookie_name': match.get('cookie_name', ''),
            'cookie_index': match.get('cookie_index', 0),
            'position': match.get('match_position', {}),
            'confidence': match.get('confidence', 1.0)
        })
    
    result = []
    for match_data in unique_matches.values():
        match_data['occurrence_count'] = len(match_data['occurrences'])
        confidences = [occ.get('confidence', 1.0) for occ in match_data['occurrences']]
        match_data['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0.0
        result.append(match_data)
    
    return result

def calculate_match_confidence(match_type, matched_text, cookie_name, key):
    """Calcule un score de confiance entre 0.0 et 1.0 pour un match."""
    confidence = 1.0
    
    if match_type == 'exact':
        confidence = 1.0
    elif match_type == 'variant':
        confidence = 0.7
    else:
        confidence = 0.5
    
    text_len = len(matched_text)
    if text_len < 3:
        confidence *= 0.3
    elif text_len < 5:
        confidence *= 0.6
    elif text_len > 20:
        confidence *= 1.2
    
    if cookie_name and key:
        cookie_lower = cookie_name.lower()
        key_lower = key.lower()
        
        if key_lower in cookie_lower:
            confidence *= 1.3
        elif any(word in cookie_lower for word in ['user', 'profile', 'account', 'session']):
            confidence *= 1.1
    
    return min(1.0, max(0.0, confidence))

def is_technical_context(val_decoded, match_start, match_end):
    """Vérifie si le match est dans un contexte technique."""
    context_before = val_decoded[max(0, match_start-10):match_start]
    context_after = val_decoded[match_end:match_end+10]
    
    technical_patterns = [
        r'[_\-\.]$',
        r'^[_\-\.]',
        r'(token|key|id|hash|uuid)$',
        r'^(token|key|id|hash|uuid)',
        r'(session|auth|api)$',
        r'^(session|auth|api)',
    ]
    
    for pattern in technical_patterns:
        if re.search(pattern, context_before, re.IGNORECASE):
            return True
        if re.search(pattern, context_after, re.IGNORECASE):
            return True
    
    return False



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
                pattern_str = rf'\b{re.escape(str(value))}\b'
                data_patterns[key]['exact'].append(get_compiled_pattern(pattern_str))
        
        # Patterns variants avec cache
        for variant in variants:
            if len(variant) >= 3:
                pattern_str = rf'\b{re.escape(variant)}\b'
                data_patterns[key]['variants'].append(get_compiled_pattern(pattern_str))
    
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
                    
                    if item['risk_score'] >= 8:
                        host_info['suspicious_tokens']['high_risk'] += 1
                    elif item['risk_score'] >= 6:
                        host_info['suspicious_tokens']['medium_risk'] += 1
                    else:
                        host_info['suspicious_tokens']['low_risk'] += 1
        
        # Dédupliquer les matches pour chaque clé d'information personnelle
        for key in personal_info.keys():
            if host_info['personal_information'][key]['matches']:
                host_info['personal_information'][key]['matches'] = deduplicate_matches(host_info['personal_information'][key]['matches'])
                host_info['personal_information'][key]['unique_count'] = len(host_info['personal_information'][key]['matches'])
        
        result[host] = host_info
    
    return result
