import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests

from client.config import SERVER_URL
from client.utils.ui import clear_root, authorized_get, add_language_switcher
from client.admin_edit_group import admin_edit_group
from client.admin_create_group import admin_create_group
from client.translation.translation_func import get_translation, get_current_language, set_language

def admin_view_groups(root):
    from client.admin_main_page import admin_main_page
    def reload():
        admin_view_groups(root)

    clear_root(root)
    root.geometry("1000x700")
    root.configure(bg="#FFFFFF")

    root.title(get_translation("title", module="admin_main_page_translation") + " — " + get_translation("admin", module="shared_translation"))

    tk.Label(root, text=get_translation("groups_title", module="admin_view_groups_translation"),
             font=("Roboto", 20, "bold"), fg="#1976D2", bg="#FFFFFF").pack(pady=10)

    # 🌐 Языковой переключатель
    add_language_switcher(root, reload)

    filter_frame = tk.Frame(root, bg="#FFFFFF")
    filter_frame.pack(pady=10)

    search_var = tk.StringVar()
    teacher_var = tk.StringVar(value="All")
    subject_var = tk.StringVar(value="All")
    student_var = tk.StringVar(value="All")
    sort_var = tk.StringVar(value="name")

    teacher_box = ttk.Combobox(filter_frame, textvariable=teacher_var, width=15, state="readonly")
    subject_box = ttk.Combobox(filter_frame, textvariable=subject_var, width=15, state="readonly")
    student_box = ttk.Combobox(filter_frame, textvariable=student_var, width=15, state="readonly")
    sort_box = ttk.Combobox(filter_frame, textvariable=sort_var, width=15, state="readonly",
                            values=["name", "subject", "teacher", "student_count"])

    entry = tk.Entry(filter_frame, textvariable=search_var, width=15)
    entry.grid(row=0, column=1, padx=5, pady=2, ipady=1)

    labels = [
        (get_translation("search_name", module="admin_view_groups_translation"), entry),
        (get_translation("subject", module="admin_view_groups_translation"), subject_box),
        (get_translation("teacher", module="admin_view_groups_translation"), teacher_box),
        (get_translation("student", module="admin_view_groups_translation"), student_box),
        (get_translation("sort", module="admin_view_groups_translation"), sort_box),
    ]

    for i, (label_text, widget) in enumerate(labels):
        tk.Label(filter_frame, text=label_text, bg="#FFFFFF").grid(row=0, column=i*2, padx=5)
        if i != 0:
            widget.grid(row=0, column=i*2+1, padx=5)

    columns = [
        get_translation("name", module="admin_view_groups_translation"),
        get_translation("subject", module="admin_view_groups_translation"),
        get_translation("teacher", module="admin_view_groups_translation"),
        get_translation("students", module="admin_view_groups_translation"),
        get_translation("action", module="admin_view_groups_translation")
    ]

    tree = ttk.Treeview(root, columns=columns, show="headings", height=20)
    for col in columns:
        tree.column(col, width=150 if col != get_translation("action", module="admin_view_groups_translation") else 60, anchor="center")
        tree.heading(col, text=col)
    tree.pack(pady=10)

    def on_item_click(event):
        item = tree.identify_row(event.y)
        if item and tree.identify_column(event.x) == f"#{len(columns)}":
            group_name = tree.item(item, "values")[0]

            def task():
                try:
                    response = authorized_get(f"{SERVER_URL}/admin/groups")
                    response.raise_for_status()
                    groups = response.json()
                    group = next((g for g in groups if g["name"] == group_name), None)
                    if group:
                        root.after(0, lambda: admin_edit_group(root, group["id"]))
                except Exception as e:
                    root.after(0, lambda: messagebox.showerror(
                        get_translation("error_title", module="errors_translation"),
                        f"{get_translation('error_open_group', module='admin_view_groups_translation')}\n{e}"
                    ))

            threading.Thread(target=task).start()

    tree.bind("<Button-1>", on_item_click)

    def filter_combobox(event, full_list, combo_var, combobox):
        typed = combo_var.get().lower()
        matches = [item for item in full_list if typed in item.lower()]
        combobox["values"] = ["All"] + matches if matches else ["All"]

    def display_table(groups):
        name_filter = search_var.get().lower()
        teacher_filter = teacher_var.get().lower()
        subject_filter = subject_var.get()
        student_filter = student_var.get().lower()

        filtered = []
        for g in groups:
            if name_filter and name_filter not in g["name"].lower():
                continue
            if teacher_var.get() != "All" and teacher_filter not in g["teacher"].lower():
                continue
            if subject_filter != "All" and subject_filter != g["subject"]:
                continue
            if student_var.get() != "All" and student_filter not in [s.lower() for s in g.get("students", [])]:
                continue
            filtered.append(g)

        key = sort_var.get()
        reverse = key == "student_count"
        filtered.sort(key=lambda g: str(g.get(key, "")).lower() if isinstance(g.get(key), str) else g.get(key, ""), reverse=reverse)

        for row in tree.get_children():
            tree.delete(row)

        for g in filtered:
            tree.insert("", "end", values=(g["name"], g["subject"], g["teacher"], g["student_count"], "✏️"))

    def refresh_table():
        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/admin/groups")
                response.raise_for_status()
                groups = response.json()
                root.after(0, lambda: display_table(groups))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_load_groups', module='admin_view_groups_translation')}\n{e}"
                ))
        threading.Thread(target=task).start()

    def load_filters():
        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/admin/group-filter-options")
                response.raise_for_status()
                data = response.json()
                root.after(0, lambda: apply_filters(data))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_load_filters', module='admin_view_groups_translation')}\n{e}"
                ))

        def apply_filters(data):
            teacher_box["values"] = ["All"] + data["teachers"]
            subject_box["values"] = ["All"] + data["subjects"]
            student_box["values"] = ["All"] + data["students"]

            teacher_box.bind("<KeyRelease>", lambda e: filter_combobox(e, data["teachers"], teacher_var, teacher_box))
            student_box.bind("<KeyRelease>", lambda e: filter_combobox(e, data["students"], student_var, student_box))

        threading.Thread(target=task).start()

    control_frame = tk.Frame(root, bg="#FFFFFF")
    control_frame.pack(pady=10)
    tk.Button(control_frame, text=get_translation("refresh", module="admin_view_groups_translation"),
              command=refresh_table, font=("Roboto", 10), bg="#E0E0E0", relief="flat").grid(row=0, column=0, padx=10)

    tk.Button(control_frame, text=get_translation("create", module="admin_view_groups_translation"),
              command=lambda: admin_create_group(root), font=("Roboto", 10, "bold"),
              bg="#1976D2", fg="white", relief="flat").grid(row=0, column=1, padx=10)

    tk.Button(root, text=get_translation("back", module="admin_view_groups_translation"),
              command=lambda: admin_main_page(root), font=("Roboto", 10), bg="#E0E0E0", relief="flat").pack(pady=10)

    load_filters()
    refresh_table()
