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
    Version optimisée avec mise en cache.
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
        vals = value if isinstance(value, list) else [value]
        for v in vals:
            if not v or not str(v).strip(): continue
            val_str = str(v)
            pattern_str = rf'\b{re.escape(val_str)}\b'
            flags = re.IGNORECASE
            if key in ['country', 'code_pays', 'language', 'lang'] and len(val_str) == 2:
                common_words = {'us', 'it', 'at', 'in', 'to', 'do', 'is', 'an', 'or', 'if', 'my', 'me', 'we', 'he', 'be', 'by', 'on', 'go', 'up', 'no', 'as', 'of'}
                if val_str.lower() in common_words:
                    flags = 0 # Case sensitive
            data_patterns[key]['exact'].append(get_compiled_pattern(pattern_str, flags))
        
        # Patterns variants
        for variant in variants:
            if len(variant) < 3:
                if not (len(variant) == 2 and key in ['country', 'code_pays', 'language', 'lang']):
                    continue
            pattern_str = rf'\b{re.escape(variant)}\b'
            flags = re.IGNORECASE
            if len(variant) == 2:
                common_words = {'us', 'it', 'at', 'in', 'to', 'do', 'is', 'an', 'or', 'if', 'my', 'me', 'we', 'he', 'be', 'by', 'on', 'go', 'up', 'no', 'as', 'of'}
                if variant.lower() in common_words:
                    flags = 0 # Case sensitive
            data_patterns[key]['variants'].append(get_compiled_pattern(pattern_str, flags))
    
    result = {}
    analysis_cache = {}
    norm_cache = {}
    
    for host, cookie_dict in cookies_by_host.items():
        host_info = {
            'personal_information': {key: {'exact': 0, 'variants': 0, 'matches': []} for key in personal_info.keys()},
            'decoded_tokens': {'count': 0, 'items': []},
            'detected_emails': {'count': 0, 'unique_emails': []},
            'suspicious_tokens': {'count': 0, 'high_risk': 0, 'medium_risk': 0, 'low_risk': 0, 'items': []}
        }
        
        for cookie_idx, (cookie_name, cookie_value) in enumerate(cookie_dict.items()):
            cookie_name_str = str(cookie_name)
            cookie_val_str = str(cookie_value)
            
            cache_key = (cookie_name_str, cookie_val_str)
            if cache_key in analysis_cache:
                cached_res = analysis_cache[cache_key]
                for key, pi_data in cached_res['pi'].items():
                    host_info['personal_information'][key]['exact'] += pi_data['exact']
                    host_info['personal_information'][key]['variants'] += pi_data['variants']
                    for m in pi_data['matches']:
                        m_copy = m.copy()
                        m_copy['cookie_index'] = cookie_idx
                        host_info['personal_information'][key]['matches'].append(m_copy)
                
                for email in cached_res['emails']:
                    if email not in host_info['detected_emails']['unique_emails']:
                        host_info['detected_emails']['unique_emails'].append(email)
                        host_info['detected_emails']['count'] += 1
                
                for token in cached_res['decoded_tokens']:
                    t_copy = token.copy()
                    t_copy['cookie_index'] = cookie_idx
                    host_info['decoded_tokens']['items'].append(t_copy)
                    host_info['decoded_tokens']['count'] += 1
                
                for st in cached_res['suspicious_tokens']:
                    st_copy = st.copy()
                    st_copy['cookie_index'] = cookie_idx
                    host_info['suspicious_tokens']['items'].append(st_copy)
                    host_info['suspicious_tokens']['count'] += 1
                continue

            if cookie_val_str not in norm_cache:
                val = urllib.parse.unquote_plus(urllib.parse.unquote(cookie_val_str))
                val_clean = re.sub(r'[^\w\s@.-]', ' ', val)
                norm_cache[cookie_val_str] = (val, val_clean)
            else:
                val, val_clean = norm_cache[cookie_val_str]
            
            current_analysis = {
                'pi': {key: {'exact': 0, 'variants': 0, 'matches': []} for key in personal_info.keys()},
                'emails': [], 'decoded_tokens': [], 'suspicious_tokens': []
            }
            
            # 1. Recherche données personnelles
            for key, patterns in data_patterns.items():
                is_exact = False
                for pattern in patterns['exact']:
                    matches_val = list(pattern.finditer(val))
                    matches_name = list(pattern.finditer(cookie_name_str))
                    for match in matches_val + matches_name:
                        source = val if match in matches_val else cookie_name_str
                        if is_technical_context(source, match.start(), match.end()):
                            continue
                        is_exact = True
                        confidence = calculate_match_confidence('exact', match.group(), cookie_name_str, key)
                        current_analysis['pi'][key]['exact'] += 1
                        current_analysis['pi'][key]['matches'].append({
                            'type': 'exact', 'matched_text': match.group(),
                            'cookie_name': cookie_name_str, 'cookie_value': source,
                            'cookie_index': cookie_idx, 'match_position': {'start': match.start(), 'end': match.end()},
                            'confidence': confidence
                        })
                
                if not is_exact:
                    for pattern in patterns['variants']:
                        matches_val = list(pattern.finditer(val_clean))
                        matches_name = list(pattern.finditer(cookie_name_str))
                        for match in matches_val + matches_name:
                            source = val_clean if match in matches_val else cookie_name_str
                            if is_technical_context(source, match.start(), match.end()):
                                continue
                            confidence = calculate_match_confidence('variant', match.group(), cookie_name_str, key)
                            current_analysis['pi'][key]['variants'] += 1
                            current_analysis['pi'][key]['matches'].append({
                                'type': 'variant', 'matched_text': match.group(),
                                'cookie_name': cookie_name_str, 'cookie_value': source,
                                'cookie_index': cookie_idx, 'match_position': {'start': match.start(), 'end': match.end()},
                                'confidence': confidence
                            })
            
            # 2. Détection tokens suspects
            suspicious_items = detect_suspicious_tokens(val, cookie_name_str, personal_info=personal_info)
            for item in suspicious_items:
                if item.get('category') == 'email_detection':
                    email = item.get('email')
                    if email: current_analysis['emails'].append(email)
                elif item.get('subtype') in ['jwt_token', 'base64_data'] and item.get('decoded_value'):
                    current_analysis['decoded_tokens'].append(item)
                else:
                    current_analysis['suspicious_tokens'].append(item)
            
            analysis_cache[cache_key] = current_analysis
            
            # Appliquer les résultats
            for key, pi_data in current_analysis['pi'].items():
                host_info['personal_information'][key]['exact'] += pi_data['exact']
                host_info['personal_information'][key]['variants'] += pi_data['variants']
                host_info['personal_information'][key]['matches'].extend(pi_data['matches'])
            
            for email in current_analysis['emails']:
                if email not in host_info['detected_emails']['unique_emails']:
                    host_info['detected_emails']['unique_emails'].append(email)
                    host_info['detected_emails']['count'] += 1
            
            for token in current_analysis['decoded_tokens']:
                host_info['decoded_tokens']['items'].append(token)
                host_info['decoded_tokens']['count'] += 1
            
            for st in current_analysis['suspicious_tokens']:
                host_info['suspicious_tokens']['items'].append(st)
                host_info['suspicious_tokens']['count'] += 1
        
        # Dédupliquer les matches
        for key in personal_info.keys():
            if host_info['personal_information'][key]['matches']:
                host_info['personal_information'][key]['matches'] = deduplicate_matches(host_info['personal_information'][key]['matches'])
                host_info['personal_information'][key]['unique_count'] = len(host_info['personal_information'][key]['matches'])
        
        result[host] = host_info
    
    return result