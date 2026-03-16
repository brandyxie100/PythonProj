"""
Django Learning Exercises - Python Libraries Reference
======================================================
This file describes important Python packages and provides two examples
of how each can be used. Run this file to see output from runnable examples.

How to use
Run all examples
py
   python3 demo.py
Run tests
   pytest demo.py -v
Run Pylint
   pylint demo.py
Optional dependencies (for numpy examples)
   pip install numpy
Django, Flask, and FastAPI are shown as commented code because they are web frameworks 
that run as separate apps. 
The file includes descriptions and two example patterns for each.

"""

# =============================================================================
# 1. OS - Operating System Interface
# =============================================================================
"""
The 'os' module provides a portable way to interact with the operating system.
It allows you to perform file/directory operations, environment variables,
process management, and path manipulation across different platforms (Windows,
macOS, Linux).
"""

import os

# --- Example 1: List files in a directory and check if path exists ---
def os_example_1():
    """List files in current directory and validate path existence."""
    current_dir = os.getcwd()  # Get current working directory
    print(f"Current directory: {current_dir}")
    # List all items in the directory
    items = os.listdir(current_dir)
    print(f"Items in directory: {items[:5]}...")  # First 5 items
    # Check if a path exists (file or directory)
    exists = os.path.exists("demo.py")
    print(f"demo.py exists: {exists}")


# --- Example 2: Create directory and join paths portably ---
def os_example_2():
    """Create a directory safely and build paths for any OS."""
    # os.path.join() works on Windows, macOS, and Linux
    new_dir = os.path.join(os.getcwd(), "temp_demo_folder")
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)  # Create directory (and parents if needed)
        print(f"Created: {new_dir}")
    # Get file size and split path into components
    if os.path.exists(__file__):
        size = os.path.getsize(__file__)
        dirname, basename = os.path.split(__file__)
        print(f"File: {basename}, Size: {size} bytes, Dir: {dirname}")


# =============================================================================
# 2. SYS - System-Specific Parameters and Functions
# =============================================================================
"""
The 'sys' module provides access to variables and functions that interact
with the Python interpreter. Use it for command-line arguments, stdin/stdout,
version info, and exiting the program.
"""

import sys

# --- Example 1: Command-line arguments and script path ---
def sys_example_1():
    """Access command-line arguments and script location."""
    # sys.argv[0] is the script name, [1:] are arguments
    print(f"Script name: {sys.argv[0]}")
    print(f"Arguments passed: {sys.argv[1:]}")
    # Get the directory containing the running script
    script_dir = sys.path[0]
    print(f"Script directory: {script_dir}")


# --- Example 2: Python version and exit codes ---
def sys_example_2():
    """Check Python version and use proper exit codes."""
    # Version info: (major, minor, micro, releaselevel, serial)
    print(f"Python version: {sys.version}")
    print(f"Version tuple: {sys.version_info}")
    # sys.exit(0) = success, non-zero = error (convention)
    # Uncomment to exit: sys.exit(1)


# =============================================================================
# 3. NUMPY - Numerical Computing
# =============================================================================
"""
NumPy is the fundamental package for scientific computing in Python. It provides
efficient multi-dimensional arrays, mathematical functions, linear algebra,
and random number generation. Essential for data science and machine learning.
"""

try:
    import numpy as np

    # --- Example 1: Array creation and basic operations ---
    def numpy_example_1():
        """Create arrays and perform element-wise math."""
        # Create 1D and 2D arrays
        arr1 = np.array([1, 2, 3, 4, 5])
        arr2 = np.array([[1, 2], [3, 4], [5, 6]])
        # Element-wise operations (no loops needed)
        squared = np.square(arr1)
        mean_val = np.mean(arr1)
        print(f"Array: {arr1}, Squared: {squared}, Mean: {mean_val}")
        print(f"2D shape: {arr2.shape}")

    # --- Example 2: Array slicing and reshaping ---
    def numpy_example_2():
        """Slice arrays and reshape dimensions."""
        arr = np.arange(12)  # [0, 1, 2, ..., 11]
        reshaped = arr.reshape(3, 4)  # 3 rows, 4 columns
        # Slice: rows 0-1, columns 1-3
        slice_result = reshaped[:2, 1:3]
        print(f"Reshaped:\n{reshaped}")
        print(f"Sliced:\n{slice_result}")

except ImportError:
    def numpy_example_1():
        print("NumPy not installed. Run: pip install numpy")

    def numpy_example_2():
        print("NumPy not installed. Run: pip install numpy")


# =============================================================================
# 4. PATHLIB - Object-Oriented Path Handling
# =============================================================================
"""
pathlib provides an object-oriented API for filesystem paths. It's more
readable and cross-platform than os.path. Path objects support methods
like .exists(), .read_text(), .mkdir(), and operator overloading.
"""

from pathlib import Path

# --- Example 1: Path construction and file operations ---
def pathlib_example_1():
    """Build paths and check file properties."""
    # Path objects work on all platforms
    p = Path(__file__).resolve()  # Absolute path of this file
    print(f"This file: {p}")
    print(f"Parent directory: {p.parent}")
    print(f"File name: {p.name}")
    print(f"Stem (no extension): {p.stem}")
    # Check existence
    print(f"Exists: {p.exists()}")


# --- Example 2: Iterate over directory and read/write files ---
def pathlib_example_2():
    """Iterate directory contents and use path methods."""
    base = Path(__file__).parent
    # List Python files in current directory
    py_files = list(base.glob("*.py"))
    print(f"Python files: {[f.name for f in py_files]}")
    # Create a temp file, write, and read
    temp_file = base / "temp_pathlib_demo.txt"
    temp_file.write_text("Hello from pathlib!", encoding="utf-8")
    content = temp_file.read_text(encoding="utf-8")
    print(f"Written and read: {content}")
    temp_file.unlink()  # Delete the temp file


# =============================================================================
# 5. DATETIME - Date and Time
# =============================================================================
"""
The datetime module supplies classes for manipulating dates and times.
datetime.datetime combines date and time; datetime.timedelta represents
durations. Essential for scheduling, logging, and time-based logic.
"""

from datetime import datetime, timedelta

# --- Example 1: Current time and formatting ---
def datetime_example_1():
    """Get current time and format for display/storage."""
    now = datetime.now()
    print(f"Now: {now}")
    # Format as string (ISO 8601, custom formats)
    iso_str = now.isoformat()
    custom_str = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"ISO: {iso_str}")
    print(f"Custom: {custom_str}")
    # Parse string back to datetime
    parsed = datetime.strptime("2025-03-08", "%Y-%m-%d")
    print(f"Parsed: {parsed}")


# --- Example 2: Time arithmetic with timedelta ---
def datetime_example_2():
    """Calculate date differences and future/past dates."""
    today = datetime.now().date()
    # Add 7 days
    next_week = today + timedelta(days=7)
    # Difference between two dates
    past_date = datetime(2024, 1, 1).date()
    diff = today - past_date
    print(f"Today: {today}, Next week: {next_week}")
    print(f"Days since 2024-01-01: {diff.days}")


# =============================================================================
# 6. LOGGING - Flexible Event Logging
# =============================================================================
"""
The logging module provides a flexible framework for emitting log messages.
Use it instead of print() for production: control levels (DEBUG, INFO, WARNING,
ERROR), output to files, and format messages consistently.
"""

import logging

# --- Example 1: Basic logging with levels ---
def logging_example_1():
    """Configure logger and emit messages at different levels."""
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    logger.debug("Detailed info for debugging")
    logger.info("General information")
    logger.warning("Something to watch")
    logger.error("An error occurred")


# --- Example 2: Log to file with custom format ---
def logging_example_2():
    """Log to a file with timestamp and module name."""
    logger = logging.getLogger("demo_logger")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("demo_log.txt", mode="w", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("This message goes to demo_log.txt")
    logger.info("Logging is useful for debugging production issues")
    print("Check demo_log.txt for log output")


# =============================================================================
# 7. DJANGO - Full-Stack Web Framework
# =============================================================================
"""
Django is a high-level Python web framework that encourages rapid development
and clean design. It includes ORM, admin panel, auth, templating, and more.
Use for: content sites, APIs, e-commerce, internal tools.
"""

# --- Example 1: Django project structure (conceptual) ---
"""
# Typical Django setup:
# 1. Create project: django-admin startproject myproject
# 2. Create app: python manage.py startapp myapp
# 3. Define model in myapp/models.py:
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# 4. Run migrations: python manage.py makemigrations && python manage.py migrate
"""

# --- Example 2: Django view and URL routing (conceptual) ---
"""
# In myapp/views.py:
from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Hello, Django!")

def article_detail(request, pk):
    article = Article.objects.get(pk=pk)
    return render(request, "article.html", {"article": article})

# In myapp/urls.py:
from django.urls import path
from . import views
urlpatterns = [
    path("", views.home),
    path("article/<int:pk>/", views.article_detail),
]
"""


# =============================================================================
# 8. FLASK - Lightweight Web Framework
# =============================================================================
"""
Flask is a micro web framework. It's minimal and flexible: you add only what
you need. Great for APIs, prototypes, and small-to-medium web apps.
"""

# --- Example 1: Minimal Flask app (conceptual) ---
"""
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Hello, Flask!</h1>"

@app.route("/api/hello/<name>")
def api_hello(name):
    return {"message": f"Hello, {name}"}

if __name__ == "__main__":
    app.run(debug=True)
"""

# --- Example 2: Flask with templates and POST (conceptual) ---
"""
from flask import Flask, render_template, request
app = Flask(__name__)

@app.route("/form", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        name = request.form.get("name")
        return f"Submitted: {name}"
    return render_template("form.html")
"""


# =============================================================================
# 9. FASTAPI - Modern High-Performance API Framework
# =============================================================================
"""
FastAPI is a modern, fast web framework for building APIs. It uses Python
type hints for automatic validation, OpenAPI docs, and async support.
"""

# --- Example 1: Basic FastAPI endpoint (conceptual) ---
"""
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello, FastAPI!"}

@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}

# Run with: uvicorn main:app --reload
"""

# --- Example 2: FastAPI with request body and validation (conceptual) ---
"""
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

@app.post("/items")
def create_item(item: Item):
    return {"received": item.name, "price": item.price}
"""


# =============================================================================
# 10. BCRYPT - Password Hashing
# =============================================================================
"""
bcrypt is a library for hashing passwords. Never store plain-text passwords.
bcrypt uses a salt and is designed to be slow (resistant to brute-force).
"""

try:
    import bcrypt

    # --- Example 1: Hash a password ---
    def bcrypt_example_1():
        """Hash a password for secure storage."""
        password = b"my_secure_password"
        # Generate salt and hash (salt is included in the hash)
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())
        print(f"Hashed (first 30 chars): {hashed[:30]}...")
        # Verify: check if password matches hash
        is_valid = bcrypt.checkpw(password, hashed)
        print(f"Verification: {is_valid}")

    # --- Example 2: Check password against stored hash ---
    def bcrypt_example_2():
        """Simulate login: verify user password against stored hash."""
        stored_hash = bcrypt.hashpw(b"user123", bcrypt.gensalt())
        # User enters password
        user_input = b"user123"
        wrong_input = b"wrong_password"
        print(f"Correct password: {bcrypt.checkpw(user_input, stored_hash)}")
        print(f"Wrong password: {bcrypt.checkpw(wrong_input, stored_hash)}")

except ImportError:
    def bcrypt_example_1():
        print("bcrypt not installed. Run: pip install bcrypt")

    def bcrypt_example_2():
        print("bcrypt not installed. Run: pip install bcrypt")


# =============================================================================
# 11. PYTEST - Testing Framework
# =============================================================================
"""
pytest is a testing framework that makes it easy to write and run tests.
Use test_*.py or *_test.py files; functions named test_* are auto-discovered.
Run with: pytest or pytest -v
"""

# --- Example 1: Simple assertion tests (run with pytest) ---
def test_addition():
    """Example test: basic assertion."""
    assert 1 + 1 == 2
    assert "hello".upper() == "HELLO"


def test_list_operations():
    """Example test: list behavior."""
    items = [1, 2, 3]
    items.append(4)
    assert len(items) == 4
    assert 4 in items


# --- Example 2: Test a function with multiple cases ---
def add(a: int, b: int) -> int:
    """Function to be tested."""
    return a + b


def test_add_positive():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-1, -1) == -2


def test_add_zero():
    assert add(0, 5) == 5


# =============================================================================
# 12. PYLINT - Code Linter
# =============================================================================
"""
Pylint is a static code analyzer. It checks for errors, style issues,
code smells, and suggests improvements. Run on files or directories.
Usage: pylint demo.py  or  pylint Week13A1/
"""

# --- Example 1: Code that Pylint would flag ---
# Unused variable (pylint: unused-variable)
# some_unused_var = 42

# --- Example 2: Code that follows Pylint conventions ---
def pylint_friendly_function(param: str) -> str:
    """A function with type hints and docstring - Pylint approves."""
    result = param.strip().lower()
    return result


# =============================================================================
# RUN ALL EXAMPLES
# =============================================================================
def main():
    """Run all library examples."""
    examples = [
        ("OS", os_example_1, os_example_2),
        ("SYS", sys_example_1, sys_example_2),
        ("NUMPY", numpy_example_1, numpy_example_2),
        ("PATHLIB", pathlib_example_1, pathlib_example_2),
        ("DATETIME", datetime_example_1, datetime_example_2),
        ("LOGGING", logging_example_1, logging_example_2),
        ("BCRYPT", bcrypt_example_1, bcrypt_example_2),
    ]
    for name, ex1, ex2 in examples:
        print(f"\n{'='*60}\n{name}\n{'='*60}")
        ex1()
        print("---")
        ex2()
    print("\n" + "=" * 60)
    print("Django, Flask, FastAPI: See comments in source (web frameworks)")
    print("pytest: Run 'pytest demo.py -v' to execute tests")
    print("pylint: Run 'pylint demo.py' to analyze code")
    print("=" * 60)


if __name__ == "__main__":
    main()
