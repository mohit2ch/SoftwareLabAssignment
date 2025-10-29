import logging
import colorlog

# Custom success log level
SUCCESS_LEVEL = 25

def setup_logger(name='proxyvpn', level=logging.INFO):
    """
    Set up and return a custom logger with colored output
    
    Args:
        name (str): Name of the logger
        level (int): Logging level to set
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Add the custom success level
    logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")
    
    # Create logger
    logger = colorlog.getLogger(name)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler
    handler = colorlog.StreamHandler()
    
    # Define format with colors
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "blue",
            "SUCCESS": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red,bg_white",
        },
        secondary_log_colors={},
        style='%'
    )
    
    # Set formatter for the handler
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Set level
    logger.setLevel(level)
    
    # Add success method to Logger class
    def success(self, message, *args, **kwargs):
        if self.isEnabledFor(SUCCESS_LEVEL):
            self._log(SUCCESS_LEVEL, message, args, **kwargs)
    
    # Add the success method to the Logger class
    logging.Logger.success = success
    
    return logger

def get_logger(name='proxyvpn'):
    """
    Get an existing logger or create a new one
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger doesn't have handlers, set it up
    if not logger.handlers:
        logger = setup_logger(name)
    
    return logger

# Default logger instance
default_logger = get_logger()
