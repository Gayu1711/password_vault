import tkinter as tk

from ui_screens import MasterPasswordScreen, SetupScreen, MainScreen
from data_manager import save_vault


class PasswordVaultApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Password Vault")
        self.geometry("860x520")
        self.minsize(860, 520)
        self.resizable(True, True)

        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)

        self.key = None
        self.salt = None
        self.entries = []

        from data_manager import vault_exists
        if vault_exists():
            self.show_login_screen()
        else:
            self.show_setup_screen()

    def show_login_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        MasterPasswordScreen(self.container, self).pack(fill="both", expand=True)

    def show_setup_screen(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        SetupScreen(self.container, self).pack(fill="both", expand=True)

    def show_main_screen(self, key, salt, entries):
        self.key = key
        self.salt = salt
        self.entries = entries
        for widget in self.container.winfo_children():
            widget.destroy()
        MainScreen(self.container, self).pack(fill="both", expand=True)

    def save_vault(self):
        if self.key and self.salt is not None:
            save_vault(self.key, self.salt, self.entries)

    def logout(self):
        self.key = None
        self.salt = None
        self.entries = []
        self.show_login_screen()


if __name__ == "__main__":
    app = PasswordVaultApp()
    app.mainloop()
