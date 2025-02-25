import os
import time
import requests
import schedule
from datetime import datetime
import logging
from typing import List, Optional, Tuple
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get configuration from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", 0))
MONITOR_TOKEN = os.getenv("MONITOR_TOKEN")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloaded_files")
LOG_DIR = os.getenv("LOG_DIR", "logs")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 5))
REPORT_INTERVAL = int(os.getenv("REPORT_INTERVAL", 6))
START_INDEX = int(os.getenv("START_INDEX", 0))
END_INDEX = int(os.getenv("END_INDEX", 100))

# Get supported file extensions from environment
SUPPORTED_EXTENSIONS = os.getenv("SUPPORTED_EXTENSIONS", "txt,zip").split(",")

# Fixed URLs
BASE_URL = f"https://api.telegram.org/file/bot{MONITOR_TOKEN}/documents/"


class StatusReporter:
    def __init__(self):
        self.start_time = datetime.now()
        self.files_found = 0
        self.files_downloaded = 0
        self.last_check_time = None
        self.current_index = 0
        self.checks_performed = 0  # New: Check count tracking

    def update_stats(self, files_found: int = 0, files_downloaded: int = 0):
        self.files_found += files_found
        self.files_downloaded += files_downloaded
        self.last_check_time = datetime.now()
        self.checks_performed += 1

    def get_status_report(self) -> str:
        runtime = datetime.now() - self.start_time
        days = runtime.days
        hours = runtime.seconds // 3600
        minutes = (runtime.seconds % 3600) // 60

        return (
            "📊 File Monitor Status Report\n"
            f"🕒 Runtime: {days}d {hours}h {minutes}m\n"
            f"🔄 Checks Performed: {self.checks_performed}\n"
            f"📁 Files Found: {self.files_found}\n"
            f"💾 Downloads Successful: {self.files_downloaded}\n"
            f"🔍 Current Index: {self.current_index}\n"
            f"⏱ Last Check: {self.last_check_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_check_time else 'Not Started'}"
        )


def validate_config():
    """Validate configuration completeness"""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set, please check .env file")
    if not CHAT_ID:
        raise ValueError("CHAT_ID not set, please check .env file")
    if not MONITOR_TOKEN:
        raise ValueError("MONITOR_TOKEN not set, please check .env file")
    if START_INDEX > END_INDEX:
        raise ValueError("START_INDEX must be less than or equal to END_INDEX")
    if not SUPPORTED_EXTENSIONS:
        raise ValueError("SUPPORTED_EXTENSIONS not set, please check .env file")

    logging.info("Configuration validation passed")
    logging.debug(
        "Current configuration:\n"
        + f"Download directory: {DOWNLOAD_DIR}\n"
        + f"Log directory: {LOG_DIR}\n"
        + f"Check interval: {CHECK_INTERVAL} minutes\n"
        + f"Report interval: {REPORT_INTERVAL} hours\n"
        + f"File index range: {START_INDEX} to {END_INDEX}\n"
        + f"Supported extensions: {', '.join(SUPPORTED_EXTENSIONS)}"
    )


def setup_logging():
    """Setup logging configuration"""
    # Create logs directory
    os.makedirs(LOG_DIR, exist_ok=True)

    # Generate log filename (with date)
    log_file = os.path.join(
        LOG_DIR, f"file_monitor_{datetime.now().strftime('%Y%m%d')}.log"
    )

    # Configure logging format
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),  # Output to console as well
        ],
    )

    logging.info("=== Logging system initialized ===")
    return log_file


def print_status(message: str, is_error: bool = False, notify_telegram: bool = False):
    """Print status information to log and terminal, optionally notify via Telegram"""
    if is_error:
        logging.error(message)
    else:
        logging.info(message)

    if notify_telegram and CHAT_ID:
        send_telegram_message(message)


def get_chat_id():
    """Get Chat ID of the most recent user interaction with the bot"""
    try:
        print_status("Attempting to get Chat ID...")
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            updates = response.json()
            if updates.get("ok") and updates.get("result"):
                latest_message = updates["result"][-1]
                chat_id = latest_message["message"]["chat"]["id"]
                print_status(f"Successfully found Chat ID: {chat_id}")
                print_status("Please copy this Chat ID to the CHAT_ID variable")
                return chat_id
            print_status(
                "No messages found. Please start a conversation with the bot (send /start)",
                True,
            )
            return None
    except Exception as e:
        print_status(f"Error getting Chat ID: {e}", True)
        print_status("Please use @userinfobot to get Chat ID manually", True)
        return None


def send_telegram_message(message: str):
    """Send Telegram message"""
    if not CHAT_ID:
        print_status("Please set CHAT_ID before running", True)
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=data, timeout=10)
    except requests.RequestException as e:
        print_status(f"Failed to send Telegram message: {e}", True)


class FileMonitor:
    def __init__(self):
        self.current_index = 0
        self.found_files = set()
        self.status_reporter = StatusReporter()
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        # Send initial status message
        startup_message = (
            "🤖 File Monitor System Started\n"
            f"📂 File save location: {os.path.abspath(DOWNLOAD_DIR)}\n"
            f"📝 Supported file types: {', '.join(SUPPORTED_EXTENSIONS)}\n"
            f"📋 Log file location: {os.path.abspath(LOG_DIR)}\n"
            "⏰ Status report will be sent every 6 hours\n"
            "❗ Immediate notification for new files"
        )
        send_telegram_message(startup_message)

    def check_file_exists(self, url: str) -> tuple:
        """Check if file exists and return its size"""
        try:
            response = requests.head(url, timeout=10)
            if response.status_code == 200:
                file_size = int(response.headers.get("content-length", 0))
                return True, file_size
            return False, 0
        except requests.RequestException as e:
            print_status(
                f"Error checking file existence: {e}", True, notify_telegram=True
            )
            return False, 0

    def download_file(self, url: str, filename: str) -> bool:
        try:
            print_status(f"Downloading file: {filename}")
            start_time = datetime.now()
            response = requests.get(url, timeout=30, stream=True)

            if response.status_code == 200:
                # 检查文件是否存在，如果存在则添加编号
                base_name, ext = os.path.splitext(filename)
                final_path = os.path.join(DOWNLOAD_DIR, filename)
                counter = 1

                while os.path.exists(final_path):
                    new_filename = f"{base_name}_{counter}{ext}"
                    final_path = os.path.join(DOWNLOAD_DIR, new_filename)
                    counter += 1

                # 如果文件名被修改，更新filename
                if counter > 1:
                    filename = os.path.basename(final_path)
                    print_status(f"File already exists, renamed to: {filename}")

                # Get file size from headers
                file_size = int(response.headers.get("content-length", 0))
                file_size_mb = file_size / (1024 * 1024)  # Convert to MB

                with open(final_path, "wb") as f:
                    f.write(response.content)

                # Calculate download time and speed
                download_time = (datetime.now() - start_time).total_seconds()
                download_speed = file_size / (1024 * 1024 * download_time)  # MB/s

                # Get file info
                file_info = (
                    f"File download completed: {filename}\n"
                    f"📦 Size: {file_size_mb:.2f} MB\n"
                    f"⚡ Speed: {download_speed:.2f} MB/s\n"
                    f"⏱ Time: {download_time:.2f} seconds"
                )
                print_status(file_info, notify_telegram=True)
                return True

            print_status(
                f"File download failed: {filename}\n"
                f"Status code: {response.status_code}\n"
                f"Response: {response.text[:200]}",  # Include part of error response
                True,
                notify_telegram=True,
            )
            return False
        except requests.RequestException as e:
            print_status(
                f"Error downloading file: {filename}\nError: {str(e)}",
                True,
                notify_telegram=True,
            )
            return False

    def process_file(self, index: int, ext: str) -> Tuple[bool, bool]:
        """Process a single file with given index and extension
        Returns: (file_found, file_downloaded)"""
        filename = f"file_{index}.{ext}"
        url = f"{BASE_URL}/{filename}"

        if url in self.found_files:
            return False, False

        print_status(f"Checking file: {filename}")
        try:
            exists, file_size = self.check_file_exists(url)
            if exists:
                # Notify Telegram only when new file is found
                file_size_mb = file_size / (1024 * 1024)  # Convert to MB
                alert_message = (
                    f"❗️New file found: {filename}\n"
                    f"📦 Size: {file_size_mb:.2f} MB\n"
                    f"👉 Attempting to download..."
                )
                send_telegram_message(alert_message)

                if self.download_file(url, filename):
                    self.found_files.add(url)
                    return True, True
                return True, False
        except Exception as e:
            print_status(
                f"Error processing file {filename}: {e}", True, notify_telegram=True
            )
        return False, False

    def send_status_report(self):
        """Send status report"""
        report = self.status_reporter.get_status_report()
        send_telegram_message(report)

    def check_new_files(self):
        print_status("Starting file check...")  # Log only, no Telegram notification
        print_status(f"Current check index: {self.current_index}")

        files_found = 0
        files_downloaded = 0

        # Check all files from START_INDEX to END_INDEX
        while self.current_index <= END_INDEX:
            for ext in SUPPORTED_EXTENSIONS:
                found, downloaded = self.process_file(self.current_index, ext)
                if found:
                    files_found += 1
                    if downloaded:
                        files_downloaded += 1

            self.current_index += 1
            # Reset to START_INDEX if we've reached the end
            if self.current_index > END_INDEX:
                self.current_index = START_INDEX
                print_status(
                    f"Completed full check cycle ({START_INDEX}-{END_INDEX}), resetting to {START_INDEX}",
                    notify_telegram=False,
                )
                break

        # Update status report data
        self.status_reporter.update_stats(files_found, files_downloaded)
        self.status_reporter.current_index = self.current_index


def main():
    try:
        # Initialize logging system
        log_file = setup_logging()
        logging.info(f"Log file created: {log_file}")

        # Validate configuration
        validate_config()

        monitor = FileMonitor()

        # Set up scheduled tasks
        schedule.every(CHECK_INTERVAL).minutes.do(monitor.check_new_files)
        schedule.every(REPORT_INTERVAL).hours.do(monitor.send_status_report)

        logging.info("Performing initial check...")
        monitor.check_new_files()

        logging.info("Entering monitoring loop...")
        while True:
            schedule.run_pending()
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Termination signal received, program ending")
        send_telegram_message("🛑 File Monitor System Stopped")
    except Exception as e:
        error_msg = f"System error occurred: {str(e)}"
        logging.error(error_msg)
        send_telegram_message(f"⚠️ {error_msg}\nPlease check log file: {log_file}")
    finally:
        logging.info("=== File Monitor System Stopped ===")


if __name__ == "__main__":
    main()
