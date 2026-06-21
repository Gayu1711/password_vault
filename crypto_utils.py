import secrets
import string

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

from config import SALT_SIZE, NONCE_SIZE, KEY_SIZE, ITERATIONS


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        salt=salt,
        iterations=ITERATIONS,
        length=KEY_SIZE,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_data(key: bytes, plaintext: str) -> bytes:
    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(NONCE_SIZE)
    ciphertext = aesgcm.encrypt(
        nonce,
        plaintext.encode("utf-8"),
        None,
    )
    return nonce + ciphertext


def decrypt_data(key: bytes, ciphertext: bytes) -> str:
    nonce = ciphertext[:NONCE_SIZE]
    ct = ciphertext[NONCE_SIZE:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ct, None)
    return plaintext.decode("utf-8")


def make_random_password(length=16) -> str:
    alphabet = string.ascii_letters + string.digits + string.punctuation
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd)
                and any(c.isdigit() for c in pwd) and any(c in string.punctuation for c in pwd)):
            return pwd
