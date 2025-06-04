import tkinter as tk
from tkinter import messagebox
import requests
import base64
import io
import threading
from PIL import Image, ImageTk
from client.utils.ui import authorized_post, authorized_get, clear_root, ScrollFrame, add_language_switcher
from client.config import SERVER_URL
from client.translation.translation_func import get_translation

def admin_view_teacher_account(root, teacher_id):
    from client.admin_view_accounts import admin_view_accounts
    from client.admin_edit_teacher_account import admin_edit_teacher_account

    clear_root(root)

    scroll = ScrollFrame(root, bg="#FFFFFF")
    scroll.pack(fill="both", expand=True)
    container = scroll.scrollable_frame
    container.configure(bg="#FFFFFF")

    tk.Label(container, text="👨‍🏫 " + get_translation("teacher", module="shared_translation"),
             font=("Roboto", 16, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=20)

    main_frame = tk.Frame(container, bg="#FFFFFF")
    main_frame.pack(pady=10)
    info_frame = tk.Frame(main_frame, bg="#F5F5F5")
    info_frame.pack(pady=10)

    def show(label_key, value):
        row = tk.Frame(info_frame, bg="#F5F5F5")
        row.pack(anchor="w", pady=4, padx=10, fill="x")
        label = get_translation(label_key, module="shared_translation")
        tk.Label(row, text=f"{label}:", font=("Roboto", 10, "bold"), bg="#F5F5F5").pack(side="left")
        tk.Label(row, text=value, font=("Roboto", 10), bg="#F5F5F5").pack(side="left", padx=5)

    def populate_teacher(teacher):
        if teacher.get("photo"):
            try:
                image_bytes = base64.b64decode(teacher["photo"])
                image = Image.open(io.BytesIO(image_bytes)).resize((100, 100))
                photo_img = ImageTk.PhotoImage(image)
                tk.Label(main_frame, image=photo_img, bg="#FFFFFF").pack()
                root.photo_ref = photo_img
            except Exception:
                tk.Label(main_frame, text=get_translation("error_photo_display", module="admin_view_student_account_translation"), bg="#FFFFFF").pack()

        show("id", teacher['id'])
        show("name", teacher['name'])
        show("login", teacher['login'])
        show("email", teacher.get('email', '—'))
        show("phone", teacher.get('phone', '—'))

        if teacher.get("groups"):
            tk.Label(main_frame, text=get_translation("groups", module="admin_view_student_account_translation"),
                     font=("Roboto", 10, "bold"), bg="#FFFFFF").pack()
            for group in teacher["groups"]:
                tk.Label(main_frame, text=f"• {group}", bg="#FFFFFF").pack(anchor="w")

    def load_teacher():
        try:
            response = authorized_get(f"{SERVER_URL}/admin/teachers/{teacher_id}")
            response.raise_for_status()
            teacher = response.json()
            root.after(0, lambda: populate_teacher(teacher))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                       f"{get_translation('error_load_teacher', module='admin_view_teacher_account_translation')}\n{e}"))

    threading.Thread(target=load_teacher).start()

    button_frame = tk.Frame(container, bg="#FFFFFF")
    button_frame.pack(pady=20)

    def go_back():
        admin_view_accounts(root)

    def edit_teacher():
        admin_edit_teacher_account(root, teacher_id)

    def delete_teacher():
        if not messagebox.askyesno(get_translation("confirm", module="shared_translation"),
                                   get_translation("confirm_delete_teacher", module="admin_view_teacher_account_translation")):
            return

        def task():
            try:
                requests.delete(f"{SERVER_URL}/admin/teachers/{teacher_id}")
                root.after(0, lambda: (
                    messagebox.showinfo(get_translation("deleted", module="shared_translation"),
                                        get_translation("teacher_deleted", module="admin_view_teacher_account_translation")),
                    go_back()
                ))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_delete_teacher', module='admin_view_teacher_account_translation')}\n{e}"))

        threading.Thread(target=task).start()

    tk.Button(button_frame, text=get_translation("back", module="shared_translation"), command=go_back, width=15,
              font=("Roboto", 10), bg="#E0E0E0", relief="flat").grid(row=0, column=0, padx=10)

    tk.Button(button_frame, text=get_translation("edit", module="shared_translation"), command=edit_teacher, width=15,
              font=("Roboto", 10), bg="#BBDEFB", relief="flat").grid(row=0, column=1, padx=10)

    tk.Button(button_frame, text=get_translation("delete", module="shared_translation"), command=delete_teacher, width=15,
              font=("Roboto", 10), bg="#FFCDD2", relief="flat").grid(row=0, column=2, padx=10)

    add_language_switcher(root, lambda: admin_view_teacher_account(root, teacher_id))


