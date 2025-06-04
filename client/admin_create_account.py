import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, base64, requests

from client.config import SERVER_URL
from client.utils.ui import (
    clear_root, authorized_post, hash_password,
    add_language_switcher
)

from client.admin_view_student_account import admin_view_student_account
from client.admin_view_teacher_account import admin_view_teacher_account
from client.admin_view_admin_account import admin_view_admin_account

from client.translation.translation_func import (
    get_translation, set_language, get_current_language
)

def admin_create_account(root):
    clear_root(root)
    root.geometry("600x700")
    root.configure(bg="#FFFFFF")
    root.title(get_translation("create_title", module="admin_create_account_translation"))

    tk.Label(root, text=get_translation("create_title", module="admin_create_account_translation"),
             font=("Roboto", 20, "bold"), fg="#1976D2", bg="#FFFFFF").pack(pady=20)

    top_frame = tk.Frame(root, bg="#FFFFFF")
    top_frame.pack(pady=10)
    tk.Label(top_frame, text=get_translation("role", module="admin_create_account_translation"),
             font=("Roboto", 12), bg="#FFFFFF").grid(row=0, column=0, padx=10)

    account_type = tk.StringVar(value="student")
    roles = ["student", "teacher", "admin"]
    ttk.OptionMenu(top_frame, account_type, roles[0], *roles).grid(row=0, column=1, padx=10)

    form_frame = tk.Frame(root, bg="#FFFFFF")
    form_frame.pack(pady=10)
    form_vars = {}
    photo_data = [None]

    def upload_photo():
        filepath = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png")])
        if filepath:
            with open(filepath, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                photo_data[0] = encoded
                photo_label.config(text=get_translation("photo_uploaded", module="admin_create_account_translation"))

    def build_form():
        for widget in form_frame.winfo_children():
            widget.destroy()
        form_vars.clear()

        fields = []
        role = account_type.get()

        if role != "admin":
            fields.append(("name", get_translation("name", module="admin_create_account_translation")))
        fields.append(("login", get_translation("login", module="admin_create_account_translation")))
        fields.append(("password", get_translation("password", module="admin_create_account_translation")))

        if role == "student":
            fields.append(("class", get_translation("class", module="admin_create_account_translation")))

        if role in ("student", "teacher"):
            fields.append(("email", get_translation("email", module="admin_create_account_translation")))
            fields.append(("phone", get_translation("phone", module="admin_create_account_translation")))

        for i, (key, label_text) in enumerate(fields):
            tk.Label(form_frame, text=label_text, bg="#FFFFFF").grid(row=i, column=0, sticky="e", padx=5, pady=2)
            var = tk.StringVar()
            ent = tk.Entry(form_frame, textvariable=var, show="*" if key == "password" else "")
            ent.grid(row=i, column=1, pady=2, padx=5)
            form_vars[key] = var

        if role in ("student", "teacher"):
            tk.Label(form_frame, text=get_translation("photo", module="admin_create_account_translation"),
                     bg="#FFFFFF").grid(columnspan=2, pady=(10, 2))
            tk.Button(form_frame, text=get_translation("upload_photo", module="admin_create_account_translation"),
                      command=upload_photo).grid(columnspan=2)
            nonlocal photo_label
            photo_label = tk.Label(form_frame, bg="#FFFFFF")
            photo_label.grid(columnspan=2)

    account_type.trace_add("write", lambda *_: build_form())
    photo_label = tk.Label(form_frame, bg="#FFFFFF")
    build_form()

    def submit():
        role = account_type.get()
        data = {k: v.get().strip() for k, v in form_vars.items()}
        if not data.get("login") or not data.get("password") or (role != "admin" and not data.get("name")):
            messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                 get_translation("fill_all_fields", module="errors_translation"))
            return

        data["password"] = hash_password(data["password"])
        if photo_data[0]:
            data["photo"] = photo_data[0]

        def worker():
            try:
                res = authorized_post(f"{SERVER_URL}/admin/{role}s", json=data)
                res.raise_for_status()
                created_id = res.json().get("id")
                def go_to_account():
                    messagebox.showinfo(get_translation("success_title", module="admin_create_account_translation"),
                                        get_translation("account_created", module="admin_create_account_translation").format(role=role))
                    if role == "student":
                        admin_view_student_account(root, created_id)
                    elif role == "teacher":
                        admin_view_teacher_account(root, created_id)
                    else:
                        admin_view_admin_account(root, created_id)
                root.after(0, go_to_account)
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_create_account', module='admin_create_account_translation')}\n{e}"))
        threading.Thread(target=worker, daemon=True).start()

    def cancel():
        from client.admin_main_page import admin_main_page
        admin_main_page(root)

    btn_frame = tk.Frame(root, bg="#FFFFFF")
    btn_frame.pack(pady=15)
    tk.Button(btn_frame, text=get_translation("submit", module="admin_create_account_translation"),
              command=submit, bg="#1976D2", fg="white", font=("Roboto", 11, "bold"),
              relief="flat", padx=10, pady=5).grid(row=0, column=0, padx=10)

    tk.Button(btn_frame, text=get_translation("back", module="admin_create_account_translation"),
              command=cancel, bg="#E0E0E0", font=("Roboto", 11),
              relief="flat", padx=10, pady=5).grid(row=0, column=1, padx=10)

    build_form()
    add_language_switcher(root, lambda: admin_create_account(root))
