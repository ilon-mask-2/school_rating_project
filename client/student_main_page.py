import tkinter as tk
import threading
from client.student_rate_teacher import student_rate_teacher
from client.utils.ui import clear_root, restart_app, add_language_switcher
from client.student_account import student_account
from client.student_rating import student_rating
from client.translation.translation_func import get_translation

def student_main_page(root, student_id):
    clear_root(root)
    root.title(get_translation("student_main_title", module="student_main_page_translation"))
    root.configure(bg="#FFFFFF")

    tk.Label(root, text=get_translation("welcome", module="student_main_page_translation"),
             font=("Roboto", 12), bg="#FFFFFF").pack(pady=20)

    def run_in_thread(fn):
        threading.Thread(target=lambda: fn(root, student_id)).start()

    btn_frame = tk.Frame(root, bg="#FFFFFF")
    btn_frame.pack()

    tk.Button(btn_frame, text=get_translation("my_account", module="student_main_page_translation"), width=25,
              command=lambda: run_in_thread(student_account), font=("Roboto", 10), bg="#E0E0E0", relief="flat").pack(pady=5)

    tk.Button(btn_frame, text=get_translation("my_ratings", module="student_main_page_translation"), width=25,
              command=lambda: run_in_thread(student_rating), font=("Roboto", 10), bg="#E0E0E0", relief="flat").pack(pady=5)

    tk.Button(btn_frame, text=get_translation("rate_teacher", module="student_main_page_translation"), width=25,
              command=lambda: run_in_thread(student_rate_teacher), font=("Roboto", 10), bg="#E0E0E0", relief="flat").pack(pady=5)

    tk.Button(btn_frame, text=get_translation("logout", module="shared_translation"), width=25,
              command=lambda: restart_app(root), font=("Roboto", 10), bg="#FFCDD2", relief="flat").pack(pady=20)

    add_language_switcher(root, lambda: student_main_page(root, student_id))
