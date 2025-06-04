import tkinter as tk
import threading
from utils.ui import clear_root, restart_app, add_language_switcher
from client.teacher_account import teacher_account
from client.teacher_rating import teacher_rating
from client.teacher_rate_student import teacher_rate_student
from client.translation.translation_func import get_translation

def teacher_main_page(root, teacher_id):
    clear_root(root)
    root.title(get_translation("teacher_main_title", module="teacher_main_page_translation"))
    root.configure(bg="#FFFFFF")

    tk.Label(root, text="👨‍🏫 " + get_translation("teacher_panel", module="teacher_main_page_translation"),
             font=("Roboto", 16, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=20)

    def open_page(func):
        threading.Thread(target=lambda: func(root, teacher_id)).start()

    btn_frame = tk.Frame(root, bg="#FFFFFF")
    btn_frame.pack()

    tk.Button(btn_frame, text=get_translation("my_account", module="teacher_main_page_translation"),
              command=lambda: open_page(teacher_account), font=("Roboto", 10), width=25,
              bg="#E0E0E0", relief="flat").pack(pady=5)

    tk.Button(btn_frame, text=get_translation("my_ratings", module="teacher_main_page_translation"),
              command=lambda: open_page(teacher_rating), font=("Roboto", 10), width=25,
              bg="#E0E0E0", relief="flat").pack(pady=5)

    tk.Button(btn_frame, text=get_translation("rate_student", module="teacher_main_page_translation"),
              command=lambda: open_page(teacher_rate_student), font=("Roboto", 10), width=25,
              bg="#E0E0E0", relief="flat").pack(pady=5)

    tk.Button(btn_frame, text=get_translation("logout", module="shared_translation"),
              command=lambda: restart_app(root), font=("Roboto", 10), width=25,
              bg="#FFCDD2", relief="flat").pack(pady=20)

    add_language_switcher(root, lambda: teacher_main_page(root, teacher_id))
