##FOOD EXPIRY TRACKER

###Overview

  Food Expiry Tracker is a simple Flask web application that helps users keep track of expiry dates of the food items. Users can upload a receipt image, and the app extracts item names using OCR (Tesseract). Each item is given an estimated expiry date based on a small internal database.
  The app includes:
  - User registration & login
  - OCR‑based item extraction
  - Automatic expiry calculation
  - Dashboard with fridge & pantry sections
  - Edit & delete options
  - Alerts for items expiring soon

Features

  - Upload receipt images (JPG/PNG)
  - OCR text extraction using Tesseract
  - Automatic expiry date calculation
  - Categorization into fridge or pantry
  - User accounts with hashed passwords
  - Dashboard showing all items
  - Edit and delete functionality
  - Expiring‑soon warning banner

Working

  1. User uploads a receipt image
  2. Tesseract OCR extracts text
  3. The app parses item names and quantities
  4. Each item is matched with:
     A category (fruit, dairy, bakery, etc.)
     A default expiry duration
  5. Items are saved to a MySQL database
  6. Dashboard displays items sorted by expiry date

Technologies Used

  - Python (Flask)
  - MySQL
  - Tesseract OCR
  - HTML/CSS (inline styles inside templates)
  - Werkzeug for password hashing
  - Pillow for image processing

Requirements

  This project uses the following Python packages:
  - Flask
  - mysql-connector-python
  - pytesseract
  - Pillow
  - Werkzeug

Database

  The project uses a MySQL database named foodtracker.
  Tables used:
      users
      food_items
  The schema was created manually in MySQL Workbench.

Running the App

  1. Install the dependencies
  2. Make sure MySQL is running
  3. Update the database credentials in app.py
  4. Run the app: python app.py
  5. Open the app in the browser

Notes

  - The database connection password is removed in the code
  - The accuracy of the OCR is dependant on the quality of the image
