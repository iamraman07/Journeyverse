import pymysql
from urllib.parse import quote_plus

# Database config
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASS = 'MySQLkaur@003'
DB_NAME = 'journeyverse_auth'

try:
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)
    cursor = conn.cursor()
    
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    print(f"Database {DB_NAME} checked/created successfully.")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error creating database: {e}")
