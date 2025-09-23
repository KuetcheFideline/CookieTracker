
import re
import urllib.parse
import math
import base64
import json
from typing import Dict, List, Union, Any




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
    """Détecte les tokens, clés et patterns suspects"""
    suspicious_items = []
    
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
    
    # Noms de cookies/clés suspects
    suspicious_keys = [
        'token', 'auth', 'session', 'user', 'login', 'account', 'profile',
        'email', 'name', 'phone', 'address', 'location', 'geo', 'lat', 'lng',
        'birth', 'age', 'gender', 'password', 'pwd', 'secret', 'key', 'id',
        'tracking', 'analytics', 'fingerprint', 'device', 'browser', 'ip'
    ]
    
    # 1. Analyse des patterns
    for pattern_name, pattern in token_patterns.items():
        matches = re.findall(pattern, value, re.IGNORECASE)
        for match in matches:
            if len(match) >= 8: 
                entropy = calculate_entropy(match)
                suspicious_items.append({
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
                    'type': 'high_entropy',
                    'subtype': 'random_string',
                    'entropy': entropy,
                    'length': len(segment),
                    'cookie': cookie_name,
                    'risk_score': min(10, entropy * 1.5)
                })
    
    # 3. Analyse du nom du cookie
    if cookie_name:
        cookie_lower = cookie_name.lower()
        for suspicious_key in suspicious_keys:
            if suspicious_key in cookie_lower:
                suspicious_items.append({
                    'type': 'suspicious_key',
                    'subtype': suspicious_key,
                    'entropy': calculate_entropy(cookie_name),
                    'length': len(cookie_name),
                    'cookie': cookie_name,
                    'risk_score': 7 if suspicious_key in ['password', 'secret', 'token'] else 5
                })
                break
    
    # 4. Détection de données JSON encodées
    try:
        # Tentative de décoder base64
        if len(value) > 10 and '=' in value[-3:]:
            try:
                decoded = base64.b64decode(value).decode('utf-8')
                if decoded.startswith('{') or decoded.startswith('['):
                    json_data = json.loads(decoded)
                    suspicious_items.append({
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
                'type': 'json_data',
                'subtype': 'direct_json',
                'entropy': calculate_entropy(value),
                'length': len(value),
                'cookie': cookie_name,
                'risk_score': 6
            })
    except:
        pass
    
    return suspicious_items


# AJOUT: Amélioration des fonctions de variants pour gérer les valeurs vides
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


def create_email_variants(email):
    if not email or not str(email).strip():  # AJOUT: Vérification valeur vide
        return []
        
    variants = [email.lower()]
    
    if '@' in email:
        username, domain = email.lower().split('@', 1)
        if username:  # AJOUT: Vérifier que le username n'est pas vide
            variants.extend([
                username,  
                f"{username}@",  
                f"{username}@gmail.com",
                f"{username}@hotmail.com", 
                f"{username}@yahoo.com",
                f"{username}@outlook.com"
            ])
    
    return [v for v in variants if v and v.strip()]  # AJOUT: Filtrer les variants vides


def create_phone_variants(phone):
    if not phone or not str(phone).strip():  # AJOUT: Vérification valeur vide
        return []
        
    digits_only = re.sub(r'\D', '', phone)
    if not digits_only:  # AJOUT: Si aucun chiffre trouvé
        return []
        
    variants = [phone, digits_only]
    
    if len(digits_only) >= 10:
        variants.extend([
            f"{digits_only[:2]} {digits_only[2:4]} {digits_only[4:6]} {digits_only[6:8]} {digits_only[8:]}",
            f"{digits_only[:2]}-{digits_only[2:4]}-{digits_only[4:6]}-{digits_only[6:8]}-{digits_only[8:]}",
            f"{digits_only[:2]}.{digits_only[2:4]}.{digits_only[4:6]}.{digits_only[6:8]}.{digits_only[8:]}",
            f"+33{digits_only[1:]}" if digits_only.startswith('0') else f"+33{digits_only}",
            digits_only[1:] if digits_only.startswith('0') else digits_only 
        ])
    
    return [v for v in set(variants) if v and v.strip()]  # AJOUT: Filtrer les variants vides


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
    return [v for v in set(variants) if v and v.strip()]  # AJOUT: Filtrer les variants vides
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
    else:
        return create_generic_variants(value_str)
