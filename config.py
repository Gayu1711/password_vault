import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "vault.enc")
SALT_SIZE = 32
NONCE_SIZE = 12
TAG_SIZE = 16
KEY_SIZE = 32
ITERATIONS = 100_000
