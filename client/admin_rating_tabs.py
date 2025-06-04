import tkinter as tk
from tkinter import ttk, messagebox
import threading

from client.utils.ui import authorized_get, sanitize_date, date_range_values
from client.admin_detailed_student_ratings import admin_detailed_student_ratings
from client.admin_detailed_teacher_ratings import admin_detailed_teacher_ratings
from client.config import SERVER_URL
from client.translation.translation_func import get_translation

def reverse_translate(value, mapping_keys, module):
    for key in mapping_keys:
        if get_translation(key, module=module) == value:
            return key
    return value

def populate_student_ratings_tab(tab_frame, root):
    tab_frame.configure(bg="#FFFFFF")
    tk.Label(tab_frame, text=get_translation("student_ratings_title", module="admin_view_rating_translation"),
             font=("Roboto", 12, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=10)

    mode_var = tk.StringVar(value="range")
    date_from_var = tk.StringVar()
    date_to_var = tk.StringVar()
    teacher_var = tk.StringVar(value=get_translation("all", module="shared_translation"))
    class_var = tk.StringVar(value=get_translation("all", module="shared_translation"))
    group_var = tk.StringVar(value=get_translation("all", module="shared_translation"))
    sort_var = tk.StringVar(value=get_translation("overall", module="shared_translation"))
    sort_order_var = tk.StringVar(value=get_translation("desc", module="shared_translation"))
    date_options = []

    def switch_mode(mode):
        mode_var.set(mode)
        if mode == "single":
            from_label.config(text=get_translation("date", module="shared_translation"))
            to_label.grid_remove()
            to_combo.grid_remove()
        else:
            from_label.config(text=get_translation("from", module="shared_translation"))
            to_label.grid()
            to_combo.grid()
        update_date_comboboxes()

    def load_data():
        def task():
            try:
                if mode_var.get() == "single":
                    date_from = sanitize_date(date_from_var.get(), True)
                    date_to = sanitize_date(date_from_var.get(), False)
                else:
                    if date_from_var.get() == get_translation("oldest_date", module="shared_translation"):
                        date_from = None
                    else:
                        date_from = sanitize_date(date_from_var.get(), True)
                    date_to = sanitize_date(date_to_var.get(), False)

                params = {
                    "date_from": date_from,
                    "date_to": date_to,
                    "teacher": None if teacher_var.get() == get_translation("all", module="shared_translation") else teacher_var.get(),
                    "class": None if class_var.get() == get_translation("all", module="shared_translation") else class_var.get(),
                    "group": None if group_var.get() == get_translation("all", module="shared_translation") else group_var.get(),
                    "sort": reverse_translate(sort_var.get(), ["attendance", "participation", "effort", "respect", "overall"], "admin_view_rating_translation"),
                    "order": reverse_translate(sort_order_var.get(), ["asc", "desc"], "shared_translation")
                }
                response = authorized_get(f"{SERVER_URL}/admin/student-ratings", params=params)
                records = response.json()
                root.after(0, lambda: display_data(records))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_load_ratings', module='admin_view_rating_translation')}\n{e}"
                ))
        threading.Thread(target=task).start()

    def on_tree_click(event):
        item_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not item_id or col != "#8":
            return
        student_name = tree.item(item_id, "values")[0]

        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/admin/student-id-by-name", params={"name": student_name})
                student_id = response.json()["id"]
                root.after(0, lambda: admin_detailed_student_ratings(root, student_id))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_open_account', module='admin_view_rating_translation')}\n{e}"
                ))
        threading.Thread(target=task).start()

    mode_frame = tk.Frame(tab_frame, bg="#FFFFFF")
    mode_frame.pack(pady=5)
    tk.Label(mode_frame, text=get_translation("date_mode", module="shared_translation"), bg="#FFFFFF", fg="#1976D2", font=("Roboto", 10, "bold")).pack(side="left")
    tk.Radiobutton(mode_frame, text=get_translation("single_date", module="shared_translation"), variable=mode_var, value="single", bg="#FFFFFF", command=lambda: switch_mode("single"), font=("Roboto", 10)).pack(side="left")
    tk.Radiobutton(mode_frame, text=get_translation("date_range", module="shared_translation"), variable=mode_var, value="range", bg="#FFFFFF", command=lambda: switch_mode("range"), font=("Roboto", 10)).pack(side="left")

    filter_frame = tk.Frame(tab_frame, bg="#FFFFFF")
    filter_frame.pack(pady=5)

    from_label = tk.Label(filter_frame, text=get_translation("from", module="shared_translation"), bg="#FFFFFF", fg="#1976D2")
    from_label.grid(row=0, column=0, padx=5)
    from_combo = ttk.Combobox(filter_frame, textvariable=date_from_var, width=12)
    from_combo.grid(row=0, column=1, padx=5)

    to_label = tk.Label(filter_frame, text=get_translation("to", module="shared_translation"), bg="#FFFFFF", fg="#1976D2")
    to_label.grid(row=0, column=2, padx=5)
    to_combo = ttk.Combobox(filter_frame, textvariable=date_to_var, width=12)
    to_combo.grid(row=0, column=3, padx=5)

    tk.Label(filter_frame, text=get_translation("teacher", module="admin_view_rating_translation"), bg="#FFFFFF", fg="#1976D2").grid(row=1, column=0, padx=5)
    teacher_box = ttk.Combobox(filter_frame, textvariable=teacher_var, width=20)
    teacher_box.grid(row=1, column=1, padx=5)

    tk.Label(filter_frame, text=get_translation("class", module="admin_view_rating_translation"), bg="#FFFFFF", fg="#1976D2").grid(row=1, column=2, padx=5)
    class_box = ttk.Combobox(filter_frame, textvariable=class_var, width=10)
    class_box.grid(row=1, column=3, padx=5)

    tk.Label(filter_frame, text=get_translation("group", module="admin_view_rating_translation"), bg="#FFFFFF", fg="#1976D2").grid(row=1, column=4, padx=5)
    group_box = ttk.Combobox(filter_frame, textvariable=group_var, width=15)
    group_box.grid(row=1, column=5, padx=5)

    tk.Button(filter_frame, text=get_translation("refresh", module="shared_translation"), command=load_data,
              font=("Roboto", 10, "bold"), bg="#1976D2", fg="white", activebackground="#1976D2", activeforeground="white",
              relief="flat", bd=0, padx=10, pady=2).grid(row=0, column=6, padx=10)

    sort_frame = tk.Frame(tab_frame, bg="#FFFFFF")
    sort_frame.pack(pady=5)
    tk.Label(sort_frame, text=get_translation("sort_by", module="shared_translation"), bg="#FFFFFF", fg="#1976D2").grid(row=0, column=0)
    ttk.Combobox(sort_frame, textvariable=sort_var,
                 values=[
                     get_translation("attendance", module="admin_view_rating_translation"),
                     get_translation("participation", module="admin_view_rating_translation"),
                     get_translation("effort", module="admin_view_rating_translation"),
                     get_translation("respect", module="admin_view_rating_translation"),
                     get_translation("overall", module="shared_translation")
                 ], width=15).grid(row=0, column=1, padx=5)

    tk.Label(sort_frame, text=get_translation("order", module="shared_translation"), bg="#FFFFFF", fg="#1976D2").grid(row=0, column=2)
    ttk.Combobox(sort_frame, textvariable=sort_order_var,
                 values=[
                     get_translation("asc", module="shared_translation"),
                     get_translation("desc", module="shared_translation")
                 ], width=10, state="readonly").grid(row=0, column=3, padx=5)

    columns = ("name", "class", "attendance", "participation", "effort", "respect", "overall", "account")
    tree = ttk.Treeview(tab_frame, columns=columns, show="headings", height=20)
    for col in columns:
        tree.heading(col, text=get_translation(col, module="admin_view_rating_translation"))
        tree.column(col, anchor="center", width=100)
    tree.pack(pady=10, fill="both", expand=True)
    tree.bind("<Button-1>", on_tree_click)

    def update_date_comboboxes():
        if mode_var.get() == "single":
            from_combo["values"] = date_options
            to_combo["values"] = []
        else:
            trimmed_dates = [d for d in date_options if d != get_translation("all_time", module="shared_translation")]
            from_combo["values"] = [get_translation("oldest_date", module="shared_translation")] + trimmed_dates
            if date_from_var.get() in trimmed_dates:
                index = trimmed_dates.index(date_from_var.get())
                to_combo["values"] = trimmed_dates[index:]
            else:
                to_combo["values"] = trimmed_dates

    def set_dates(dates):
        nonlocal date_options
        date_options = dates
        date_from_var.set(dates[0])
        date_to_var.set(dates[-1])
        update_date_comboboxes()

    def load_date_options():
        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/admin/student-ratings/filters")
                data = response.json()
                dates = date_range_values(data["dates"])
                root.after(0, lambda: set_dates(dates))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_load_dates', module='admin_view_rating_translation')}\n{e}"
                ))
        threading.Thread(target=task).start()

    def load_filters():
        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/admin/student-ratings/filters")
                data = response.json()
                root.after(0, lambda: set_filters(data))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_load_filters', module='admin_view_rating_translation')}\n{e}"
                ))
        threading.Thread(target=task).start()

    def set_filters(data):
        teacher_box["values"] = [get_translation("all", module="shared_translation")] + data["teachers"]
        class_box["values"] = [get_translation("all", module="shared_translation")] + data["classes"]
        group_box["values"] = [get_translation("all", module="shared_translation")] + data["groups"]



    def display_data(records):
        tree.delete(*tree.get_children())
        for r in records:
            tree.insert("", "end", values=(r["name"], r["class"], r["attendance"], r["participation"],
                                             r["effort"], r["respect"], r["overall"], "🔎"))



    load_filters()
    load_date_options()
    load_data()

def populate_teacher_ratings_tab(tab_frame, root):
    tab_frame.configure(bg="#FFFFFF")
    tk.Label(tab_frame, text=get_translation("teacher_ratings_title", module="admin_view_rating_translation"),
             font=("Roboto", 12, "bold"), bg="#FFFFFF", fg="#1976D2").pack(pady=10)

    mode_var = tk.StringVar(value="range")
    date_from_var = tk.StringVar()
    date_to_var = tk.StringVar()
    teacher_var = tk.StringVar(value=get_translation("all", module="shared_translation"))
    sort_var = tk.StringVar(value=get_translation("overall", module="shared_translation"))
    sort_order_var = tk.StringVar(value=get_translation("desc", module="shared_translation"))
    date_options = []

    def switch_mode(mode):
        mode_var.set(mode)
        if mode == "single":
            from_label.config(text=get_translation("date", module="shared_translation"))
            to_label.grid_remove()
            to_combo.grid_remove()
        else:
            from_label.config(text=get_translation("from", module="shared_translation"))
            to_label.grid()
            to_combo.grid()
        update_date_comboboxes()

    def load_data():
        def task():
            try:
                if mode_var.get() == "single":
                    date_from = sanitize_date(date_from_var.get(), True)
                    date_to = sanitize_date(date_from_var.get(), False)
                else:
                    if date_from_var.get() == get_translation("oldest_date", module="shared_translation"):
                        date_from = None
                    else:
                        date_from = sanitize_date(date_from_var.get(), True)
                    date_to = sanitize_date(date_to_var.get(), False)

                params = {
                    "date_from": date_from,
                    "date_to": date_to,
                    "teacher": None if teacher_var.get() == get_translation("all", module="shared_translation") else teacher_var.get(),
                    "sort": reverse_translate(sort_var.get(), ["interest", "teaching", "comfort", "respect", "overall"], "admin_view_rating_translation"),
                    "order": reverse_translate(sort_order_var.get(), ["asc", "desc"], "shared_translation")
                }
                response = authorized_get(f"{SERVER_URL}/admin/teacher-ratings", params=params)
                records = response.json()
                root.after(0, lambda: display_data(records))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_load_ratings', module='admin_view_rating_translation')}\n{e}"
                ))
        threading.Thread(target=task).start()

    def on_tree_click(event):
        item_id = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not item_id or col != "#7":
            return
        teacher_name = tree.item(item_id, "values")[0]

        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/admin/teacher-id-by-name", params={"name": teacher_name})
                teacher_id = response.json()["id"]
                root.after(0, lambda: admin_detailed_teacher_ratings(root, teacher_id))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_open_account', module='admin_view_rating_translation')}\n{e}"
                ))
        threading.Thread(target=task).start()

    mode_frame = tk.Frame(tab_frame, bg="#FFFFFF")
    mode_frame.pack(pady=5)
    tk.Label(mode_frame, text=get_translation("date_mode", module="shared_translation"), bg="#FFFFFF", fg="#1976D2", font=("Roboto", 10, "bold")).pack(side="left")
    tk.Radiobutton(mode_frame, text=get_translation("single_date", module="shared_translation"), variable=mode_var, value="single", bg="#FFFFFF", command=lambda: switch_mode("single"), font=("Roboto", 10)).pack(side="left")
    tk.Radiobutton(mode_frame, text=get_translation("date_range", module="shared_translation"), variable=mode_var, value="range", bg="#FFFFFF", command=lambda: switch_mode("range"), font=("Roboto", 10)).pack(side="left")

    filter_frame = tk.Frame(tab_frame, bg="#FFFFFF")
    filter_frame.pack(pady=5)

    from_label = tk.Label(filter_frame, text=get_translation("from", module="shared_translation"), bg="#FFFFFF", fg="#1976D2")
    from_label.grid(row=0, column=0, padx=5)
    from_combo = ttk.Combobox(filter_frame, textvariable=date_from_var, width=12)
    from_combo.grid(row=0, column=1, padx=5)

    to_label = tk.Label(filter_frame, text=get_translation("to", module="shared_translation"), bg="#FFFFFF", fg="#1976D2")
    to_label.grid(row=0, column=2, padx=5)
    to_combo = ttk.Combobox(filter_frame, textvariable=date_to_var, width=12)
    to_combo.grid(row=0, column=3, padx=5)

    tk.Label(filter_frame, text=get_translation("teacher", module="admin_view_rating_translation"), bg="#FFFFFF", fg="#1976D2").grid(row=1, column=0, padx=5)
    teacher_box = ttk.Combobox(filter_frame, textvariable=teacher_var, width=25)
    teacher_box.grid(row=1, column=1, padx=5)

    tk.Button(filter_frame, text=get_translation("refresh", module="shared_translation"), command=load_data,
              font=("Roboto", 10, "bold"), bg="#1976D2", fg="white", activebackground="#1976D2", activeforeground="white",
              relief="flat", bd=0, padx=10, pady=2).grid(row=0, column=4, padx=10)

    sort_frame = tk.Frame(tab_frame, bg="#FFFFFF")
    sort_frame.pack(pady=5)
    tk.Label(sort_frame, text=get_translation("sort_by", module="shared_translation"), bg="#FFFFFF", fg="#1976D2").grid(row=0, column=0)
    ttk.Combobox(sort_frame, textvariable=sort_var,
                 values=[
                     get_translation("interest", module="admin_view_rating_translation"),
                     get_translation("teaching", module="admin_view_rating_translation"),
                     get_translation("comfort", module="admin_view_rating_translation"),
                     get_translation("respect", module="admin_view_rating_translation"),
                     get_translation("overall", module="shared_translation")
                 ], width=15).grid(row=0, column=1, padx=5)

    tk.Label(sort_frame, text=get_translation("order", module="shared_translation"), bg="#FFFFFF", fg="#1976D2").grid(row=0, column=2)
    ttk.Combobox(sort_frame, textvariable=sort_order_var,
                 values=[
                     get_translation("asc", module="shared_translation"),
                     get_translation("desc", module="shared_translation")
                 ], width=10, state="readonly").grid(row=0, column=3, padx=5)

    columns = ("name", "interest", "teaching", "comfort", "respect", "overall", "account")
    tree = ttk.Treeview(tab_frame, columns=columns, show="headings", height=20)
    for col in columns:
        tree.heading(col, text=get_translation(col, module="admin_view_rating_translation"))
        tree.column(col, anchor="center", width=100)
    tree.pack(pady=10, fill="both", expand=True)
    tree.bind("<Button-1>", on_tree_click)

    def update_date_comboboxes():
        if mode_var.get() == "single":
            from_combo["values"] = date_options
            to_combo["values"] = []
        else:
            trimmed_dates = [d for d in date_options if d != get_translation("all_time", module="shared_translation")]
            from_combo["values"] = [get_translation("oldest_date", module="shared_translation")] + trimmed_dates
            if date_from_var.get() in trimmed_dates:
                index = trimmed_dates.index(date_from_var.get())
                to_combo["values"] = trimmed_dates[index:]
            else:
                to_combo["values"] = trimmed_dates

    def set_dates(dates):
        nonlocal date_options
        date_options = dates
        date_from_var.set(dates[0])
        date_to_var.set(dates[-1])
        update_date_comboboxes()

    def load_date_options():
        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/admin/student-ratings/filters")
                data = response.json()
                dates = date_range_values(data["dates"])
                root.after(0, lambda: set_dates(dates))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_load_dates', module='admin_view_rating_translation')}\n{e}"
                ))
        threading.Thread(target=task).start()

    def load_filters():
        def task():
            try:
                response = authorized_get(f"{SERVER_URL}/auth/teachers")
                teachers = [t["name"] for t in response.json()]
                root.after(0, lambda: teacher_box.configure(values=[get_translation("all", module="shared_translation")] + teachers))
            except Exception as e:
                root.after(0, lambda: messagebox.showerror(
                    get_translation("error_title", module="errors_translation"),
                    f"{get_translation('error_load_teachers', module='admin_view_rating_translation')}\n{e}"
                ))
        threading.Thread(target=task).start()



    def display_data(records):
        tree.delete(*tree.get_children())
        for r in records:
            tree.insert("", "end", values=(r["name"], r["interest"], r["teaching"], r["comfort"], r["respect"], r["overall"], "🔎"))



    load_filters()
    load_date_options()
    load_data()



