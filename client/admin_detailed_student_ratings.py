import threading
import tkinter as tk
from tkinter import ttk, messagebox
import requests

from client.config import SERVER_URL
from client.utils.ui import sanitize_date  # если у тебя вынесена функция обработки дат
from client.utils.ui import authorized_post, authorized_get
def admin_detailed_student_ratings(root, student_id):
    from client.admin_view_rating import admin_view_rating
    for widget in root.winfo_children():
        widget.destroy()
    root.geometry("1400x650")
    tk.Label(root, text=f"👤 Подробные оценки ученика", font=("Arial", 14, "bold")).pack(pady=10)

    date_from_var = tk.StringVar(value="За всё время")
    date_to_var = tk.StringVar(value="За всё время")
    teacher_var = tk.StringVar(value="All")

    filter_frame = tk.Frame(root)
    filter_frame.pack(pady=5)

    try:
        resp = authorized_get(f"{SERVER_URL}/student/{student_id}/grade-options")
        resp.raise_for_status()
        data = resp.json()
        date_options = ["За всё время"] + data["dates"]
        teacher_options = ["All"] + data["teachers"]
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить фильтры: {e}")
        date_options = ["За всё время"]
        teacher_options = ["All"]

    tk.Label(filter_frame, text="С:").grid(row=0, column=0, padx=5)
    ttk.Combobox(filter_frame, textvariable=date_from_var, values=date_options, width=12).grid(row=0, column=1, padx=5)

    tk.Label(filter_frame, text="По:").grid(row=0, column=2, padx=5)
    ttk.Combobox(filter_frame, textvariable=date_to_var, values=date_options, width=12).grid(row=0, column=3, padx=5)

    tk.Label(filter_frame, text="Преподаватель:").grid(row=0, column=4, padx=5)
    ttk.Combobox(filter_frame, textvariable=teacher_var, values=teacher_options, width=25).grid(row=0, column=5, padx=5)

    columns = ("teacher", "date", "attendance", "participation", "effort", "respect")
    tree = ttk.Treeview(root, columns=columns, show="headings", height=20)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=110)
    tree.pack(pady=10, fill="both", expand=True)

    def load_data():
        def worker():
            try:
                params = {
                    "date_from": sanitize_date(date_from_var.get(), True),
                    "date_to": sanitize_date(date_to_var.get(), False),
                    "teacher": teacher_var.get()
                }
                resp = authorized_get(f"{SERVER_URL}/admin/student-detailed-ratings/{student_id}", params=params)
                resp.raise_for_status()
                records = resp.json()

                def update_ui():
                    for row in tree.get_children():
                        tree.delete(row)
                    for r in records:
                        tree.insert("", "end", values=(
                            r["teacher"], r["date"], r["attendance"], r["participation"], r["effort"], r["respect"]
                        ))
                root.after(0, update_ui)
            except Exception as e:
                root.after(0, lambda: messagebox.showerror("Ошибка", f"Не удалось загрузить данные: {e}"))

        threading.Thread(target=worker).start()

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="🔄 Обновить", command=load_data).pack(side="left", padx=10)

    def go_back():
        admin_view_rating(root)

    tk.Button(btn_frame, text="⬅ Назад", command=go_back).pack(side="left", padx=10)

    load_data()
