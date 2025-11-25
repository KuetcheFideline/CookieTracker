
import sys
import os
import base64
import json

sys.path.append(os.getcwd())
from treatement.helpers import decode_token, detect_suspicious_tokens

print("=== VÉRIFICATION DU DÉCODAGE DE TOKENS ===")

# 1. Test Base64 Simple
print("\n[TEST 1] Base64 Simple")
original_text = "Ceci est un test de décodage"
encoded = base64.b64encode(original_text.encode('utf-8')).decode('utf-8')
print(f"Encoded: {encoded}")
decoded = decode_token(encoded, 'base64_data')
print(f"Decoded: {decoded}")
assert decoded == original_text

# 2. Test Base64 JSON
print("\n[TEST 2] Base64 JSON")
json_data = {"user_id": 12345, "role": "admin"}
json_str = json.dumps(json_data)
encoded_json = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
print(f"Encoded: {encoded_json}")
decoded_json_res = decode_token(encoded_json, 'base64_data')
print(f"Decoded: {decoded_json_res}")
assert "user_id" in decoded_json_res

# 3. Test JWT (Fake)
print("\n[TEST 3] JWT (Fake)")
header = base64.b64encode('{"alg":"HS256","typ":"JWT"}'.encode('utf-8')).decode('utf-8')
payload = base64.b64encode('{"sub":"1234567890","name":"John Doe","iat":1516239022}'.encode('utf-8')).decode('utf-8')
signature = "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
jwt_token = f"{header}.{payload}.{signature}"
print(f"JWT: {jwt_token}")
decoded_jwt = decode_token(jwt_token, 'jwt_token')
print(f"Decoded Payload: {decoded_jwt}")
assert "John Doe" in decoded_jwt

print("\n=== TOUS LES TESTS SONT PASSÉS ✅ ===")
