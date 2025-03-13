"""
Logging utilities for SPATRAC.
"""
import os
import logging
import pandas as pd
from datetime import datetime

def setup_logger(name, log_dir='logs', log_level=logging.INFO):
    """
    Set up a logger with file and console handlers.
    
    Args:
        name (str): Logger name
        log_dir (str): Directory to store log files
        log_level (int): Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove existing handlers if any
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create file handler
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f'{name}_{timestamp}.log')
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_dataframe(logger, df, message="DataFrame contents:", level=logging.INFO):
    """
    Log a pandas DataFrame with proper formatting.
    
    Args:
        logger (logging.Logger): Logger to use
        df (pandas.DataFrame): DataFrame to log
        message (str): Message to log before the DataFrame
        level (int): Logging level
    """
    if df is None or df.empty:
        logger.log(level, f"{message} Empty DataFrame")
        return
    
    # Format DataFrame as string with limited rows
    max_rows = min(10, len(df))
    df_str = df.head(max_rows).to_string()
    
    # Log the message and DataFrame
    logger.log(level, f"{message}\n{df_str}")
    
    # If DataFrame has more rows than shown, log a message
    if len(df) > max_rows:
        logger.log(level, f"... {len(df) - max_rows} more rows not shown")

def log_error(logger, error, context=None):
    """
    Log an error with context information.
    
    Args:
        logger (logging.Logger): Logger to use
        error (Exception): Error to log
        context (dict, optional): Additional context information
    """
    error_message = f"Error: {type(error).__name__}: {str(error)}"
    
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        error_message += f" | Context: {context_str}"
    
    logger.error(error_message)

def log_transaction(logger, transaction_type, details, status="SUCCESS"):
    """
    Log a transaction with structured information.
    
    Args:
        logger (logging.Logger): Logger to use
        transaction_type (str): Type of transaction (e.g., 'INVENTORY_UPDATE', 'PRODUCT_RECEIVE')
        details (dict): Transaction details
        status (str): Transaction status ('SUCCESS', 'FAILURE', 'WARNING')
    """
    # Format details as string
    details_str = ", ".join(f"{k}={v}" for k, v in details.items())
    
    # Log with appropriate level based on status
    if status == "SUCCESS":
        logger.info(f"TRANSACTION [{transaction_type}] {status}: {details_str}")
    elif status == "WARNING":
        logger.warning(f"TRANSACTION [{transaction_type}] {status}: {details_str}")
    elif status == "FAILURE":
        logger.error(f"TRANSACTION [{transaction_type}] {status}: {details_str}")
    else:
        logger.info(f"TRANSACTION [{transaction_type}] UNKNOWN STATUS: {details_str}")
