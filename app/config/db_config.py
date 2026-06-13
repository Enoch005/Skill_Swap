import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="ENOCH@2005",
        database="skillswap"
    )

    return connection