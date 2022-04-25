import sqlite3
from datetime import datetime


connection = sqlite3.connect("../db/games.db")
cursor = connection.cursor()
query = cursor.execute("SELECT created_date FROM games").fetchall()
count = 0
for i in query:
    for j in i:
        count += 1
        cursor.execute(f"UPDATE games set created_date = '{datetime.now()}' WHERE id = {count}")
        cursor.execute(f"UPDATE games set updated_date = '{datetime.now()}' WHERE id = {count}")
connection.commit()
