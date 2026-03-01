import pymysql
from urllib.parse import quote_plus

# Database configuration
password = quote_plus('MySQLkaur@003')

# Connect to the database
try:
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='MySQLkaur@003',
        database='journeyverse_auth',
        cursorclass=pymysql.cursors.DictCursor
    )

    with connection.cursor() as cursor:
        # Check if column exists
        cursor.execute("SHOW COLUMNS FROM `my_journey_requests` LIKE 'request_message'")
        result = cursor.fetchone()
        
        if result:
            print("Column 'request_message' already exists in 'my_journey_requests'.")
        else:
            print("Adding 'request_message' column to 'my_journey_requests'...")
            sql = "ALTER TABLE `my_journey_requests` ADD COLUMN `request_message` TEXT NULL;"
            cursor.execute(sql)
            connection.commit()
            print("Column added successfully.")

finally:
    if 'connection' in locals() and connection.open:
        connection.close()
