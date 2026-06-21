import json
import os

from config import DATA_FILE, SALT_SIZE
from crypto_utils import derive_key, encrypt_data, decrypt_data


def vault_exists() -> bool:
    return os.path.exists(DATA_FILE)


def load_vault(password: str):
    with open(DATA_FILE, "rb") as f:
        content = f.read()

    salt = content[:SALT_SIZE]
    ciphertext = content[SALT_SIZE:]
    key = derive_key(password, salt)

    decrypted = decrypt_data(key, ciphertext)
    entries = json.loads(decrypted)
    return key, salt, entries


def save_vault(key: bytes, salt: bytes, entries: list):
    plaintext = json.dumps(entries)
    encrypted = encrypt_data(key, plaintext)
    with open(DATA_FILE, "wb") as f:
        f.write(salt + encrypted)


def wipe_vault():
    if vault_exists():
        os.remove(DATA_FILE)
