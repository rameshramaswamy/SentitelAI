# sentinel_security/src/core/encryption.py
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from src.config import settings

class TenantKeyManager:
    def __init__(self):
        # The Master Key (KEK) wraps the Tenant Keys (DEK)
        # Fernet guarantees that the DEK cannot be modified or read without KEK
        try:
            self.kek = Fernet(settings.MASTER_KEY.encode())
        except Exception as e:
            raise ValueError(f"Invalid MASTER_KEY: {e}")

    def generate_tenant_key(self) -> dict:
        """
        Creates a new random AES-256 key for a tenant.
        Returns:
            {
                'dek_raw': bytes (The key used in memory to encrypt data),
                'dek_encrypted': str (The blob to save in Postgres)
            }
        """
        # 1. Generate 32 bytes (256 bits) random key
        dek_raw = AESGCM.generate_key(bit_length=256)
        
        # 2. Encrypt this key using the Master Key
        dek_encrypted_bytes = self.kek.encrypt(dek_raw)
        
        return {
            "dek_raw": dek_raw,
            "dek_encrypted": base64.urlsafe_b64encode(dek_encrypted_bytes).decode()
        }

    def unwrap_tenant_key(self, dek_encrypted_str: str) -> bytes:
        """
        Decrypts the stored tenant key using the Master Key.
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(dek_encrypted_str)
            dek_raw = self.kek.decrypt(encrypted_bytes)
            return dek_raw
        except Exception:
            raise ValueError("Failed to decrypt Tenant Key. Master Key mismatch or data corruption.")

class DataEncryptor:
    def __init__(self, tenant_dek: bytes):
        """
        Initialized with the specific Tenant's Raw DEK.
        """
        self.aesgcm = AESGCM(tenant_dek)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        
        # AES-GCM requires a unique Nonce (IV) for every encryption
        nonce = os.urandom(12)
        data = plaintext.encode("utf-8")
        
        # Encrypt
        ciphertext = self.aesgcm.encrypt(nonce, data, None)
        
        # We must store Nonce + Ciphertext together
        # Format: base64(nonce + ciphertext)
        combined = nonce + ciphertext
        return base64.urlsafe_b64encode(combined).decode("utf-8")

    def decrypt(self, blob: str) -> str:
        if not blob:
            return ""
            
        try:
            combined = base64.urlsafe_b64decode(blob)
            
            # Extract Nonce (first 12 bytes)
            nonce = combined[:12]
            ciphertext = combined[12:]
            
            # Decrypt
            plaintext_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext_bytes.decode("utf-8")
        except Exception:
            raise ValueError("Decryption failed. Invalid Key or Corrupt Data.")