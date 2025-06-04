import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from client.config import SERVER_URL
from client.utils.ui import authorized_post, authorized_get, clear_root, add_language_switcher
from client.translation.translation_func import get_translation

def admin_create_group(root):
    from client.admin_edit_group import admin_edit_group
    from client.admin_view_groups import admin_view_groups

    clear_root(root)
    root.geometry("700x400")
    root.configure(bg="#FFFFFF")

    tk.Label(root, text="➕ " + get_translation("create_group", module="admin_create_group_translation"),
             font=("Roboto", 16, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=20)

    form_frame = tk.Frame(root, bg="#FFFFFF")
    form_frame.pack(pady=10)

    tk.Label(form_frame, text=get_translation("group_name", module="admin_edit_group_translation"), bg="#FFFFFF").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    name_var = tk.StringVar()
    tk.Entry(form_frame, textvariable=name_var, width=30).grid(row=0, column=1, padx=5, pady=5)

    tk.Label(form_frame, text=get_translation("subject", module="admin_create_group_translation"), bg="#FFFFFF").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    subject_var = tk.StringVar()
    tk.Entry(form_frame, textvariable=subject_var, width=30).grid(row=1, column=1, padx=5, pady=5)

    tk.Label(form_frame, text=get_translation("teacher", module="shared_translation"), bg="#FFFFFF").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    teacher_var = tk.StringVar()
    teacher_box = ttk.Combobox(form_frame, textvariable=teacher_var, width=28)
    teacher_box.grid(row=2, column=1, padx=5, pady=5)

    def filter_teachers(event=None):
        typed = teacher_var.get().lower()
        matches = [t for t in teacher_list if typed in t.lower()]
        teacher_box["values"] = matches if matches else [""]

    teacher_box.bind("<KeyRelease>", filter_teachers)

    try:
        response = authorized_get(f"{SERVER_URL}/admin/group-edit-options")
        response.raise_for_status()
        teacher_list = response.json()["teachers"]
        teacher_box["values"] = teacher_list
    except Exception as e:
        messagebox.showerror(get_translation("error_title", module="errors_translation"),
                             f"{get_translation('error_load_teachers', module='admin_create_group_translation')}\n{e}")
        return

    btn_frame = tk.Frame(root, bg="#FFFFFF")
    btn_frame.pack(pady=20)

    def create_group():
        name = name_var.get().strip()
        subject = subject_var.get().strip()
        teacher = teacher_var.get().strip()

        if not name or not subject:
            messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                 get_translation("fill_name_subject", module="admin_create_group_translation"))
            return

        def on_success(group_id):
            root.after(0, lambda: (
                messagebox.showinfo(get_translation("success_title", module="shared_translation"),
                                    get_translation("group_created", module="admin_create_group_translation")),
                admin_edit_group(root, group_id)
            ))

        def on_error(e):
            root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                       f"{get_translation('error_create_group', module='admin_create_group_translation')}\n{e}"))

        threading.Thread(target=lambda: create_group_thread(name, subject, teacher, on_success, on_error)).start()

    def create_group_thread(name, subject, teacher, on_success, on_error):
        try:
            resp = authorized_post(f"{SERVER_URL}/admin/groups", json={
                "name": name,
                "subject": subject,
                "teacher": teacher
            })
            resp.raise_for_status()
            group_id = resp.json()["id"]
            on_success(group_id)
        except Exception as e:
            on_error(e)

    def go_back():
        admin_view_groups(root)

    tk.Button(btn_frame, text=get_translation("create", module="admin_create_group_translation"), command=create_group,
              font=("Roboto", 10), bg="#C8E6C9", relief="flat", width=15).grid(row=0, column=0, padx=10)

    tk.Button(btn_frame, text=get_translation("back", module="shared_translation"), command=go_back,
              font=("Roboto", 10), bg="#E0E0E0", relief="flat", width=15).grid(row=0, column=1, padx=10)

    add_language_switcher(root, lambda: admin_create_group(root))

