
# app_logging.py
import logging
import logging.handlers
import os
import sys
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
import socket
import time

load_dotenv()

def setup_handlers(logger, log_file, log_level=logging.ERROR, to_stdout=True):
    log_directory = "/home/robert/github/skymonitor/logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    log_file_path = os.path.join(log_directory, log_file)

    if not any(isinstance(h, logging.handlers.RotatingFileHandler) for h in logger.handlers):
        file_handler = logging.handlers.RotatingFileHandler(log_file_path, maxBytes=1048576, backupCount=5)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    logger.setLevel(log_level)

    if to_stdout:
        if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

def setup_email_logging(logger):
    # Add specific conditions for logging
    # class AlertFilter(logging.Filter):
    #     def filter(self, record):
    #         return "High CPU temperature" in record.getMessage() or "High disk usage" in record.getMessage()
    email_host = os.getenv('EMAIL_HOST')
    email_port = int(os.getenv('EMAIL_PORT'))  # Convert port to int
    email_username = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')

    # Setting up a separate logger for email errors to avoid recursion
    email_error_logger = logging.getLogger('email_error')
    fh = logging.FileHandler('email_errors.log')
    fh.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    email_error_logger.addHandler(fh)

    resolved = False
    for _ in range(3):  # Try to resolve up to 3 times
        try:
            # Check if DNS can resolve the host
            socket.gethostbyname(email_host)
            resolved = True
            break
        except socket.gaierror:
            logger.error("DNS resolution failed for %s. Retrying...", email_host)
            time.sleep(5)  # Wait for 5 seconds before retrying

    if not resolved:
        logger.error("Failed to resolve SMTP server address after multiple attempts.")
        return

    try:
        server = smtplib.SMTP(email_host, email_port)
        server.starttls()  # Secure the connection
        server.login(email_username, email_password)
        server.quit()

        mail_handler = logging.handlers.SMTPHandler(
            mailhost=(email_host, email_port),
            fromaddr=email_username,
            toaddrs="rongen.robert@gmail.com",
            subject="Critical Error Logged",
            credentials=(email_username, email_password),
            secure=()
        )
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(mail_handler)

    except Exception as e:
        if attempt_to_email_errors:
            email_error_logger.error("Failed to set up email logging: %s", str(e))
            # Disable further attempts to log errors via email to prevent recursion
            setup_email_logging(logger, attempt_to_email_errors=False)

def setup_logger(name, log_file, level=logging.INFO):
    try:
        logger = logging.getLogger(name)
        setup_handlers(logger, log_file, log_level=level)  # Setup with console output
        setup_email_logging(logger)
        return logger
    except Exception as e:
        sys.stderr.write("Failed to set up logger: {}\n".format(e))
        sys.exit(1)

# Example usage:
logger = setup_logger('test_email_alert', 'application.log')
logger.error("This is a test error message to trigger an email alert!")
