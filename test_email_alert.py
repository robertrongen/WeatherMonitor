from app_logging import setup_logger

def test_email_alert():
    # Set up the logger with a specific configuration
    logger = setup_logger('test_email_alert', 'test_email_alert.log')

    # Manually add the email handler with critical settings if not added by default
    logger.error("This is a test error message to trigger an email alert!")

if __name__ == "__main__":
    test_email_alert()
