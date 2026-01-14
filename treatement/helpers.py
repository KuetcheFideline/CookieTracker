
import re
import urllib.parse
import math
import base64
import json
from typing import Dict, List, Union, Any
import datetime



# ============================================================================
# FONCTIONS UTILITAIRES PARTAGÉES (cookie_treatment.py et dom_treatment.py)
# ============================================================================

# Cache global pour les regex compilées (amélioration performance)
_regex_cache = {}

def get_compiled_pattern(pattern_str, flags=re.IGNORECASE):
    """
    Cache les regex compilées pour éviter la recompilation.
    Améliore les performances de 30-40% en évitant de recompiler les mêmes patterns.
    """
    cache_key = (pattern_str, flags)
    if cache_key not in _regex_cache:
        _regex_cache[cache_key] = re.compile(pattern_str, flags)
    return _regex_cache[cache_key]


def deduplicate_matches(matches):
    """
    Groupe les matches identiques ensemble pour éviter la redondance.
    Retourne une liste de matches uniques avec leurs occurrences.
    
    Args:
        matches: Liste de dictionnaires contenant les matches
        
    Returns:
        Liste de matches dédupliqués avec compteur d'occurrences
    """
    if not matches:
        return []
    
    unique_matches = {}
    
    for match in matches:
        # Clé unique basée sur le texte matché et le type
        key = (match.get('matched_text', ''), match.get('type', ''))
        
        if key not in unique_matches:
            unique_matches[key] = {
                'matched_text': match.get('matched_text', ''),
                'type': match.get('type', ''),
                'occurrences': []
            }
        
        # Ajouter cette occurrence
        unique_matches[key]['occurrences'].append({
            'cookie_name': match.get('cookie_name', ''),
            'cookie_index': match.get('cookie_index', 0),
            'position': match.get('match_position', {}),
            'confidence': match.get('confidence', 1.0)
        })
    
    # Convertir en liste et ajouter le compteur + confiance moyenne
    result = []
    for match_data in unique_matches.values():
        match_data['occurrence_count'] = len(match_data['occurrences'])
        # Calculer la confiance moyenne
        confidences = [occ.get('confidence', 1.0) for occ in match_data['occurrences']]
        match_data['avg_confidence'] = sum(confidences) / len(confidences) if confidences else 0.0
        result.append(match_data)
    
    return result


def calculate_match_confidence(match_type, matched_text, cookie_name, key):
    """
    Calcule un score de confiance entre 0.0 et 1.0 pour un match.
    
    Args:
        match_type: Type de match ('exact' ou 'variant')
        matched_text: Texte qui a matché
        cookie_name: Nom du cookie
        key: Clé de l'information personnelle (email, name, etc.)
        
    Returns:
        Score de confiance entre 0.0 et 1.0
    """
    confidence = 1.0
    
    # 1. Type de match
    if match_type == 'exact':
        confidence = 1.0
    elif match_type == 'variant':
        confidence = 0.7
    else:
        confidence = 0.5
    
    # 2. Longueur du texte matché
    text_len = len(matched_text)
    if text_len < 3:
        confidence *= 0.3  # Très court = peu fiable
    elif text_len < 5:
        confidence *= 0.6
    elif text_len > 20:
        confidence *= 1.2  # Long = plus fiable
    
    # 3. Contexte du cookie (nom pertinent)
    if cookie_name and key:
        cookie_lower = cookie_name.lower()
        key_lower = key.lower()
        
        # Bonus si le nom du cookie correspond à la clé
        if key_lower in cookie_lower:
            confidence *= 1.3
        # Bonus pour cookies avec noms pertinents
        elif any(word in cookie_lower for word in ['user', 'profile', 'account', 'session']):
            confidence *= 1.1
    
    # Normaliser entre 0 et 1
    return min(1.0, max(0.0, confidence))


def is_technical_context(val_decoded, match_start, match_end):
    """
    Vérifie si le match est dans un contexte technique (identifiant, token, etc.)
    pour éviter les faux positifs.
    
    Args:
        val_decoded: Valeur complète du cookie
        match_start: Position de début du match
        match_end: Position de fin du match
        
    Returns:
        True si le contexte est technique (à ignorer), False sinon
    """
    # Contexte avant et après (10 caractères)
    context_before = val_decoded[max(0, match_start-10):match_start]
    context_after = val_decoded[match_end:match_end+10]
    
    # Patterns techniques à détecter
    technical_patterns = [
        r'[_\-\.]$',                    # Underscore, tiret, point avant
        r'^[_\-\.]',                    # Underscore, tiret, point après
        r'(token|key|id|hash|uuid)$',  # Mots techniques avant
        r'^(token|key|id|hash|uuid)',  # Mots techniques après
        r'(session|auth|api)$',        # Contexte d'authentification
        r'^(session|auth|api)',
    ]
    
    for pattern in technical_patterns:
        if re.search(pattern, context_before, re.IGNORECASE):
            return True
        if re.search(pattern, context_after, re.IGNORECASE):
            return True
    
    return False

# ============================================================================
# FIN DES FONCTIONS UTILITAIRES PARTAGÉES
# ============================================================================





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


def is_valid_email(email):
    """
    Valide qu'un email est réel et non un faux positif (code JavaScript, etc.).
    
    Args:
        email: String à valider comme email
        
    Returns:
        True si c'est probablement un vrai email, False sinon
    """
    if not email or '@' not in email:
        return False
    
    email_lower = email.lower()
    
    # 1. Filtrer les patterns JavaScript/code communs
    code_patterns = [
        # Patterns JavaScript
        r'@[a-z]+\.(apply|call|bind|prototype|constructor|length|name)',
        r'@[a-z]+\.(push|pop|shift|unshift|slice|splice|concat)',
        r'@[a-z]+\.(map|filter|reduce|foreach|find|some|every)',
        r'@[a-z]+\.(includes|indexof|lastindexof|startswith|endswith)',
        r'@[a-z]+\.(tolowercase|touppercase|trim|split|replace|match)',
        r'@[a-z]+\.(parse|stringify|keys|values|entries|assign)',
        r'@[a-z]+\.(log|warn|error|info|debug|trace)',
        r'@[a-z]+\.(get|set|has|delete|clear|add)',
        r'@[a-z]+\.(then|catch|finally|resolve|reject)',
        r'@[a-z]+\.(register|lookup|factory|module|component)',
        
        # Patterns de fichiers/chemins
        r'@\d+x\.(png|jpg|jpeg|gif|svg|webp|ico)',
        r'@[a-z0-9-]+\.(json|html|css|js|xml|txt)',
        r'@[a-z0-9-]+\.(min|bundle|chunk|vendor)',
        
        # Patterns techniques
        r'@[a-z]{1,2}\.(us|to|ne|cm)$',  # TLDs suspects avec préfixe très court
        r'^\d+@[a-z]\.',  # Commence par chiffres + lettre unique
        r'^[a-z]@[a-z]{1,3}\.',  # Lettre unique @ mot très court
    ]
    
    for pattern in code_patterns:
        if re.search(pattern, email_lower):
            return False
    
    # 2. Vérifier la structure de base
    try:
        username, domain = email_lower.split('@', 1)
    except ValueError:
        return False
    
    # 3. Validation du username
    if not username or len(username) < 1:  # Username vide
        return False
    
    # Filtrer les usernames suspects (1 lettre + chiffres uniquement)
    if len(username) <= 3 and username[0].isalpha() and username[1:].isdigit():
        return False
        
    # Cas spécifique alumni.edu (souvent des faux positifs avec usernames courts)
    if domain == 'alumni.edu' and len(username) <= 2:
        return False
    
    # 4. Validation du domaine
    if '.' not in domain:  # Pas de TLD
        return False
    
    domain_parts = domain.split('.')
    if len(domain_parts) < 2:
        return False
    
    domain_name = domain_parts[0]
    tld = domain_parts[-1]
    
    # Domaine trop court (sauf exceptions connues)
    if len(domain_name) < 2:
        return False
    
    # 5. Validation du TLD
    # TLDs valides communs (liste non exhaustive mais couvre 99% des cas)
    valid_tlds = {
        # TLDs génériques
        'com', 'org', 'net', 'edu', 'gov', 'mil', 'int',
        'info', 'biz', 'name', 'pro', 'museum', 'coop', 'aero',
        'xxx', 'jobs', 'mobi', 'tel', 'travel', 'cat', 'asia',
        'post', 'geo',
        
        # TLDs nouveaux
        'app', 'dev', 'web', 'site', 'online', 'store', 'shop',
        'blog', 'news', 'media', 'tech', 'digital', 'cloud',
        'email', 'work', 'live', 'studio', 'agency', 'company',
        
        # TLDs pays (sélection des plus courants)
        'fr', 'uk', 'de', 'it', 'es', 'nl', 'be', 'ch', 'at',
        'us', 'ca', 'mx', 'br', 'ar', 'cl', 'co', 'pe',
        'cn', 'jp', 'kr', 'in', 'au', 'nz', 'sg', 'hk',
        'ru', 'pl', 'cz', 'se', 'no', 'dk', 'fi',
        'za', 'eg', 'ng', 'ke', 'ma', 'tn',
        'ae', 'sa', 'il', 'tr', 'ir', 'pk',
        'cm', 'ci', 'sn', 'ml', 'bf', 'bj',
        
        # TLDs composés courants
        'co.uk', 'co.jp', 'co.kr', 'co.nz', 'co.za',
        'com.au', 'com.br', 'com.mx', 'com.ar',
        'ac.uk', 'gov.uk', 'org.uk',
    }
    
    # Vérifier le TLD (ou les 2 dernières parties pour TLDs composés)
    tld_to_check = tld
    if len(domain_parts) >= 3:
        # Vérifier aussi le TLD composé (ex: co.uk)
        composite_tld = f"{domain_parts[-2]}.{domain_parts[-1]}"
        if composite_tld in valid_tlds:
            tld_to_check = composite_tld
    
    if tld_to_check not in valid_tlds:
        # TLD non reconnu, mais on accepte si >= 3 caractères (pour les nouveaux TLDs)
        if len(tld) < 2 or len(tld) > 6:
            return False
    
    # 6. Filtrer les mots réservés JavaScript dans le domaine
    js_reserved_words = {
        'apply', 'call', 'bind', 'prototype', 'constructor',
        'function', 'object', 'array', 'string', 'number',
        'boolean', 'undefined', 'null', 'this', 'super',
        'class', 'extends', 'static', 'async', 'await',
        'return', 'yield', 'import', 'export', 'default',
        'console', 'window', 'document', 'navigator',
        'tolowercase', 'touppercase', 'escaperegexp',
        'foreignapi', 'registry', 'factory', 'drawline'
    }
    
    if domain_name in js_reserved_words:
        return False
    
    # 7. Filtrer les patterns de fichiers images (domaine ou extension)
    image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico', 'bmp'}
    if tld in image_extensions:
        return False
        
    if re.search(r'\d+[a-z]*@\d+x?\.(png|jpg|jpeg|gif|svg)', email_lower):
        return False
    
    # 8. Filtrer les IDs WhatsApp/Telegram (chiffres@c.us, chiffres@g.us)
    if re.match(r'^\d+@[a-z]\.us$', email_lower):
        return False
    
    # 9. Filtrer les emails Sentry/tracking (longue chaîne alphanumérique)
    if 'sentry.io' in domain or 'ingest' in domain:
        # Accepte hex ou alphanumérique long (32+ chars)
        if len(username) >= 32:
            return False
    
    # 10. Vérifier que le username contient au moins une lettre
    if not any(c.isalpha() for c in username):
        return False
        
    # 11. Filtrer les TLDs suspects ou inconnus de 3 lettres qui ne sont pas dans la liste
    # Si le TLD n'est pas dans notre liste valid_tlds et fait 3 lettres (souvent des extensions de fichiers ou typos), on rejette
    # Sauf si c'est un TLD composé connu
    if len(tld) == 3 and tld not in valid_tlds and tld_to_check not in valid_tlds:
        # Liste blanche pour quelques TLDs de 3 lettres qui pourraient manquer
        extra_tlds = {'xyz', 'top', 'pro', 'biz', 'cat', 'edu', 'gov', 'mil', 'net', 'org', 'int', 'pub', 'red', 'run'}
        if tld not in extra_tlds:
            return False

    # 12. Filtrer les domaines suspects courts (ex: siotw.ne)
    if len(domain_name) <= 5 and len(tld) == 2 and tld not in {'fr', 'uk', 'de', 'it', 'es', 'us', 'ca', 'eu', 'io', 'co', 'ai'}:
        # Heuristique : domaine court + TLD 2 lettres rare = souvent suspect (généré)
        # On garde les TLDs majeurs
        return False

    # Si tous les tests passent, c'est probablement un vrai email
    return True


    # Si tous les tests passent, c'est probablement un vrai email
    return True

def decode_token(token, token_type, depth=0):
    """
    Tente de décoder un token (Base64 ou JWT) pour révéler son contenu.
    Supporte le décodage récursif et l'URL-safe Base64.
    """
    if depth > 2: # Éviter les boucles infinies
        return token

    try:
        if token_type == 'jwt_token':
            parts = token.split('.')
            if len(parts) >= 2:
                payload = parts[1]
                # Fix padding
                payload += '=' * (-len(payload) % 4)
                try:
                    decoded_bytes = base64.urlsafe_b64decode(payload)
                    decoded_str = decoded_bytes.decode('utf-8')
                    try:
                        decoded = json.loads(decoded_str)
                        return json.dumps(decoded, indent=2)
                    except json.JSONDecodeError:
                        return decoded_str
                except Exception:
                    pass
        
        elif token_type == 'base64_data':
            # Essayer d'abord URL-safe (couvre aussi standard avec -_)
            # Fix padding
            token_padded = token + '=' * (-len(token) % 4)
            
            try:
                decoded_bytes = base64.urlsafe_b64decode(token_padded)
            except Exception:
                try:
                    decoded_bytes = base64.b64decode(token_padded, validate=True)
                except Exception:
                    return None

            # Try to decode as UTF-8
            try:
                decoded_str = decoded_bytes.decode('utf-8', errors='ignore') # Ignore errors to get partial strings
                
                # Heuristic: check if it looks like meaningful text OR another base64 string
                # 1. Is it another Base64 string? (Recursive check)
                if len(decoded_str) > 20 and re.match(r'^[A-Za-z0-9\-_+/=]+$', decoded_str.strip()):
                     # Recursive call
                     recursive_result = decode_token(decoded_str.strip(), 'base64_data', depth + 1)
                     if recursive_result and recursive_result != decoded_str:
                         return recursive_result

                # 2. Is it JSON?
                try:
                    decoded_json = json.loads(decoded_str)
                    return json.dumps(decoded_json, indent=2)
                except json.JSONDecodeError:
                    pass
                
                # 3. Is it printable text with low entropy (not random noise)?
                # Filter out strings with too many control characters or non-printable
                printable_chars = [c for c in decoded_str if c.isprintable() or c in '\n\r\t']
                if not printable_chars:
                    return None
                    
                printable_ratio = len(printable_chars) / len(decoded_str)
                
                # Stricter check: require high percentage of printable chars
                if len(decoded_str) > 0 and printable_ratio > 0.85: 
                    # Additional check: avoid "garbage" that is technically printable but meaningless
                    # e.g. lots of special chars
                    alnum_count = sum(1 for c in decoded_str if c.isalnum() or c.isspace())
                    if alnum_count / len(decoded_str) > 0.7:
                        return decoded_str
                    
            except Exception:
                pass
                
    except Exception:
        pass
        
    return None

def search_personal_info_in_decoded(decoded_value, personal_info):
    """
    Recherche les informations personnelles dans une valeur décodée.
    
    Args:
        decoded_value: Valeur décodée (string)
        personal_info: Dictionnaire des informations personnelles
        
    Returns:
        Liste de dictionnaires contenant les matches trouvés
    """
    matches = []
    
    if not decoded_value or not personal_info:
        return matches
    
    # Convertir en minuscules pour la recherche
    decoded_lower = str(decoded_value).lower()
    
    # Rechercher chaque type d'information personnelle
    for key, value in personal_info.items():
        if not value:
            continue
            
        # Gérer les listes de valeurs
        values_to_search = []
        if isinstance(value, list):
            values_to_search = [str(v) for v in value if v]
        else:
            values_to_search = [str(value)]
        
        # Rechercher chaque valeur
        for search_value in values_to_search:
            if not search_value.strip():
                continue
                
            # Recherche insensible à la casse
            if search_value.lower() in decoded_lower:
                matches.append({
                    'info_type': key,
                    'matched_value': search_value,
                    'found_in_decoded': True
                })
    
    return matches

def detect_suspicious_tokens(value, cookie_name, personal_info=None):
    """
    Fonction unifiée qui détecte à la fois :
    - Les tokens, clés et patterns suspects
    - La collecte d'historiques de navigation
    - Les informations personnelles dans les tokens décodés
    
    Args:
        value: Valeur à analyser (contenu du cookie, localStorage, etc.)
        cookie_name: Nom du cookie/clé (peut être None)
        personal_info: Dictionnaire des informations personnelles à rechercher (optionnel)
    """
    suspicious_items = []
    
    # ========== DÉTECTION DE TOKENS SUSPECTS ==========
    
    # Patterns de tokens/clés suspectes
    token_patterns = {
        'jwt_token': r'eyJ[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]+\.[A-Za-z0-9+/=]+',
        'api_key': r'[A-Za-z0-9]{32,}',
        'session_id': r'[A-Fa-f0-9]{32,}|[A-Za-z0-9_-]{20,}',
        'user_id': r'user[_-]?id[=:](\d+)',
        'device_id': r'device[_-]?id[=:]([a-f0-9-]+)',
        'timezone': r'timezone[=:]([A-Za-z/_]+)',
        'theme': r'theme[=:](dark|light)',
        'user_agent': r'Mozilla/[0-9.]+\s*\([^)]+\)[^"\']*',
        'uuid': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
        'base64_data': r'[A-Za-z0-9+/_-]{20,}={0,2}',
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
            # Si le pattern a des groupes, findall retourne un tuple ou la string du groupe
            if isinstance(match, tuple):
                match = match[0] # On prend le premier groupe capturé
            
            # Gestion spéciale pour les nouveaux types qui peuvent être courts ou longs
            is_short_allowed = pattern_name in ['user_id', 'device_id', 'timezone', 'theme', 'user_agent']
            
            if len(match) >= 8 or (is_short_allowed and len(match) >= 2): 
                
                # Tentative de décodage pour les types pertinents
                decoded_value = None
                personal_info_matches = []
                
                if pattern_name in ['jwt_token', 'base64_data']:
                    decoded_value = decode_token(match, pattern_name)
                    
                    # Recherche d'informations personnelles dans la valeur décodée
                    if decoded_value and personal_info:
                        personal_info_matches = search_personal_info_in_decoded(decoded_value, personal_info)

                suspicious_items.append({
                    'category': 'token_detection',
                    'type': 'token_pattern',
                    'subtype': pattern_name,
                    'length': len(match),
                    'cookie': cookie_name,
                    'decoded_value': decoded_value,
                    'personal_info_matches': personal_info_matches if personal_info_matches else None
                })
    
    # 1.5. Détection d'emails (tous les emails, pas seulement ceux du profil)
    # Utilise une validation robuste pour éviter les faux positifs (code JS, etc.)
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    email_matches = re.findall(email_pattern, value, re.IGNORECASE)
    for email in email_matches:
        # Valider l'email pour filtrer les faux positifs
        if is_valid_email(email):
            suspicious_items.append({
                'category': 'email_detection',
                'type': 'detected_email',
                'email': email.lower(),  # Normaliser en minuscules
                'cookie': cookie_name
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
                    'length': len(cookie_name),
                    'cookie': cookie_name
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
                        'length': len(value),
                        'cookie': cookie_name
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
                'length': len(value),
                'cookie': cookie_name
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
                'length': len(value) if value else 0,
                'detected_in': 'value'
            })
    
    # 6. Analyse des patterns de stockage suspects
    if value:
        for pattern_name, pattern in storage_patterns.items():
            matches = re.findall(pattern, value, re.IGNORECASE)
            if matches:
                for match in matches[:3]:  # Limite à 3 matches
                    suspicious_items.append({
                        'category': 'navigation_collection',
                        'type': 'suspicious_storage_pattern',
                        'subtype': pattern_name,
                        'cookie_name': cookie_name,
                        'length': len(match),
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
                    'length': len(cookie_name),
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
                        'length': len(value),
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
                            'length': len(value),
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
                'length': len(value),
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
                'length': len(value),
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
                'length': len(value),
                'detected_in': 'value'
            })
    
    return suspicious_items



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

def create_generic_variants(value):
    """
    Crée une variante générique (la valeur elle-même)
    """
    if not value or not str(value).strip():
        return []
    return [str(value)]


def get_variants_for_key(key: str, value: Union[str, List]) -> List[str]:
    """
    Génère les variantes appropriées selon le type de clé (nom, email, etc.)
    """
    if not value:
        return []
        
    # S'assurer que value est une string pour les traitements génériques
    if isinstance(value, list):
        value_str = " ".join([str(v) for v in value])
    else:
        value_str = str(value)

    if key in ['name', 'nom', 'prenom', 'surname', 'lastname', 'firstname', 'full_name']:
        return create_name_variants(value_str)
    elif key in ['account_number']:
        return create_account_number_variants(value_str)
    elif key in ['language', 'lang', 'locale', 'langue']:
        return create_language_variants()
    else:
        return create_generic_variants(value_str)

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
