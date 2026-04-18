import tkinter as tk
from tkinter import ttk
import threading
import webbrowser
import time
import subprocess
import sys
import os

def start_flask():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    subprocess.Popen(
        [sys.executable, os.path.join(script_dir, "dashboard.py")],
        creationflags=subprocess.CREATE_NO_WINDOW
    )

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Mój Portfel GPW")
        self.geometry("400x300")
        self.resizable(False, False)
        self.configure(bg="#0f1117")

        # Tytuł
        tk.Label(
            self, text="📈 Mój Portfel GPW",
            font=("Segoe UI", 18, "bold"),
            bg="#0f1117", fg="#ffffff"
        ).pack(pady=(40, 10))

        tk.Label(
            self, text="Panel zarządzania portfelem akcji GPW",
            font=("Segoe UI", 10),
            bg="#0f1117", fg="#666666"
        ).pack(pady=(0, 30))

        # Status
        self.status = tk.Label(
            self, text="⏳ Uruchamianie serwera...",
            font=("Segoe UI", 10),
            bg="#0f1117", fg="#f39c12"
        )
        self.status.pack(pady=(0, 20))

        # Przycisk
        self.btn = tk.Button(
            self, text="Otwórz Dashboard",
            font=("Segoe UI", 11, "bold"),
            bg="#26c281", fg="#000000",
            relief="flat", padx=20, pady=10,
            cursor="hand2",
            command=self.otworz_dashboard,
            state="disabled"
        )
        self.btn.pack(pady=10)

        tk.Label(
            self, text="Dashboard otwiera się w przeglądarce",
            font=("Segoe UI", 8),
            bg="#0f1117", fg="#444444"
        ).pack(pady=(5, 0))

        # Uruchom Flask w tle
        threading.Thread(target=self.uruchom_serwer, daemon=True).start()

    def uruchom_serwer(self):
        start_flask()
        time.sleep(3)
        self.status.config(text="✅ Serwer działa", fg="#26c281")
        self.btn.config(state="normal")

    def otworz_dashboard(self):
        webbrowser.open("http://localhost:5000")

if __name__ == "__main__":
    app = App()
    app.mainloop()