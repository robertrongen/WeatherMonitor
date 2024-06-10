import logging
import logging.handlers
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def setup_handlers(logger, log_file, log_level=logging.ERROR, to_stdout=True):
    log_directory = "/home/robert/github/skymonitor/log"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    log_file_path = os.path.join(log_directory, log_file)

    file_handler = logging.handlers.RotatingFileHandler(log_file_path, maxBytes=1048576, backupCount=5)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    logger.setLevel(log_level)

    if to_stdout:
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

    email_error_logger = logging.getLogger('email_errors')
    setup_handlers(email_error_logger, 'email_errors.log', log_level=logging.ERROR, to_stdout=False)  # No console output for email errors

    try:
        email_handler = logging.handlers.SMTPHandler(
            mailhost=(email_host, email_port),
            fromaddr=email_username,
            toaddrs=["rongen.robert@gmail.com"],
            subject="Critical Error Logged",
            credentials=(email_username, email_password),
            secure=()
        )
        email_handler.setLevel(logging.ERROR)
        email_handler.setFormatter(logging.Formatter("Critical error in %(name)s: %(message)s"))
        logger.addHandler(email_handler)
    except Exception as e:
        logger.error("Failed to set up email logging: %s", e)

def setup_logger(name, log_file, level=logging.INFO):
    try:
        logger = logging.getLogger(name)
        setup_handlers(logger, log_file, log_level=level)  # Setup with console output
        setup_email_logging(logger)
        return logger
    except Exception as e:
        sys.stderr.write("Failed to set up logger: {}\n".format(e))
        sys.exit(1)

    return logger
