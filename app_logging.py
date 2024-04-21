import logging
import logging.handlers
from dotenv import load_dotenv
import os
inport sys

# Load environment variables from .env file
load_dotenv()

# Now you can use os.getenv to access your variables
email_host = os.getenv('EMAIL_HOST')
email_port = int(os.getenv('EMAIL_PORT'))  # Convert port to int
email_username = os.getenv('EMAIL_USERNAME')
email_password = os.getenv('EMAIL_PASSWORD')
slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')

def setup_email_logging(logger):
    mail_handler = SMTPHandler(
        mailhost=(email_host, email_port),
        fromaddr=f"{email_username}",
        toaddrs=["rongen.robert@gmail.com"],
        subject="Critical Error Logged",
        credentials=(email_username, email_password),
        secure=()
    )
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter("Critical error in %(name)s: %(message)s"))
    logger.addHandler(mail_handler)

def setup_logger(name, log_file, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File handler
    file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=1048576, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler for output to stdout (useful for systemd)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Email and Slack handlers
    setup_email_logging(logger)
    # slack_handler = SlackHandler()
    # slack_handler.setLevel(logging.ERROR)
    # logger.addHandler(slack_handler)
    
    return logger
