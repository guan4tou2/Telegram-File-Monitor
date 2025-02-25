# Telegram File Monitor

A Python script that monitors specific URLs for file updates and sends notifications via Telegram Bot.

## Features

- 🔄 Regular file checks (default: every 30 minutes)
- 📊 Periodic status reports (default: every 6 hours)
- 📁 Automatic download of new files
- 🤖 Real-time Telegram notifications
- 📝 Support for multiple file formats
- 📋 Detailed logging
- ⚙️ Configurable monitoring parameters

## Supported File Types

- Text files (.txt)
- Archive files (.zip)
- PDF files (.pdf)
- Word documents (.doc, .docx)
- Excel spreadsheets (.xls, .xlsx)
- CSV files (.csv)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create and configure `.env` file:
```env
# Telegram Bot Configuration
BOT_TOKEN=your_bot_token
CHAT_ID=your_chat_id

# Monitor Token
MONITOR_TOKEN=toekn_to_monitor

# File Configuration
DOWNLOAD_DIR=downloaded_files
LOG_DIR=logs

# Check Intervals
CHECK_INTERVAL=30    # File check interval (minutes)
REPORT_INTERVAL=6   # Status report interval (hours)

# File Index Range
START_INDEX=0       # Start index for file checking
END_INDEX=50       # End index for file checking

# Supported File Extensions (comma-separated)
SUPPORTED_EXTENSIONS=txt,zip  # json,pdf...

# Thread Configuration
MAX_WORKERS=5      # Maximum number of concurrent threads 
```

## Configuration Guide

### Required Configuration

1. **Get BOT_TOKEN**:
   - Find @BotFather on Telegram
   - Send `/newbot` to create a new bot
   - Copy the token to `.env` file

2. **Get CHAT_ID**:
   - Method 1: Send any message to @userinfobot
   - Method 2: Run the program and it will get the chat ID automatically after you message your bot

3. **Set BASE_URL**:
   - Set the base URL path for file monitoring

### Optional Configuration

- `DOWNLOAD_DIR`: Location to save downloaded files (default: downloaded_files)
- `LOG_DIR`: Location to save log files (default: logs)
- `CHECK_INTERVAL`: File check interval in minutes (default: 5)
- `REPORT_INTERVAL`: Status report interval in hours (default: 6)

## Running the Program

```bash
python file_monitor.py
```

## Notification Types

1. **Status Report** (Every 6 hours):
```
📊 File Monitor Status Report
🕒 Runtime: 1d 2h 30m
🔄 Checks Performed: 72
📁 Files Found: 5
💾 Downloads Successful: 5
🔍 Current Index: 12
⏱ Last Check: 2024-03-21 15:30:00
```

2. **File Discovery Notification** (Real-time):
```
❗️New file found: file_1.txt
👉 Attempting to download...
✅ File download successful: file_1.txt
```

## Logging

- Log file location: `logs/file_monitor_YYYYMMDD.log`
- Log format: `timestamp [log_level] message`
- Outputs to both console and log file

## Important Notes

- Ensure stable network connection
- Check available disk space
- Do not commit `.env` file to version control
- Add `logs` and `downloaded_files` to `.gitignore`

## Error Handling

- Automatically handles network errors and download failures
- All errors are logged to the log file
- Important errors are notified via Telegram
- Can be safely stopped using Ctrl+C 
