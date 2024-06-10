import logging
import logging.handlers
from logging.handlers import RotatingFileHandler
import os
import sys
from dotenv import load_dotenv

load_dotenv()

email_host = os.getenv('EMAIL_HOST')
email_port = int(os.getenv('EMAIL_PORT'))  # Convert port to int
email_username = os.getenv('EMAIL_USERNAME')
email_password = os.getenv('EMAIL_PASSWORD')
# slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')

def setup_email_logging(logger):

    # Add specific conditions for logging
    class AlertFilter(logging.Filter):
        def filter(self, record):
            return "High CPU temperature" in record.getMessage() or "High disk usage" in record.getMessage()

    email_handler = logging.handlers.SMTPHandler(
        mailhost=(email_host, email_port),
        fromaddr=f"{email_username}",
        toaddrs=["rongen.robert@gmail.com"],
        subject="Critical Error Logged",
        credentials=(email_username, email_password),
        secure=()
    )
    email_handler.setLevel(logging.ERROR)
    email_handler.setFormatter(logging.Formatter("Critical error in %(name)s: %(message)s"))
    logger.addHandler(email_handler)

def setup_logger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Ensure the /log directory exists
    log_directory = "/home/robert/github/skymonitor/log"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    # Construct the full log file path
    log_file_path = os.path.join(log_directory, log_file)
    print(f"Logging to: {log_file_path}")

    # File handler
    file_handler = RotatingFileHandler(log_file_path, maxBytes=1048576, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler for output to stdout (useful for systemd)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Email and Slack handlers
    # setup_email_logging(logger)
    # slack_handler = SlackHandler()
    # slack_handler.setLevel(logging.ERROR)
    # logger.addHandler(slack_handler)
    
    return logger
