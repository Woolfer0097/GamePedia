import sqlite3


connection = sqlite3.connect("../db/games.db")
cursor = connection.cursor()
query = cursor.execute("SELECT user_id FROM games").fetchall()
count = 0
for i in query:
    for j in i:
        count += 1
        cursor.execute(f"UPDATE games set user_id = 1 WHERE id = {count}")
connection.commit()
