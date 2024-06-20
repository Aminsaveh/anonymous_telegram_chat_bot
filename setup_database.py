import sqlite3

# Connect to the database
conn = sqlite3.connect('chat.db')
c = conn.cursor()

# Create the users table
c.execute('''CREATE TABLE IF NOT EXISTS users (
             user_id INTEGER PRIMARY KEY AUTOINCREMENT,
             telegram_id INTEGER UNIQUE,
             username TEXT
             )''')

# Create the chatrooms table with unique constraint on participants
c.execute('''CREATE TABLE IF NOT EXISTS chatrooms (
             chatroom_id INTEGER PRIMARY KEY AUTOINCREMENT,
             participant1_id INTEGER,
             participant2_id INTEGER,
             UNIQUE(participant1_id, participant2_id)
             )''')

# Create the messages table
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
