import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import colorchooser
import os
import sys

FONT_SIZE_MIN = 1
FONT_SIZE_MAX = 1000
DEFAULT_FONT_SIZE = 10

# Create or connect to SQLite database for themes
def connect_theme_db():
    conn = sqlite3.connect("salar.db")
    cursor = conn.cursor()
    
    # Create user_settings table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            theme_id INTEGER NOT NULL
        )
    """)

    # Check and add font_size column if it doesn't exist
    cursor.execute("PRAGMA table_info(user_settings)")
    columns = [column[1] for column in cursor.fetchall()]
    if "font_size" not in columns:
        cursor.execute("ALTER TABLE user_settings ADD COLUMN font_size INTEGER NOT NULL DEFAULT 12")
    
    # Check if settings exist, if not insert default theme (theme_id=1)
    cursor.execute("SELECT COUNT(*) FROM user_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO user_settings (theme_id, font_size) VALUES (?, ?)", (1, 12))
    
    conn.commit()
    conn.close()


# Create or connect to SQLite database for questions
def connect_db():
    conn = sqlite3.connect("xert.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            background_color TEXT NOT NULL,
            foreground_color TEXT NOT NULL,
            entry_background TEXT NOT NULL,
            entry_foreground TEXT NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM themes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO themes (name, background_color, foreground_color, entry_background, entry_foreground) VALUES (?, ?, ?, ?, ?)",
                       ("Dark", "black", "white", "gray", "white"))
        cursor.execute("INSERT INTO themes (name, background_color, foreground_color, entry_background, entry_foreground) VALUES (?, ?, ?, ?, ?)",
                       ("Light", "white", "black", "white", "black"))
    
    conn.commit()
    conn.close()


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


def load_questions():
    for row in tree.get_children():
        tree.delete(row)
    questions = fetch_sql("xert.db", "SELECT * FROM questions")
    for row in questions:
        tree.insert("", tk.END, values=row)


def load_themes():
    return fetch_sql("xert.db", "SELECT * FROM themes")


def add_question():
    question = entry_question.get()
    answer = entry_answer.get()

    if question and answer:
        exists = fetch_sql("xert.db", "SELECT COUNT(*) FROM questions WHERE question = ?", (question,))[0][0]
        if exists > 0:
            messagebox.showwarning("Warning", "This question already exists.")
        else:
            execute_sql("xert.db", "INSERT INTO questions (question, answer) VALUES (?, ?)", (question, answer))
            load_questions()
        clear_entries()
    else:
        messagebox.showwarning("Warning", "Please enter both question and answer.")


def edit_question():
    if not tree.selection():
        messagebox.showwarning("Warning", "Please select a question to edit.")
        return

    selected_item = tree.selection()[0]
    question_id = tree.item(selected_item)['values'][0]
    question = entry_question.get()
    answer = entry_answer.get()
    
    if question and answer:
        execute_sql("xert.db", "UPDATE questions SET question = ?, answer = ? WHERE id = ?", (question, answer, question_id))
        load_questions()
        clear_entries()
    else:
        messagebox.showwarning("Warning", "Please enter both question and answer.")


def delete_question():
    if not tree.selection():
        messagebox.showwarning("Warning", "Please select a question to delete.")
        return

    selected_item = tree.selection()[0]
    question_id = tree.item(selected_item)['values'][0]
    execute_sql("xert.db", "DELETE FROM questions WHERE id = ?", (question_id,))
    load_questions()


def select_item(event):
    if tree.selection():
        selected_item = tree.selection()[0]
        question = tree.item(selected_item)['values'][1]
        answer = tree.item(selected_item)['values'][2]

        entry_question.delete(0, tk.END)
        entry_answer.delete(0, tk.END)

        entry_question.insert(0, question)
        entry_answer.insert(0, answer)


def clear_entries():
    entry_question.delete(0, tk.END)
    entry_answer.delete(0, tk.END)


def search_questions():
    query = entry_search.get()
    for row in tree.get_children():
        tree.delete(row)

    results = fetch_sql("xert.db", "SELECT * FROM questions WHERE question LIKE ?", ("%" + query + "%",))
    for row in results:
        tree.insert("", tk.END, values=row)


def change_theme(selected_theme_index):
    themes = load_themes()
    if selected_theme_index < len(themes):
        selected_theme = themes[selected_theme_index]
        root.configure(bg=selected_theme[2])
        style.configure("TFrame", background=selected_theme[2])
        style.configure("TLabel", background=selected_theme[2], foreground=selected_theme[3])
        style.configure("TEntry", fieldbackground=selected_theme[4], foreground=selected_theme[5])
        style.configure("TButton", background=selected_theme[4], foreground=selected_theme[3])
        tree.configure(style='dark.Treeview' if selected_theme[1] == 'Dark' else 'light.Treeview')

        # Update user theme preference in 'salar.db'
        execute_sql("salar.db", "UPDATE user_settings SET theme_id = ?", (selected_theme[0],))


def apply_last_selected_theme():
    # Fetch theme_id from user_settings
    current_theme_id, font_size = fetch_sql("salar.db", "SELECT theme_id, font_size FROM user_settings")[0]
    change_theme(current_theme_id - 1)  # Subtract 1 to convert to zero-based index
    change_font_size(font_size)


def open_color_picker(entry):
    color = colorchooser.askcolor(parent=root)[1]
    if color:
        entry.delete(0, tk.END)
        entry.insert(0, color)


def open_new_theme_window():
    new_theme_window = tk.Toplevel(root)
    new_theme_window.title("Create New Theme")

    tk.Label(new_theme_window, text="Theme Name:").grid(row=0, column=0)
    entry_theme_name = tk.Entry(new_theme_window)
    entry_theme_name.grid(row=0, column=1)

    tk.Label(new_theme_window, text="Background Color:").grid(row=1, column=0)
    entry_bg_color = tk.Entry(new_theme_window)
    entry_bg_color.grid(row=1, column=1)
    tk.Button(new_theme_window, text="Select Color", command=lambda: open_color_picker(entry_bg_color)).grid(row=1, column=2)

    tk.Label(new_theme_window, text="Foreground Color:").grid(row=2, column=0)
    entry_fg_color = tk.Entry(new_theme_window)
    entry_fg_color.grid(row=2, column=1)
    tk.Button(new_theme_window, text="Select Color", command=lambda: open_color_picker(entry_fg_color)).grid(row=2, column=2)

    tk.Label(new_theme_window, text="Entry Background:").grid(row=3, column=0)
    entry_entry_bg = tk.Entry(new_theme_window)
    entry_entry_bg.grid(row=3, column=1)
    tk.Button(new_theme_window, text="Select Color", command=lambda: open_color_picker(entry_entry_bg)).grid(row=3, column=2)

    tk.Label(new_theme_window, text="Entry Foreground:").grid(row=4, column=0)
    entry_entry_fg = tk.Entry(new_theme_window)
    entry_entry_fg.grid(row=4, column=1)
    tk.Button(new_theme_window, text="Select Color", command=lambda: open_color_picker(entry_entry_fg)).grid(row=4, column=2)

    def save_theme():
        name = entry_theme_name.get()
        bg_color = entry_bg_color.get()
        fg_color = entry_fg_color.get()
        entry_bg = entry_entry_bg.get()
        entry_fg = entry_entry_fg.get()

        if name and bg_color and fg_color and entry_bg and entry_fg:
            execute_sql("xert.db", "INSERT INTO themes (name, background_color, foreground_color, entry_background, entry_foreground) VALUES (?, ?, ?, ?, ?)",
                        (name, bg_color, fg_color, entry_bg, entry_fg))
            messagebox.showinfo("Success", "Theme created successfully!")
            # Update theme menu
            update_theme_menu()
            new_theme_window.destroy()
        else:
            messagebox.showwarning("Warning", "Please enter all fields.")

    tk.Button(new_theme_window, text="Save Theme", command=save_theme).grid(row=5, columnspan=3)


def change_font_size(size):
    if FONT_SIZE_MIN <= size <= FONT_SIZE_MAX:
        style.configure("TLabel", font=("TkDefaultFont", size))
        style.configure("TButton", font=("TkDefaultFont", size))
        style.configure("TEntry", font=("TkDefaultFont", size))
        tree.tag_configure('default', font=("TkDefaultFont", size))
        execute_sql("salar.db", "UPDATE user_settings SET font_size = ?", (size,))
    else:
        messagebox.showwarning("Warning", f"Font size must be between {FONT_SIZE_MIN} and {FONT_SIZE_MAX}.")


def reset_font_size():
    change_font_size(DEFAULT_FONT_SIZE)

    # Restart the application
    execute_sql("salar.db", "UPDATE user_settings SET font_size = ?", (DEFAULT_FONT_SIZE,))
    messagebox.showinfo("Info", "Font size has been reset. The application will now restart.")
    python = sys.executable
    os.execl(python, python, *sys.argv)


def open_font_size_window():
    font_size_window = tk.Toplevel(root)
    font_size_window.title("Change Font Size")

    tk.Label(font_size_window, text="Font Size:").grid(row=0, column=0)
    spin_font_size = tk.Spinbox(font_size_window, from_=FONT_SIZE_MIN, to=FONT_SIZE_MAX, width=5)
    spin_font_size.grid(row=0, column=1)

    current_font_size = fetch_sql("salar.db", "SELECT font_size FROM user_settings")[0][0]
    spin_font_size.delete(0, tk.END)
    spin_font_size.insert(0, current_font_size)

    def update_font_size():
        try:
            size = int(spin_font_size.get())
            change_font_size(size)
            font_size_window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Invalid font size entered.")

    tk.Button(font_size_window, text="Apply", command=update_font_size).grid(row=0, column=2)

    tk.Button(font_size_window, text="Reset to Default", command=reset_font_size).grid(row=1, column=0, columnspan=3, pady=5)


def on_exit():
    if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
        root.quit()
        root.destroy()


def create_theme_menu(menu):
    themes = load_themes()
    for index, theme in enumerate(themes):
        menu.add_command(label=theme[1], command=lambda idx=index: change_theme(idx))


def update_theme_menu():
    theme_menu.delete(0, tk.END)
    theme_menu.add_command(label="Create New Theme", command=open_new_theme_window)
    theme_menu.add_separator()
    create_theme_menu(theme_menu)


# Create user interface
root = tk.Tk()
root.title("Questions Database")

# Menu Bar
menu_bar = tk.Menu(root)
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Exit", command=on_exit)
menu_bar.add_cascade(label="File", menu=file_menu)

# Font Size Menu
font_menu = tk.Menu(menu_bar, tearoff=0)
font_menu.add_command(label="Change Font Size", command=open_font_size_window)
font_menu.add_command(label="Reset Font Size", command=reset_font_size)
menu_bar.add_cascade(label="Font", menu=font_menu)

# Theme Menu
theme_menu = tk.Menu(menu_bar, tearoff=0)
theme_menu.add_command(label="Create New Theme", command=open_new_theme_window)
theme_menu.add_separator()
create_theme_menu(theme_menu)
menu_bar.add_cascade(label="Themes", menu=theme_menu)

# Help Menu
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Questions Database App Version 1.0"))
menu_bar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menu_bar)

# Style configurations
style = ttk.Style()
style.configure("Treeview", rowheight=25)
style.configure("TButton", padding=5)
style.configure('dark.Treeview', background='gray', foreground='white')
style.configure('light.Treeview', background='white', foreground='black')

# Connect to databases
connect_db()
connect_theme_db()

frame = tk.Frame(root)
frame.pack(pady=10)

entry_search = ttk.Entry(frame, width=30)
entry_search.grid(row=1, column=1, padx=5, pady=5)
ttk.Button(frame, text="Search", command=search_questions).grid(row=1, column=2, pady=5)
ttk.Label(frame, text="Search").grid(row=1, column=0)

entry_question = ttk.Entry(frame, width=30)
entry_question.grid(row=2, column=1, padx=5, pady=5)
ttk.Label(frame, text="Question").grid(row=2, column=0)

entry_answer = ttk.Entry(frame, width=30)
entry_answer.grid(row=3, column=1, padx=5, pady=5)
ttk.Label(frame, text="Answer").grid(row=3, column=0)

# Buttons
btn_add = ttk.Button(frame, text="Add Question", command=add_question)
btn_add.grid(row=4, columnspan=2, pady=5)

btn_edit = ttk.Button(frame, text="Edit Question", command=edit_question)
btn_edit.grid(row=5, columnspan=2, pady=5)

btn_delete = ttk.Button(frame, text="Delete Question", command=delete_question)
btn_delete.grid(row=6, columnspan=2, pady=5)

# Questions display table
tree = ttk.Treeview(root, columns=("ID", "Question", "Answer"), show='headings')
tree.heading("ID", text="ID")
tree.heading("Question", text="Question")
tree.heading("Answer", text="Answer")
tree.pack(pady=10)

tree.tag_configure('default', font=("TkDefaultFont", 12))
tree.bind("<<TreeviewSelect>>", select_item)

# Load data
load_questions()

# Apply the last selected theme and font size
apply_last_selected_theme()

root.mainloop()
