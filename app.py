import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, session
from PIL import Image
import pytesseract
import mysql.connector

app = Flask(__name__)
app.secret_key = "key123" 

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# DATABASES
EXPIRY_DB = {
    "apple": 30, "banana": 4, "orange": 14, "pear": 7, "grapes": 10,
    "strawberry": 3, "blueberry": 7, "kiwi": 7, "watermelon": 5,
    "lemon": 14, "raspberry": 3,
    "milk": 7, "cheese": 14, "yogurt": 10, "butter": 30, "cream": 7,
    "bread": 5, "cake": 4, "pastry": 3, "donut": 2,
    "eggs": 21
}

CATEGORY_DB = {
    "apple": "fruit", "banana": "fruit", "orange": "fruit", "pear": "fruit",
    "grapes": "fruit", "strawberry": "fruit", "blueberry": "fruit",
    "kiwi": "fruit", "watermelon": "fruit", "lemon": "fruit",
    "raspberry": "fruit",
    "milk": "dairy", "cheese": "dairy", "yogurt": "dairy",
    "butter": "dairy", "cream": "dairy",
    "bread": "bakery", "cake": "bakery", "pastry": "bakery",
    "donut": "bakery",
    "eggs": "eggs"
}

FRIDGE_CATEGORIES = ["fruit", "dairy", "eggs", "vegetables", "drinks", "meat", "leftovers"]
PANTRY_CATEGORIES = ["bakery", "snacks", "dry", "canned"]

# FUNCTIONS
def get_item_details(item_name):
    item_name = item_name.lower()
    return EXPIRY_DB.get(item_name), CATEGORY_DB.get(item_name)

def calculate_expiry_date(days):
    today = datetime.now().date()
    return today + timedelta(days=days)

def parse_item_line(line):
    parts = line.split()
    if len(parts) < 2:
        return None

    try:
        quantity = int(parts[0])
        rest = parts[1:]
    except ValueError:
        quantity = 1
        rest = parts

    if rest[-1].replace('.', '', 1).isdigit():
        rest = rest[:-1]

    item_name = " ".join(rest).lower()
    return item_name, quantity

def parse_all_items(ocr_text):
    items = []
    for line in ocr_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        result = parse_item_line(line)
        if result:
            items.append(result)
    return items

def process_ocr_and_save(ocr_text, user_id):
    items = parse_all_items(ocr_text)
    print("Parsed items:", items)

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=" ",
        database="foodtracker"
    )
    cursor = conn.cursor()

    inserted_count = 0

    for item_name, quantity in items:
        expiry_days, category = get_item_details(item_name)
        if expiry_days is None:
            continue

        expiry_date = calculate_expiry_date(expiry_days)

        if category in FRIDGE_CATEGORIES:
            location = "fridge"
        elif category in PANTRY_CATEGORIES:
            location = "pantry"
        else:
            location = "pantry"

        print("Inserting:", item_name, quantity, category, expiry_date, user_id, location)

        sql = """
            INSERT INTO food_items (item_name, quantity, category, expiry_date, user_id, location, ocr_raw_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (item_name, quantity, category, expiry_date, user_id, location, ocr_text)
        cursor.execute(sql, values)
        inserted_count += 1

    conn.commit()
    conn.close()

    return inserted_count
# ROUTES
@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("welcome_back"))
    return render_template("home.html")

@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("name", "").strip()
    password = request.form.get("password", "").strip()

    if not name or not password:
        return render_template("home.html", message="Please enter both name and password.")

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=" ",
        database="foodtracker"
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return render_template("home.html", message="User not found. Please register first.")

    stored_hash = user.get("password")
    if not stored_hash or not check_password_hash(stored_hash, password):
        return render_template("home.html", message="Incorrect password. Please try again.")

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]

    return redirect(url_for("welcome_back"))


@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name", "").strip()
    password = request.form.get("password", "").strip()

    if not name or not password:
        return render_template("home.html", message="Please enter both name and password.")

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=" ",
        database="foodtracker"
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users WHERE name = %s", (name,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return render_template("home.html", message="User already exists. Please log in.")

    hashed = generate_password_hash(password)

    cursor.execute(
        "INSERT INTO users (name, password) VALUES (%s, %s)",
        (name, hashed)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()

    session["user_id"] = user_id
    session["user_name"] = name

    return redirect(url_for("welcome_back"))


@app.route("/welcome")
def welcome_back():
    if "user_id" not in session:
        return redirect(url_for("home"))
    return render_template("welcome.html", user_name=session["user_name"])

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user_id" not in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        print("UPLOAD ROUTE HIT")

        if "image" not in request.files:
            return redirect(url_for("dashboard", msg="noitems"))

        file = request.files["image"]
        if file.filename == "":
            return redirect(url_for("dashboard", msg="noitems"))

        file_path = os.path.join(os.getcwd(), "uploaded_image.jpg")
        file.save(file_path)

        img = Image.open(file_path).convert("RGB")
        ocr_text = pytesseract.image_to_string(img)

        print("=== OCR TEXT START ===")
        print(ocr_text)
        print("=== OCR TEXT END ===")

        count = process_ocr_and_save(ocr_text, session["user_id"])

        if count == 0:
            return redirect(url_for("dashboard", msg="noitems"))
        else:
            return redirect(url_for("dashboard", msg="success"))

    return render_template("upload.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("home"))

    message = None
    msg = request.args.get("msg")

    if msg == "success":
        message = "Receipt processed successfully!"
    elif msg == "noitems":
        message = "No valid items detected. Please try another receipt."

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=" ",
        database="foodtracker"
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, item_name, quantity, category, expiry_date, location, added_on
        FROM food_items
        WHERE user_id = %s
        ORDER BY expiry_date ASC
    """, (session["user_id"],))
    items = cursor.fetchall()
    conn.close()

    today = datetime.now().date()
    expiring_soon_count = 0

    for item in items:
        expiry = item["expiry_date"]
        if isinstance(expiry, datetime):
            expiry = expiry.date()
        days_left = (expiry - today).days
        item["days_left"] = days_left
        if days_left <= 3:
            expiring_soon_count += 1

    return render_template(
        "dashboard.html",
        items=items,
        expiring_soon_count=expiring_soon_count,
        message=message
    )

@app.route("/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("home"))

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=" ",
        database="foodtracker"
    )
    cursor = conn.cursor()
    cursor.execute("DELETE FROM food_items WHERE id = %s AND user_id = %s", (item_id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/edit/<int:item_id>", methods=["POST"])
def edit_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("home"))

    new_quantity = request.form.get("quantity")
    new_expiry = request.form.get("expiry_date")
    new_location = request.form.get("location")

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=" ",
        database="foodtracker"
    )
    cursor = conn.cursor()

    if new_location:
        cursor.execute(
            "UPDATE food_items SET quantity = %s, expiry_date = %s, location = %s WHERE id = %s AND user_id = %s",
            (new_quantity, new_expiry, new_location, item_id, session["user_id"])
        )
    else:
        cursor.execute(
            "UPDATE food_items SET quantity = %s, expiry_date = %s WHERE id = %s AND user_id = %s",
            (new_quantity, new_expiry, item_id, session["user_id"])
        )

    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
