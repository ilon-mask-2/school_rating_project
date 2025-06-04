import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import base64
import io
from PIL import Image, ImageTk
import threading
from client.utils.ui import authorized_post, authorized_get, hash_password, clear_root, ScrollFrame, add_language_switcher
from client.config import SERVER_URL
from client.translation.translation_func import get_translation

def admin_edit_teacher_account(root, teacher_id):
    from client.admin_view_teacher_account import admin_view_teacher_account
    clear_root(root)

    scroll = ScrollFrame(root, bg="#FFFFFF")
    scroll.pack(fill="both", expand=True)
    container = scroll.scrollable_frame
    container.configure(bg="#FFFFFF")

    tk.Label(container, text="✏️ " + get_translation("edit", module="shared_translation") + " — " + get_translation("teacher", module="shared_translation"),
             font=("Roboto", 16, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=20)

    form_frame = tk.Frame(container, bg="#FFFFFF")
    form_frame.pack(pady=10)

    fields = [
        (get_translation("name", module="shared_translation"), "name"),
        (get_translation("login", module="shared_translation"), "login"),
        (get_translation("password", module="shared_translation"), "password"),
        (get_translation("email", module="shared_translation"), "email"),
        (get_translation("phone", module="shared_translation"), "phone")
    ]
    field_vars = {}

    photo_frame = tk.Frame(container, bg="#FFFFFF")
    photo_frame.pack(pady=10)
    tk.Label(photo_frame, text=get_translation("photo", module="shared_translation"), bg="#FFFFFF").pack()
    photo_data = [None]
    teacher = [{}]

    def populate_form(data):
        teacher[0] = data
        for idx, (label, key) in enumerate(fields):
            tk.Label(form_frame, text=label, font=("Roboto", 10, "bold"), bg="#FFFFFF").grid(row=idx, column=0, sticky="e", padx=5, pady=3)
            var = tk.StringVar(value=data.get(key, ""))
            tk.Entry(form_frame, textvariable=var, width=30).grid(row=idx, column=1, padx=5, pady=3)
            field_vars[key] = var

        if data.get("photo"):
            try:
                image_bytes = base64.b64decode(data["photo"])
                image = Image.open(io.BytesIO(image_bytes)).resize((100, 100))
                photo_img = ImageTk.PhotoImage(image)
                tk.Label(photo_frame, image=photo_img, bg="#FFFFFF").pack()
                root.photo_ref = photo_img
            except Exception:
                tk.Label(photo_frame, text=get_translation("error_photo_display", module="admin_view_student_account_translation"), bg="#FFFFFF").pack()

    def upload_photo():
        filepath = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
        if filepath:
            try:
                with open(filepath, "rb") as f:
                    photo_data[0] = base64.b64encode(f.read()).decode("utf-8")
                tk.Label(photo_frame, text=get_translation("photo_uploaded", module="admin_edit_student_account_translation"), bg="#FFFFFF").pack()
            except Exception:
                messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                     get_translation("error_upload_photo", module="admin_edit_student_account_translation"))

    tk.Button(photo_frame, text=get_translation("upload_photo", module="admin_edit_student_account_translation"),
              command=upload_photo, font=("Roboto", 10), bg="#BBDEFB", relief="flat").pack(pady=5)

    btn_frame = tk.Frame(container, bg="#FFFFFF")
    btn_frame.pack(pady=20)

    def save_changes():
        def task():
            data = {}
            for key, var in field_vars.items():
                val = var.get().strip()
                if key == "password":
                    if val:
                        data["password"] = hash_password(val)
                    else:
                        data["password"] = teacher[0].get("password", "")
                else:
                    data[key] = val or teacher[0].get(key, "")
            data["photo"] = photo_data[0] or teacher[0].get("photo")
            try:
                response = requests.put(f"{SERVER_URL}/admin/teachers/{teacher_id}", json=data)
                response.raise_for_status()
                root.after(0, lambda: (
                    messagebox.showinfo(get_translation("success_title", module="shared_translation"),
                                        get_translation("teacher_updated", module="admin_edit_teacher_account_translation")),
                    admin_view_teacher_account(root, teacher_id)
                ))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_update_teacher', module='admin_edit_teacher_account_translation')}\n{e}"))

        threading.Thread(target=task).start()

    def cancel():
        admin_view_teacher_account(root, teacher_id)

    tk.Button(btn_frame, text=get_translation("save", module="shared_translation"), command=save_changes, width=15,
              font=("Roboto", 10), bg="#1976D2", fg="white", relief="flat").grid(row=0, column=0, padx=10)

    tk.Button(btn_frame, text=get_translation("cancel", module="shared_translation"), command=cancel, width=15,
              font=("Roboto", 10), bg="#E0E0E0", relief="flat").grid(row=0, column=1, padx=10)

    def load_teacher():
        try:
            response = authorized_get(f"{SERVER_URL}/admin/teachers/{teacher_id}")
            response.raise_for_status()
            teacher_data = response.json()
            root.after(0, lambda: populate_form(teacher_data))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                       f"{get_translation('error_load_teacher', module='admin_view_teacher_account_translation')}\n{e}"))

    add_language_switcher(root, lambda: admin_edit_teacher_account(root, teacher_id))
    threading.Thread(target=load_teacher).start()

