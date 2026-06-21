# 🔐 Password Vault

A secure, offline password manager built with Python and Tkinter. All credentials are encrypted on disk using **AES-256-GCM** authenticated encryption, with the master password never stored anywhere — only a derived key lives in memory during your session.

---

## 📋 Table of Contents

- [Features](#-features)
- [Security Design](#-security-design)
- [Project Structure](#-project-structure)
- [Vault File Format](#-vault-file-format)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the App](#running-the-app)
- [Usage Guide](#-usage-guide)
- [Cryptographic Details](#-cryptographic-details)
- [Configuration](#-configuration)
- [Known Limitations](#-known-limitations)
- [Future Enhancements](#-future-enhancements)
- [License](#-license)

---

## ✨ Features

- 🔒 **AES-256-GCM** authenticated encryption — protects against both data theft and tampering
- 🔑 **PBKDF2-HMAC-SHA256** key derivation (100,000 iterations) — makes brute-force attacks computationally expensive
- 🎲 **Random password generator** — cryptographically secure, enforces character class diversity
- 🖥️ **Tkinter GUI** — clean, cross-platform graphical interface, no browser required
- 📴 **Fully offline** — no network calls, no cloud sync, no telemetry
- 🧹 **Session management** — in-memory key is wiped on logout
- 🔄 **Master password reset** — wipes all data and lets you start fresh

---

## 🔒 Security Design

| Concern | Solution |
|---|---|
| Credential storage | AES-256-GCM encrypted binary file (`vault.enc`) |
| Key derivation | PBKDF2-HMAC-SHA256, 100k iterations, 32-byte salt |
| Randomness | `secrets` module (wraps OS CSPRNG / `os.urandom`) |
| Tamper detection | GCM authentication tag — any modification triggers `InvalidTag` |
| Wrong password detection | Same `InvalidTag` failure — no oracle leakage |
| In-memory exposure | Key nulled out on logout; never written to disk |
| Nonce reuse | Fresh 12-byte nonce generated per save operation |

> **No homegrown crypto.** All primitives come from the [`cryptography`](https://cryptography.io) library's `hazmat` layer.

---

## 📁 Project Structure

```
password-vault/
│
├── main.py             # App controller (tk.Tk subclass), navigation, shared state
├── ui_screens.py       # All Tkinter screens and popup windows
├── crypto_utils.py     # Cryptographic primitives (derive, encrypt, decrypt, generate)
├── data_manager.py     # Disk I/O — read/write/wipe vault.enc
├── config.py           # Global constants (sizes, iteration count, file path)
│
├── vault.enc           # Encrypted vault (auto-created on first run, gitignored)
├── password_vault.py   # Legacy single-file version (kept for reference)
│
└── README.md
```

### Module Responsibilities

```
main.py  ──────────────────────────────────────────────────┐
  │  Owns: self.key, self.salt, self.entries               │
  │  Routes between: Login → Setup → Main                  │
  ▼                                                         │
ui_screens.py  ────────────────────────────────────────┐   │
  │  MasterPasswordScreen  (login)                      │   │
  │  SetupScreen           (first run / after wipe)     │   │
  │  MainScreen            (dashboard)                  │◄──┘
  │  CreateEntryWindow, FetchEntriesWindow,             │
  │  DeleteEntryWindow, RecommendPasswordWindow         │
  ▼                                                     │
data_manager.py  ──────────────────────────────────┐   │
  │  load_vault()   save_vault()   wipe_vault()    │◄──┘
  ▼                                                │
crypto_utils.py  ◄───────────────────────────────┘
     derive_key()   encrypt_data()   decrypt_data()   make_random_password()
```

---

## 🗃️ Vault File Format

`vault.enc` is a raw binary file — not JSON, not Base64. Its byte layout:

```
┌──────────────┬────────────────┬──────────────────────────┬─────────────┐
│  Salt        │  Nonce         │  Ciphertext              │  GCM Tag    │
│  32 bytes    │  12 bytes      │  variable                │  16 bytes   │
└──────────────┴────────────────┴──────────────────────────┴─────────────┘
```

The plaintext that gets encrypted is always a JSON array:

```json
[
  {"Site": "github.com", "Username": "alice", "Password": "s3cr3t!"},
  {"Site": "gmail.com",  "Username": "alice@example.com", "Password": "hunter2"}
]
```

**Reading the file:**
1. Bytes `0–31` → salt (used to re-derive the AES key)
2. Bytes `32+` → encrypted blob, passed to `decrypt_data()`
3. `decrypt_data()` slices bytes `0–11` as the nonce, passes the rest to `AESGCM.decrypt()`

---

## 🚀 Getting Started

### Prerequisites

- Python **3.8+**
- pip

### Installation

```bash
# 1. Clone the repository and then
cd password-vault

# 2. Install the only external dependency
pip install cryptography
```

> `tkinter` ships with the standard Python distribution on Windows and macOS.  
> On Linux you may need: `sudo apt install python3-tk`

### Running the App

```bash
python main.py
```

On first launch, no `vault.enc` exists — you will be prompted to create a master password. On subsequent launches, you will be asked to enter it.

---

## 📖 Usage Guide

### First Run — Create a Master Password

1. Launch the app with `python main.py`.
2. Enter a strong master password and click **Set Password**.
3. The vault is initialised with an empty entries list, encrypted and saved to `vault.enc`.

### Login

1. Enter your master password and press **Enter** or click **Submit**.
2. The password is never stored — it is used to derive the AES key, which is held in memory for the session.
3. An incorrect password triggers `InvalidTag` from the GCM layer, displayed as a generic error.

### Create Entry

Click **Create Entry**, fill in Site, Username, and Password, then click **Save**. The entry is appended to the in-memory list and the vault is re-encrypted and saved immediately.

### Fetch Entries

Click **Fetch Entries** to open a read-only view of all stored credentials.

### Delete Entry

Click **Delete Entry**, select an entry from the list, and click **Delete**. The vault is re-saved after removal.

### Random Password Generator

Click **Recommend Random Password** to generate a 16-character cryptographically secure password. Use **Copy to Clipboard** to copy it. The generated password is guaranteed to contain at least one lowercase letter, one uppercase letter, one digit, and one punctuation character.

### Logout

Click **Logout** to wipe the in-memory key and entries, returning to the login screen. The vault file on disk remains intact.

### Reset Master Password ⚠️

Click **Reset Master Password** (shown in red). This action **permanently deletes `vault.enc`** and all stored credentials. It cannot be undone. You will be prompted to confirm before anything is deleted.

### Forgot Password ⚠️

On the login screen, the **Forgot Password? (Wipes all data)** button performs the same destructive wipe as the reset flow above.

---

## 🔬 Cryptographic Details

### Key Derivation — `derive_key(password, salt)`

```python
PBKDF2HMAC(
    algorithm = hashes.SHA256(),
    salt      = salt,           # 32 random bytes, unique per vault
    iterations= 100_000,        # configurable in config.py
    length    = 32,             # 256-bit AES key
)
```

The salt is stored in plaintext alongside the ciphertext — this is intentional. The salt's role is to ensure that two vaults with the same password produce different keys, defeating precomputed (rainbow table) attacks. The secrecy of the key depends entirely on the master password.

### Encryption — `encrypt_data(key, plaintext)`

```python
aesgcm   = AESGCM(key)
nonce    = secrets.token_bytes(12)          # fresh per save
output   = aesgcm.encrypt(nonce, plaintext.encode(), None)
# output = nonce || ciphertext || 16-byte GCM tag
```

A new nonce is generated on every call to `encrypt_data`, so saving the vault twice with the same data produces different ciphertext each time (IND-CPA security).

### Decryption — `decrypt_data(key, blob)`

```python
nonce      = blob[:12]
ciphertext = blob[12:]
plaintext  = AESGCM(key).decrypt(nonce, ciphertext, None)
# Raises InvalidTag if key is wrong or data was tampered with
```

### Random Password — `make_random_password(length=16)`

```python
alphabet = ascii_letters + digits + punctuation   # 94 characters
while True:
    pwd = "".join(secrets.choice(alphabet) for _ in range(length))
    if has_lower and has_upper and has_digit and has_punct:
        return pwd
```

Entropy ≈ log₂(94¹⁶) ≈ **104 bits** before the character-class filter. The filter slightly reduces entropy in theory but guarantees the password satisfies common site requirements.

---

## ⚙️ Configuration

All magic numbers live in `config.py`. Change them here and they propagate everywhere:

```python
SALT_SIZE  = 32        # bytes of random salt
NONCE_SIZE = 12        # bytes for AES-GCM nonce (standard)
TAG_SIZE   = 16        # GCM authentication tag size (informational)
KEY_SIZE   = 32        # 256-bit AES key
ITERATIONS = 100_000   # PBKDF2 rounds — increase for stronger KDF
```

> Changing `ITERATIONS` after a vault is created does not automatically re-encrypt existing vaults. Users would need to reset their master password for the new value to take effect.


---

## 📄 License

This project is released for educational purposes as part of the Secure Software Engineering course (24CS404T).  
Feel free to fork, modify, and learn from it.

---

> Built with Python · AES-256-GCM · PBKDF2-HMAC-SHA256 · Tkinter
