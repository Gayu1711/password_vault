import tkinter as tk
from tkinter import messagebox, ttk

from crypto_utils import make_random_password
from data_manager import load_vault, save_vault, wipe_vault, vault_exists
from vault_logger import log_event, get_logs

# ── Design Tokens ─────────────────────────────────────────────────────────────
BG          = "#0F1117"
SURFACE     = "#1A1D27"
SURFACE2    = "#22263A"
ACCENT      = "#4F8EF7"
ACCENT_HOV  = "#3A7AE4"
DANGER      = "#E05252"
DANGER_HOV  = "#C93D3D"
SUCCESS     = "#3ECF8E"
TEXT        = "#E8EAF0"
TEXT_DIM    = "#8A8FA8"
BORDER      = "#2E3250"
FONT        = "Segoe UI"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _styled_btn(parent, text, command, color=ACCENT, hover=ACCENT_HOV, width=22, fg=BG):
    btn = tk.Button(
        parent, text=text, command=command,
        font=(FONT, 11, "bold"), bg=color, fg=fg,
        activebackground=hover, activeforeground=fg,
        relief="flat", bd=0, cursor="hand2",
        padx=16, pady=10, width=width,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=hover))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def _styled_entry(parent, show=None, width=32):
    return tk.Entry(
        parent,
        font=(FONT, 12), bg=SURFACE2, fg=TEXT,
        insertbackground=ACCENT, relief="flat",
        bd=0, width=width, show=show,
        highlightthickness=1, highlightbackground=BORDER,
        highlightcolor=ACCENT,
    )


def _label(parent, text, size=12, bold=False, color=TEXT, anchor="w"):
    bg = BG
    try:
        bg = parent["bg"]
    except Exception:
        pass
    return tk.Label(
        parent, text=text,
        font=(FONT, size, "bold" if bold else "normal"),
        bg=bg, fg=color, anchor=anchor,
    )


# ── Screens ───────────────────────────────────────────────────────────────────

class MasterPasswordScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)
        self.controller = controller
        self._build()

    def _build(self):
        tk.Frame(self, bg=ACCENT, height=4).pack(fill="x")

        outer = tk.Frame(self, bg=BG)
        outer.pack(expand=True)

        card = tk.Frame(outer, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        card.pack(padx=60, pady=40, ipadx=40, ipady=30)

        tk.Label(card, text="🔐", font=(FONT, 36), bg=SURFACE).pack(pady=(20, 4))
        tk.Label(card, text="Password Vault", font=(FONT, 20, "bold"), bg=SURFACE, fg=TEXT).pack()
        tk.Label(card, text="Enter your master password to unlock", font=(FONT, 10),
                 bg=SURFACE, fg=TEXT_DIM).pack(pady=(2, 20))

        tk.Label(card, text="Master Password", font=(FONT, 10), bg=SURFACE, fg=TEXT_DIM,
                 anchor="w").pack(anchor="w", padx=10)
        self.mpw_entry = _styled_entry(card, show="*")
        self.mpw_entry.pack(padx=10, pady=(4, 16), ipady=8)
        self.mpw_entry.bind("<Return>", lambda e: self._handle_login())
        self.mpw_entry.focus_set()

        _styled_btn(card, "Unlock Vault", self._handle_login).pack(pady=(0, 10))

        if vault_exists():
            fp = tk.Label(card, text="Forgot password? Wipe & reset",
                          font=(FONT, 9), bg=SURFACE, fg=DANGER, cursor="hand2")
            fp.pack(pady=(4, 16))
            fp.bind("<Button-1>", lambda e: self._handle_forgot_password())

    def _handle_login(self):
        password = self.mpw_entry.get()
        if not password:
            messagebox.showwarning("Warning", "Password cannot be empty.")
            return
        if vault_exists():
            try:
                key, salt, entries = load_vault(password)
                log_event("LOGIN_SUCCESS", "Vault unlocked successfully")
                self.controller.show_main_screen(key, salt, entries)
            except Exception:
                log_event("LOGIN_FAILED", "Incorrect password or corrupted vault")
                messagebox.showerror("Error", "Incorrect master password or corrupted vault.")
        else:
            messagebox.showerror("Error", "No vault found. Please create a new vault.")

    def _handle_forgot_password(self):
        if messagebox.askyesno("WARNING",
                "This will WIPE ALL ENTRIES permanently.\nProceed?",
                icon=messagebox.WARNING):
            log_event("VAULT_WIPED", "Forgot-password flow — all entries deleted")
            wipe_vault()
            self.controller.show_setup_screen()


class SetupScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)
        self.controller = controller
        self._build()

    def _build(self):
        tk.Frame(self, bg=SUCCESS, height=4).pack(fill="x")

        outer = tk.Frame(self, bg=BG)
        outer.pack(expand=True)

        card = tk.Frame(outer, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
        card.pack(padx=60, pady=40, ipadx=40, ipady=30)

        tk.Label(card, text="🔑", font=(FONT, 36), bg=SURFACE).pack(pady=(20, 4))
        tk.Label(card, text="Create Your Vault", font=(FONT, 20, "bold"), bg=SURFACE, fg=TEXT).pack()
        tk.Label(card, text="Choose a strong master password. It cannot be recovered.",
                 font=(FONT, 10), bg=SURFACE, fg=TEXT_DIM).pack(pady=(2, 20))

        tk.Label(card, text="New Master Password", font=(FONT, 10), bg=SURFACE,
                 fg=TEXT_DIM, anchor="w").pack(anchor="w", padx=10)
        self.mpw_entry = _styled_entry(card, show="*")
        self.mpw_entry.pack(padx=10, pady=(4, 16), ipady=8)
        self.mpw_entry.bind("<Return>", lambda e: self._handle_setup())
        self.mpw_entry.focus_set()

        _styled_btn(card, "Create Vault", self._handle_setup,
                    color=SUCCESS, hover="#2EBF7A", fg=BG).pack(pady=(0, 20))

    def _handle_setup(self):
        password = self.mpw_entry.get()
        if not password:
            messagebox.showwarning("Warning", "Password cannot be empty.")
            return
        import secrets
        from crypto_utils import derive_key
        salt = secrets.token_bytes(32)
        key = derive_key(password, salt)
        save_vault(key, salt, [])
        log_event("VAULT_CREATED", "New vault initialised")
        self.controller.show_main_screen(key, salt, [])


class MainScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG)
        self.controller = controller
        self._build()

    def _build(self):
        # ── Sidebar
        sidebar = tk.Frame(self, bg=SURFACE, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=ACCENT, height=4).pack(fill="x")
        tk.Label(sidebar, text="🔐", font=(FONT, 28), bg=SURFACE).pack(pady=(24, 2))
        tk.Label(sidebar, text="Vault", font=(FONT, 15, "bold"), bg=SURFACE, fg=TEXT).pack()
        tk.Label(sidebar, text="Password Manager", font=(FONT, 9), bg=SURFACE, fg=TEXT_DIM).pack(pady=(0, 20))
        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=6)

        nav = [
            ("📋  View Entries",       self._fetch_entries),
            ("➕  Create Entry",        self._create_entry),
            ("🗑  Delete Entry",        self._delete_entry),
            ("🎲  Generate Password",   self._recommend_password),
            ("📜  Access Logs",         self._view_logs),
        ]
        for label, cmd in nav:
            b = tk.Button(sidebar, text=label, command=cmd, font=(FONT, 10),
                          bg=SURFACE, fg=TEXT, activebackground=SURFACE2,
                          activeforeground=ACCENT, relief="flat", bd=0,
                          anchor="w", padx=18, pady=10, cursor="hand2")
            b.pack(fill="x")
            b.bind("<Enter>", lambda e, btn=b: btn.config(bg=SURFACE2, fg=ACCENT))
            b.bind("<Leave>", lambda e, btn=b: btn.config(bg=SURFACE, fg=TEXT))

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=16, pady=8)
        _styled_btn(sidebar, "⎋  Logout", self._logout,
                    color=SURFACE2, hover=BORDER, fg=TEXT_DIM, width=18).pack(pady=4, padx=16)
        _styled_btn(sidebar, "⚠  Reset Password", self._reset_master_password,
                    color=SURFACE, hover="#2A1A1A", fg=DANGER, width=18).pack(pady=4, padx=16)

        # ── Content area
        content = tk.Frame(self, bg=BG)
        content.pack(side="left", fill="both", expand=True)

        bar = tk.Frame(content, bg=SURFACE, height=56)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="Dashboard", font=(FONT, 14, "bold"),
                 bg=SURFACE, fg=TEXT).pack(side="left", padx=24, pady=16)

        # Stats strip — 3 cards side by side, text wraps inside each
        stats = tk.Frame(content, bg=BG)
        stats.pack(fill="x", padx=16, pady=(14, 6))
        stats.columnconfigure(0, weight=1)
        stats.columnconfigure(1, weight=1)
        stats.columnconfigure(2, weight=1)

        stat_data = [
            ("📦", str(len(self.controller.entries)), "Stored Entries"),
            ("🔒", "Locked on Exit", "Vault Status"),
            ("🛡", "AES-256-GCM", "Encryption"),
        ]
        for col, (icon, val, lbl) in enumerate(stat_data):
            c = tk.Frame(stats, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
            c.grid(row=0, column=col, sticky="nsew", padx=5, ipady=8)
            tk.Label(c, text=icon, font=(FONT, 16), bg=SURFACE).pack(anchor="w", padx=12, pady=(8,2))
            tk.Label(c, text=val, font=(FONT, 12, "bold"), bg=SURFACE, fg=ACCENT,
                     wraplength=140, justify="left").pack(anchor="w", padx=12)
            tk.Label(c, text=lbl, font=(FONT, 8), bg=SURFACE, fg=TEXT_DIM,
                     wraplength=140, justify="left").pack(anchor="w", padx=12, pady=(0, 8))

        # Action cards — 2-column grid, text wraps properly
        grid = tk.Frame(content, bg=BG)
        grid.pack(fill="both", expand=True, padx=16, pady=6)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        actions = [
            ("📋  View Entries",      "See all saved credentials",    self._fetch_entries,      ACCENT),
            ("➕  Create Entry",      "Store a new credential",        self._create_entry,       SUCCESS),
            ("🗑  Delete Entry",      "Remove a saved credential",     self._delete_entry,       DANGER),
            ("🎲  Generate Password", "Get a strong random password",  self._recommend_password, "#A78BFA"),
            ("📜  Access Logs",       "See vault access history",      self._view_logs,          "#F59E0B"),
        ]
        for i, (title, desc, cmd, color) in enumerate(actions):
            row, col = divmod(i, 2)
            cell = tk.Frame(grid, bg=SURFACE, highlightthickness=1,
                            highlightbackground=BORDER, cursor="hand2")
            cell.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            grid.rowconfigure(row, weight=1)

            tk.Frame(cell, bg=color, height=3).pack(fill="x")
            tk.Label(cell, text=title, font=(FONT, 11, "bold"),
                     bg=SURFACE, fg=TEXT, anchor="w",
                     wraplength=260, justify="left").pack(anchor="w", padx=16, pady=(12, 2))
            tk.Label(cell, text=desc, font=(FONT, 9),
                     bg=SURFACE, fg=TEXT_DIM, anchor="w",
                     wraplength=260, justify="left").pack(anchor="w", padx=16, pady=(0, 12))

            for w in [cell] + list(cell.winfo_children()):
                w.bind("<Button-1>", lambda e, c=cmd: c())
            cell.bind("<Enter>", lambda e, f=cell: f.config(bg=SURFACE2, highlightbackground=ACCENT))
            cell.bind("<Leave>", lambda e, f=cell: f.config(bg=SURFACE, highlightbackground=BORDER))

    def _fetch_entries(self):    FetchEntriesWindow(self, self.controller.entries)
    def _create_entry(self):     CreateEntryWindow(self, self.controller.entries, self.controller.save_vault)
    def _delete_entry(self):     DeleteEntryWindow(self, self.controller.entries, self.controller.save_vault)
    def _recommend_password(self): RecommendPasswordWindow(self)
    def _view_logs(self):        LogsWindow(self)

    def _reset_master_password(self):
        if messagebox.askyesno("WARNING",
                "This will WIPE ALL ENTRIES.\nThis action cannot be undone.\n\nProceed?",
                icon=messagebox.WARNING):
            log_event("MASTER_RESET", "Master password reset — vault wiped")
            wipe_vault()
            self.controller.show_setup_screen()

    def _logout(self):
        log_event("LOGOUT", "Session ended")
        self.controller.logout()


# ── Sub-Windows ───────────────────────────────────────────────────────────────

class _BaseWindow(tk.Toplevel):
    def __init__(self, parent, title, w=480, h=380):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{w}x{h}")
        self.resizable(False, False)
        self.configure(bg=BG)
        tk.Frame(self, bg=ACCENT, height=4).pack(fill="x")


class CreateEntryWindow(_BaseWindow):
    def __init__(self, parent, entries, save_callback):
        super().__init__(parent, "Create Entry", 440, 360)
        self.entries = entries
        self.save_callback = save_callback

        inner = tk.Frame(self, bg=BG)
        inner.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(inner, text="New Credential", font=(FONT, 15, "bold"), bg=BG, fg=TEXT,
                 anchor="w").pack(anchor="w", pady=(0, 16))

        for field, attr, hidden in [
            ("Site / Service", "site_entry", False),
            ("Username / Email", "user_entry", False),
            ("Password", "pass_entry", True),
        ]:
            tk.Label(inner, text=field, font=(FONT, 10), bg=BG, fg=TEXT_DIM,
                     anchor="w").pack(anchor="w")
            e = _styled_entry(inner, show="*" if hidden else None, width=36)
            e.pack(fill="x", pady=(4, 12), ipady=8)
            setattr(self, attr, e)

        self.site_entry.focus_set()
        _styled_btn(inner, "Save Entry", self._save_entry, width=20).pack(pady=(4, 0))

    def _save_entry(self):
        site = self.site_entry.get().strip()
        user = self.user_entry.get().strip()
        pwd  = self.pass_entry.get().strip()
        if not site or not user or not pwd:
            messagebox.showwarning("Warning", "All fields are required.", parent=self)
            return
        self.entries.append({"Site": site, "Username": user, "Password": pwd})
        self.save_callback()
        log_event("ENTRY_CREATED", f"New entry added for: {site}")
        self.destroy()
        messagebox.showinfo("Saved", f"Entry for '{site}' saved successfully.")


class FetchEntriesWindow(_BaseWindow):
    def __init__(self, parent, entries):
        super().__init__(parent, "All Entries", 520, 460)
        log_event("ENTRIES_VIEWED", f"{len(entries)} entries viewed")

        inner = tk.Frame(self, bg=BG)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        tk.Label(inner, text=f"Stored Entries  ({len(entries)})", font=(FONT, 13, "bold"),
                 bg=BG, fg=TEXT, anchor="w").pack(anchor="w", pady=(0, 10))

        if not entries:
            tk.Label(inner, text="No entries yet.\nCreate one from the dashboard.",
                     font=(FONT, 11), bg=BG, fg=TEXT_DIM, justify="center").pack(expand=True)
            return

        canvas = tk.Canvas(inner, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(inner, orient="vertical", command=canvas.yview)
        sf = tk.Frame(canvas, bg=BG)
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        for i, entry in enumerate(entries, 1):
            card = tk.Frame(sf, bg=SURFACE, highlightthickness=1, highlightbackground=BORDER)
            card.pack(fill="x", pady=4, padx=2)

            tk.Label(card, text=f"#{i}  {entry['Site']}", font=(FONT, 11, "bold"),
                     bg=SURFACE, fg=ACCENT, anchor="w").pack(anchor="w", padx=14, pady=(10, 2))

            for k in ("Username", "Password"):
                row = tk.Frame(card, bg=SURFACE)
                row.pack(fill="x", padx=14, pady=2)
                tk.Label(row, text=k + ":", font=(FONT, 9), bg=SURFACE, fg=TEXT_DIM,
                         width=10, anchor="w").pack(side="left")
                val = entry[k]
                display = val if k != "Password" else "•" * len(val)
                lbl = tk.Label(row, text=display, font=(FONT, 10), bg=SURFACE, fg=TEXT, anchor="w")
                lbl.pack(side="left")
                if k == "Password":
                    shown = [False]
                    def toggle(l=lbl, v=val, s=shown):
                        s[0] = not s[0]
                        l.config(text=v if s[0] else "•" * len(v))
                    tk.Button(row, text="👁", font=(FONT, 9), bg=SURFACE, fg=TEXT_DIM,
                              relief="flat", cursor="hand2", command=toggle).pack(side="left", padx=6)
            tk.Frame(card, bg=BG, height=8).pack()


class DeleteEntryWindow(_BaseWindow):
    def __init__(self, parent, entries, save_callback):
        super().__init__(parent, "Delete Entry", 440, 340)
        self.entries = entries
        self.save_callback = save_callback

        inner = tk.Frame(self, bg=BG)
        inner.pack(fill="both", expand=True, padx=24, pady=16)

        tk.Label(inner, text="Delete Entry", font=(FONT, 13, "bold"), bg=BG, fg=TEXT,
                 anchor="w").pack(anchor="w", pady=(0, 10))

        if not entries:
            tk.Label(inner, text="No entries to delete.", font=(FONT, 11),
                     bg=BG, fg=TEXT_DIM).pack(expand=True)
            return

        tk.Label(inner, text="Select an entry to remove:", font=(FONT, 10),
                 bg=BG, fg=TEXT_DIM, anchor="w").pack(anchor="w")

        self.listbox = tk.Listbox(inner, font=(FONT, 11), bg=SURFACE2, fg=TEXT,
                                  selectbackground=DANGER, selectforeground="white",
                                  relief="flat", bd=0, highlightthickness=1,
                                  highlightbackground=BORDER, activestyle="none")
        self.listbox.pack(fill="both", expand=True, pady=10, ipady=4)
        for e in entries:
            self.listbox.insert(tk.END, f"  {e['Site']}  —  {e['Username']}")

        _styled_btn(inner, "Delete Selected", self._confirm_delete,
                    color=DANGER, hover=DANGER_HOV, fg="white", width=20).pack()

    def _confirm_delete(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Please select an entry.", parent=self)
            return
        idx = sel[0]
        site = self.entries[idx]["Site"]
        del self.entries[idx]
        self.save_callback()
        log_event("ENTRY_DELETED", f"Entry deleted: {site}")
        self.destroy()
        messagebox.showinfo("Deleted", f"Entry for '{site}' removed.")


class RecommendPasswordWindow(_BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, "Password Generator", 440, 240)
        self._password = make_random_password()
        log_event("PASSWORD_GENERATED", "Random password generated")

        inner = tk.Frame(self, bg=BG)
        inner.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(inner, text="Generated Password", font=(FONT, 13, "bold"),
                 bg=BG, fg=TEXT, anchor="w").pack(anchor="w", pady=(0, 4))
        tk.Label(inner, text="16 chars · uppercase · lowercase · digit · symbol",
                 font=(FONT, 9), bg=BG, fg=TEXT_DIM, anchor="w").pack(anchor="w", pady=(0, 12))

        pw_frame = tk.Frame(inner, bg=SURFACE, highlightthickness=1, highlightbackground=ACCENT)
        pw_frame.pack(fill="x", pady=(0, 16))
        self.pw_entry = tk.Entry(pw_frame, font=("Courier New", 14), bg=SURFACE, fg=SUCCESS,
                                 relief="flat", bd=0, readonlybackground=SURFACE,
                                 state="readonly")
        self.pw_entry.pack(fill="x", padx=14, pady=12)
        self._set_pw(self._password)

        btn_row = tk.Frame(inner, bg=BG)
        btn_row.pack(fill="x")
        _styled_btn(btn_row, "Copy", self._copy, width=12).pack(side="left")
        _styled_btn(btn_row, "Regenerate", self._regen,
                    color=SURFACE2, hover=BORDER, fg=TEXT, width=14).pack(side="left", padx=10)

    def _set_pw(self, pw):
        self.pw_entry.config(state="normal")
        self.pw_entry.delete(0, tk.END)
        self.pw_entry.insert(0, pw)
        self.pw_entry.config(state="readonly")
        self._password = pw

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self._password)
        self.update()
        messagebox.showinfo("Copied", "Password copied to clipboard.")

    def _regen(self):
        pw = make_random_password()
        log_event("PASSWORD_GENERATED", "Password regenerated")
        self._set_pw(pw)


class LogsWindow(_BaseWindow):
    def __init__(self, parent):
        super().__init__(parent, "Access Logs", 640, 500)

        inner = tk.Frame(self, bg=BG)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        hdr = tk.Frame(inner, bg=BG)
        hdr.pack(fill="x", pady=(0, 10))
        tk.Label(hdr, text="📜  Access Logs", font=(FONT, 14, "bold"),
                 bg=BG, fg=TEXT).pack(side="left")

        def clear_logs():
            import json
            from vault_logger import LOG_FILE
            if messagebox.askyesno("Clear Logs", "Delete all log entries?", parent=self):
                with open(LOG_FILE, "w") as f:
                    json.dump([], f)
                log_event("LOGS_CLEARED", "All logs cleared by user")
                self.destroy()
                LogsWindow(parent)

        _styled_btn(hdr, "Clear Logs", clear_logs,
                    color=SURFACE2, hover=BORDER, fg=DANGER, width=12).pack(side="right")

        # Column header
        col_hdr = tk.Frame(inner, bg=SURFACE2)
        col_hdr.pack(fill="x")
        for txt, w in [("Timestamp", 19), ("Event", 24), ("Detail", 34)]:
            tk.Label(col_hdr, text=txt, font=(FONT, 9, "bold"), bg=SURFACE2,
                     fg=TEXT_DIM, width=w, anchor="w", padx=8, pady=6).pack(side="left")

        # Scrollable rows
        canvas = tk.Canvas(inner, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(inner, orient="vertical", command=canvas.yview)
        rows = tk.Frame(canvas, bg=BG)
        rows.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=rows, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True, pady=4)
        sb.pack(side="right", fill="y")

        logs = list(reversed(get_logs()))

        if not logs:
            tk.Label(rows, text="No log entries yet.", font=(FONT, 11),
                     bg=BG, fg=TEXT_DIM).pack(pady=30)
            return

        event_colors = {
            "LOGIN_SUCCESS": SUCCESS, "LOGIN_FAILED": DANGER,
            "LOGOUT": TEXT_DIM, "ENTRY_CREATED": ACCENT,
            "ENTRY_DELETED": DANGER, "ENTRIES_VIEWED": "#A78BFA",
            "PASSWORD_GENERATED": "#F59E0B", "VAULT_CREATED": SUCCESS,
            "VAULT_WIPED": DANGER, "MASTER_RESET": DANGER,
            "LOGS_CLEARED": TEXT_DIM,
        }

        for i, log in enumerate(logs):
            bg = SURFACE if i % 2 == 0 else BG
            row = tk.Frame(rows, bg=bg)
            row.pack(fill="x")
            color = event_colors.get(log.get("event", ""), TEXT)
            tk.Label(row, text=log.get("timestamp", ""), font=("Courier New", 9),
                     bg=bg, fg=TEXT_DIM, width=19, anchor="w", padx=8, pady=5).pack(side="left")
            tk.Label(row, text=log.get("event", ""), font=(FONT, 9, "bold"),
                     bg=bg, fg=color, width=24, anchor="w", padx=8).pack(side="left")
            tk.Label(row, text=log.get("detail", ""), font=(FONT, 9),
                     bg=bg, fg=TEXT, anchor="w", padx=8).pack(side="left")
