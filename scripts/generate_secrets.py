
import base64
import secrets

print(f"JWT_SECRET={secrets.token_urlsafe(48)}")
print(f"ENCRYPTION_KEYS=1:{base64.b64encode(secrets.token_bytes(32)).decode()}")
print(f"HMAC_KEY={secrets.token_urlsafe(48)}")
print(f"DB_PASSWORD={secrets.token_urlsafe(24)}")
print(f"DB_MIGRATION_PASSWORD={secrets.token_urlsafe(24)}")
print(f"ADMIN_PASSWORD={secrets.token_urlsafe(12)}Aa1!")
