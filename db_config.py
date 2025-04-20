import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="vaishu",
        password="1999",
        database="mindmasters"
    )


