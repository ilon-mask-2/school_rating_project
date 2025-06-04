
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests

from client.config import SERVER_URL
from client.utils.ui import (
    clear_root, wrap_with_scrollframe,
    authorized_get, sanitize_date, date_range_values,
    add_language_switcher
)
from client.admin_detailed_student_ratings import admin_detailed_student_ratings
from client.admin_detailed_teacher_ratings import admin_detailed_teacher_ratings
from client.translation.translation_func import get_translation

def go_back_to_main(root):
    from client.admin_main_page import admin_main_page
    admin_main_page(root)

def admin_view_rating(root):
    clear_root(root)
    root.geometry("1200x700")
    root.title(get_translation("ratings_title", module="admin_view_rating_translation"))
    root.configure(bg="#FFFFFF")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview", background="#FFFFFF", foreground="#000000", rowheight=25, font=("Roboto", 10))
    style.configure("Treeview.Heading", font=("Roboto", 10, "bold"), background="#E3F2FD", foreground="#0D47A1")
    style.map("Treeview", background=[("selected", "#BBDEFB")])

    tk.Label(root,
             text=get_translation("ratings_title", module="admin_view_rating_translation"),
             font=("Roboto", 18, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=10)

    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill="both", padx=10, pady=10)

    from client.admin_rating_tabs import populate_student_ratings_tab, populate_teacher_ratings_tab

    student_tab = tk.Frame(notebook, bg="#FFFFFF")
    teacher_tab = tk.Frame(notebook, bg="#FFFFFF")

    notebook.add(student_tab, text=get_translation("student_ratings_tab", module="admin_view_rating_translation"))
    notebook.add(teacher_tab, text=get_translation("teacher_ratings_tab", module="admin_view_rating_translation"))

    populate_student_ratings_tab(wrap_with_scrollframe(student_tab), root)
    populate_teacher_ratings_tab(wrap_with_scrollframe(teacher_tab), root)

    add_language_switcher(root, lambda: admin_view_rating(root))

    back_btn_frame = tk.Frame(root, bg="#FFFFFF")
    back_btn_frame.pack(pady=10)
    tk.Button(
        back_btn_frame,
        text=get_translation("back_main", module="shared_translation"),
        command=lambda: go_back_to_main(root),
        font=("Roboto", 10),
        bg="#E0E0E0",
        relief="flat"
    ).pack()
