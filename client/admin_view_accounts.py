from utils.ui import clear_root, ScrollFrame
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from client.config import SERVER_URL
from client.utils.ui import authorized_post, authorized_get


def admin_view_accounts(root):
    from client.admin_main_page import admin_main_page
    from client.admin_view_student_account import admin_view_student_account
    from client.admin_view_teacher_account import admin_view_teacher_account
    from client.admin_view_admin_account import admin_view_admin_account

    from client.translation.translation_func import get_translation, set_language, get_current_language

    clear_root(root)
    root.geometry("600x700")
    root.configure(bg="#FFFFFF")
    root.title(f"{get_translation('app_name', module='admin_main_page_translation')} — {get_translation('title', module='admin_main_page_translation')}")

    scroll = ScrollFrame(root, bg="#FFFFFF")
    scroll.pack(fill="both", expand=True)
    container = scroll.scrollable_frame
    container.configure(bg="#FFFFFF")

    tk.Label(container, text=get_translation("title", module="admin_view_accounts_translation"),
             font=("Roboto", 20, "bold"), fg="#1976D2", bg="#FFFFFF").pack(pady=20)

    filter_frame = tk.LabelFrame(container, text=get_translation("filters", module="admin_view_accounts_translation"),
                                 bg="#FAFAFA", padx=10, pady=10)
    filter_frame.pack(padx=20, pady=10, fill='x')

    role_var = tk.StringVar(value="All")
    subject_var = tk.StringVar()
    class_var = tk.StringVar()
    group_var = tk.StringVar()
    name_var = tk.StringVar()

    tk.Label(filter_frame, text=get_translation("role", module="admin_view_accounts_translation"), bg="#FAFAFA").grid(row=0, column=0, sticky="w", pady=5)
    role_combo = ttk.Combobox(filter_frame, textvariable=role_var, values=["All", "student", "teacher", "admin"], width=15, state="readonly")
    role_combo.grid(row=0, column=1, sticky="w", padx=5)

    label_subject = tk.Label(filter_frame, text=get_translation("subject", module="admin_view_accounts_translation"), bg="#FAFAFA")
    combo_subject = ttk.Combobox(filter_frame, textvariable=subject_var, width=15, state="readonly")

    label_class = tk.Label(filter_frame, text=get_translation("class", module="admin_view_accounts_translation"), bg="#FAFAFA")
    combo_class = ttk.Combobox(filter_frame, textvariable=class_var, width=10, state="readonly")

    label_group = tk.Label(filter_frame, text=get_translation("group", module="admin_view_accounts_translation"), bg="#FAFAFA")
    combo_group = ttk.Combobox(filter_frame, textvariable=group_var, width=15, state="readonly")

    label_name = tk.Label(filter_frame, text=get_translation("name", module="admin_view_accounts_translation"), bg="#FAFAFA")
    entry_name = tk.Entry(filter_frame, textvariable=name_var, width=20)

    widgets = {
        "subject": [label_subject, combo_subject],
        "class": [label_class, combo_class],
        "group": [label_group, combo_group],
        "name": [label_name, entry_name]
    }

    filters = {
        "subject": subject_var,
        "class": class_var,
        "group": group_var,
        "name": name_var
    }

    def update_filter_fields(*_):
        role = role_var.get()
        for key, elements in widgets.items():
            for widget in elements:
                widget.grid_forget()

        if role == "All" or role == "admin":
            widgets["name"][0].grid(row=1, column=0, sticky="w", pady=5)
            widgets["name"][1].grid(row=1, column=1, sticky="w", padx=5)
        elif role == "student":
            widgets["name"][0].grid(row=1, column=0, sticky="w", pady=5)
            widgets["name"][1].grid(row=1, column=1, sticky="w", padx=5)
            widgets["class"][0].grid(row=0, column=2, sticky="w")
            widgets["class"][1].grid(row=0, column=3, sticky="w", padx=5)
            widgets["group"][0].grid(row=0, column=4, sticky="w")
            widgets["group"][1].grid(row=0, column=5, sticky="w", padx=5)
        elif role == "teacher":
            widgets["name"][0].grid(row=1, column=0, sticky="w", pady=5)
            widgets["name"][1].grid(row=1, column=1, sticky="w", padx=5)
            widgets["subject"][0].grid(row=0, column=2, sticky="w")
            widgets["subject"][1].grid(row=0, column=3, sticky="w", padx=5)
            widgets["group"][0].grid(row=0, column=4, sticky="w")
            widgets["group"][1].grid(row=0, column=5, sticky="w", padx=5)

        for key in filters:
            if key not in widgets:
                filters[key].set("")

    role_var.trace_add("write", update_filter_fields)

    def load_filter_options():
        def task():
            try:
                resp = authorized_get(f"{SERVER_URL}/admin/filter-options")
                resp.raise_for_status()
                filters_data = resp.json()
                root.after(0, lambda: update_filter_values(filters_data))
            except Exception:
                root.after(0, lambda: update_filter_values({}))

        def update_filter_values(filters_data):
            combo_class['values'] = [""] + filters_data.get("classes", [])
            combo_group['values'] = [""] + filters_data.get("groups", [])
            combo_subject['values'] = [""] + filters_data.get("subjects", [])

        threading.Thread(target=task).start()

    def load_accounts():
        def task():
            try:
                role = role_var.get()
                params = {"role": role, "name": name_var.get()}
                if role == "student":
                    params["class"] = class_var.get()
                    params["group"] = group_var.get()
                elif role == "teacher":
                    params["subject"] = subject_var.get()
                    params["group"] = group_var.get()

                response = authorized_get(f"{SERVER_URL}/admin/accounts", params=params)
                response.raise_for_status()
                users = response.json()
                root.after(0, lambda: display_accounts(users))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_connection', module='errors_translation')}:\n{e}"
                ))

        threading.Thread(target=task).start()

    result_frame = tk.Frame(container, bg="#FFFFFF", highlightbackground="#FFFFFF", highlightthickness=0)
    result_frame.pack(fill="both", expand=True, padx=30, pady=10)

    def display_accounts(users):
        for widget in result_frame.winfo_children():
            widget.destroy()

        if not users:
            tk.Label(result_frame, text=get_translation("no_accounts", module="admin_view_accounts_translation"),
                     bg="#FFFFFF", font=("Roboto", 12)).pack()
            return

        for user in users:
            item_frame = tk.Frame(result_frame, bg="#F5F5F5", highlightbackground="#E0E0E0", highlightthickness=1)
            item_frame.pack(fill="x", padx=10, pady=4)
            label = tk.Label(item_frame, text=f"[{user['role']}] {user['name']} (ID: {user['id']})",
                             anchor="w", bg="#F5F5F5", font=("Roboto", 11))
            label.pack(side="left", padx=10, pady=6)
            tk.Button(item_frame, text=get_translation("view", module="admin_view_accounts_translation"),
                      font=("Roboto", 10), bg="#1976D2", fg="white", relief="flat", bd=0,
                      activebackground="#63A4FF", command=lambda u=user: open_account(root, u)).pack(side="right", padx=10, pady=5)

    def open_account(root, user):
        if user['role'] == 'student':
            admin_view_student_account(root, user['id'])
        elif user['role'] == 'teacher':
            admin_view_teacher_account(root, user['id'])
        elif user['role'] == 'admin':
            admin_view_admin_account(root, user['id'])

    tk.Button(filter_frame, text=get_translation("refresh", module="admin_view_accounts_translation"),
              font=("Roboto", 10, "bold"), bg="#E0E0E0", relief="flat",
              command=load_accounts).grid(row=1, column=4, columnspan=2, padx=10, pady=5)

    tk.Button(container, text=get_translation("back", module="admin_view_accounts_translation"),
              font=("Roboto", 10), bg="#E0E0E0", relief="flat",
              command=lambda: admin_main_page(root)).pack(pady=10)

    # ✅ Языковой переключатель, работающий правильно
    from client.utils.ui import add_language_switcher
    add_language_switcher(root, lambda: admin_view_accounts(root))

    update_filter_fields()
    load_filter_options()
    load_accounts()


