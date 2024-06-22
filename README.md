# Telegram Anonymous Chat Bot

## Project Overview
This Telegram bot allows users to send and receive anonymous messages within a controlled environment. Users can register to receive a unique ID and then use this ID to communicate anonymously with other registered users. The bot supports creating chatrooms, sending messages, replying to messages, and viewing the message history between two users.

## Features
- **User Registration**: Users can register and receive a unique ID for anonymous communication.
- **Send Messages**: Users can send anonymous messages using the recipient's unique ID.
- **Reply to Messages**: Users can directly reply to any message they receive.
- **View History**: Users can request a chat history with any user they have previously communicated with.

## Installation
To set up this project, you will need Python and pip installed on your system. If you do not have these installed, please refer to the official Python documentation for installation instructions applicable to your operating system.

### Prerequisites
- Python 3.x
- pip (Python package installer)

### Required Libraries
This project uses the `python-telegram-bot` library for interacting with the Telegram Bot API and `sqlite3` for database management, which is included with Python.

To install the required Python library, run the following command in your terminal:

```bash
pip install python-telegram-bot --upgrade

## Setup
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/telegram-anonymous-chat-bot.git
   cd telegram-anonymous-chat-bot
   ```
2. **Create a Bot**:
    - Talk to @BotFather on Telegram to create a new bot and receive a token.
    - Replace 'YOUR_BOT_TOKEN' in the main.py with your new token.
3. **Initialize the Database**:
    - Run the setup_database.py to set up the initial database.
    ```bash
    python setup_database.py
    ```