
# app_logging.py
import logging
import logging.handlers
import os
import sys
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText

load_dotenv()

def setup_handlers(logger, log_file, log_level=logging.ERROR, to_stdout=True):
    log_directory = "/home/robert/github/skymonitor/log"
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

    if not any(isinstance(h, logging.handlers.SMTPHandler) for h in logger.handlers):
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
            logger.error("Failed to set up email logging: %s", str(e))
            setup_handlers(logger, 'email_setup_failures.log', log_level=logging.ERROR, to_stdout=False)

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
