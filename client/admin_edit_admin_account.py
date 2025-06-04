import tkinter as tk
from tkinter import messagebox
import threading
from client.utils.ui import authorized_get, authorized_post, clear_root, ScrollFrame, add_language_switcher
from client.config import SERVER_URL
from client.translation.translation_func import get_translation
from utils.ui import authorized_put
def admin_edit_admin_account(root, admin_id):
    from client.admin_view_admin_account import admin_view_admin_account

    clear_root(root)
    scroll = ScrollFrame(root, bg="#FFFFFF")
    scroll.pack(fill="both", expand=True)
    container = scroll.scrollable_frame
    container.configure(bg="#FFFFFF")

    tk.Label(container, text=get_translation("edit", module="shared_translation") + " — " + get_translation("admin", module="shared_translation"),
             font=("Roboto", 16, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=20)

    form_frame = tk.Frame(container, bg="#FFFFFF")
    form_frame.pack(pady=10)

    name_var = tk.StringVar()
    login_var = tk.StringVar()
    password_var = tk.StringVar()

    def create_row(label_text, text_var, show=None):
        row = tk.Frame(form_frame, bg="#FFFFFF")
        row.pack(anchor="w", pady=5)
        tk.Label(row, text=label_text, font=("Roboto", 10, "bold"), bg="#FFFFFF").pack(side="left", padx=5)
        entry = tk.Entry(row, textvariable=text_var, width=30, show=show)
        entry.pack(side="left")

    create_row(get_translation("name", module="shared_translation"), name_var)
    create_row(get_translation("login", module="shared_translation"), login_var)
    create_row(get_translation("password", module="shared_translation"), password_var, show="*")

    def load_admin():
        try:
            response = authorized_get(f"{SERVER_URL}/admin/admins/{admin_id}")
            response.raise_for_status()
            data = response.json()
            name_var.set(data.get("name", ""))
            login_var.set(data.get("login", ""))
        except Exception as e:
            messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                 f"{get_translation('error_load_admin', module='admin_edit_admin_account_translation')}\n{e}")

    def save():
        name = name_var.get().strip()
        login = login_var.get().strip()
        password = password_var.get().strip()

        if not login:
            messagebox.showwarning(get_translation("error_title", module="errors_translation"),
                                   get_translation("fill_all_fields", module="errors_translation"))
            return

        payload = {"name": name, "login": login}
        if password:
            payload["password"] = password

        def task():
            try:
                resp = authorized_put(f"{SERVER_URL}/admin/admins/{admin_id}", json=payload)
                resp.raise_for_status()
                root.after(0, lambda: (
                    messagebox.showinfo(get_translation("success_title", module="admin_edit_admin_account_translation"),
                                        get_translation("admin_updated",
                                                        module="admin_edit_admin_account_translation")),
                    admin_view_admin_account(root, admin_id)
                ))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_update_admin', module='admin_edit_admin_account_translation')}\n{e}"
                ))

        threading.Thread(target=task).start()

    button_frame = tk.Frame(container, bg="#FFFFFF")
    button_frame.pack(pady=20)

    tk.Button(button_frame, text=get_translation("back", module="shared_translation"),
              command=lambda: admin_view_admin_account(root, admin_id), font=("Roboto", 10), bg="#E0E0E0",
              relief="flat", width=15).grid(row=0, column=0, padx=10)

    tk.Button(button_frame, text=get_translation("save", module="shared_translation"), command=save,
              font=("Roboto", 10, "bold"), bg="#1976D2", fg="white", relief="flat", width=15).grid(row=0, column=1,
                                                                                                         padx=10)

    add_language_switcher(root, lambda: admin_edit_admin_account(root, admin_id))

    threading.Thread(target=load_admin).start()