import sqlite3
import hashlib

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Connect to database
conn = sqlite3.connect('database.db')  # Change to your actual database file name
cursor = conn.cursor()

# Set admin credentials
admin_username = "admin"
admin_password = "admin123"  # Change this to your desired password

# Hash the password
hashed_password = hash_password(admin_password)

# Check if admin user exists
cursor.execute("SELECT * FROM users WHERE username = ?", (admin_username,))
existing_user = cursor.fetchone()

if existing_user:
    # Update existing admin user
    cursor.execute("UPDATE users SET password = ? WHERE username = ?",
                   (hashed_password, admin_username))
    print(f"Admin password updated successfully!")
else:
    # Insert new admin user
    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                   (admin_username, hashed_password))
    print(f"Admin user created successfully!")

print(f"\nLogin Credentials:")
print(f"Username: {admin_username}")
print(f"Password: {admin_password}")
print(f"Hashed Password: {hashed_password}")

conn.commit()
conn.close()