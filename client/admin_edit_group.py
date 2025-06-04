import threading
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from client.utils.ui import clear_root, authorized_post, authorized_get, add_language_switcher
from client.config import SERVER_URL
from client.translation.translation_func import get_translation

def admin_edit_group(root, group_id):
    from client.admin_view_groups import admin_view_groups
    clear_root(root)
    root.geometry("1000x700")
    root.configure(bg="#FFFFFF")

    # === Получаем данные о группе ===
    try:
        group_resp = authorized_get(f"{SERVER_URL}/admin/groups/{group_id}")
        group_resp.raise_for_status()
        group = group_resp.json()

        filters_resp = authorized_get(f"{SERVER_URL}/admin/group-edit-options")
        filters_resp.raise_for_status()
        filters = filters_resp.json()
    except Exception as e:
        messagebox.showerror(get_translation("error_title", module="errors_translation"),
                             f"{get_translation('error_load_group', module='admin_edit_group_translation')}\n{e}")
        return

    tk.Label(root, text="✏️ " + get_translation("edit_group", module="admin_edit_group_translation"),
             font=("Roboto", 16, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=10)

    top_frame = tk.Frame(root, bg="#FFFFFF")
    top_frame.pack(pady=5)

    tk.Label(top_frame, text=get_translation("group_name", module="admin_edit_group_translation"), bg="#FFFFFF").grid(row=0, column=0, padx=5)
    name_var = tk.StringVar(value=group["name"])
    tk.Entry(top_frame, textvariable=name_var, width=30).grid(row=0, column=1, padx=5)

    tk.Label(top_frame, text=get_translation("teacher", module="shared_translation"), bg="#FFFFFF").grid(row=0, column=2, padx=5)
    teacher_var = tk.StringVar(value=group["teacher"])
    teacher_box = ttk.Combobox(top_frame, textvariable=teacher_var, values=filters["teachers"], width=30)
    teacher_box.grid(row=0, column=3, padx=5)

    def save_group_info():
        def worker():
            try:
                response = requests.put(f"{SERVER_URL}/admin/groups/{group_id}", json={
                    "name": name_var.get().strip(),
                    "teacher": teacher_var.get().strip()
                })
                response.raise_for_status()
                root.after(0, lambda: (
                    messagebox.showinfo(get_translation("success_title", module="shared_translation"),
                                        get_translation("group_updated", module="admin_edit_group_translation")),
                    admin_edit_group(root, group_id)
                ))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_update_group', module='admin_edit_group_translation')}\n{e}"))

        threading.Thread(target=worker).start()

    tk.Button(top_frame, text=get_translation("save", module="shared_translation"), command=save_group_info,
              font=("Roboto", 10), bg="#1976D2", fg="white", relief="flat").grid(row=0, column=4, padx=10)

    tk.Label(root, text=get_translation("group_members", module="admin_edit_group_translation"), font=("Roboto", 12), bg="#FFFFFF").pack(pady=(10, 0))
    members_frame = tk.Frame(root, bg="#FFFFFF")
    members_frame.pack()

    def remove_student(student_id):
        def worker():
            try:
                authorized_post(f"{SERVER_URL}/admin/groups/{group_id}/remove-student", json={"student_id": student_id})
                root.after(0, lambda: admin_edit_group(root, group_id))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_remove_student', module='admin_edit_group_translation')}\n{e}"))

        threading.Thread(target=worker).start()

    for student in group["students"]:
        row = tk.Frame(members_frame, bg="#FFFFFF")
        row.pack(fill="x", pady=2)
        tk.Label(row, text=f"{student['name']} ({get_translation('class', module='shared_translation')} {student['clas']})", anchor="w", width=40, bg="#FFFFFF").pack(side="left")
        tk.Button(row, text=get_translation("delete", module="shared_translation"),
                  command=lambda s_id=student["id"]: remove_student(s_id), bg="#FFCDD2", relief="flat").pack(side="right")

    search_frame = tk.Frame(root, bg="#FFFFFF")
    search_frame.pack(pady=15)

    tk.Label(search_frame, text=get_translation("class", module="shared_translation"), bg="#FFFFFF").grid(row=0, column=0)
    class_var = tk.StringVar()
    class_box = ttk.Combobox(search_frame, textvariable=class_var, values=[""] + filters["classes"], width=10, state="readonly")
    class_box.grid(row=0, column=1, padx=5)

    tk.Label(search_frame, text=get_translation("name", module="shared_translation"), bg="#FFFFFF").grid(row=0, column=2)
    student_var = tk.StringVar()
    student_box = ttk.Combobox(search_frame, textvariable=student_var, values=filters["students"], width=30)
    student_box.grid(row=0, column=3, padx=5)

    def filter_students(event=None):
        name_filter = student_var.get().lower()
        class_filter = class_var.get()
        matches = [
            s for s in filters["students"]
            if (not name_filter or name_filter in s.lower()) and
               (not class_filter or class_filter in s.split(" | ")[-1])
        ]
        student_box["values"] = matches if matches else [get_translation("not_found", module="admin_edit_group_translation")]

    student_box.bind("<KeyRelease>", filter_students)
    class_box.bind("<<ComboboxSelected>>", filter_students)

    def add_student():
        def worker():
            try:
                name = student_var.get().split(" | ")[0].strip()
                response = authorized_post(f"{SERVER_URL}/admin/groups/{group_id}/add-student", json={"student_name": name})
                response.raise_for_status()
                root.after(0, lambda: admin_edit_group(root, group_id))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_add_student', module='admin_edit_group_translation')}\n{e}"))

        threading.Thread(target=worker).start()

    tk.Button(search_frame, text=get_translation("add", module="admin_edit_group_translation"), command=add_student,
              font=("Roboto", 10), bg="#C8E6C9", relief="flat").grid(row=0, column=4, padx=10)

    back_btn_frame = tk.Frame(root, bg="#FFFFFF")
    back_btn_frame.pack(pady=10)

    def go_back_to_groups():
        admin_view_groups(root)

    tk.Button(back_btn_frame, text=get_translation("back_to_groups", module="admin_edit_group_translation"),
              command=go_back_to_groups, font=("Roboto", 10), bg="#E0E0E0", relief="flat").pack()

    add_language_switcher(root, lambda: admin_edit_group(root, group_id))


