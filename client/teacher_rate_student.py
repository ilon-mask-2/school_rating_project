import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from utils.ui import clear_root, add_language_switcher
from client.utils.ui import authorized_post, authorized_get
from client.translation.translation_func import get_translation

SERVER_URL = "http://127.0.0.1:5000"

def teacher_rate_student(root, teacher_id):
    from client.teacher_main_page import teacher_main_page
    clear_root(root)
    root.configure(bg="#FFFFFF")

    tk.Label(root, text="📝 " + get_translation("rate_student_title", module="teacher_rate_student_translation"),
             font=("Roboto", 14, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=10)

    top_frame = tk.Frame(root, bg="#FFFFFF")
    top_frame.pack(pady=5)

    tk.Label(top_frame, text=get_translation("group", module="teacher_rate_student_translation"), bg="#FFFFFF").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    group_var = tk.StringVar()
    group_combo = ttk.Combobox(top_frame, textvariable=group_var, state="readonly", width=30)
    group_combo.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(top_frame, text=get_translation("student", module="teacher_rate_student_translation"), bg="#FFFFFF").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    student_var = tk.StringVar()
    student_combo = ttk.Combobox(top_frame, textvariable=student_var, state="readonly", width=30)
    student_combo.grid(row=1, column=1, padx=5, pady=5)

    score_frame = tk.Frame(root, bg="#FFFFFF")
    score_frame.pack(pady=10)

    rating_vars = {}
    fields = [
        (get_translation("attendance", module="teacher_rate_student_translation"), "attendance"),
        (get_translation("participation", module="teacher_rate_student_translation"), "participation"),
        (get_translation("effort", module="teacher_rate_student_translation"), "effort"),
        (get_translation("respect", module="teacher_rate_student_translation"), "respect")
    ]

    for idx, (label, key) in enumerate(fields):
        tk.Label(score_frame, text=f"{label}:", width=15, anchor="e", bg="#FFFFFF").grid(row=idx, column=0, padx=5, pady=3)
        var = tk.IntVar(value=5)
        ttk.Spinbox(score_frame, from_=1, to=10, textvariable=var, width=5).grid(row=idx, column=1, padx=5)
        rating_vars[key] = var

    group_map = {}
    student_map = {}

    def load_groups():
        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/teacher/{teacher_id}/groups")
                response.raise_for_status()
                groups = response.json()
                root.after(0, lambda: apply_groups(groups))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_load_groups', module='teacher_rate_student_translation')}\n{e}"))

        def apply_groups(groups):
            group_names = [g['name'] for g in groups]
            group_combo['values'] = group_names
            group_map.clear()
            for g in groups:
                group_map[g['name']] = g['id']

        threading.Thread(target=task).start()

    def load_students(*args):
        student_combo.set("")
        group_name = group_var.get()
        group_id = group_map.get(group_name)
        if not group_id:
            return

        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/admin/group-members/{group_id}")
                response.raise_for_status()
                students = response.json()
                root.after(0, lambda: apply_students(students))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_load_students', module='teacher_rate_student_translation')}\n{e}"))

        def apply_students(students):
            student_names = [s['name'] for s in students]
            student_combo['values'] = student_names
            student_map.clear()
            for s in students:
                student_map[s['name']] = s['id']

        threading.Thread(target=task).start()

    def submit_rating():
        group_name = group_var.get()
        student_name = student_var.get()

        if not group_name or not student_name:
            messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                 get_translation("select_group_student", module="teacher_rate_student_translation"))
            return

        student_id = student_map.get(student_name)
        if not student_id:
            messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                 get_translation("invalid_student", module="teacher_rate_student_translation"))
            return

        payload = {
            "teacher_id": teacher_id,
            "student_id": student_id,
            "attendance": rating_vars["attendance"].get(),
            "participation": rating_vars["participation"].get(),
            "effort": rating_vars["effort"].get(),
            "respect": rating_vars["respect"].get()
        }

        def task():
            try:
                response = authorized_post(f"{SERVER_URL}/teacher/rate-student", json=payload)
                response.raise_for_status()
                root.after(0, lambda: messagebox.showinfo(get_translation("success_title", module="shared_translation"),
                                                          get_translation("rating_saved", module="teacher_rate_student_translation")))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_save_rating', module='teacher_rate_student_translation')}\n{e}"))

        threading.Thread(target=task).start()

    group_var.trace_add("write", load_students)
    load_groups()

    btn_frame = tk.Frame(root, bg="#FFFFFF")
    btn_frame.pack(pady=15)

    tk.Button(btn_frame, text=get_translation("save_rating", module="teacher_rate_student_translation"), command=submit_rating,
              font=("Roboto", 10), bg="#C8E6C9", relief="flat", width=20).grid(row=0, column=0, padx=10)

    tk.Button(btn_frame, text=get_translation("back", module="shared_translation"),
              command=lambda: teacher_main_page(root, teacher_id), font=("Roboto", 10),
              bg="#E0E0E0", relief="flat", width=20).grid(row=0, column=1, padx=10)

    add_language_switcher(root, lambda: teacher_rate_student(root, teacher_id))
