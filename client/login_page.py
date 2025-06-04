import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
from client.config import SERVER_URL
from client.utils.ui import (
    clear_root, add_language_switcher,
    authorized_post, hash_password
)
from client.student_main_page import student_main_page
from client.teacher_main_page import teacher_main_page
from client.admin_main_page import admin_main_page
from client import config
from client.translation.translation_func import current_language, get_translation


def login_action(root, login_entry, password_entry, role_var):
    login = login_entry.get().strip()
    password = password_entry.get().strip()
    role = role_var.get()

    if not login or not password or not role:
        messagebox.showerror(
            get_translation("error_title", module="errors_translation"),
            get_translation("fill_all_fields", module="errors_translation")
        )
        return

    def worker():
        try:
            response = authorized_post(f"{SERVER_URL}/auth/login", json={
                "login": login,
                "password": hash_password(password),
                "role": role
            })
            data = response.json()

            if data.get("status") == "success":
                user_id = data["id"]
                name = data.get("name", "")
                config.jwt_token = data.get("token")

                def go_to_dashboard():
                    messagebox.showinfo(
                        get_translation("success_login", module="errors_translation"),
                        get_translation("welcome_user", module="errors_translation").format(name=name)
                    )
                    if role == "student":
                        student_main_page(root, user_id)
                    elif role == "teacher":
                        teacher_main_page(root, user_id)
                    elif role == "admin":
                        admin_main_page(root)

                root.after(0, go_to_dashboard)
            else:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("login_failed", module="errors_translation"),
                    data.get("message", get_translation("unknown_error", module="errors_translation"))
                ))
        except requests.exceptions.RequestException as e:
            error_message = str(e)
            root.after(0, lambda: messagebox.showerror(
                get_translation("error_connection", module="errors_translation"),
                error_message
            ))
    threading.Thread(target=worker, daemon=True).start()


def show_login_page(root=None):
    if root is None:
        root = tk.Tk()
    else:
        clear_root(root)

    root.title(get_translation("login_title", module="login_page_translation"))
    root.geometry("450x540")
    root.configure(bg="#FFFFFF")

    # ttk стиль
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('TLabel', font=('Roboto', 14), background='#FFFFFF', foreground='#212121')
    style.configure('Header.TLabel', font=('Roboto', 24, 'bold'), foreground='#1976D2', background='#FFFFFF')

    ttk.Label(root, text="🔵 School Ratings", style='Header.TLabel').pack(pady=(30, 5))
    ttk.Label(
        root,
        text=get_translation("login_title", module="login_page_translation"),
        font=('Roboto', 16),
        background="#FFFFFF",
        foreground="#757575"
    ).pack(pady=(0, 15))

    # Основная карточка
    card = tk.Frame(root, bg='white', highlightbackground="#CCCCCC", highlightthickness=1)
    card.pack(pady=10, padx=20, fill='both', expand=False)

    ttk.Label(card, text=get_translation("login", module="login_page_translation")).pack(anchor='w', pady=(20, 0), padx=20)
    entry_login = ttk.Entry(card)
    entry_login.pack(fill='x', pady=5, padx=20, ipady=5)

    ttk.Label(card, text=get_translation("password", module="login_page_translation")).pack(anchor='w', pady=(10, 0), padx=20)
    entry_password = ttk.Entry(card, show='•')
    entry_password.pack(fill='x', pady=5, padx=20, ipady=5)

    ttk.Label(card, text=get_translation("role", module="login_page_translation")).pack(anchor='w', pady=(10, 0), padx=20)
    role_var = tk.StringVar()
    combo_role = ttk.Combobox(card, textvariable=role_var, state="readonly", values=["student", "teacher", "admin"])
    combo_role.current(0)
    combo_role.pack(fill='x', pady=5, padx=20, ipady=2)

    tk.Button(
        card,
        text=get_translation("login_button", module="login_page_translation"),
        font=("Roboto", 14, "bold"),
        bg="#1976D2",
        fg="white",
        activebackground="#63A4FF",
        activeforeground="white",
        relief="flat",
        bd=0,
        padx=10,
        pady=5,
        command=lambda: login_action(root, entry_login, entry_password, role_var)
    ).pack(pady=20, padx=20, fill='x')

    # 🌍 Переключение языка
    add_language_switcher(root, lambda: show_login_page(root))

    root.mainloop()


if __name__ == '__main__':
    show_login_page()

