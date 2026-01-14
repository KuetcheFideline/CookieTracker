
import sys
import base64
import os
sys.path.append(os.getcwd())

from treatement.helpers import decode_token

def test_decode(name, token, token_type):
    print(f"--- Testing {name} ---")
    print(f"Input: {token}")
    print(f"Type: {token_type}")
    result = decode_token(token, token_type)
    print(f"Result: {result}")
    print("-" * 20)
test_decode("Simple Base64", "SGVsbG8gV29ybGQ=", "base64_data")
test_decode("Base64 with padding missing", "SGVsbG8gV29ybGQ", "base64_data")
test_decode("Base64 URL Safe", "SGVsbG8tV29ybGQ", "base64_data")

test_decode("Base64 URL Safe 2", "SGVsbG8-V29ybGQ", "base64_data") 

test_decode("Invalid Base64", "Not a base64 string!!!", "base64_data")

test_decode("JWT Token (fake)", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c", "jwt_token")

test_decode("Short string", "YWJj", "base64_data") # "abc"
s = "AD723fwPmxtRS_DxgUSDfV9FieWkOIuovO72DY2-HqDjpQxQnuA3lt70iMsKNJQyaw1xccQIphddqHYzdEo1cFsJV4L4tc1bSQ3nsommUrElRme61MDGT1PrqN6peyi2hqM8XvwKGEZnoHC-xsm3ib-egkUBQzcF-w"

s_padded = s + "=" * (-len(s) % 4)

decoded = base64.urlsafe_b64decode(s_padded)
print(decoded)
test_decode("Base64 with spaces", "SGVsbG8g V29ybGQ=", "base64_data")
test_decode("Base64 with newlines", "SGVsbG8g\nV29ybGQ=", "base64_data")
