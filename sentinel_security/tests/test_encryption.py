# sentinel_security/tests/test_encryption.py
import pytest
from cryptography.fernet import Fernet
from src.core.encryption import TenantKeyManager, DataEncryptor
from src.config import settings

# Setup a valid master key for testing
settings.MASTER_KEY = Fernet.generate_key().decode()

def test_key_generation():
    km = TenantKeyManager()
    keys = km.generate_tenant_key()
    
    assert keys["dek_raw"] is not None
    assert len(keys["dek_raw"]) == 32 # 256 bits
    assert keys["dek_encrypted"] is not None
    assert isinstance(keys["dek_encrypted"], str)

def test_encryption_decryption_cycle():
    km = TenantKeyManager()
    keys = km.generate_tenant_key()
    
    encryptor = DataEncryptor(keys["dek_raw"])
    
    secret_data = "Sensitive Patient Data"
    encrypted = encryptor.encrypt(secret_data)
    
    assert encrypted != secret_data
    
    decrypted = encryptor.decrypt(encrypted)
    assert decrypted == secret_data

def test_tenant_isolation():
    km = TenantKeyManager()
    
    # Tenant A
    keys_a = km.generate_tenant_key()
    encryptor_a = DataEncryptor(keys_a["dek_raw"])
    data_a = encryptor_a.encrypt("Tenant A Secret")
    
    # Tenant B
    keys_b = km.generate_tenant_key()
    encryptor_b = DataEncryptor(keys_b["dek_raw"])
    
    # Tenant B tries to decrypt Tenant A's data
    with pytest.raises(Exception): # Should fail auth tag check
        encryptor_b.decrypt(data_a)