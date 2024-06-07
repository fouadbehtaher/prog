import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from PIL import Image, ImageTk
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Create the main window
window = tk.Tk()
window.title("Student Housing Management Application")
window.geometry("1200x800")

# Background Image
background_image_path = "background.jpg"  # Ensure this image is in the same directory
background_image = Image.open(background_image_path)
background_photo = ImageTk.PhotoImage(background_image)

background_label = tk.Label(window, image=background_photo)
background_label.place(relwidth=1, relheight=1)

# Background frame to hold all widgets on top of the background image
main_frame = tk.Frame(window, bg='#ffffff')
main_frame.place(relwidth=1, relheight=1)

# Connect to SQLite database
conn = sqlite3.connect('housing_extended.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS apartments
             (id INTEGER PRIMARY KEY AUTOINCREMENT, address TEXT, price REAL, description TEXT, images TEXT, video TEXT, user_role TEXT, user_id TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS users
             (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, role TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS actions
             (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, timestamp TEXT)''')
conn.commit()

# Global variables for pagination
page_size = 10
current_page = 0
uploaded_images = []

# Log Action
def log_action(action):
    c.execute("INSERT INTO actions (action, timestamp) VALUES (?, datetime('now'))", (action,))
    conn.commit()

# Function to add data to the database
def add_data():
    address = address_entry.get()
    price = price_entry.get()
    description = description_entry.get()
    user_role = user_role_var.get()
    user_id = user_id_entry.get()
    image_paths = ','.join(uploaded_images)
    video_path = video_entry.get()

    if not address or not price or not description or not user_id:
        messagebox.showerror("Input Error", "All fields are required.")
        return

    try:
        price = float(price)
    except ValueError:
        messagebox.showerror("Input Error", "Price must be a number.")
        return

    c.execute("INSERT INTO apartments (address, price, description, images, video, user_role, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (address, price, description, image_paths, video_path, user_role, user_id))
    conn.commit()
    log_action(f"Added apartment at {address}")
    messagebox.showinfo("Success", "Apartment added successfully.")
    clear_entries()
    load_data()
    load_user_data()

# Function to clear the input entries
def clear_entries():
    address_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    description_entry.delete(0, tk.END)
    user_role_var.set('Student')
    user_id_entry.delete(0, tk.END)
    uploaded_images.clear()
    update_image_preview()
    video_entry.delete(0, tk.END)
    toggle_user_id_entry()

# Function to load data from the database with pagination
def load_data(page=0):
    global current_page
    current_page = page
    for row in tree.get_children():
        tree.delete(row)

    c.execute("SELECT * FROM apartments LIMIT ? OFFSET ?", (page_size, page * page_size))
    for row in c.fetchall():
        tree.insert('', tk.END, values=row)

    update_pagination()

# Function to load all user data without pagination
def load_user_data():
    for row in user_data_tree.get_children():
        user_data_tree.delete(row)

    c.execute("SELECT * FROM apartments")
    for row in c.fetchall():
        user_data_tree.insert('', tk.END, values=row)

# Function to update data in the database
def update_data():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Selection Error", "No item selected.")
        return

    address = address_entry.get()
    price = price_entry.get()
    description = description_entry.get()
    user_role = user_role_var.get()
    user_id = user_id_entry.get()
    image_paths = ','.join(uploaded_images)
    video_path = video_entry.get()

    if not address or not price or not description or not user_id:
        messagebox.showerror("Input Error", "All fields are required.")
        return

    try:
        price = float(price)
    except ValueError:
        messagebox.showerror("Input Error", "Price must be a number.")
        return

    item_id = tree.item(selected_item)['values'][0]
    c.execute("UPDATE apartments SET address=?, price=?, description=?, images=?, video=?, user_role=?, user_id=? WHERE id=?",
              (address, price, description, image_paths, video_path, user_role, user_id, item_id))
    conn.commit()
    log_action(f"Updated apartment at {address}")
    messagebox.showinfo("Success", "Apartment updated successfully.")
    clear_entries()
    load_data(current_page)
    load_user_data()

# Function to delete data from the database
def delete_data():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Selection Error", "No item selected.")
        return

    item_id = tree.item(selected_item)['values'][0]
    c.execute("DELETE FROM apartments WHERE id=?", (item_id,))
    conn.commit()
    log_action(f"Deleted apartment with ID {item_id}")
    messagebox.showinfo("Success", "Apartment deleted successfully.")
    clear_entries()
    load_data(current_page)
    load_user_data()

# Function to search data in the database
def search_data():
    search_term = search_entry.get()
    for row in tree.get_children():
        tree.delete(row)

    c.execute("SELECT * FROM apartments WHERE address LIKE ? OR price LIKE ? OR description LIKE ? OR images LIKE ? OR video LIKE ? OR user_role LIKE ?",
              ('%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%', '%' + search_term + '%'))
    for row in c.fetchall():
        tree.insert('', tk.END, values=row)

# Function to clear search results and reload all data
def clear_search():
    search_entry.delete(0, tk.END)
    load_data()

# Function to view apartment details
def view_details():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Selection Error", "No item selected.")
        return

    item_id = tree.item(selected_item)['values'][0]
    c.execute("SELECT * FROM apartments WHERE id=?", (item_id,))
    apartment = c.fetchone()

    if apartment:
        details_window = tk.Toplevel(window)
        details_window.title("Apartment Details")
        details_window.geometry("400x400")

        address, price, description, images, video, user_role, user_id = apartment[1:]

        tk.Label(details_window, text=f"Address: {address}").pack(pady=5)
        tk.Label(details_window, text=f"Price: {price}").pack(pady=5)
        tk.Label(details_window, text=f"Description: {description}").pack(pady=5)
        tk.Label(details_window, text=f"User Role: {user_role}").pack(pady=5)
        tk.Label(details_window, text=f"User ID: {user_id}").pack(pady=5)

        if images:
            image_paths = images.split(',')
            for image_path in image_paths:
                img = Image.open(image_path)
                img.thumbnail((100, 100))
                img = ImageTk.PhotoImage(img)
                panel = tk.Label(details_window, image=img)
                panel.image = img
                panel.pack(pady=5)

        if video:
            tk.Label(details_window, text=f"Video: {video}").pack(pady=5)
            ttk.Button(details_window, text="Play Video", command=lambda: os.startfile(video)).pack(pady=5)

# Function to export data to a CSV file
def export_data():
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return

    c.execute("SELECT * FROM apartments")
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Address", "Price", "Description", "Images", "Video", "User Role", "User ID"])
        writer.writerows(c.fetchall())

    messagebox.showinfo("Success", "Data exported successfully.")

# Function to update pagination buttons
def update_pagination():
    total_records = c.execute("SELECT COUNT(*) FROM apartments").fetchone()[0]
    total_pages = (total_records + page_size - 1) // page_size
    prev_button.config(state=tk.NORMAL if current_page > 0 else tk.DISABLED)
    next_button.config(state=tk.NORMAL if current_page < total_pages - 1 else tk.DISABLED)

# Function to upload images
def upload_images():
    filenames = filedialog.askopenfilenames(title="Select Images", filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
    if len(uploaded_images) + len(filenames) > 6:
        messagebox.showerror("Image Error", "You can upload a maximum of 6 images.")
        return
    uploaded_images.extend(filenames)
    update_image_preview()

# Function to upload a video
def upload_video():
    filename = filedialog.askopenfilename(title="Select Video", filetypes=[("Video files", "*.mp4;*.mov;*.avi")])
    if filename:
        video_entry.delete(0, tk.END)
        video_entry.insert(0, filename)

# Function to update the image preview
def update_image_preview():
    for widget in image_frame.winfo_children():
        widget.destroy()
    for idx, image_path in enumerate(uploaded_images):
        img = Image.open(image_path)
        img.thumbnail((100, 100))
        img = ImageTk.PhotoImage(img)
        panel = tk.Label(image_frame, image=img)
        panel.image = img  # Keep a reference to avoid garbage collection
        panel.grid(row=0, column=idx, padx=5, pady=5)

# Function to load data with filters
def load_filtered_data():
    filter_term = filter_entry.get()
    for row in tree.get_children():
        tree.delete(row)

    query = "SELECT * FROM apartments WHERE user_role = ?"
    c.execute(query, (filter_term,))
    for row in c.fetchall():
        tree.insert('', tk.END, values=row)

# Function to load apartments by price range
def load_by_price_range():
    min_price = min_price_entry.get()
    max_price = max_price_entry.get()
    for row in tree.get_children():
        tree.delete(row)

    try:
        min_price = float(min_price)
        max_price = float(max_price)
    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numbers for price range.")
        return

    query = "SELECT * FROM apartments WHERE price BETWEEN ? AND ?"
    c.execute(query, (min_price, max_price))
    for row in c.fetchall():
        tree.insert('', tk.END, values=row)

# Additional functionalities
def reset_database():
    response = messagebox.askyesno("Reset Database", "Are you sure you want to reset the database? This action cannot be undone.")
    if response:
        c.execute("DROP TABLE IF EXISTS apartments")
        c.execute('''CREATE TABLE IF NOT EXISTS apartments
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, address TEXT, price REAL, description TEXT, images TEXT, video TEXT, user_role TEXT, user_id TEXT)''')
        conn.commit()
        load_data()
        load_user_data()
        messagebox.showinfo("Success", "Database has been reset.")

def change_address():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Selection Error", "No item selected.")
        return

    new_address = address_entry.get()
    if not new_address:
        messagebox.showerror("Input Error", "New address is required.")
        return

    item_id = tree.item(selected_item)['values'][0]
    c.execute("UPDATE apartments SET address=? WHERE id=?", (new_address, item_id))
    conn.commit()
    load_data(current_page)
    load_user_data()
    messagebox.showinfo("Success", "Address updated successfully.")

def advanced_search():
    search_term = search_entry.get()
    price_range = advanced_price_range_entry.get()
    min_price, max_price = 0, float('inf')

    if price_range:
        try:
            min_price, max_price = map(float, price_range.split('-'))
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid price range in the format 'min-max'.")
            return

    query = "SELECT * FROM apartments WHERE (address LIKE ? OR description LIKE ?) AND price BETWEEN ? AND ?"
    c.execute(query, ('%' + search_term + '%', '%' + search_term + '%', min_price, max_price))
    for row in tree.get_children():
        tree.delete(row)
    for row in c.fetchall():
        tree.insert('', tk.END, values=row)

# Function to toggle the visibility of the user ID entry field based on user role
def toggle_user_id_entry(*args):
    user_role = user_role_var.get()
    if user_role == "Student":
        user_id_label.config(text="Student ID:")
        user_id_entry.grid(column=1, row=4, padx=10, pady=10)
    elif user_role == "Management":
        user_id_label.config(text="National ID:")
        user_id_entry.grid(column=1, row=4, padx=10, pady=10)
    else:
        user_id_label.grid_remove()
        user_id_entry.grid_remove()

# Function to show recent actions
def show_recent_actions():
    recent_actions_window = tk.Toplevel(window)
    recent_actions_window.title("Recent Actions")
    recent_actions_window.geometry("400x400")
    actions_tree = ttk.Treeview(recent_actions_window, columns=("ID", "Action", "Timestamp"), show="headings")
    actions_tree.heading("ID", text="ID")
    actions_tree.heading("Action", text="Action")
    actions_tree.heading("Timestamp", text="Timestamp")
    actions_tree.pack(expand=True, fill='both')
    c.execute("SELECT * FROM actions ORDER BY timestamp DESC LIMIT 100")
    for row in c.fetchall():
        actions_tree.insert('', tk.END, values=row)

# Create notebook for tabs
notebook = ttk.Notebook(main_frame)
notebook.pack(expand=1, fill='both')

# Create first tab for data entry
entry_frame = ttk.Frame(notebook)
notebook.add(entry_frame, text="Data Entry")

# Create second tab for data display
display_frame = ttk.Frame(notebook)
notebook.add(display_frame, text="Data Display")

# Create third tab for data management
management_frame = ttk.Frame(notebook)
notebook.add(management_frame, text="Data Management")

# Create fourth tab for filters
filter_frame = ttk.Frame(notebook)
notebook.add(filter_frame, text="Filters")

# Create fifth tab for advanced features
advanced_frame = ttk.Frame(notebook)
notebook.add(advanced_frame, text="Advanced Features")

# Create sixth tab for user data
user_data_frame = ttk.Frame(notebook)
notebook.add(user_data_frame, text="User Data")

# Create seventh tab for recent actions
actions_frame = ttk.Frame(notebook)
notebook.add(actions_frame, text="Recent Actions")

# Widgets for data entry tab
ttk.Label(entry_frame, text="Address:").grid(column=0, row=0, padx=10, pady=10)
address_entry = ttk.Entry(entry_frame)
address_entry.grid(column=1, row=0, padx=10, pady=10)

ttk.Label(entry_frame, text="Price:").grid(column=0, row=1, padx=10, pady=10)
price_entry = ttk.Entry(entry_frame)
price_entry.grid(column=1, row=1, padx=10, pady=10)

ttk.Label(entry_frame, text="Description:").grid(column=0, row=2, padx=10, pady=10)
description_entry = ttk.Entry(entry_frame)
description_entry.grid(column=1, row=2, padx=10, pady=10)

# User Role dropdown
ttk.Label(entry_frame, text="User Role:").grid(column=0, row=3, padx=10, pady=10)
user_role_var = tk.StringVar(value="Student")
user_role_var.trace('w', toggle_user_id_entry)
user_role_menu = ttk.Combobox(entry_frame, textvariable=user_role_var, values=["Student", "Management"])
user_role_menu.grid(column=1, row=3, padx=10, pady=10)

# User ID entry
user_id_label = ttk.Label(entry_frame)
user_id_label.grid(column=0, row=4, padx=10, pady=10)
user_id_entry = ttk.Entry(entry_frame)

# Image upload
ttk.Button(entry_frame, text="Upload Images", command=upload_images).grid(column=0, row=5, padx=10, pady=10)

image_frame = ttk.Frame(entry_frame)
image_frame.grid(column=1, row=5, padx=10, pady=10)

# Video upload
ttk.Label(entry_frame, text="Video:").grid(column=0, row=6, padx=10, pady=10)
video_entry = ttk.Entry(entry_frame)
video_entry.grid(column=1, row=6, padx=10, pady=10)
ttk.Button(entry_frame, text="Upload Video", command=upload_video).grid(column=2, row=6, padx=10, pady=10)

add_button = ttk.Button(entry_frame, text="Add Apartment", command=add_data)
add_button.grid(column=0, row=7, padx=10, pady=10)

update_button = ttk.Button(entry_frame, text="Update Apartment", command=update_data)
update_button.grid(column=1, row=7, padx=10, pady=10)

delete_button = ttk.Button(entry_frame, text="Delete Apartment", command=delete_data)
delete_button.grid(column=2, row=7, padx=10, pady=10)

# Widgets for data display tab
ttk.Label(display_frame, text="Search:").grid(column=0, row=0, padx=10, pady=10)
search_entry = ttk.Entry(display_frame)
search_entry.grid(column=1, row=0, padx=10, pady=10)
search_button = ttk.Button(display_frame, text="Search", command=search_data)
search_button.grid(column=2, row=0, padx=10, pady=10)
clear_search_button = ttk.Button(display_frame, text="Clear Search", command=clear_search)
clear_search_button.grid(column=3, row=0, padx=10, pady=10)

view_details_button = ttk.Button(display_frame, text="View Details", command=view_details)
view_details_button.grid(column=1, row=1, padx=10, pady=10)
export_button = ttk.Button(display_frame, text="Export to CSV", command=export_data)
export_button.grid(column=0, row=1, padx=10, pady=10)

# Create a Treeview to display data
columns = ("id", "address", "price", "description", "images", "video", "user_role", "user_id")
tree = ttk.Treeview(display_frame, columns=columns, show='headings')
for col in columns:
    tree.heading(col, text=col.capitalize())
tree.grid(column=0, row=2, columnspan=4, padx=10, pady=10)

# Pagination buttons
prev_button = ttk.Button(display_frame, text="Previous", command=lambda: load_data(current_page - 1))
prev_button.grid(column=0, row=3, padx=10, pady=10)
next_button = ttk.Button(display_frame, text="Next", command=lambda: load_data(current_page + 1))
next_button.grid(column=2, row=3, padx=10, pady=10)

# Widgets for data management tab
ttk.Label(management_frame, text="Search:").grid(column=0, row=0, padx=10, pady=10)
management_search_entry = ttk.Entry(management_frame)
management_search_entry.grid(column=1, row=0, padx=10, pady=10)
management_search_button = ttk.Button(management_frame, text="Search", command=search_data)
management_search_button.grid(column=2, row=0, padx=10, pady=10)
management_clear_search_button = ttk.Button(management_frame, text="Clear Search", command=clear_search)
management_clear_search_button.grid(column=3, row=0, padx=10, pady=10)

management_view_details_button = ttk.Button(management_frame, text="View Details", command=view_details)
management_view_details_button.grid(column=1, row=1, padx=10, pady=10)
management_export_button = ttk.Button(management_frame, text="Export to CSV", command=export_data)
management_export_button.grid(column=0, row=1, padx=10, pady=10)

# Create a Treeview to display data in the management tab
management_tree = ttk.Treeview(management_frame, columns=columns, show='headings')
for col in columns:
    management_tree.heading(col, text=col.capitalize())
management_tree.grid(column=0, row=2, columnspan=4, padx=10, pady=10)

# Pagination buttons for the management tab
management_prev_button = ttk.Button(management_frame, text="Previous", command=lambda: load_data(current_page - 1))
management_prev_button.grid(column=0, row=3, padx=10, pady=10)
management_next_button = ttk.Button(management_frame, text="Next", command=lambda: load_data(current_page + 1))
management_next_button.grid(column=2, row=3, padx=10, pady=10)

# Widgets for filter tab
ttk.Label(filter_frame, text="Filter by User Role:").grid(column=0, row=0, padx=10, pady=10)
filter_entry = ttk.Entry(filter_frame)
filter_entry.grid(column=1, row=0, padx=10, pady=10)
filter_button = ttk.Button(filter_frame, text="Filter", command=load_filtered_data)
filter_button.grid(column=2, row=0, padx=10, pady=10)

ttk.Label(filter_frame, text="Filter by Price Range:").grid(column=0, row=1, padx=10, pady=10)
ttk.Label(filter_frame, text="Min Price:").grid(column=0, row=2, padx=10, pady=10)
min_price_entry = ttk.Entry(filter_frame)
min_price_entry.grid(column=1, row=2, padx=10, pady=10)
ttk.Label(filter_frame, text="Max Price:").grid(column=0, row=3, padx=10, pady=10)
max_price_entry = ttk.Entry(filter_frame)
max_price_entry.grid(column=1, row=3, padx=10, pady=10)
price_range_button = ttk.Button(filter_frame, text="Filter by Price Range", command=load_by_price_range)
price_range_button.grid(column=2, row=3, padx=10, pady=10)

# Widgets for advanced features tab
ttk.Label(advanced_frame, text="Advanced Search:").grid(column=0, row=0, padx=10, pady=10)
advanced_price_range_entry = ttk.Entry(advanced_frame)
advanced_price_range_entry.grid(column=1, row=0, padx=10, pady=10)
advanced_search_button = ttk.Button(advanced_frame, text="Search", command=advanced_search)
advanced_search_button.grid(column=2, row=0, padx=10, pady=10)

reset_button = ttk.Button(advanced_frame, text="Reset Database", command=reset_database)
reset_button.grid(column=0, row=1, padx=10, pady=10)

change_address_button = ttk.Button(advanced_frame, text="Change Address", command=change_address)
change_address_button.grid(column=1, row=1, padx=10, pady=10)

# Widgets for user data tab
user_data_tree = ttk.Treeview(user_data_frame, columns=columns, show='headings')
for col in columns:
    user_data_tree.heading(col, text=col.capitalize())
user_data_tree.grid(column=0, row=0, columnspan=4, padx=10, pady=10)

# Widgets for recent actions tab
actions_tree = ttk.Treeview(actions_frame, columns=("ID", "Action", "Timestamp"), show="headings")
actions_tree.heading("ID", text="ID")
actions_tree.heading("Action", text="Action")
actions_tree.heading("Timestamp", text="Timestamp")
actions_tree.grid(column=0, row=0, columnspan=4, padx=10, pady=10)
show_recent_actions_button = ttk.Button(actions_frame, text="Refresh", command=show_recent_actions)
show_recent_actions_button.grid(column=0, row=1, padx=10, pady=10)

# Initial data load
load_data()
load_user_data()

# Run the Tkinter event loop
window.mainloop()

# Close the database connection when done
conn.close()
