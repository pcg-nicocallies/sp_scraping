import pyotp
import os

totp = pyotp.parse_uri(os.getenv("verra_totp_uri"))

print(totp.now())