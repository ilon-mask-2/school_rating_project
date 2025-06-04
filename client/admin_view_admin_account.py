import tkinter as tk
from tkinter import messagebox
import requests
import threading
from client.utils.ui import authorized_post, authorized_get
from client.config import SERVER_URL
from client.utils.ui import clear_root, ScrollFrame, add_language_switcher
from client.translation.translation_func import get_translation

def admin_view_admin_account(root, admin_id):
    from client.admin_view_accounts import admin_view_accounts
    from client.admin_edit_admin_account import admin_edit_admin_account

    clear_root(root)
    scroll = ScrollFrame(root, bg="#FFFFFF")
    scroll.pack(fill="both", expand=True)
    container = scroll.scrollable_frame
    container.configure(bg="#FFFFFF")

    tk.Label(container, text="🛠 " + get_translation("admin", module="shared_translation"),
             font=("Roboto", 16, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=20)

    info_frame = tk.Frame(container, bg="#F5F5F5")
    info_frame.pack(pady=10)

    def display(label_key, value):
        row = tk.Frame(info_frame, bg="#F5F5F5")
        row.pack(anchor="w", pady=4, padx=10, fill="x")
        translated_label = get_translation(label_key, module="shared_translation")
        tk.Label(row, text=f"{translated_label}:", font=("Roboto", 10, "bold"), bg="#F5F5F5").pack(side="left")
        tk.Label(row, text=value, font=("Roboto", 10), bg="#F5F5F5").pack(side="left", padx=5)

    button_frame = tk.Frame(container, bg="#FFFFFF")
    button_frame.pack(pady=30)

    def go_back():
        admin_view_accounts(root)

    def edit_admin():
        admin_edit_admin_account(root, admin_id)

    def delete_admin():
        if not messagebox.askyesno(get_translation("confirm", module="shared_translation"),
                                   get_translation("confirm_delete_admin", module="admin_view_admin_account_translation")):
            return

        def task():
            try:
                requests.delete(f"{SERVER_URL}/admin/admins/{admin_id}")
                root.after(0, lambda: (
                    messagebox.showinfo(get_translation("deleted", module="shared_translation"),
                                        get_translation("admin_deleted", module="admin_view_admin_account_translation")),
                    go_back()
                ))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_delete_admin', module='admin_view_admin_account_translation')}\n{e}"))

        threading.Thread(target=task).start()

    tk.Button(button_frame, text=get_translation("back", module="shared_translation"), command=go_back,
              font=("Roboto", 10), bg="#E0E0E0", relief="flat", width=15).grid(row=0, column=0, padx=10)

    tk.Button(button_frame, text=get_translation("edit", module="shared_translation"), command=edit_admin,
              font=("Roboto", 10), bg="#BBDEFB", relief="flat", width=15).grid(row=0, column=1, padx=10)

    tk.Button(button_frame, text=get_translation("delete", module="shared_translation"), command=delete_admin,
              font=("Roboto", 10), bg="#FFCDD2", relief="flat", width=15).grid(row=0, column=2, padx=10)

    def load_admin_data():
        try:
            response = authorized_get(f"{SERVER_URL}/admin/admins/{admin_id}")
            response.raise_for_status()
            admin = response.json()
            root.after(0, lambda: show_admin_info(admin))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                       f"{get_translation('error_load_admin', module='admin_view_admin_account_translation')}\n{e}"))

    def show_admin_info(admin):
        display("id", admin["id"])
        display("name", admin.get("name", "—"))
        display("login", admin.get("login", "—"))

    threading.Thread(target=load_admin_data).start()

    add_language_switcher(root, lambda: admin_view_admin_account(root, admin_id))

