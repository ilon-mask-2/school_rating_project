import tkinter as tk
import threading
from client.utils.ui import clear_root, restart_app, add_language_switcher
from client.translation.translation_func import (
    get_translation, get_current_language, set_language
)

from client.admin_view_accounts import admin_view_accounts
from client.admin_create_account import admin_create_account
from admin_view_groups import admin_view_groups
from admin_view_rating import admin_view_rating

def admin_main_page(root):
    clear_root(root)
    root.title(f"{get_translation('app_name', module='admin_main_page_translation')} — {get_translation('admin', module='admin_main_page_translation')}")
    root.geometry("550x600")
    root.configure(bg="#FFFFFF")

    # Заголовок
    tk.Label(root, text=get_translation("app_name", module="admin_main_page_translation"),
             font=("Roboto", 24, "bold"), fg="#1976D2", bg="#FFFFFF").pack(pady=(30, 10))

    tk.Label(root, text=get_translation("title", module="admin_main_page_translation"),
             font=("Roboto", 16), fg="#757575", bg="#FFFFFF").pack(pady=(0, 30))

    def threaded_call(func):
        threading.Thread(target=lambda: func(root), daemon=True).start()

    def styled_button(text_key, command):
        return tk.Button(
            root,
            text=get_translation(text_key, module="admin_main_page_translation"),
            font=("Roboto", 14, "bold"),
            bg="#1976D2",
            fg="white",
            activebackground="#63A4FF",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=10,
            command=command
        )

    styled_button("view_accounts", lambda: threaded_call(admin_view_accounts)).pack(pady=5, fill='x', padx=60)
    styled_button("create_account", lambda: threaded_call(admin_create_account)).pack(pady=5, fill='x', padx=60)
    styled_button("view_groups", lambda: threaded_call(admin_view_groups)).pack(pady=5, fill='x', padx=60)
    styled_button("view_ratings", lambda: threaded_call(admin_view_rating)).pack(pady=5, fill='x', padx=60)

    # Переключатели языка через универсальный компонент
    add_language_switcher(root, lambda: admin_main_page(root))

    # Кнопка выхода
    tk.Button(
        root,
        text=get_translation("exit", module="admin_main_page_translation"),
        font=("Roboto", 12),
        bg="#E0E0E0",
        fg="#000000",
        activebackground="#BDBDBD",
        relief="flat",
        bd=0,
        command=lambda: restart_app(root)
    ).pack(pady=30)
