# User Information Application

This project is a user information management application built using Python and Tkinter. It provides functionalities for user registration, login, data management, and more.

## Features

- User registration with validation
- User login with session management
- Role-based information management (Student/Owner)
- Data storage using SQLite
- File uploads for images and videos
- Search and filter listings
- User profile management
- Sidebar navigation

## Requirements

- Python 3.x
- Tkinter
- PIL (Pillow)
- bcrypt
- ttkbootstrap
- sqlite3
- pandas
- numpy

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/User-Information-Application.git
    cd User-Information-Application
    ```

2. Create a virtual environment and activate it:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the application:

    ```bash
    python new.py
    ```

## Usage

1. **Register**: Create a new user account by providing a username and password.
2. **Login**: Login with your registered username and password.
3. **Dashboard**: Access various functionalities like adding listings, searching, and managing your profile.
4. **Add Listings**: Add new listings with details like role, user ID, name, price, description, image, and video.
5. **Search**: Search listings based on description and price range.
6. **Manage Listings**: Edit or delete your listings.
7. **Profile**: Update your profile information and change your password.

## Project Structure

```plaintext
User-Information-Application/
│
├── application.log          # Log file
├── new.py                   # The User Information Application described here
├── main.py                  # Separate Student Housing prototype (see Notes)
├── README.md                # Project documentation
├── requirements.txt         # List of required packages
└── user_data.db             # SQLite database file

## Notes

- `new.py` is the application this README describes (registration and login with bcrypt hashing, SQLite file `user_data.db`, Student/Owner listings). Run it with `python new.py`.
- `main.py` is an earlier, separate "Student Housing Management" prototype. It has no login or password handling, uses `housing_extended.db`, and uses an optional `background.jpg` in the same folder (not included in this repository); without it the window opens with a plain white background.
- `requirements.txt` lists the packages both scripts import. `sqlite3` and `tkinter` come with Python (on some Linux systems install the `python3-tk` package).
- These scripts compile (`python -m py_compile`) and their non-GUI dependencies install. The missing-image fallback in `main.py` was checked only by compiling it and confirming that Pillow raises the exception it catches. The GUI itself was not launched in a test environment (Tk was not available).
