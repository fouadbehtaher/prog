import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import sqlite3
import ttkbootstrap as tb
import logging
import pandas as pd
import numpy as np
import os
import bcrypt
import time

# Set up logging
logging.basicConfig(filename='application.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

def validate_username(username):
    if len(username) < 5:
        return "Username must be at least 5 characters long"
    if not username.isalnum():
        return "Username must be alphanumeric"
    return None

def validate_password(password):
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    return None

def validate_price(price):
    try:
        price = float(price)
        if price < 0:
            return "Price must be a positive number"
    except ValueError:
        return "Price must be a number"
    return None

class SessionManager:
    def __init__(self):
        self.logged_in_users = {}

    def login(self, username):
        session_token = hash_password(username + str(time.time()))
        self.logged_in_users[session_token] = username
        return session_token

    def logout(self, session_token):
        if session_token in self.logged_in_users:
            del self.logged_in_users[session_token]

    def is_logged_in(self, session_token):
        return session_token in self.logged_in_users

session_manager = SessionManager()

class Application(tb.Window):
    def __init__(self):
        super().__init__(themename="darkly")
        self.title("User Information Application")
        self.geometry("1000x700")
        self.bind("<Configure>", self.on_resize)

        self.sidebar_visible = True

        self.sidebar_frame = ttk.Frame(self, width=200, style="primary.TFrame")
        self.sidebar_frame.grid(row=0, column=0, sticky="ns")
        self.create_sidebar()

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=1, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_database()
        self.create_register_page()
        self.create_login_page()
        self.create_dashboard_page()

    def on_resize(self, event):
        self.geometry(f"{event.width}x{event.height}")

    def setup_database(self):
        self.conn = sqlite3.connect('user_data.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS users
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          role TEXT,
                          user_id TEXT,
                          name TEXT,
                          price REAL,
                          description TEXT,
                          image BLOB,
                          video BLOB,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS accounts
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          username TEXT UNIQUE,
                          password TEXT)''')
        self.conn.commit()

    def create_register_page(self):
        self.register_page = ttk.Frame(self.notebook)
        self.notebook.add(self.register_page, text="Register")

        ttk.Label(self.register_page, text="Create an Account", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)
        self.create_form(self.register_page, [
            ("Username:", "reg_username_var"),
            ("Password:", "reg_password_var", "*")
        ])
        ttk.Button(self.register_page, text="Register", command=self.register_account, style="success.TButton").grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(self.register_page, text="Go to Login", command=self.go_to_login, style="info.TButton").grid(row=4, column=0, columnspan=2, pady=5)

    def create_login_page(self):
        self.login_page = ttk.Frame(self.notebook)
        self.notebook.add(self.login_page, text="Login")

        self.create_form(self.login_page, [
            ("Username:", "username_var"),
            ("Password:", "password_var", "*")
        ])
        ttk.Button(self.login_page, text="Login", command=self.login, style="success.TButton").grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(self.login_page, text="Create Account", command=self.go_to_register, style="info.TButton").grid(row=3, column=0, columnspan=2, pady=5)

    def create_form(self, parent, fields):
        for i, (label_text, var_name, *show) in enumerate(fields):
            ttk.Label(parent, text=label_text, font=('Helvetica', 12)).grid(row=i, column=0, sticky="e", pady=5)
            setattr(self, var_name, tk.StringVar())
            entry = ttk.Entry(parent, textvariable=getattr(self, var_name), show=show[0] if show else "")
            entry.grid(row=i, column=1, pady=5)
            entry.bind("<Enter>", lambda e: entry.config(style="info.TEntry"))
            entry.bind("<Leave>", lambda e: entry.config(style="TEntry"))

    def register_account(self):
        """
        This function registers a new account. It validates the input,
        hashes the password, and stores the account information in the database.
        """
        username = self.reg_username_var.get()
        password = self.reg_password_var.get()

        username_error = validate_username(username)
        password_error = validate_password(password)

        if username_error:
            messagebox.showerror("Error", username_error)
            return
        if password_error:
            messagebox.showerror("Error", password_error)
            return

        hashed_password = hash_password(password)

        try:
            self.c.execute("INSERT INTO accounts (username, password) VALUES (?, ?)", (username, hashed_password))
            self.conn.commit()
            messagebox.showinfo("Success", "Account created successfully")
            self.go_to_login()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
        except Exception as e:
            logging.error(f"Error registering account: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again.")

    def login(self):
        """
        This function handles the login process. It validates the input,
        checks the password, and sets the current user if successful.
        """
        username = self.username_var.get()
        password = self.password_var.get()

        self.c.execute("SELECT * FROM accounts WHERE username=?", (username,))
        account = self.c.fetchone()

        if account and check_password(account[2], password):
            self.current_user = username
            self.show_main_pages()
            self.notebook.forget(self.login_page)
            self.notebook.forget(self.register_page)
            self.notebook.select(self.dashboard_page)
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def go_to_register(self):
        self.notebook.select(self.register_page)

    def go_to_login(self):
        self.notebook.select(self.login_page)

    def show_main_pages(self):
        if not hasattr(self, 'welcome_page'):
            self.create_welcome_page()
        if not hasattr(self, 'main_display_page'):
            self.create_main_display_page()
        if not hasattr(self, 'search_page'):
            self.create_search_page()
        if not hasattr(self, 'my_listings_page'):
            self.create_my_listings_page()
        if not hasattr(self, 'profile_page'):
            self.create_profile_page()

    def create_dashboard_page(self):
        self.dashboard_page = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_page, text="Dashboard")

        ttk.Label(self.dashboard_page, text="Dashboard", font=('Helvetica', 18, 'bold')).grid(row=0, column=0, pady=10)

        buttons = [
            ("Welcome", lambda: self.notebook.select(self.welcome_page)),
            ("Main Display", lambda: self.notebook.select(self.main_display_page)),
            ("Search", lambda: self.notebook.select(self.search_page)),
            ("My Listings", lambda: self.notebook.select(self.my_listings_page)),
            ("Profile", lambda: self.notebook.select(self.profile_page))
        ]

        for i, (text, command) in enumerate(buttons):
            ttk.Button(self.dashboard_page, text=text, command=command, style="primary.TButton").grid(row=i+1, column=0, pady=5)

    def create_welcome_page(self):
        self.welcome_page = ttk.Frame(self.notebook)
        self.notebook.add(self.welcome_page, text="Welcome")

        ttk.Label(self.welcome_page, text="Welcome! Please select your role:", font=('Helvetica', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)

        self.role_var = tk.StringVar()
        student_rb = ttk.Radiobutton(self.welcome_page, text="Student", variable=self.role_var, value="Student")
        owner_rb = ttk.Radiobutton(self.welcome_page, text="Owner", variable=self.role_var, value="Owner")
        student_rb.grid(row=1, column=0, pady=5)
        owner_rb.grid(row=1, column=1, pady=5)

        ttk.Button(self.welcome_page, text="Next", command=self.show_next_page, style="success.TButton").grid(row=2, column=0, columnspan=2, pady=20)

    def show_next_page(self):
        role = self.role_var.get()
        if role == "Student":
            self.create_student_page()
        elif role == "Owner":
            self.create_owner_page()
            self.title("Student Housing")
        else:
            messagebox.showerror("Error", "Please select a role")
        self.notebook.forget(self.welcome_page)

    def create_student_page(self):
        if hasattr(self, 'student_page'):
            self.notebook.select(self.student_page)
            return

        self.student_page = ttk.Frame(self.notebook)
        self.notebook.add(self.student_page, text="Student Information")
        self.notebook.select(self.student_page)

        ttk.Label(self.student_page, text="Student ID:", font=('Helvetica', 12)).grid(row=0, column=0, sticky="e", pady=5)
        self.student_id_var = tk.StringVar()
        ttk.Entry(self.student_page, textvariable=self.student_id_var).grid(row=0, column=1, pady=5)

        self.common_input_fields(self.student_page, "Student")

        ttk.Button(self.student_page, text="Save Data", command=self.save_data, style="success.TButton").grid(row=7, column=0, columnspan=2, pady=20)

    def create_owner_page(self):
        if hasattr(self, 'owner_page'):
            self.notebook.select(self.owner_page)
            return

        self.owner_page = ttk.Frame(self.notebook)
        self.notebook.add(self.owner_page, text="Owner Information")
        self.notebook.select(self.owner_page)

        ttk.Label(self.owner_page, text="National ID (15 digits):", font=('Helvetica', 12)).grid(row=0, column=0, sticky="e", pady=5)
        self.owner_id_var = tk.StringVar()
        self.owner_id_entry = ttk.Entry(self.owner_page, textvariable=self.owner_id_var)
        self.owner_id_entry.grid(row=0, column=1, pady=5)

        self.common_input_fields(self.owner_page, "Owner")

        ttk.Button(self.owner_page, text="Save Data", command=self.save_data, style="success.TButton").grid(row=7, column=0, columnspan=2, pady=20)

    def common_input_fields(self, page, role):
        ttk.Label(page, text="Name:", font=('Helvetica', 12)).grid(row=1, column=0, sticky="e", pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(page, textvariable=self.name_var).grid(row=1, column=1, pady=5)

        if role == "Owner":
            ttk.Label(page, text="Enter the rental price you want:", font=('Helvetica', 12)).grid(row=2, column=0, sticky="e", pady=5)
        else:
            ttk.Label(page, text="Price:", font=('Helvetica', 12)).grid(row=2, column=0, sticky="e", pady=5)

        self.price_var = tk.DoubleVar()
        ttk.Entry(page, textvariable=self.price_var).grid(row=2, column=1, pady=5)

        ttk.Label(page, text="Description:", font=('Helvetica', 12)).grid(row=3, column=0, sticky="e", pady=5)
        self.description_var = tk.StringVar()
        self.description_combobox = ttk.Combobox(page, textvariable=self.description_var)
        self.description_combobox['values'] = ("Standard Room", "Air-conditioned Room", "Bed") if role == "Student" else ("Student Bed", "Room with Two Beds", "Air-conditioned Room")
        self.description_combobox.grid(row=3, column=1, pady=5)

        ttk.Label(page, text="Image (optional):", font=('Helvetica', 12)).grid(row=4, column=0, sticky="e", pady=5)
        self.image_path_var = tk.StringVar()
        ttk.Button(page, text="Upload Image", command=self.load_image, style="info.TButton").grid(row=4, column=1, pady=5)
        self.image_label = ttk.Label(page)
        self.image_label.grid(row=5, column=0, columnspan=2, pady=5)

        ttk.Label(page, text="Video (optional):", font=('Helvetica', 12)).grid(row=6, column=0, sticky="e", pady=5)
        self.video_path_var = tk.StringVar()
        ttk.Button(page, text="Upload Video", command=self.load_video, style="info.TButton").grid(row=6, column=1, pady=5)
        self.video_label = ttk.Label(page)
        self.video_label.grid(row=7, column=0, columnspan=2, pady=5)

    def load_image(self):
        image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
        if image_path:
            self.image_path_var.set(image_path)
            image = Image.open(image_path)
            image = image.resize((100, 100), Image.ANTIALIAS)
            self.photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=self.photo)
            self.image_label.image = self.photo

    def load_video(self):
        video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi")])
        if video_path:
            self.video_path_var.set(video_path)
            self.video_label.config(text=video_path)

    def save_data(self):
        """
        This function saves the user data to the database. It validates the input,
        converts the image and video to binary, and stores the information in the database.
        """
        role = self.role_var.get()
        user_id = self.student_id_var.get() if role == "Student" else self.owner_id_var.get()

        if role == "Owner" and (len(user_id) != 15 or not user_id.isdigit()):
            messagebox.showerror("Error", "National ID must be 15 digits")
            return

        name = self.name_var.get()
        price = self.price_var.get()
        description = self.description_var.get()
        image = self.image_path_var.get()
        video = self.video_path_var.get()

        if not user_id or not name or not price or not description:
            messagebox.showerror("Error", "Please fill out all required fields")
            return

        try:
            # Convert image and video to binary
            with open(image, 'rb') as img_file:
                img_blob = img_file.read()
            with open(video, 'rb') as vid_file:
                vid_blob = vid_file.read()

            self.c.execute("INSERT INTO users (role, user_id, name, price, description, image, video) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (role, user_id, name, price, description, img_blob, vid_blob))
            self.conn.commit()
            messagebox.showinfo("Success", "Data saved successfully")

            self.load_main_display_data()
            self.load_my_listings_data()
        except Exception as e:
            logging.error(f"Error saving data: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again.")

    def create_search_page(self):
        self.search_page = ttk.Frame(self.notebook)
        self.notebook.add(self.search_page, text="Search")

        ttk.Label(self.search_page, text="Search Listings:", font=('Helvetica', 14, 'bold')).grid(row=0, column=0, pady=10)

        self.search_var = tk.StringVar()
        ttk.Label(self.search_page, text="Description:").grid(row=1, column=0, sticky="e")
        self.search_entry = ttk.Entry(self.search_page, textvariable=self.search_var)
        self.search_entry.grid(row=1, column=1, pady=5)

        self.price_min_var = tk.DoubleVar()
        ttk.Label(self.search_page, text="Price Min:").grid(row=2, column=0, sticky="e")
        self.price_min_entry = ttk.Entry(self.search_page, textvariable=self.price_min_var)
        self.price_min_entry.grid(row=2, column=1, pady=5)

        self.price_max_var = tk.DoubleVar()
        ttk.Label(self.search_page, text="Price Max:").grid(row=3, column=0, sticky="e")
        self.price_max_entry = ttk.Entry(self.search_page, textvariable=self.price_max_var)
        self.price_max_entry.grid(row=3, column=1, pady=5)

        ttk.Button(self.search_page, text="Search", command=self.search, style="primary.TButton").grid(row=4, column=0, columnspan=2, pady=20)

        self.search_results_text = tk.StringVar()
        ttk.Label(self.search_page, textvariable=self.search_results_text).grid(row=5, column=0, columnspan=2, pady=10)

    def search(self):
        """
        This function handles the search functionality. It constructs a query based on the
        search criteria and fetches the matching records from the database.
        """
        search_query = self.search_var.get()
        price_min = self.price_min_var.get()
        price_max = self.price_max_var.get()

        query = "SELECT * FROM users WHERE description LIKE ?"
        params = ['%' + search_query + '%']

        if price_min:
            query += " AND price >= ?"
            params.append(price_min)
        if price_max:
            query += " AND price <= ?"
            params.append(price_max)

        try:
            self.c.execute(query, params)
            results = self.c.fetchall()

            if results:
                result_texts = [f"ID: {r[2]}, Name: {r[3]}, Price: {r[4]}, Description: {r[5]}" for r in results]
                self.search_results_text.set("\n".join(result_texts))
            else:
                self.search_results_text.set("No results found.")
        except Exception as e:
            logging.error(f"Error searching data: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again.")

    def create_main_display_page(self):
        self.main_display_page = ttk.Frame(self.notebook)
        self.notebook.add(self.main_display_page, text="Main Display")

        ttk.Label(self.main_display_page, text="Latest Listings:", font=('Helvetica', 14, 'bold')).grid(row=0, column=0, pady=10)

        ttk.Button(self.main_display_page, text="Refresh", command=self.load_main_display_data, style="primary.TButton").grid(row=0, column=1, pady=10, padx=10)
        ttk.Button(self.main_display_page, text="Sort by Price", command=self.sort_by_price, style="primary.TButton").grid(row=0, column=2, pady=10, padx=10)

        self.main_display_canvas = tk.Canvas(self.main_display_page)
        self.main_display_canvas.grid(row=1, column=0, pady=10, sticky="nsew")

        self.main_display_scrollbar = ttk.Scrollbar(self.main_display_page, orient="vertical", command=self.main_display_canvas.yview)
        self.main_display_scrollbar.grid(row=1, column=1, sticky="ns")

        self.main_display_frame = ttk.Frame(self.main_display_canvas)
        self.main_display_frame.bind("<Configure>", lambda e: self.main_display_canvas.configure(scrollregion=self.main_display_canvas.bbox("all")))

        self.main_display_canvas.create_window((0, 0), window=self.main_display_frame, anchor="nw")
        self.main_display_canvas.configure(yscrollcommand=self.main_display_scrollbar.set)

        self.load_main_display_data()

    def load_main_display_data(self):
        """
        This function loads the latest listings and displays them in the main display area.
        """
        for widget in self.main_display_frame.winfo_children():
            widget.destroy()

        try:
            self.c.execute("SELECT * FROM users ORDER BY id DESC LIMIT 10")
            results = self.c.fetchall()
            self.display_results(results)
        except Exception as e:
            logging.error(f"Error loading main display data: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again.")

    def display_results(self, results):
        """
        This function displays the results in the main display area.
        """
        if results:
            for result in results:
                frame = ttk.Frame(self.main_display_frame, borderwidth=1, relief="solid", padding=10)
                frame.pack(fill="x", pady=5, padx=10)

                ttk.Label(frame, text=f"Role: {result[1]}", font=('Helvetica', 12, 'bold')).grid(row=0, column=0, sticky="w")
                ttk.Label(frame, text=f"ID: {result[2]}", font=('Helvetica', 12)).grid(row=1, column=0, sticky="w")
                ttk.Label(frame, text=f"Name: {result[3]}", font=('Helvetica', 12)).grid(row=2, column=0, sticky="w")
                ttk.Label(frame, text=f"Price: {result[4]}", font=('Helvetica', 12)).grid(row=3, column=0, sticky="w")
                ttk.Label(frame, text=f"Description: {result[5]}", font=('Helvetica', 12)).grid(row=4, column=0, sticky="w")
                ttk.Label(frame, text=f"Date & Time: {result[7]}", font=('Helvetica', 12)).grid(row=5, column=0, sticky="w")

                if result[6]:
                    img_data = Image.open(result[6])
                    img_data = img_data.resize((50, 50), Image.ANTIALIAS)
                    img = ImageTk.PhotoImage(img_data)
                    img_label = ttk.Label(frame, image=img)
                    img_label.image = img
                    img_label.grid(row=0, column=1, rowspan=6, padx=10)
        else:
            ttk.Label(self.main_display_frame, text="No listings found.", font=('Helvetica', 12)).pack(pady=10)

    def sort_by_price(self):
        """
        This function sorts the listings by price and displays them.
        """
        try:
            self.c.execute("SELECT * FROM users ORDER BY price ASC")
            results = self.c.fetchall()
            self.display_results(results)
        except Exception as e:
            logging.error(f"Error sorting by price: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again.")

    def create_my_listings_page(self):
        self.my_listings_page = ttk.Frame(self.notebook)
        self.notebook.add(self.my_listings_page, text="My Listings")

        ttk.Label(self.my_listings_page, text="My Listings:", font=('Helvetica', 14, 'bold')).grid(row=0, column=0, pady=10)

        self.my_listings_canvas = tk.Canvas(self.my_listings_page)
        self.my_listings_canvas.grid(row=1, column=0, pady=10, sticky="nsew")

        self.my_listings_scrollbar = ttk.Scrollbar(self.my_listings_page, orient="vertical", command=self.my_listings_canvas.yview)
        self.my_listings_scrollbar.grid(row=1, column=1, sticky="ns")

        self.my_listings_frame = ttk.Frame(self.my_listings_canvas)
        self.my_listings_frame.bind("<Configure>", lambda e: self.my_listings_canvas.configure(scrollregion=self.my_listings_canvas.bbox("all")))

        self.my_listings_canvas.create_window((0, 0), window=self.my_listings_frame, anchor="nw")
        self.my_listings_canvas.configure(yscrollcommand=self.my_listings_scrollbar.set)

        self.load_my_listings_data()

    def load_my_listings_data(self):
        """
        This function loads the current user's listings and displays them.
        """
        for widget in self.my_listings_frame.winfo_children():
            widget.destroy()

        try:
            self.c.execute("SELECT * FROM users WHERE user_id IN (SELECT user_id FROM accounts WHERE username=?) ORDER BY id DESC", (self.current_user,))
            results = self.c.fetchall()

            if results:
                for result in results:
                    frame = ttk.Frame(self.my_listings_frame, borderwidth=1, relief="solid", padding=10)
                    frame.pack(fill="x", pady=5, padx=10)

                    ttk.Label(frame, text=f"Role: {result[1]}", font=('Helvetica', 12, 'bold')).grid(row=0, column=0, sticky="w")
                    ttk.Label(frame, text=f"ID: {result[2]}", font=('Helvetica', 12)).grid(row=1, column=0, sticky="w")
                    ttk.Label(frame, text=f"Name: {result[3]}", font=('Helvetica', 12)).grid(row=2, column=0, sticky="w")
                    ttk.Label(frame, text=f"Price: {result[4]}", font=('Helvetica', 12)).grid(row=3, column=0, sticky="w")
                    ttk.Label(frame, text=f"Description: {result[5]}", font=('Helvetica', 12)).grid(row=4, column=0, sticky="w")
                    ttk.Label(frame, text=f"Date & Time: {result[7]}", font=('Helvetica', 12)).grid(row=5, column=0, sticky="w")

                    ttk.Button(frame, text="Edit", command=lambda r=result: self.edit_listing(r), style="info.TButton").grid(row=6, column=0, sticky="w", pady=5)
                    ttk.Button(frame, text="Delete", command=lambda r=result: self.delete_listing(r), style="danger.TButton").grid(row=6, column=1, sticky="e", pady=5)
            else:
                ttk.Label(self.my_listings_frame, text="No listings found.", font=('Helvetica', 12)).pack(pady=10)
        except Exception as e:
            logging.error(f"Error loading my listings data: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again.")

    def edit_listing(self, listing):
        self.edit_window = tk.Toplevel(self)
        self.edit_window.title("Edit Listing")

        ttk.Label(self.edit_window, text="Role:", font=('Helvetica', 12)).grid(row=0, column=0, sticky="e", pady=5)
        role_var = tk.StringVar(value=listing[1])
        ttk.Entry(self.edit_window, textvariable=role_var).grid(row=0, column=1, pady=5)

        ttk.Label(self.edit_window, text="ID:", font=('Helvetica', 12)).grid(row=1, column=0, sticky="e", pady=5)
        id_var = tk.StringVar(value=listing[2])
        ttk.Entry(self.edit_window, textvariable=id_var).grid(row=1, column=1, pady=5)

        ttk.Label(self.edit_window, text="Name:", font=('Helvetica', 12)).grid(row=2, column=0, sticky="e", pady=5)
        name_var = tk.StringVar(value=listing[3])
        ttk.Entry(self.edit_window, textvariable=name_var).grid(row=2, column=1, pady=5)

        ttk.Label(self.edit_window, text="Price:", font=('Helvetica', 12)).grid(row=3, column=0, sticky="e", pady=5)
        price_var = tk.DoubleVar(value=listing[4])
        ttk.Entry(self.edit_window, textvariable=price_var).grid(row=3, column=1, pady=5)

        ttk.Label(self.edit_window, text="Description:", font=('Helvetica', 12)).grid(row=4, column=0, sticky="e", pady=5)
        description_var = tk.StringVar(value=listing[5])
        ttk.Entry(self.edit_window, textvariable=description_var).grid(row=4, column=1, pady=5)

        ttk.Label(self.edit_window, text="Image:", font=('Helvetica', 12)).grid(row=5, column=0, sticky="e", pady=5)
        image_var = tk.StringVar(value=listing[6])
        ttk.Entry(self.edit_window, textvariable=image_var).grid(row=5, column=1, pady=5)

        ttk.Label(self.edit_window, text="Video:", font=('Helvetica', 12)).grid(row=6, column=0, sticky="e", pady=5)
        video_var = tk.StringVar(value=listing[7])
        ttk.Entry(self.edit_window, textvariable=video_var).grid(row=6, column=1, pady=5)

        def update_listing():
            """
            This function updates the listing with the new data.
            """
            try:
                self.c.execute("UPDATE users SET role=?, user_id=?, name=?, price=?, description=?, image=?, video=? WHERE id=?",
                               (role_var.get(), id_var.get(), name_var.get(), price_var.get(), description_var.get(), image_var.get(), video_var.get(), listing[0]))
                self.conn.commit()
                messagebox.showinfo("Success", "Listing updated successfully")
                self.edit_window.destroy()
                self.load_my_listings_data()
                self.load_main_display_data()
            except Exception as e:
                logging.error(f"Error updating listing: {e}")
                messagebox.showerror("Error", "An unexpected error occurred. Please try again.")

        ttk.Button(self.edit_window, text="Update", command=update_listing, style="success.TButton").grid(row=7, column=0, columnspan=2, pady=20)

    def delete_listing(self, listing):
        """
        This function deletes the listing from the database.
        """
        try:
            self.c.execute("DELETE FROM users WHERE id=?", (listing[0],))
            self.conn.commit()

            messagebox.showinfo("Success", "Listing deleted successfully")
            self.load_my_listings_data()
            self.load_main_display_data()
        except Exception as e:
            logging.error(f"Error deleting listing: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again.")

    def create_profile_page(self):
        self.profile_page = ttk.Frame(self.notebook)
        self.notebook.add(self.profile_page, text="Profile")

        ttk.Label(self.profile_page, text="Profile Information", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(self.profile_page, text="Username:", font=('Helvetica', 12)).grid(row=1, column=0, sticky="e", pady=5)
        self.profile_username_var = tk.StringVar()
        ttk.Entry(self.profile_page, textvariable=self.profile_username_var, state='disabled').grid(row=1, column=1, pady=5)

        ttk.Label(self.profile_page, text="New Password:", font=('Helvetica', 12)).grid(row=2, column=0, sticky="e", pady=5)
        self.profile_password_var = tk.StringVar()
        ttk.Entry(self.profile_page, textvariable=self.profile_password_var, show="*").grid(row=2, column=1, pady=5)

        ttk.Button(self.profile_page, text="Update Profile", command=self.update_profile, style="success.TButton").grid(row=3, column=0, columnspan=2, pady=20)

    def update_profile(self):
        """
        This function updates the user's profile with the new password.
        """
        new_password = self.profile_password_var.get()

        if not new_password:
            messagebox.showerror("Error", "Please enter a new password")
            return

        hashed_password = hash_password(new_password)

        try:
            self.c.execute("UPDATE accounts SET password=? WHERE username=?", (hashed_password, self.current_user))
            self.conn.commit()
            messagebox.showinfo("Success", "Profile updated successfully")
        except Exception as e:
            logging.error(f"Error updating profile: {e}")
            messagebox.showerror("Error", "An unexpected error occurred. Please try again.")

    def create_sidebar(self):
        toggle_button = ttk.Button(self.sidebar_frame, text="☰", command=self.toggle_sidebar, style="info.TButton")
        toggle_button.pack(side="top", fill="x")

        ttk.Button(self.sidebar_frame, text="Dashboard", command=lambda: self.notebook.select(self.dashboard_page), style="primary.TButton").pack(fill='x', pady=5)
        ttk.Button(self.sidebar_frame, text="Register", command=lambda: self.notebook.select(self.register_page), style="primary.TButton").pack(fill='x', pady=5)
        ttk.Button(self.sidebar_frame, text="Login", command=lambda: self.notebook.select(self.login_page), style="primary.TButton").pack(fill='x', pady=5)
        ttk.Button(self.sidebar_frame, text="Search", command=lambda: self.notebook.select(self.search_page), style="primary.TButton").pack(fill='x', pady=5)
        ttk.Button(self.sidebar_frame, text="Profile", command=lambda: self.notebook.select(self.profile_page), style="primary.TButton").pack(fill='x', pady=5)
        ttk.Button(self.sidebar_frame, text="My Listings", command=lambda: self.notebook.select(self.my_listings_page), style="primary.TButton").pack(fill='x', pady=5)
        ttk.Button(self.sidebar_frame, text="Exit", command=self.quit, style="danger.TButton").pack(fill='x', pady=5)

    def toggle_sidebar(self):
        """
        This function toggles the visibility of the sidebar.
        """
        if self.sidebar_visible:
            self.sidebar_frame.grid_remove()
            self.notebook.grid_configure(row=0, column=0, sticky="nsew")
            self.grid_columnconfigure(0, weight=1)
        else:
            self.sidebar_frame.grid()
            self.notebook.grid_configure(row=0, column=1, sticky="nsew")
            self.grid_columnconfigure(1, weight=1)
        self.sidebar_visible = not self.sidebar_visible

if __name__ == "__main__":
    app = Application()
    app.mainloop()
