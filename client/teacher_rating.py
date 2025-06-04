import tkinter as tk
from tkinter import ttk, messagebox
import threading
from utils.ui import clear_root, add_language_switcher
from client.utils.ui import authorized_get
from client.translation.translation_func import get_translation

SERVER_URL = "http://127.0.0.1:5000"

def teacher_rating(root, teacher_id):
    from client.teacher_main_page import teacher_main_page
    clear_root(root)
    root.geometry("900x500")
    root.configure(bg="#FFFFFF")

    tk.Label(root, text="📊 " + get_translation("teacher_rating_title", module="teacher_rating_translation"),
             font=("Roboto", 14, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=10)

    mode_var = tk.StringVar(value="single")

    # === Переключение режима ===
    mode_frame = tk.Frame(root, bg="#FFFFFF")
    mode_frame.pack(pady=5)
    tk.Label(mode_frame, text=get_translation("mode", module="teacher_rating_translation"),
             font=("Roboto", 10), bg="#FFFFFF").pack(side="left", padx=5)
    tk.Radiobutton(mode_frame, text=get_translation("date", module="teacher_rating_translation"),
                   variable=mode_var, value="single", bg="#FFFFFF",
                   command=lambda: update_filter_fields()).pack(side="left")
    tk.Radiobutton(mode_frame, text=get_translation("date_from", module="teacher_rating_translation") + " + " +
                   get_translation("date_to", module="teacher_rating_translation"),
                   variable=mode_var, value="range", bg="#FFFFFF",
                   command=lambda: update_filter_fields()).pack(side="left")

    filter_frame = tk.Frame(root, bg="#FFFFFF")
    filter_frame.pack(pady=5)

    date_from_var = tk.StringVar()
    date_to_var = tk.StringVar()

    date_from_box = ttk.Combobox(filter_frame, textvariable=date_from_var, state="readonly", width=20)
    date_to_box = ttk.Combobox(filter_frame, textvariable=date_to_var, state="readonly", width=20)

    from_label = tk.Label(filter_frame, text=get_translation("date", module="teacher_rating_translation"), bg="#FFFFFF")
    to_label = tk.Label(filter_frame, text=get_translation("date_to", module="teacher_rating_translation"), bg="#FFFFFF")

    from_label.grid(row=0, column=0, padx=5)
    date_from_box.grid(row=0, column=1, padx=5)
    to_label.grid(row=0, column=2, padx=5)
    date_to_box.grid(row=0, column=3, padx=5)

    tk.Button(filter_frame, text=get_translation("show_ratings", module="teacher_rating_translation"),
              command=lambda: fetch_average(), font=("Roboto", 10), bg="#C8E6C9", relief="flat").grid(row=0, column=4, padx=10)

    result_frame = tk.Frame(root, bg="#FFFFFF")
    result_frame.pack(pady=10)

    def update_date_to_values(event=None):
        selected = date_from_var.get()
        if selected == "oldest_date":
            filtered = real_dates
        else:
            filtered = [d for d in real_dates if d >= selected]
        date_to_box["values"] = filtered
        if filtered:
            date_to_var.set(filtered[0])

    def update_filter_fields():
        is_range = mode_var.get() == "range"
        if is_range:
            from_label.config(text=get_translation("date_from", module="teacher_rating_translation"))
            to_label.grid()
            date_to_box.grid()
            date_from_box["values"] = ["oldest_date"] + real_dates
            date_from_var.set("oldest_date")
            update_date_to_values()
        else:
            from_label.config(text=get_translation("date", module="teacher_rating_translation"))
            to_label.grid_remove()
            date_to_box.grid_remove()
            date_from_box["values"] = ["all_time"] + real_dates
            date_from_var.set("all_time")

    def fetch_dates():
        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/teacher/{teacher_id}/grade-options")
                response.raise_for_status()
                data = response.json()
                nonlocal real_dates
                real_dates = sorted(data.get("dates", []))
                root.after(0, lambda: (
                    update_filter_fields(),
                    date_from_box.bind("<<ComboboxSelected>>", update_date_to_values)
                ))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_load_dates', module='teacher_rating_translation')}\n{str(e)}"
                ))
        threading.Thread(target=task).start()

    def fetch_average():
        for widget in result_frame.winfo_children():
            widget.destroy()

        is_range = mode_var.get() == "range"
        params = {}

        if is_range:
            params = {
                "from": "0000-00-00" if date_from_var.get() == "oldest_date" else date_from_var.get(),
                "to": date_to_var.get()
            }
        else:
            date = date_from_var.get()
            if date == "all_time":
                params = {"from": "0000-00-00", "to": "9999-12-31"}
            else:
                params = {"from": date, "to": date}

        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/teacher/{teacher_id}/average-ratings", params=params)
                response.raise_for_status()
                result = response.json()
                root.after(0, lambda: show_results(result))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_load_ratings', module='teacher_rating_translation')}\n{str(e)}"
                ))

        threading.Thread(target=task).start()

    def show_results(result):
        for widget in result_frame.winfo_children():
            widget.destroy()

        if not result:
            tk.Label(result_frame, text=get_translation("no_data", module="teacher_rating_translation"),
                     bg="#FFFFFF", font=("Roboto", 10)).pack()
            return

        for key in ["interest", "teaching", "comfort", "respect"]:
            row = tk.Frame(result_frame, bg="#FFFFFF")
            row.pack(pady=2)
            tk.Label(row, text=get_translation(key, module="teacher_rating_translation") + ":",
                     width=20, anchor="e", font=("Roboto", 10, "bold"), bg="#FFFFFF").pack(side="left")
            tk.Label(row, text=str(result.get(key, "-")), font=("Roboto", 10), bg="#FFFFFF").pack(side="left")

        tk.Label(result_frame, text="-" * 30, bg="#FFFFFF").pack(pady=5)
        row = tk.Frame(result_frame, bg="#FFFFFF")
        row.pack()
        tk.Label(row, text=get_translation("overall", module="teacher_rating_translation") + ":",
                 width=20, anchor="e", font=("Roboto", 10, "bold"), bg="#FFFFFF").pack(side="left")
        tk.Label(row, text=str(result.get("overall", "-")),
                 font=("Roboto", 10, "bold"), bg="#FFFFFF").pack(side="left")

    # === Назад и язык ===
    tk.Button(root, text=get_translation("back", module="shared_translation"),
              command=lambda: teacher_main_page(root, teacher_id),
              font=("Roboto", 10), width=20, bg="#E0E0E0", relief="flat").pack(pady=10)

    add_language_switcher(root, lambda: teacher_rating(root, teacher_id))

    real_dates = []
    fetch_dates()



