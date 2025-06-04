import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from utils.ui import clear_root, add_language_switcher
from client.utils.ui import authorized_post, authorized_get
from client.translation.translation_func import get_translation

SERVER_URL = "http://127.0.0.1:5000"

def student_rate_teacher(root, student_id):
    from client.student_main_page import student_main_page
    clear_root(root)
    root.configure(bg="#FFFFFF")

    tk.Label(root, text="📝 " + get_translation("student_rate_teacher_title", module="student_rate_teacher_translation"),
             font=("Roboto", 14, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=10)

    frame = tk.Frame(root, bg="#FFFFFF")
    frame.pack(pady=10)
    tk.Label(frame, text=get_translation("teacher", module="student_rate_teacher_translation"), bg="#FFFFFF").grid(row=0, column=0, padx=5)

    teacher_var = tk.StringVar()
    teacher_combo = ttk.Combobox(frame, textvariable=teacher_var, state="readonly", width=30)
    teacher_combo.grid(row=0, column=1)

    rating_vars = {}
    fields = [
        (get_translation("interest", module="student_rate_teacher_translation"), "interest"),
        (get_translation("teaching", module="student_rate_teacher_translation"), "teaching"),
        (get_translation("comfort", module="student_rate_teacher_translation"), "comfort"),
        (get_translation("respect", module="student_rate_teacher_translation"), "respect")
    ]

    score_frame = tk.Frame(root, bg="#FFFFFF")
    score_frame.pack(pady=10)

    for idx, (label, key) in enumerate(fields):
        tk.Label(score_frame, text=f"{label}:", width=15, anchor="e", bg="#FFFFFF").grid(row=idx, column=0, padx=5, pady=3)
        var = tk.IntVar(value=5)
        ttk.Spinbox(score_frame, from_=1, to=10, textvariable=var, width=5).grid(row=idx, column=1, padx=5)
        rating_vars[key] = var

    teacher_map = {}

    def load_teachers():
        def task():
            try:
                res = authorized_get(f"{SERVER_URL}/auth/teachers")
                res.raise_for_status()
                teachers = res.json()
                local_map = {t["name"]: t["id"] for t in teachers}
                local_names = list(local_map.keys())
                root.after(0, lambda: apply_teachers(local_map, local_names))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_load_teachers', module='student_rate_teacher_translation')}\n{e}"))

        def apply_teachers(mapping, names):
            teacher_map.update(mapping)
            teacher_combo["values"] = names

        threading.Thread(target=task).start()

    def submit():
        teacher_name = teacher_var.get()
        if not teacher_name:
            messagebox.showwarning(get_translation("error_title", module="errors_translation"),
                                   get_translation("select_teacher", module="student_rate_teacher_translation"))
            return

        payload = {
            "teacher_id": teacher_map[teacher_name],
            "student_id": student_id,
            "interest": rating_vars["interest"].get(),
            "teaching": rating_vars["teaching"].get(),
            "comfort": rating_vars["comfort"].get(),
            "respect": rating_vars["respect"].get()
        }

        def task():
            try:
                res = authorized_post(f"{SERVER_URL}/student/rate-teacher", json=payload)
                res.raise_for_status()
                root.after(0, lambda: messagebox.showinfo(get_translation("success_title", module="shared_translation"),
                                                          get_translation("rating_saved", module="student_rate_teacher_translation")))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_save_rating', module='student_rate_teacher_translation')}\n{e}"))

        threading.Thread(target=task).start()

    btn_frame = tk.Frame(root, bg="#FFFFFF")
    btn_frame.pack(pady=15)

    tk.Button(btn_frame, text=get_translation("save_rating", module="student_rate_teacher_translation"),
              command=submit, font=("Roboto", 10), bg="#1976D2", fg="white", relief="flat", width=25).pack(pady=5)

    tk.Button(btn_frame, text=get_translation("back", module="shared_translation"),
              command=lambda: student_main_page(root, student_id), font=("Roboto", 10),
              bg="#E0E0E0", relief="flat", width=25).pack(pady=5)

    load_teachers()
    add_language_switcher(root, lambda: student_rate_teacher(root, student_id))

