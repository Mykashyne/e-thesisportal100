"""
Database Fix Script for E-Thesis Portal
Run this script ONCE to fix the "no such column: password" error
"""

import sqlite3
from werkzeug.security import generate_password_hash


def fix_database():
    print("=" * 60)
    print("E-Thesis Portal - Database Fix Script")
    print("=" * 60)

    try:
        # Connect to database
        conn = sqlite3.connect('ethesis.db')
        cursor = conn.cursor()

        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("\n✗ Users table doesn't exist. Creating it...")
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            ''')
            conn.commit()
            print("✓ Users table created successfully!")
        else:
            print("\n✓ Users table exists")

        # Check if password column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        print(f"\nCurrent columns in users table: {', '.join(column_names)}")

        if 'password' not in column_names:
            print("\n✗ Password column is missing. Adding it now...")
            cursor.execute('ALTER TABLE users ADD COLUMN password TEXT')
            conn.commit()
            print("✓ Password column added successfully!")
        else:
            print("✓ Password column exists")

        # Check if admin user exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        admin_user = cursor.fetchone()

        if not admin_user:
            print("\n✗ Admin user doesn't exist. Creating it...")
            hashed_password = generate_password_hash('admin123')
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                           ('admin', hashed_password))
            conn.commit()
            print("✓ Admin user created successfully!")
        else:
            print("\n✓ Admin user exists")
            # Update admin password just in case
            print("  Resetting admin password to 'admin123'...")
            hashed_password = generate_password_hash('admin123')
            cursor.execute('UPDATE users SET password = ? WHERE username = ?',
                           (hashed_password, 'admin'))
            conn.commit()
            print("  ✓ Admin password updated!")

        # Verify everything works
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        cursor.execute("SELECT id, username FROM users")
        users = cursor.fetchall()
        print(f"\nTotal users in database: {len(users)}")
        for user in users:
            print(f"  - User ID: {user[0]}, Username: {user[1]}")

        print("\n" + "=" * 60)
        print("DATABASE FIX COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nLogin Credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nYou can now run your Flask application!")

        conn.close()

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        print("\nPlease contact support if this error persists.")
        return False

    return True


if __name__ == '__main__':
    fix_database()