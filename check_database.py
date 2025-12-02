import sqlite3

# Connect to your database
conn = sqlite3.connect('database.db')  # Change to your actual database file name
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:", tables)

# Check structure of users table (change 'users' to your actual table name)
cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()
print("\nColumns in 'users' table:")
for column in columns:
    print(f"  - {column[1]} ({column[2]})")

conn.close()