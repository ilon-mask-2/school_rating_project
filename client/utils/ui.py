# utils/ui.py
import tkinter as tk
from tkinter import ttk
import hashlib
from client import config
import requests
from tkinter import Frame, Button
from client.config import jwt_token

from client.translation.translation_func import set_language, get_current_language, get_translation

def switch_language(lang, reload_func):
    if get_current_language() != lang:
        set_language(lang)
        reload_func()

def restart_app(current_root):
    from client.login_page import show_login_page
    current_root.destroy()  # Закрываем текущее окно
    show_login_page()

def clear_root(root):
    for widget in root.winfo_children():
        widget.destroy()


def add_language_switcher(parent, reload_func):
    frame = tk.Frame(parent, bg="#FFFFFF")
    frame.pack(pady=10)
    for code, label in [("ru", "🌐 Русский"), ("en", "🌐 English"), ("he", "🌐 עברית")]:
        is_selected = get_current_language() == code
        tk.Button(
            frame, text=label,
            font=("Roboto", 10),
            bg="#B0BEC5" if is_selected else "#E0E0E0",
            fg="white" if is_selected else "black",
            state="disabled" if is_selected else "normal",
            relief="flat", bd=0,
            command=lambda c=code: switch_language(c, reload_func)
        ).pack(side="left", padx=8)

def authorized_put(url, json=None):
    headers = {"Authorization": f"Bearer {config.jwt_token}"} if config.jwt_token else {}
    return requests.put(url, json=json, headers=headers)

class ScrollFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        canvas = tk.Canvas(self, bg=kwargs.get("bg", "#FFFFFF"), highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


def wrap_with_scrollframe(parent_frame):
    scroll = ScrollFrame(parent_frame)
    scroll.pack(fill="both", expand=True, padx=10, pady=10)
    return scroll.scrollable_frame

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def date_range_values(dates):
    return ["За всё время"] + dates

def sanitize_date(date_value, is_start=True):
    if date_value == "За всё время" or not date_value:
        return "0000-00-00" if is_start else "9999-12-31"
    return date_value

def update_combobox_dates(combobox, values):
    combobox["values"] = values
    if values:
        combobox.set(values[0])


def authorized_get(url, **kwargs):
    headers = kwargs.pop("headers", {})
    if config.jwt_token:
        headers["Authorization"] = f"Bearer {config.jwt_token}"
    return requests.get(url, headers=headers, **kwargs)

def authorized_post(url, json=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if config.jwt_token:
        headers["Authorization"] = f"Bearer {config.jwt_token}"
    return requests.post(url, json=json, headers=headers, **kwargs)