import sqlite3

conn = sqlite3.connect('chat.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
             user_id INTEGER PRIMARY KEY AUTOINCREMENT,
             telegram_id INTEGER UNIQUE,
             username TEXT
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS chatrooms (
             chatroom_id INTEGER PRIMARY KEY AUTOINCREMENT,
             participant1_id INTEGER,
             participant2_id INTEGER,
             UNIQUE(participant1_id, participant2_id)
             )''')

c.execute('''CREATE TABLE IF NOT EXISTS messages (
             message_id INTEGER PRIMARY KEY AUTOINCREMENT,
             chatroom_id INTEGER,
             sender_id INTEGER,
             message TEXT,
             timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
             )''')

conn.commit()
conn.close()

print("Database setup complete.")
