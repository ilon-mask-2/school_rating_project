import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from client.utils.ui import authorized_post, authorized_get
from client.utils.ui import clear_root, ScrollFrame, add_language_switcher
from client.config import SERVER_URL
from client.translation.translation_func import get_translation

def student_rating1(root, student_id):
    from client.student_main_page import student_main_page
    clear_root(root)
    root.configure(bg="#FFFFFF")

    scroll = ScrollFrame(root, bg="#FFFFFF")
    scroll.pack(fill="both", expand=True)
    container = scroll.scrollable_frame
    container.configure(bg="#FFFFFF")

    tk.Label(container, text="📊 " + get_translation("teacher_ratings", module="student_rating_translation"),
             font=("Roboto", 14, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=10)

    avg_frame = tk.LabelFrame(container, text=get_translation("avg_title", module="student_rating_translation"),
                              font=("Roboto", 12, "bold"), bg="#FFFFFF", fg="#1976D2")
    avg_frame.pack(fill="x", padx=10, pady=10)

    det_frame = tk.LabelFrame(container, text=get_translation("det_title", module="student_rating_translation"),
                              font=("Roboto", 12, "bold"), bg="#FFFFFF", fg="#1976D2")
    det_frame.pack(fill="both", expand=True, padx=10, pady=10)

    date_from_var = tk.StringVar(value=get_translation("all_dates", module="student_rating_translation"))
    date_to_var = tk.StringVar(value=get_translation("all_dates", module="student_rating_translation"))
    teacher_avg_var = tk.StringVar(value="All")

    date_from_det = tk.StringVar(value=get_translation("all_dates", module="student_rating_translation"))
    date_to_det = tk.StringVar(value=get_translation("all_dates", module="student_rating_translation"))
    teacher_det_var = tk.StringVar(value="All")

    date_options = [get_translation("all_dates", module="student_rating_translation")]
    teacher_options = ["All"]

    avg_filter = tk.Frame(avg_frame, bg="#FFFFFF")
    avg_filter.pack(pady=5)

    ttk.Label(avg_filter, text=get_translation("from", module="shared_translation"), background="#FFFFFF").grid(row=0, column=0, padx=5)
    from_avg_box = ttk.Combobox(avg_filter, textvariable=date_from_var, state="readonly", width=20)
    from_avg_box.grid(row=0, column=1)

    ttk.Label(avg_filter, text=get_translation("to", module="shared_translation"), background="#FFFFFF").grid(row=1, column=0, padx=5)
    to_avg_box = ttk.Combobox(avg_filter, textvariable=date_to_var, state="readonly", width=20)
    to_avg_box.grid(row=1, column=1)

    ttk.Label(avg_filter, text=get_translation("teacher", module="student_rating_translation"), background="#FFFFFF").grid(row=2, column=0, padx=5)
    teacher_avg_box = ttk.Combobox(avg_filter, textvariable=teacher_avg_var, state="readonly", width=20)
    teacher_avg_box.grid(row=2, column=1)

    avg_content = tk.Frame(avg_frame, bg="#FFFFFF")
    avg_content.pack()

    det_filter = tk.Frame(det_frame, bg="#FFFFFF")
    det_filter.pack(pady=5)

    ttk.Label(det_filter, text=get_translation("from", module="shared_translation"), background="#FFFFFF").grid(row=0, column=0, padx=5)
    from_det_box = ttk.Combobox(det_filter, textvariable=date_from_det, state="readonly", width=20)
    from_det_box.grid(row=0, column=1)

    ttk.Label(det_filter, text=get_translation("to", module="shared_translation"), background="#FFFFFF").grid(row=1, column=0, padx=5)
    to_det_box = ttk.Combobox(det_filter, textvariable=date_to_det, state="readonly", width=20)
    to_det_box.grid(row=1, column=1)

    ttk.Label(det_filter, text=get_translation("teacher", module="student_rating_translation"), background="#FFFFFF").grid(row=2, column=0, padx=5)
    teacher_det_box = ttk.Combobox(det_filter, textvariable=teacher_det_var, state="readonly", width=20)
    teacher_det_box.grid(row=2, column=1)

    det_content = tk.Frame(det_frame, bg="#FFFFFF")
    det_content.pack()

    def load_filter_options():
        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/student/{student_id}/grade-options")
                response.raise_for_status()
                data = response.json()
                dates = [get_translation("all_dates", module="student_rating_translation")] + sorted(data.get("dates", []))
                teachers = ["All"] + sorted(data.get("teachers", []))
                root.after(0, lambda: apply_filters(dates, teachers))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_filter_load', module='student_rating_translation')}\n{e}"))

        def apply_filters(dates, teachers):
            nonlocal date_options, teacher_options
            date_options = dates
            teacher_options = teachers

            for box in [from_avg_box, to_avg_box, from_det_box, to_det_box]:
                box["values"] = date_options

            for box in [teacher_avg_box, teacher_det_box]:
                box["values"] = teacher_options

            date_from_var.set(date_options[0])
            date_to_var.set(date_options[0])
            date_from_det.set(date_options[0])
            date_to_det.set(date_options[0])
            teacher_avg_var.set("All")
            teacher_det_var.set("All")

        threading.Thread(target=task).start()

    def fetch_avg():
        def task():
            for widget in avg_content.winfo_children():
                widget.destroy()

            params = {
                "from": "0000-00-00" if date_from_var.get() == get_translation("all_dates", module="student_rating_translation") else date_from_var.get(),
                "to": "9999-12-31" if date_to_var.get() == get_translation("all_dates", module="student_rating_translation") else date_to_var.get(),
                "teacher": teacher_avg_var.get()
            }

            try:
                res = authorized_get(f"{SERVER_URL}/student/{student_id}/average-ratings", params=params)
                res.raise_for_status()
                result = res.json()
                root.after(0, lambda: display_avg(result))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_fetch_avg', module='student_rating_translation')}\n{e}"))

        def display_avg(result):
            for widget in avg_content.winfo_children():
                widget.destroy()

            if not result:
                tk.Label(avg_content, text=get_translation("no_data", module="student_rating_translation"), bg="#FFFFFF").pack()
                return

            for label, key in [(get_translation("attendance", module="student_rating_translation"), "attendance"),
                               (get_translation("participation", module="student_rating_translation"), "participation"),
                               (get_translation("effort", module="student_rating_translation"), "effort"),
                               (get_translation("respect", module="student_rating_translation"), "respect")]:
                row = tk.Frame(avg_content, bg="#FFFFFF")
                row.pack(anchor="w")
                tk.Label(row, text=f"{label}:", width=20, bg="#FFFFFF").pack(side="left")
                tk.Label(row, text=result.get(key, "-"), bg="#FFFFFF").pack(side="left")

            tk.Label(avg_content, text="-" * 30, bg="#FFFFFF").pack(pady=5)
            row = tk.Frame(avg_content, bg="#FFFFFF")
            row.pack()
            tk.Label(row, text=get_translation("overall", module="student_rating_translation"), width=20, bg="#FFFFFF").pack(side="left")
            tk.Label(row, text=result.get("overall", "-"), font=("Roboto", 10, "bold"), bg="#FFFFFF").pack(side="left")

        threading.Thread(target=task).start()

    def fetch_det():
        def task():
            for widget in det_content.winfo_children():
                widget.destroy()

            params = {
                "from": "0000-00-00" if date_from_det.get() == get_translation("all_dates", module="student_rating_translation") else date_from_det.get(),
                "to": "9999-12-31" if date_to_det.get() == get_translation("all_dates", module="student_rating_translation") else date_to_det.get(),
                "teacher": teacher_det_var.get()
            }

            try:
                res = authorized_get(f"{SERVER_URL}/student/{student_id}/detailed-ratings", params=params)
                res.raise_for_status()
                records = res.json()
                root.after(0, lambda: display_det(records))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_fetch_det', module='student_rating_translation')}\n{e}"))

        def display_det(records):
            for widget in det_content.winfo_children():
                widget.destroy()

            if not records:
                tk.Label(det_content, text=get_translation("no_ratings", module="student_rating_translation"), bg="#FFFFFF").pack()
                return

            for rec in records:
                box = tk.LabelFrame(det_content, text=f"{rec['teacher']} — {rec['date']}", padx=5, pady=5, bg="#FFFFFF")
                box.pack(fill="x", pady=5)
                for lbl, val in [(get_translation("attendance", module="student_rating_translation"), rec["attendance"]),
                                 (get_translation("participation", module="student_rating_translation"), rec["participation"]),
                                 (get_translation("effort", module="student_rating_translation"), rec["effort"]),
                                 (get_translation("respect", module="student_rating_translation"), rec["respect"])]:
                    row = tk.Frame(box, bg="#FFFFFF")
                    row.pack(anchor="w")
                    tk.Label(row, text=f"{lbl}:", width=20, anchor="e", bg="#FFFFFF").pack(side="left")
                    tk.Label(row, text=val, bg="#FFFFFF").pack(side="left")

        threading.Thread(target=task).start()

    tk.Button(avg_frame, text=get_translation("show_avg", module="student_rating_translation"),
              command=fetch_avg, font=("Roboto", 10), bg="#1976D2", fg="white", relief="flat", width=30).pack(pady=5)
    tk.Button(det_frame, text=get_translation("show_det", module="student_rating_translation"),
              command=fetch_det, font=("Roboto", 10), bg="#1976D2", fg="white", relief="flat", width=30).pack(pady=5)

    tk.Button(container, text=get_translation("back", module="shared_translation"),
              command=lambda: student_main_page(root, student_id), font=("Roboto", 10), bg="#E0E0E0", relief="flat", width=20).pack(pady=20)

    add_language_switcher(container, lambda: student_rating(root, student_id))
    load_filter_options()

def student_rating(root, student_id):
    import tkinter as tk
    from tkinter import ttk, messagebox
    import threading
    from client.utils.ui import clear_root, authorized_get, ScrollFrame, add_language_switcher
    from client.translation.translation_func import get_translation
    from client.student_main_page import student_main_page

    SERVER_URL = "http://127.0.0.1:5000"
    clear_root(root)
    root.configure(bg="#FFFFFF")

    scroll = ScrollFrame(root, bg="#FFFFFF")
    scroll.pack(fill="both", expand=True)
    container = scroll.scrollable_frame
    container.configure(bg="#FFFFFF")

    tk.Label(container, text="📊 " + get_translation("student_rating_title", module="student_rating_translation"),
             font=("Roboto", 14, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=10)

    # ============ ФУНКЦИИ ОБЩИЕ ============

    def get_dates_and_teachers(callback):
        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/student/{student_id}/grade-options")
                response.raise_for_status()
                data = response.json()
                root.after(0, lambda: callback(data.get("dates", []), data.get("teachers", [])))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           f"{get_translation('error_filter_load', module='student_rating_translation')}\n{e}"))
        threading.Thread(target=task).start()

    def apply_filter_widgets(frame, label_prefix, fetch_func):
        mode_var = tk.StringVar(value="single")
        date_var = tk.StringVar()
        date_from_var = tk.StringVar()
        date_to_var = tk.StringVar()
        teacher_var = tk.StringVar(value="All")

        all_dates = []
        teacher_list = []

        date_widgets = {}

        def switch_mode(mode):
            for widget in date_widgets.values():
                widget.grid_remove()
            if mode == "single":
                date_widgets["date_label"].grid(row=1, column=0, padx=5, sticky="e")
                date_widgets["date_combo"].grid(row=1, column=1, padx=5)
            else:
                date_widgets["from_label"].grid(row=1, column=0, padx=5, sticky="e")
                date_widgets["from_combo"].grid(row=1, column=1, padx=5)
                date_widgets["to_label"].grid(row=2, column=0, padx=5, sticky="e")
                date_widgets["to_combo"].grid(row=2, column=1, padx=5)

        filter_frame = tk.Frame(frame, bg="#FFFFFF")
        filter_frame.pack(pady=5)

        tk.Label(filter_frame, text=get_translation("mode", module="teacher_rating_translation"),
                 bg="#FFFFFF", font=("Roboto", 10)).grid(row=0, column=0, padx=5)

        tk.Button(filter_frame, text=get_translation("date", module="teacher_rating_translation"),
                  command=lambda: (mode_var.set("single"), switch_mode("single")),
                  font=("Roboto", 9), bg="#E0F7FA", relief="flat").grid(row=0, column=1, padx=5)
        tk.Button(filter_frame, text=get_translation("date_from", module="teacher_rating_translation") + " → " +
                                    get_translation("date_to", module="teacher_rating_translation"),
                  command=lambda: (mode_var.set("range"), switch_mode("range")),
                  font=("Roboto", 9), bg="#FFF9C4", relief="flat").grid(row=0, column=2, padx=5)

        # Одиночная дата
        date_widgets["date_label"] = tk.Label(filter_frame, text=get_translation("date", module="teacher_rating_translation"), bg="#FFFFFF")
        date_widgets["date_combo"] = ttk.Combobox(filter_frame, textvariable=date_var, state="readonly", width=25)

        # Диапазон дат
        date_widgets["from_label"] = tk.Label(filter_frame, text=get_translation("date_from", module="teacher_rating_translation"), bg="#FFFFFF")
        date_widgets["from_combo"] = ttk.Combobox(filter_frame, textvariable=date_from_var, state="readonly", width=25)

        date_widgets["to_label"] = tk.Label(filter_frame, text=get_translation("date_to", module="teacher_rating_translation"), bg="#FFFFFF")
        date_widgets["to_combo"] = ttk.Combobox(filter_frame, textvariable=date_to_var, state="readonly", width=25)

        # Преподаватель
        tk.Label(filter_frame, text=get_translation("teacher", module="student_rating_translation"),
                 bg="#FFFFFF").grid(row=3, column=0, padx=5)
        teacher_combo = ttk.Combobox(filter_frame, textvariable=teacher_var, state="readonly", width=25)
        teacher_combo.grid(row=3, column=1, padx=5)

        # Контент
        content_frame = tk.Frame(frame, bg="#FFFFFF")
        content_frame.pack(pady=5)

        # Кнопка "Показать"
        def get_params():
            if mode_var.get() == "single":
                date = date_var.get()
                return {
                    "from": date if date != get_translation("all_time", module="teacher_rating_translation") else "0000-00-00",
                    "to": date if date != get_translation("all_time", module="teacher_rating_translation") else "9999-12-31",
                    "teacher": teacher_var.get()
                }
            else:
                return {
                    "from": date_from_var.get() if date_from_var.get() != get_translation("oldest_date", module="teacher_rating_translation") else "0000-00-00",
                    "to": date_to_var.get(),
                    "teacher": teacher_var.get()
                }

        tk.Button(frame, text=get_translation("show_ratings", module="teacher_rating_translation"),
                  command=lambda: fetch_func(get_params(), content_frame),
                  font=("Roboto", 10), bg="#C8E6C9", relief="flat", width=30).pack(pady=5)

        # Подгрузка значений
        def update_values(dates, teachers):
            nonlocal all_dates, teacher_list
            all_dates = dates
            teacher_list = teachers

            # Single date
            single_date_options = [get_translation("all_time", module="teacher_rating_translation")] + sorted(dates)
            date_widgets["date_combo"]["values"] = single_date_options
            date_var.set(single_date_options[0])

            # Range
            range_from = [get_translation("oldest_date", module="teacher_rating_translation")] + sorted(dates)
            date_widgets["from_combo"]["values"] = range_from
            date_from_var.set(range_from[0])

            date_widgets["to_combo"]["values"] = sorted(dates)
            date_to_var.set(dates[-1] if dates else "")

            teacher_combo["values"] = ["All"] + teachers
            teacher_var.set("All")

            switch_mode("single")

        get_dates_and_teachers(update_values)

    # ============ СРЕДНИЕ ОЦЕНКИ ============
    avg_frame = tk.LabelFrame(container, text=get_translation("avg_title", module="student_rating_translation"),
                              font=("Roboto", 12, "bold"), bg="#FFFFFF", fg="#1976D2")
    avg_frame.pack(fill="x", padx=10, pady=10)

    def fetch_avg(params, content_frame):
        def task():
            for widget in content_frame.winfo_children():
                widget.destroy()
            try:
                res = authorized_get(f"{SERVER_URL}/student/{student_id}/average-ratings", params=params)
                res.raise_for_status()
                result = res.json()
                root.after(0, lambda: display_avg(result, content_frame))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           get_translation("error_load_ratings", module="student_rating_translation") + f"\n{e}"))
        def display_avg(result, frame):
            if not result:
                tk.Label(frame, text=get_translation("no_data", module="student_rating_translation"), bg="#FFFFFF").pack()
                return
            for label, key in [(get_translation("attendance", module="student_rating_translation"), "attendance"),
                               (get_translation("participation", module="student_rating_translation"), "participation"),
                               (get_translation("effort", module="student_rating_translation"), "effort"),
                               (get_translation("respect", module="student_rating_translation"), "respect")]:
                row = tk.Frame(frame, bg="#FFFFFF")
                row.pack(anchor="w")
                tk.Label(row, text=f"{label}:", width=20, bg="#FFFFFF").pack(side="left")
                tk.Label(row, text=result.get(key, "-"), bg="#FFFFFF").pack(side="left")
            tk.Label(frame, text="-" * 30, bg="#FFFFFF").pack(pady=5)
            row = tk.Frame(frame, bg="#FFFFFF")
            row.pack()
            tk.Label(row, text=get_translation("overall", module="student_rating_translation"), width=20, bg="#FFFFFF").pack(side="left")
            tk.Label(row, text=result.get("overall", "-"), font=("Roboto", 10, "bold"), bg="#FFFFFF").pack(side="left")

        threading.Thread(target=task).start()

    apply_filter_widgets(avg_frame, "avg", fetch_avg)

    # ============ ДЕТАЛЬНЫЕ ОЦЕНКИ ============
    det_frame = tk.LabelFrame(container, text=get_translation("det_title", module="student_rating_translation"),
                              font=("Roboto", 12, "bold"), bg="#FFFFFF", fg="#1976D2")
    det_frame.pack(fill="x", padx=10, pady=10)

    def fetch_det(params, content_frame):
        def task():
            for widget in content_frame.winfo_children():
                widget.destroy()
            try:
                res = authorized_get(f"{SERVER_URL}/student/{student_id}/detailed-ratings", params=params)
                res.raise_for_status()
                records = res.json()
                root.after(0, lambda: display_det(records, content_frame))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(get_translation("error_title", module="errors_translation"),
                                                           get_translation("error_load_ratings", module="student_rating_translation") + f"\n{e}"))
        def display_det(records, frame):
            if not records:
                tk.Label(frame, text=get_translation("no_ratings", module="student_rating_translation"), bg="#FFFFFF").pack()
                return
            for rec in records:
                box = tk.LabelFrame(frame, text=f"{rec['teacher']} — {rec['date']}", padx=5, pady=5, bg="#FFFFFF")
                box.pack(fill="x", pady=5)
                for lbl, val in [(get_translation("attendance", module="student_rating_translation"), rec["attendance"]),
                                 (get_translation("participation", module="student_rating_translation"), rec["participation"]),
                                 (get_translation("effort", module="student_rating_translation"), rec["effort"]),
                                 (get_translation("respect", module="student_rating_translation"), rec["respect"])]:
                    row = tk.Frame(box, bg="#FFFFFF")
                    row.pack(anchor="w")
                    tk.Label(row, text=f"{lbl}:", width=20, anchor="e", bg="#FFFFFF").pack(side="left")
                    tk.Label(row, text=val, bg="#FFFFFF").pack(side="left")

        threading.Thread(target=task).start()

    apply_filter_widgets(det_frame, "det", fetch_det)

    # Кнопка Назад и переключатель языка
    tk.Button(container, text=get_translation("back", module="shared_translation"),
              command=lambda: student_main_page(root, student_id), font=("Roboto", 10),
              bg="#E0E0E0", relief="flat", width=20).pack(pady=20)
    add_language_switcher(container, lambda: student_rating(root, student_id))