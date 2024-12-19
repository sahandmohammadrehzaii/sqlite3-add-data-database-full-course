import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk, colorchooser
import os
import sys
from datetime import datetime, timedelta

# --- تنظیمات اولیه ---
FONT_SIZE_MIN = 1
FONT_SIZE_MAX = 1000
DEFAULT_FONT_SIZE = 10
PERMANENT_PASSWORD = "1234567890123456"  # رمز عبور دائمی 16 رقمی

# --- اتصال به دیتابیس‌ها ---
def connect_theme_db():
    conn = sqlite3.connect("database/salar.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme_id INTEGER NOT NULL,
            font_size INTEGER NOT NULL DEFAULT 12
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM user_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO user_settings (theme_id, font_size) VALUES (?, ?)", (1, 12))
    conn.commit()
    conn.close()

def connect_question_db():
    conn = sqlite3.connect("database/xert.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def connect_betf_db():
    conn = sqlite3.connect("database/betf.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_date TEXT NOT NULL,
            access_granted INTEGER NOT NULL DEFAULT 0
        )
    """)
    cursor.execute("SELECT COUNT(*) FROM app_access")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO app_access (start_date, access_granted) VALUES (?, ?)", (now, 0))
    conn.commit()
    conn.close()

# --- توابع پایگاه داده ---
def execute_sql(db_name, query, params=()):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def fetch_sql(db_name, query, params=()):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result

# --- بررسی دسترسی ---
def check_access():
    data = fetch_sql("database/betf.db", "SELECT start_date, access_granted FROM app_access LIMIT 1")[0]
    start_date = datetime.strptime(data[0], "%Y-%m-%d")
    access_granted = bool(data[1])
    current_date = datetime.now()

    if access_granted:
        return True

    if current_date > start_date + timedelta(days=0):
        return False

    return True

def activate_program():
    password_window = tk.Toplevel(root)
    password_window.title("Enter Activation Code")

    tk.Label(password_window, text="Enter 16-Digit Activation Code:").grid(row=0, column=0, padx=10, pady=10)
    entry_password = ttk.Entry(password_window, show="*", width=30)
    entry_password.grid(row=1, column=0, padx=10, pady=10)

    def validate_password():
        entered_password = entry_password.get()
        if entered_password == PERMANENT_PASSWORD:
            execute_sql("database/betf.db", "UPDATE app_access SET access_granted = 1 WHERE id = 1")
            messagebox.showinfo("Success", "Program activated successfully!")
            password_window.destroy()
            app_reload()
        else:
            messagebox.showerror("Error", "Invalid activation code.")

    ttk.Button(password_window, text="Activate", command=validate_password).grid(row=2, column=0, padx=10, pady=10)

def app_reload():
    python = sys.executable
    os.execl(python, python, *sys.argv)

# --- اگر دسترسی محدود باشد، پنجره فعال‌سازی نمایش داده می‌شود ---
def enforce_access():
    if not check_access():
        msg = """
        Your 30-day trial period has ended.
        Please enter a 16-digit activation code to unlock the program.
        """
        messagebox.showerror("Activation Required", msg)
        activate_program()
        root.wait_window()

# --- توابع مدیریت سوالات ---
def load_questions():
    for row in tree.get_children():
        tree.delete(row)
    questions = fetch_sql("database/xert.db", "SELECT * FROM questions")
    for row in questions:
        tree.insert("", tk.END, values=row)

def add_question():
    question = entry_question.get()
    answer = entry_answer.get()
    if question and answer:
        execute_sql("database/xert.db", "INSERT INTO questions (question, answer) VALUES (?, ?)", (question, answer))
        load_questions()
        entry_question.delete(0, tk.END)
        entry_answer.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Please fill in both Question and Answer fields.")

def edit_question():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "Please select a question to edit.")
        return

    question_id = tree.item(selected_item[0])["values"][0]
    edited_question = entry_question.get()
    edited_answer = entry_answer.get()
    if edited_question and edited_answer:
        execute_sql("database/xert.db", "UPDATE questions SET question = ?, answer = ? WHERE id = ?",
                    (edited_question, edited_answer, question_id))
        load_questions()
        entry_question.delete(0, tk.END)
        entry_answer.delete(0, tk.END)
    else:
        messagebox.showwarning("Warning", "Please enter both Question and Answer fields.")

def delete_question():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("Warning", "Please select a question to delete.")
        return

    question_id = tree.item(selected_item[0])["values"][0]
    execute_sql("database/xert.db", "DELETE FROM questions WHERE id = ?", (question_id,))
    load_questions()

def select_item(event):
    selected_item = tree.selection()
    if not selected_item:
        return
    question = tree.item(selected_item[0])["values"][1]
    answer = tree.item(selected_item[0])["values"][2]
    entry_question.delete(0, tk.END)
    entry_question.insert(0, question)
    entry_answer.delete(0, tk.END)
    entry_answer.insert(0, answer)

# --- رابط کاربری ---
root = tk.Tk()
root.title("Questions Database")

# منوی بالا
menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)
root.config(menu=menu_bar)

# فریم ورودی‌ها
frame = tk.Frame(root)
frame.pack(pady=10)

entry_question = ttk.Entry(frame, width=30)
entry_question.grid(row=0, column=1, padx=5, pady=5)
ttk.Label(frame, text="Question: ").grid(row=0, column=0)

entry_answer = ttk.Entry(frame, width=30)
entry_answer.grid(row=1, column=1, padx=5, pady=5)
ttk.Label(frame, text="Answer: ").grid(row=1, column=0)

btn_add = ttk.Button(frame, text="Add Question", command=add_question)
btn_add.grid(row=2, column=0, pady=5)

btn_edit = ttk.Button(frame, text="Edit Question", command=edit_question)
btn_edit.grid(row=2, column=1, pady=5)

btn_delete = ttk.Button(frame, text="Delete Question", command=delete_question)
btn_delete.grid(row=2, column=2, pady=5)

# جدول نمایش سوالات
tree = ttk.Treeview(root, columns=("ID", "Question", "Answer"), show='headings')
tree.heading("ID", text="ID")
tree.heading("Question", text="Question")
tree.heading("Answer", text="Answer")
tree.pack(pady=10)
tree.bind("<<TreeviewSelect>>", select_item)

# اجرای الزامات
connect_theme_db()
connect_question_db()
connect_betf_db()
enforce_access()
load_questions()

# اجرا
root.mainloop()
