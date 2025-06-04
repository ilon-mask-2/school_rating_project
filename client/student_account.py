import tkinter as tk
from tkinter import messagebox
import requests
import io
import base64
import threading
from PIL import Image, ImageTk
from client.utils.ui import authorized_get
from utils.ui import clear_root, add_language_switcher
from translation.translation_func import get_translation

SERVER_URL = "http://127.0.0.1:5000"

def student_account(root, student_id):
    from client.student_main_page import student_main_page
    clear_root(root)
    root.configure(bg="#FFFFFF")

    frame = tk.Frame(root, bg="#FFFFFF")
    frame.pack(padx=20, pady=20)

    tk.Label(frame, text="👨‍🎓 " + get_translation("student_account_title", module="student_account_translation"),
             font=("Roboto", 14, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=10)

    def populate(data):
        if data.get("photo"):
            try:
                image_data = base64.b64decode(data["photo"])
                image = Image.open(io.BytesIO(image_data)).resize((150, 150))
                photo = ImageTk.PhotoImage(image)
                img_label = tk.Label(frame, image=photo, bg="#FFFFFF")
                img_label.image = photo
                img_label.pack(pady=5)
            except Exception:
                tk.Label(frame, text=get_translation("error_photo_display", module="admin_view_student_account_translation"), bg="#FFFFFF").pack()

        info = [
            ("name", data.get("name", "")),
            ("class", data.get("class", "")),
            ("login", data.get("login", "")),
            ("email", data.get("email", "")),
            ("phone", data.get("phone", ""))
        ]
        for key, value in info:
            row = tk.Frame(frame, bg="#FFFFFF")
            row.pack(anchor="w", pady=2)
            tk.Label(row, text=f"{get_translation(key, module='shared_translation')}:",
                     font=("Roboto", 10, "bold"), width=12, anchor="w", bg="#FFFFFF").pack(side="left")
            tk.Label(row, text=value, font=("Roboto", 10), bg="#FFFFFF").pack(side="left")

        if data.get("groups"):
            tk.Label(frame, text=get_translation("groups", module="shared_translation"),
                     font=("Roboto", 10, "bold"), bg="#FFFFFF").pack(pady=(10, 0))
            for group in data["groups"]:
                tk.Label(frame, text=f"• {group}", anchor="w", bg="#FFFFFF").pack()

        if data.get("teachers"):
            tk.Label(frame, text=get_translation("teachers", module="student_account_translation"),
                     font=("Roboto", 10, "bold"), bg="#FFFFFF").pack(pady=(10, 0))
            for teacher in data["teachers"]:
                tk.Label(frame, text=f"• {teacher}", anchor="w", bg="#FFFFFF").pack()

        tk.Button(frame, text=get_translation("back", module="shared_translation"),
                  command=lambda: student_main_page(root, student_id), font=("Roboto", 10), bg="#E0E0E0",
                  relief="flat", width=15).pack(pady=15)

    def load_student():
        try:
            response = authorized_get(f"{SERVER_URL}/admin/students/{student_id}")
            response.raise_for_status()
            data = response.json()
            root.after(0, lambda: populate(data))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                       f"{get_translation('error_load_student', module='student_account_translation')}\n{e}"))

    threading.Thread(target=load_student).start()
    add_language_switcher(root, lambda: student_account(root, student_id))
