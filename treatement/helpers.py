
import re
import urllib.parse
import math
import base64
import json
from typing import Dict, List, Union, Any
import datetime








def create_account_number_variants(account_number):
    """
    Crée toutes les variantes possibles d'un numéro de compte bancaire
    Supporte différents formats de séparateurs et groupements
    """
    if not account_number or not str(account_number).strip():
        return []
    
    account_str = str(account_number).strip()
    variants = [account_str]  # Format original
    
    # Extraire seulement les chiffres et lettres
    digits_letters_only = re.sub(r'[^\w]', '', account_str)
    if digits_letters_only:
        variants.append(digits_letters_only)
    
    # Extraire seulement les chiffres
    digits_only = re.sub(r'\D', '', account_str)
    if digits_only:
        variants.append(digits_only)
        
        # Formats avec différents séparateurs pour les chiffres
        if len(digits_only) >= 8:  # Assez long pour être formaté
            # Groupements classiques des comptes bancaires
            variants.extend([
                # Groupes de 4 chiffres
                ' '.join([digits_only[i:i+4] for i in range(0, len(digits_only), 4)]),
                '-'.join([digits_only[i:i+4] for i in range(0, len(digits_only), 4)]),
                '.'.join([digits_only[i:i+4] for i in range(0, len(digits_only), 4)]),
                
                # Groupes de 3 chiffres
                ' '.join([digits_only[i:i+3] for i in range(0, len(digits_only), 3)]),
                '-'.join([digits_only[i:i+3] for i in range(0, len(digits_only), 3)]),
                '.'.join([digits_only[i:i+3] for i in range(0, len(digits_only), 3)]),
                
                # Groupes de 5 chiffres
                ' '.join([digits_only[i:i+5] for i in range(0, len(digits_only), 5)]),
                '-'.join([digits_only[i:i+5] for i in range(0, len(digits_only), 5)]),
                
                # Format IBAN-like (groupes de 4)
                f"{digits_only[:4]} {digits_only[4:8]} {digits_only[8:12]} {digits_only[12:16]} {digits_only[16:]}".strip(),
                f"{digits_only[:4]}-{digits_only[4:8]}-{digits_only[8:12]}-{digits_only[12:16]}-{digits_only[16:]}".strip(),
            ])
            
            # Formats spécifiques français (si applicable)
            if len(digits_only) >= 11:
                # Format RIB français : 5 + 5 + 11 + 2
                if len(digits_only) >= 23:
                    variants.extend([
                        f"{digits_only[:5]} {digits_only[5:10]} {digits_only[10:21]} {digits_only[21:23]}",
                        f"{digits_only[:5]}-{digits_only[5:10]}-{digits_only[10:21]}-{digits_only[21:23]}",
                    ])
    
    # Si le numéro contient des lettres (comme IBAN), les traiter séparément
    if digits_letters_only != digits_only:
        # Formats avec lettres et chiffres
        if len(digits_letters_only) >= 8:
            variants.extend([
                # Groupes de 4 caractères
                ' '.join([digits_letters_only[i:i+4] for i in range(0, len(digits_letters_only), 4)]),
                '-'.join([digits_letters_only[i:i+4] for i in range(0, len(digits_letters_only), 4)]),
                
                # Format IBAN standard (4 caractères par groupe)
                f"{digits_letters_only[:4]} {digits_letters_only[4:8]} {digits_letters_only[8:12]} {digits_letters_only[12:16]} {digits_letters_only[16:20]} {digits_letters_only[20:]}".strip(),
            ])
    
    # Variantes avec différents séparateurs appliqués à l'original
    variants.extend([
        account_str.replace(' ', ''),           # Supprimer espaces
        account_str.replace('-', ''),           # Supprimer tirets
        account_str.replace('.', ''),           # Supprimer points
        account_str.replace('_', ''),           # Supprimer underscores
        account_str.replace(' ', '-'),          # Remplacer espaces par tirets
        account_str.replace('-', ' '),          # Remplacer tirets par espaces
        account_str.replace('.', ' '),          # Remplacer points par espaces
        account_str.replace(' ', '.'),          # Remplacer espaces par points
        account_str.replace('_', '-'),          # Remplacer underscores par tirets
        account_str.upper(),                    # Majuscules
        account_str.lower(),                    # Minuscules
    ])
    
    cleaned_variants = []
    for variant in variants:
        # Supprimer préfixes communs
        for prefix in ['ACCOUNT', 'ACC', 'NO', 'N°', '#', 'COMPTE', 'CPT']:
            if variant.upper().startswith(prefix):
                cleaned = variant[len(prefix):].strip(' -.:_')
                if cleaned:
                    cleaned_variants.append(cleaned)
    
    variants.extend(cleaned_variants)
    
    # Nettoyer et retourner les variants uniques
    return [v for v in set(variants) if v and v.strip()]


def calculate_entropy(text):
    """Calcule l'entropie de Shannon d'une chaîne"""
    if not text:
        return 0
    
    # Fréquences des caractères
    char_counts = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1
    
    # Calcul entropie
    entropy = 0
    text_len = len(text)
    for count in char_counts.values():
        prob = count / text_len
        entropy -= prob * math.log2(prob)
    
    return entropy

def detect_suspicious_tokens(value, cookie_name):
    """
    Fonction unifiée qui détecte à la fois :
    - Les tokens, clés et patterns suspects
    - La collecte d'historiques de navigation
    
    Args:
        value: Valeur à analyser (contenu du cookie, localStorage, etc.)
        cookie_name: Nom du cookie/clé (peut être None)
    """
    suspicious_items = []
    
    # ========== DÉTECTION DE TOKENS SUSPECTS ==========
    
    # Patterns de tokens/clés suspectes
    token_patterns = {
        'jwt_token': r'eyJ[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]+',
        'api_key': r'[A-Za-z0-9]{32,}',
        'session_id': r'[A-Fa-f0-9]{32,}|[A-Za-z0-9_-]{20,}',
        'uuid': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        'base64_data': r'[A-Za-z0-9+/]{20,}={0,2}',
        'hash_sha256': r'[a-fA-F0-9]{64}',
        'hash_md5': r'[a-fA-F0-9]{32}',
        'encoded_data': r'%[0-9A-Fa-f]{2}',
    }
    
    # Noms de cookies/clés suspects pour tokens
    suspicious_token_keys = [
        'token', 'auth', 'session', 'user', 'login', 'account', 'profile',
        'email', 'name', 'phone', 'address', 'location', 'geo', 'lat', 'lng',
        'birth', 'age', 'gender', 'password', 'pwd', 'secret', 'key', 'id',
        'tracking', 'analytics', 'fingerprint', 'device', 'browser', 'ip'
    ]
    
    # 1. Analyse des patterns de tokens
    for pattern_name, pattern in token_patterns.items():
        matches = re.findall(pattern, value, re.IGNORECASE)
        for match in matches:
            if len(match) >= 8: 
                entropy = calculate_entropy(match)
                suspicious_items.append({
                    'category': 'token_detection',
                    'type': 'token_pattern',
                    'subtype': pattern_name,
                    'entropy': entropy,
                    'length': len(match),
                    'cookie': cookie_name,
                    'risk_score': min(10, entropy + len(match)/10)
                })
    
    # 2. Analyse entropique des segments
    segments = re.split(r'[&=;,|:\s]+', value)
    for segment in segments:
        if len(segment) >= 8:
            entropy = calculate_entropy(segment)
            
            # Seuils d'entropie suspects
            if entropy > 4.5:  # Haute entropie = potentiellement encodé/crypté
                suspicious_items.append({
                    'category': 'token_detection',
                    'type': 'high_entropy',
                    'subtype': 'random_string',
                    'entropy': entropy,
                    'length': len(segment),
                    'cookie': cookie_name,
                    'risk_score': min(10, entropy * 1.5)
                })
    
    # 3. Analyse du nom du cookie pour tokens
    if cookie_name:
        cookie_lower = cookie_name.lower()
        for suspicious_key in suspicious_token_keys:
            if suspicious_key in cookie_lower:
                suspicious_items.append({
                    'category': 'token_detection',
                    'type': 'suspicious_key',
                    'subtype': suspicious_key,
                    'name': cookie_name,
                    'entropy': calculate_entropy(cookie_name),
                    'length': len(cookie_name),
                    'cookie': cookie_name,
                    'risk_score': 7 if suspicious_key in ['password', 'secret', 'token'] else 5
                })
                break
    
    # 4. Détection de données JSON encodées pour tokens
    try:
        # Tentative de décoder base64
        if len(value) > 10 and '=' in value[-3:]:
            try:
                decoded = base64.b64decode(value).decode('utf-8')
                if decoded.startswith('{') or decoded.startswith('['):
                    json_data = json.loads(decoded)
                    suspicious_items.append({
                        'category': 'token_detection',
                        'type': 'encoded_json',
                        'subtype': 'base64_json',
                        'entropy': calculate_entropy(value),
                        'length': len(value),
                        'cookie': cookie_name,
                        'risk_score': 8
                    })
            except:
                pass
        
        # JSON direct
        if value.strip().startswith(('{', '[')):
            json_data = json.loads(value)
            suspicious_items.append({
                'category': 'token_detection',
                'type': 'json_data',
                'subtype': 'direct_json',
                'entropy': calculate_entropy(value),
                'length': len(value),
                'cookie': cookie_name,
                'risk_score': 6
            })
    except:
        pass
    
    # ========== DÉTECTION DE COLLECTE DE NAVIGATION ==========
    
    # Patterns indiquant la collecte d'historique de navigation
    navigation_collection_patterns = {
        # Stockage d'URLs visitées
        'visited_urls': r'(visited_urls?|browsing_history|page_history|url_history|site_history)',
        'referrer_tracking': r'(referrer|referer|previous_page|last_page|came_from)',
        'page_sequence': r'(page_sequence|navigation_path|user_journey|page_flow)',
        
        # Métadonnées de navigation
        'scroll_tracking': r'(scroll_position|scroll_depth|scroll_time|page_scroll)',
        'time_on_page': r'(time_spent|dwell_time|session_duration|page_time|visit_duration)',
        'click_tracking': r'(click_map|click_tracking|mouse_tracking|interaction_data)',
        
        # Fingerprinting du navigateur
        'browser_fingerprint': r'(fingerprint|browser_id|device_signature|client_signature)',
        'screen_resolution': r'(screen_width|screen_height|resolution|display_size)',
        'browser_features': r'(plugins|extensions|fonts|webgl|canvas_fingerprint)',
        
        # Données de session détaillées
        'session_replay': r'(session_replay|user_session|replay_data|interaction_log)',
        'keystroke_logging': r'(keylog|keystroke|input_tracking|form_analytics)',
        'mouse_movements': r'(mouse_move|cursor_tracking|pointer_events)',
        
        # Données de géolocalisation

        # Analytics avancés
        'behavior_analytics': r'(behavior|user_analytics|engagement_metrics|activity_log)',
        'conversion_tracking': r'(conversion|funnel|attribution|campaign_tracking)',
        'ab_testing': r'(ab_test|split_test|variant|experiment_data)'
    }
    
    # Patterns de stockage suspect dans les valeurs
    storage_patterns = {
        # Données encodées suspectes
        'encoded_navigation': r'[A-Za-z0-9+/]{50,}={0,2}',  # Base64 long
        'json_navigation': r'\{[^}]*(?:url|page|visit|history|navigation)[^}]*\}',
        'serialized_data': r'(a:\d+:\{|O:\d+:|s:\d+:)',  # PHP serialize
        
        # URLs multiples stockées
        'multiple_urls': r'https?://[^\s,;|]+[,;|]https?://',
        'url_array': r'\[(.*https?://.*)\]',
        
        # Timestamps de visite
        'visit_timestamps': r'\d{10,13}[,;|]\d{10,13}',  # Unix timestamps
        'iso_timestamps': r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
        
        # Données de session complexes
        'complex_session': r'[{[].*(?:page|url|time|duration).*[}\]]',
    }
    
    # Noms de cookies/clés suspects pour la collecte de navigation
    suspicious_navigation_keys = [
        'history', 'visited', 'pages', 'navigation', 'journey', 'path',
        'referrer', 'previous', 'last_page', 'came_from', 'source',
        'scroll', 'time_on_page', 'dwell', 'duration', 'engagement',
        'clicks', 'interactions', 'mouse', 'cursor', 'tracking',
        'fingerprint', 'signature', 'browser_id', 'device_id',
        'session_data', 'replay', 'analytics', 'behavior',
        'location', 'geo', 'coordinates', 'timezone',
        'conversion', 'funnel', 'attribution', 'campaign'
    ]
    
    # 5. Analyse des patterns de collecte dans la valeur
    value_lower = value.lower() if value else ""
    for pattern_name, pattern in navigation_collection_patterns.items():
        if re.search(pattern, value_lower, re.IGNORECASE):
            suspicious_items.append({
                'category': 'navigation_collection',
                'type': 'navigation_collection_pattern',
                'subtype': pattern_name,
                'cookie_name': cookie_name,
                'entropy': calculate_entropy(value) if value else 0,
                'length': len(value) if value else 0,
                'risk_score': get_collection_risk_score(pattern_name),
                'detected_in': 'value'
            })
    
    # 6. Analyse des patterns de stockage suspects
    if value:
        for pattern_name, pattern in storage_patterns.items():
            matches = re.findall(pattern, value, re.IGNORECASE)
            if matches:
                for match in matches[:3]:  # Limite à 3 matches
                    entropy = calculate_entropy(match)
                    suspicious_items.append({
                        'category': 'navigation_collection',
                        'type': 'suspicious_storage_pattern',
                        'subtype': pattern_name,
                        'cookie_name': cookie_name,
                        'entropy': entropy,
                        'length': len(match),
                        'risk_score': min(10, entropy + len(match)/50),
                        'detected_in': 'value'
                    })
    
    # 7. Analyse du nom du cookie/clé pour navigation
    if cookie_name:
        cookie_lower = cookie_name.lower()
        for suspicious_key in suspicious_navigation_keys:
            if suspicious_key in cookie_lower:
                suspicious_items.append({
                    'category': 'navigation_collection',
                    'type': 'suspicious_navigation_key',
                    'subtype': suspicious_key,
                    'cookie_name': cookie_name,
                    'entropy': calculate_entropy(cookie_name),
                    'length': len(cookie_name),
                    'risk_score': get_key_risk_score(suspicious_key),
                    'detected_in': 'cookie_name'
                })
                break
    
    # 8. Détection de données JSON avec informations de navigation
    if value and len(value) > 10:
        try:
            # JSON direct
            if value.strip().startswith(('{', '[')):
                json_data = json.loads(value)
                navigation_indicators = ['url', 'page', 'visit', 'history', 'navigation', 'referrer', 'timestamp', 'time', 'duration']
                found_indicators = [key for key in navigation_indicators if key in str(json_data).lower()]
                
                if found_indicators:
                    suspicious_items.append({
                        'category': 'navigation_collection',
                        'type': 'json_navigation_data',
                        'subtype': 'structured_navigation_storage',
                        'cookie_name': cookie_name,
                        'navigation_keys': found_indicators,
                        'entropy': calculate_entropy(value),
                        'length': len(value),
                        'risk_score': min(10, len(found_indicators) * 2),
                        'detected_in': 'value'
                    })
        except:
            pass
    
    # 9. Détection de données Base64 avec contenu de navigation
    if value and len(value) > 20 and '=' in value[-3:]:
        try:
            # Vérifier si c'est du Base64 valide
            if re.match(r'^[A-Za-z0-9+/]+={0,2}$', value.replace(' ', '')):
                decoded = base64.b64decode(value).decode('utf-8', errors='ignore')
                if len(decoded) > 10:
                    navigation_keywords = ['http', 'url', 'page', 'visit', 'history', 'referrer', 'navigation']
                    found_keywords = [kw for kw in navigation_keywords if kw in decoded.lower()]
                    
                    if found_keywords:
                        suspicious_items.append({
                            'category': 'navigation_collection',
                            'type': 'encoded_navigation_data',
                            'subtype': 'base64_navigation_storage',
                            'cookie_name': cookie_name,
                            'decoded_preview': decoded[:100],
                            'navigation_keywords': found_keywords,
                            'entropy': calculate_entropy(value),
                            'length': len(value),
                            'risk_score': 9,
                            'detected_in': 'value'
                        })
        except:
            pass
    
    # 10. Détection d'URLs multiples (historique de navigation)
    if value:
        # Recherche d'URLs multiples
        urls = re.findall(r'https?://[^\s,;|<>"\']+', value)
        if len(urls) > 1:
            suspicious_items.append({
                'category': 'navigation_collection',
                'type': 'multiple_urls_storage',
                'subtype': 'navigation_history_urls',
                'cookie_name': cookie_name,
                'urls_count': len(urls),
                'urls_sample': urls[:3],
                'entropy': calculate_entropy(value),
                'length': len(value),
                'risk_score': min(10, len(urls)),
                'detected_in': 'value'
            })
    
    # 11. Détection de timestamps multiples (séquence de navigation)
    if value:
        timestamps = re.findall(r'\d{10,13}', value)  # Unix timestamps
        if len(timestamps) > 2:
            suspicious_items.append({
                'category': 'navigation_collection',
                'type': 'navigation_timestamps',
                'subtype': 'visit_sequence_tracking',
                'cookie_name': cookie_name,
                'timestamps_count': len(timestamps),
                'entropy': calculate_entropy(value),
                'length': len(value),
                'risk_score': min(9, len(timestamps)),
                'detected_in': 'value'
            })
    
    # 12. Détection de coordonnées géographiques
    if value:
        # Coordonnées GPS
        coord_matches = re.findall(r'[-]?\d+\.\d+,[-]?\d+\.\d+', value)
        if coord_matches:
            suspicious_items.append({
                'category': 'navigation_collection',
                'type': 'geolocation_tracking',
                'subtype': 'gps_coordinates',
                'cookie_name': cookie_name,
                'coordinates_found': len(coord_matches),
                'entropy': calculate_entropy(value),
                'length': len(value),
                'risk_score': 8,
                'detected_in': 'value'
            })
    
    return suspicious_items

def get_collection_risk_score(pattern_name):
    """Score de risque pour les patterns de collecte de navigation"""
    risk_scores = {
        'visited_urls': 10,
        'referrer_tracking': 7,
        'page_sequence': 9,
        'scroll_tracking': 6,
        'time_on_page': 5,
        'click_tracking': 8,
        'browser_fingerprint': 9,
        'screen_resolution': 6,
        'browser_features': 8,
        'session_replay': 10,
        'keystroke_logging': 10,
        'mouse_movements': 9,
        'location_history': 9,
        'timezone_tracking': 5,
        'behavior_analytics': 7,
        'conversion_tracking': 6,
        'ab_testing': 4
    }
    return risk_scores.get(pattern_name, 5)

def get_key_risk_score(key_name):
    """Score de risque pour les noms de clés/cookies suspects"""
    high_risk_keys = ['history', 'visited', 'navigation', 'tracking', 'fingerprint', 'session_data', 'replay']
    medium_risk_keys = ['pages', 'journey', 'referrer', 'scroll', 'clicks', 'analytics', 'location']
    
    if key_name in high_risk_keys:
        return 9
    elif key_name in medium_risk_keys:
        return 7
    else:
        return 5

def create_name_variants(name):
    if not name or not str(name).strip():  # AJOUT: Vérification valeur vide
        return []
        
    variants = []
    name_clean = re.sub(r'[^\w\s]', '', name.lower())
    words = name_clean.split()
    
    if not words:  # AJOUT: Si après nettoyage il n'y a plus rien
        return []
        
    variants.extend([
        name.lower(),
        name.upper(),
        name.title(),
        name_clean,
        ''.join(words),
    ])

    if len(words) > 1:
        variants.extend([
            ' '.join(reversed(words)),
            ''.join(reversed(words))
        ])
        
    variants.extend(words)
    
    # AJOUT: Filtrer les variants vides
    return [v for v in set(variants) if v and v.strip()]



def create_pobox_variants(pobox):
    """Crée des variants pour les P.O. Box / Boîtes postales"""
    if not pobox or not str(pobox).strip():
        return []
    
    variants = [pobox.lower(), pobox.upper()]
    pobox_clean = pobox.strip()
    
    # Vérification si c'est juste un nombre (utilisateur a saisi que les chiffres)
    if pobox_clean.isdigit():
        num = pobox_clean
        
        # Si c'est juste un nombre, ajouter tous les préfixes possibles
        variants.extend([
            # Variants français
            f"bp {num}",
            f"bp{num}",
            f"b.p. {num}",
            f"b.p.{num}",
            f"boite postale {num}",
            f"boîte postale {num}",
            f"cedex {num}",
            
            # Variants anglais
            f"po box {num}",
            f"pobox {num}",
            f"po.box {num}",
            f"p.o. box {num}",
            f"p.o.box {num}",
            f"post office box {num}",
            f"postbox {num}",
            
            # Variants allemands
            f"postfach {num}",
            f"pf {num}",
            
            # Variants espagnols/italiens
            f"apartado {num}",
            f"ap {num}",
            f"casella postale {num}",
            f"cp {num}",
            
            # Formats numériques
            f"#{num}",
            f"no {num}",
            f"n° {num}",
            f"nr {num}"
        ])
    else:
        # Extraction du numéro de boîte postale
        box_number = re.search(r'\b(\d+)\b', pobox_clean)
        if box_number:
            num = box_number.group(1)
            
            # Variants français
            variants.extend([
                f"bp {num}",
                f"bp{num}",
                f"b.p. {num}",
                f"b.p.{num}",
                f"boite postale {num}",
                f"boîte postale {num}",
                f"cedex {num}",
                
                # Variants anglais
                f"po box {num}",
                f"pobox {num}",
                f"po.box {num}",
                f"p.o. box {num}",
                f"p.o.box {num}",
                f"post office box {num}",
                f"postbox {num}",
                
                # Variants allemands
                f"postfach {num}",
                f"pf {num}",
                
                # Variants espagnols/italiens
                f"apartado {num}",
                f"ap {num}",
                f"casella postale {num}",
                f"cp {num}",
                
                # Formats numériques
                num,
                f"#{num}",
                f"no {num}",
                f"n° {num}",
                f"nr {num}"
            ])
    
    # Patterns de reconnaissance de boîtes postales
    pobox_patterns = [
        r'(bp|b\.p\.?)\s*(\d+)',
        r'(po\.?\s*box|pobox)\s*(\d+)',
        r'(postfach|pf)\s*(\d+)',
        r'(apartado|ap)\s*(\d+)',
        r'(cedex)\s*(\d+)',
        r'(boite|boîte)\s*postale\s*(\d+)',
        r'casella\s*postale\s*(\d+)'
    ]
    
    for pattern in pobox_patterns:
        match = re.search(pattern, pobox_clean.lower())
        if match and len(match.groups()) >= 2:
            prefix = match.group(1)
            number = match.group(2)
            variants.extend([
                f"{prefix} {number}",
                f"{prefix}{number}",
                number
            ])
    
    return [v for v in set(variants) if v and v.strip()]

def create_email_variants(email):
    if not email or not str(email).strip():  # AJOUT: Vérification valeur vide
        return []
        
    variants = [email.lower()]
    
    if '@' in email:
        username, domain = email.lower().split('@', 1)
        if username:  
            variants.extend([
                f"{username}@", 
            ])
    
    return [v for v in variants if v and v.strip()]  


def create_phone_variants(phone):
    if not phone or not str(phone).strip():  
        return []
        
    digits_only = re.sub(r'\D', '', phone)
    if not digits_only: 
        return []
        
    variants = [phone, digits_only]
    
    if len(digits_only) >= 10:
        variants.extend([
            f"{digits_only[:2]} {digits_only[2:4]} {digits_only[4:6]} {digits_only[6:8]} {digits_only[8:]}",
            f"{digits_only[:2]}-{digits_only[2:4]}-{digits_only[4:6]}-{digits_only[6:8]}-{digits_only[8:]}",
            f"{digits_only[:2]}.{digits_only[2:4]}.{digits_only[4:6]}.{digits_only[6:8]}.{digits_only[8:]}",
            f"+33{digits_only[1:]}" if digits_only.startswith('0') else f"+33{digits_only}",
            f"+237{digits_only[1:]}" if digits_only.startswith('0') else f"+237{digits_only}",
            digits_only[1:] if digits_only.startswith('0') else digits_only 
        ])
    
    return [v for v in set(variants) if v and v.strip()]



def create_generic_variants(value):
    if not value or not str(value).strip():  
        return []
        
    variants = [
        value.lower(),
        value.upper(),
        value.title(),
        re.sub(r'[^\w]', '', value.lower()),  
        re.sub(r'\s+', '', value.lower())   
    ]
    return [v for v in set(variants) if v and v.strip()]  
def create_generic_variants(value: str) -> List[str]:
    """Variants génériques pour autres données"""
    variants = [
        value.lower(),
        value.upper(),
        value.title(),
        re.sub(r'[^\w]', '', value.lower()),
        re.sub(r'\s+', '', value.lower())
    ]
    return list(set(variants))

def create_birthdate_variants(birthdate: str) -> List[str]:
    """
    Crée toutes les variantes possibles d'une date de naissance
    Supporte les formats: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, YYYY-MM-DD, etc.
    """
    if not birthdate or not str(birthdate).strip():
        return []
    
    birthdate_str = str(birthdate).strip()
    variants = [birthdate_str]  # Format original
    
    # Extraction des composants de date avec différents patterns
    date_patterns = [
        r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})', 
        r'(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})', 
        r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2})',  
        r'(\d{2})[/\-\.](\d{1,2})[/\-\.](\d{1,2})',  
    ]
    
    day, month, year = None, None, None
    
    # Tentative d'extraction avec différents patterns
    for pattern in date_patterns:
        match = re.search(pattern, birthdate_str)
        if match:
            parts = match.groups()
            
            # Détecter le format basé sur la position et les valeurs
            if len(parts[0]) == 4:  # YYYY en premier
                year, month, day = parts[0], parts[1], parts[2]
            elif len(parts[2]) == 4:  # YYYY en dernier
                day, month, year = parts[0], parts[1], parts[2]
            elif len(parts[2]) == 2:  # YY en dernier
                day, month = parts[0], parts[1]
                year_short = parts[2]
                # Convertir YY en YYYY (assume 19XX si > 50, sinon 20XX)
                year = f"19{year_short}" if int(year_short) > 50 else f"20{year_short}"
            elif len(parts[0]) == 2 and int(parts[0]) > 31:  # YY en premier
                year_short, month, day = parts[0], parts[1], parts[2]
                year = f"19{year_short}" if int(year_short) > 50 else f"20{year_short}"
            
            break
    
    # Si aucun pattern ne correspond, essayer d'extraire juste les chiffres
    if not all([day, month, year]):
        digits = re.findall(r'\d+', birthdate_str)
        if len(digits) >= 3:
            # Essayer différentes interprétations
            if len(digits[0]) == 4:  # YYYY MM DD
                year, month, day = digits[0], digits[1], digits[2]
            elif len(digits[2]) == 4:  # DD MM YYYY
                day, month, year = digits[0], digits[1], digits[2]
            else:
                # Par défaut, assume DD MM YY
                day, month = digits[0], digits[1]
                year_val = int(digits[2])
                if year_val < 100:
                    year = f"19{digits[2]:0>2}" if year_val > 50 else f"20{digits[2]:0>2}"
                else:
                    year = str(year_val)
    
    # Si on a réussi à extraire les composants
    if all([day, month, year]):
        # S'assurer que les valeurs sont formatées correctement
        day = day.zfill(2)
        month = month.zfill(2)
        year = year.zfill(4)
        
        # Vérification basique de validité
        try:
            datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
        except ValueError:
            # Si la date n'est pas valide, retourner seulement l'original
            return [v for v in set(variants) if v and v.strip()]
        
        # Générer tous les formats possibles
        date_formats = [
            # Formats avec séparateurs
            f"{day}/{month}/{year}",           # DD/MM/YYYY
            f"{day}-{month}-{year}",           # DD-MM-YYYY  
            f"{day}.{month}.{year}",           # DD.MM.YYYY
            f"{day} {month} {year}",           # DD MM YYYY
            f"{year}/{month}/{day}",           # YYYY/MM/DD
            f"{year}-{month}-{day}",           # YYYY-MM-DD
            f"{year}.{month}.{day}",           # YYYY.MM.DD
            f"{year} {month} {day}",           # YYYY MM DD
            f"{month}/{day}/{year}",           # MM/DD/YYYY (format US)
            f"{month}-{day}-{year}",           # MM-DD-YYYY
            f"{month}.{day}.{year}",           # MM.DD.YYYY
            
            # Formats sans séparateurs
            f"{day}{month}{year}",             # DDMMYYYY
            f"{year}{month}{day}",             # YYYYMMDD
            f"{month}{day}{year}",             # MMDDYYYY
            
            # Formats courts (2 chiffres pour l'année)
            f"{day}/{month}/{year[2:]}",       # DD/MM/YY
            f"{day}-{month}-{year[2:]}",       # DD-MM-YY
            f"{day}.{month}.{year[2:]}",       # DD.MM.YY
            f"{year[2:]}/{month}/{day}",       # YY/MM/DD
            f"{year[2:]}-{month}-{day}",       # YY-MM-DD
            f"{year[2:]}.{month}.{day}",       # YY.MM.DD
            f"{month}/{day}/{year[2:]}",       # MM/DD/YY
            f"{month}-{day}-{year[2:]}",       # MM-DD-YY
            
            # Formats sans zéros de tête
            f"{int(day)}/{int(month)}/{year}",         # D/M/YYYY
            f"{int(day)}-{int(month)}-{year}",         # D-M-YYYY
            f"{int(day)}.{int(month)}.{year}",         # D.M.YYYY
            f"{year}/{int(month)}/{int(day)}",         # YYYY/M/D
            f"{year}-{int(month)}-{int(day)}",         # YYYY-M-D
            f"{int(month)}/{int(day)}/{year}",         # M/D/YYYY
            f"{int(month)}-{int(day)}-{year}",         # M-D-YYYY
        ]
        
        variants.extend(date_formats)
    
    # Variantes génériques additionnelles
    variants.extend([
        birthdate_str.replace('/', '-'),        # Remplacer / par -
        birthdate_str.replace('-', '/'),        # Remplacer - par /
        birthdate_str.replace('.', '/'),        # Remplacer . par /
        birthdate_str.replace(' ', ''),         # Supprimer espaces
        birthdate_str.replace(' ', '/'),        # Remplacer espaces par /
        birthdate_str.replace(' ', '-'),        # Remplacer espaces par -
        re.sub(r'\D', '', birthdate_str),       # Que les chiffres
    ])
    
    # Nettoyer et retourner les variants uniques
    return [v for v in set(variants) if v and v.strip()]

def create_language_variants():
    """
    Retourne toutes les variantes possibles des codes de langues/localisations
    pour les langues les plus connues.
    """
    language_mappings = {
        'fr': ['fr', 'FR', 'fr-FR', 'fr_FR', 'french', 'français', 'francais', 'france'],
        
        'en': ['en', 'EN', 'en-US', 'en-GB', 'en_US', 'en_GB', 'english', 'anglais', 'america', 'usa', 'uk', 'britain'],
        
    }
    
    all_variants = set()
    for variants in language_mappings.values():
        all_variants.update(variants)
    
    return sorted(all_variants)



# Mise à jour de la fonction get_variants_for_key pour inclure les dates de naissance
def get_variants_for_key(key: str, value: Union[str, List]) -> List[str]:
    """Retourne les variants selon le type de donnée"""
    if isinstance(value, list):
        all_variants = []
        for v in value:
            all_variants.extend(get_variants_for_key(key, v))
        return all_variants
    
    value_str = str(value)
    
    if key in ['name', 'firstname', 'lastname', 'username']:
        return create_name_variants(value_str)
    elif key == 'email' or '@' in value_str:
        return create_email_variants(value_str)
    elif key in ['phone', 'phone_number', 'tel']:
        return create_phone_variants(value_str)
    elif key in ['pobox', 'po_box', 'boite_postale', 'box']:
        return create_pobox_variants(value_str)
    elif key in ['birthdate', 'date_of_birth', 'birth_date', 'dob', 'date_naissance', 'naissance']:
        return create_birthdate_variants(value_str)
    elif key in ['account_number']:
        return create_account_number_variants(value_str)
    elif key in ['language', 'lang', 'locale', 'langue']:
        return create_language_variants()
    else:
        return create_generic_variants(value_str)
