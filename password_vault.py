import tkinter as tk
import os
import json
import secrets
import string

from tkinter import messagebox, simpledialog
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

DATA_FILE = "vault.enc"
SALT_SIZE = 32
NONCE_SIZE = 12
TAG_SIZE = 16
KEY_SIZE = 32
ITERATIONS = 100_000

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
    ciphertext = aesgcm.encrypt(
        secrets.token_bytes(NONCE_SIZE),
        plaintext.encode("utf-8"),
        None,
    )
    return ciphertext

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
        if any(c.islower() for c in pwd) and any(c.isupper() for c in pwd) and any(c.isdigit() for c in pwd) and any(c in string.punctuation for c in pwd):
            return pwd

class PasswordVaultApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Password Vault")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        self.salt = None
        self.key = None
        self.entries = []
        self._build_master_password_screen()

    def _clear_frame(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def _build_master_password_screen(self):
        self._clear_frame()

        if os.path.exists(DATA_FILE):
            label_text = "Enter Master Password"
        else:
            label_text = "Create Master Password"

        self.mpw_label = tk.Label(self.root, text=label_text, font=("Helvetica", 16, "bold"))
        self.mpw_label.pack(pady=30)

        self.mpw_entry = tk.Entry(self.root, show="*", font=("Helvetica", 14), width=30)
        self.mpw_entry.pack(pady=10)
        self.mpw_entry.bind("<Return>", lambda event: self._handle_master_password())

        self.mpw_button = tk.Button(self.root, text="Submit", font=("Helvetica", 12), command=self._handle_master_password)
        self.mpw_button.pack(pady=15)

    def _handle_master_password(self):
        password = self.mpw_entry.get()
        if not password:
            messagebox.showwarning("Warning", "Password cannot be empty.")
            return

        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "rb") as f:
                    content = f.read()

                self.salt = content[:SALT_SIZE]
                ciphertext = content[SALT_SIZE:]
                self.key = derive_key(password, self.salt)

                decrypted = decrypt_data(self.key, ciphertext)
                self.entries = json.loads(decrypted)
                self._build_main_screen()
            except Exception as e:
                messagebox.showerror("Error", "Incorrect master password or corrupted vault.")
                self.key = None
        else:
            self.salt = secrets.token_bytes(SALT_SIZE)
            self.key = derive_key(password, self.salt)
            self.entries = []
            self._build_main_screen()

    def _save_vault(self):
        plaintext = json.dumps(self.entries)
        encrypted = encrypt_data(self.key, plaintext)
        with open(DATA_FILE, "wb") as f:
            f.write(self.salt + encrypted[NONCE_SIZE:])

    def _build_main_screen(self):
        self._clear_frame()

        self.main_label = tk.Label(self.root, text="Password Vault", font=("Helvetica", 18, "bold"))
        self.main_label.pack(pady=20)

        button_width = 25

        self.create_entry_btn = tk.Button(self.root, text="Create Entry", width=button_width, command=self._create_entry, font=("Helvetica", 12))
        self.create_entry_btn.pack(pady=8)

        self.fetch_entries_btn = tk.Button(self.root, text="Fetch Entries", width=button_width, command=self._fetch_entries, font=("Helvetica", 12))
        self.fetch_entries_btn.pack(pady=8)

        self.delete_entry_btn = tk.Button(self.root, text="Delete Entry", width=button_width, command=self._delete_entry, font=("Helvetica", 12))
        self.delete_entry_btn.pack(pady=8)

        self.recommend_password_btn = tk.Button(self.root, text="Recommend Random Password", width=button_width, command=self._recommend_password, font=("Helvetica", 12))
        self.recommend_password_btn.pack(pady=8)

        self.reset_master_passwd_btn = tk.Button(self.root, text="Reset Master Password", width=button_width, command=self._reset_master_password, font=("Helvetica", 12), fg="red")
        self.reset_master_passwd_btn.pack(pady=8)

        self.logout_btn = tk.Button(self.root, text="Logout", width=button_width, command=self._logout, font=("Helvetica", 12))
        self.logout_btn.pack(pady=8)

    def _create_entry(self):
        self.create_window = tk.Toplevel(self.root)
        self.create_window.title("Create Entry")
        self.create_window.geometry("400x250")
        self.create_window.resizable(False, False)

        tk.Label(self.create_window, text="Site:", font=("Helvetica", 12)).pack(pady=5)
        self.site_entry = tk.Entry(self.create_window, font=("Helvetica", 12), width=30)
        self.site_entry.pack(pady=5)

        tk.Label(self.create_window, text="Username:", font=("Helvetica", 12)).pack(pady=5)
        self.user_entry = tk.Entry(self.create_window, font=("Helvetica", 12), width=30)
        self.user_entry.pack(pady=5)

        tk.Label(self.create_window, text="Password:", font=("Helvetica", 12)).pack(pady=5)
        self.pass_entry = tk.Entry(self.create_window, show="*", font=("Helvetica", 12), width=30)
        self.pass_entry.pack(pady=5)

        tk.Button(self.create_window, text="Save", command=self._save_entry, font=("Helvetica", 12)).pack(pady=15)

    def _save_entry(self):
        site = self.site_entry.get().strip()
        user = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()

        if not site or not user or not password:
            messagebox.showwarning("Warning", "All fields are required.")
            return

        self.entries.append({"Site": site, "Username": user, "Password": password})
        self._save_vault()
        self.create_window.destroy()
        messagebox.showinfo("Success", "Entry saved successfully.")

    def _fetch_entries(self):
        if not self.entries:
            messagebox.showinfo("Info", "No entries found.")
            return

        self.fetch_window = tk.Toplevel(self.root)
        self.fetch_window.title("Entries")
        self.fetch_window.geometry("500x400")
        self.fetch_window.resizable(False, False)

        text_widget = tk.Text(self.fetch_window, wrap=tk.WORD, font=("Helvetica", 12))
        text_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        for i, entry in enumerate(self.entries, 1):
            text_widget.insert(tk.END, f"Entry {i}:\n")
            for key, value in entry.items():
                text_widget.insert(tk.END, f"  {key}: {value}\n")
            text_widget.insert(tk.END, "-" * 40 + "\n")

        text_widget.config(state=tk.DISABLED)

    def _delete_entry(self):
        if not self.entries:
            messagebox.showinfo("Info", "No entries to delete.")
            return

        self.delete_window = tk.Toplevel(self.root)
        self.delete_window.title("Delete Entry")
        self.delete_window.geometry("400x300")
        self.delete_window.resizable(False, False)

        tk.Label(self.delete_window, text="Select entry to delete:", font=("Helvetica", 12)).pack(pady=10)

        self.delete_listbox = tk.Listbox(self.delete_window, font=("Helvetica", 12), width=40)
        self.delete_listbox.pack(pady=10)

        for entry in self.entries:
            self.delete_listbox.insert(tk.END, f"{entry['Site']} - {entry['Username']}")

        tk.Button(self.delete_window, text="Delete", command=self._confirm_delete, font=("Helvetica", 12)).pack(pady=10)

    def _confirm_delete(self):
        selection = self.delete_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an entry.")
            return

        index = selection[0]
        del self.entries[index]
        self._save_vault()
        self.delete_window.destroy()
        messagebox.showinfo("Success", "Entry deleted successfully.")

    def _recommend_password(self):
        password = make_random_password()
        self.recommend_window = tk.Toplevel(self.root)
        self.recommend_window.title("Recommended Password")
        self.recommend_window.geometry("400x150")
        self.recommend_window.resizable(False, False)

        tk.Label(self.recommend_window, text="Your recommended password is:", font=("Helvetica", 12)).pack(pady=10)
        pass_entry = tk.Entry(self.recommend_window, font=("Helvetica", 14), width=30)
        pass_entry.pack(pady=5)
        pass_entry.insert(0, password)
        pass_entry.config(state="readonly")

        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(password)
            self.root.update()
            messagebox.showinfo("Copied", "Password copied to clipboard.")

        tk.Button(self.recommend_window, text="Copy to Clipboard", command=copy_to_clipboard, font=("Helvetica", 12)).pack(pady=10)

    def _reset_master_password(self):
        response = messagebox.askyesno(
            "WARNING",
            "Resetting the master password will WIPE ALL ENTRIES.\n\nThis action cannot be undone.\n\nDo you want to proceed?",
            icon=messagebox.WARNING,
        )
        if response:
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            self.entries = []
            self.salt = None
            self.key = None
            messagebox.showinfo("Success", "Master password reset. All entries have been wiped.")
            self._build_master_password_screen()

    def _logout(self):
        self.key = None
        self.salt = None
        self.entries = []
        self._build_master_password_screen()


if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordVaultApp(root)
    root.mainloop()
