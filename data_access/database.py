"""
Database utility functions.
"""
import pandas as pd
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config.settings import DATABASE_URL

# Configure logging
logger = logging.getLogger(__name__)

# Create database engine
try:
    engine = create_engine(DATABASE_URL)
    logger.info(f"Successfully connected to database")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    raise

# Create a session factory
Session = sessionmaker(bind=engine)

# Create a session instance
db_session = Session()

def load_data(query, params=None):
    """
    Load data from database using the provided query.
    
    Args:
        query (str): SQL query to execute
        params (dict or list, optional): Parameters for the query
        
    Returns:
        pandas.DataFrame: Result of the query
    """
    try:
        if params is not None:
            # Handle list of parameters for positional binding
            if isinstance(params, list):
                # Convert the query to use SQLAlchemy positional parameters
                modified_query = query.replace('%s', ':param')
                # Create a dictionary of parameters
                param_dict = {f'param{i}': val for i, val in enumerate(params)}
                with engine.connect() as conn:
                    return pd.read_sql_query(text(modified_query), conn, params=param_dict)
            # Handle dictionary of parameters
            elif isinstance(params, dict):
                # Convert psycopg2 style parameters to SQLAlchemy style
                modified_query = query.replace('%(', ':').replace(')s', '')
                with engine.connect() as conn:
                    return pd.read_sql_query(text(modified_query), conn, params=params)
        with engine.connect() as conn:
            return pd.read_sql_query(text(query), conn)
    except SQLAlchemyError as e:
        logger.error(f"Database error in load_data: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error in load_data: {e}")
        return pd.DataFrame()

def execute_query(query, params=None):
    """
    Execute a database query without returning results.
    
    Args:
        query (str): SQL query to execute
        params (dict or list, optional): Parameters for the query
        
    Returns:
        list: Result rows for SELECT queries, None for other queries
    """
    try:
        with engine.begin() as conn:
            if params:
                # Handle list of parameters for positional binding
                if isinstance(params, list):
                    # For positional parameters, directly replace %s with named parameters
                    modified_query = query
                    param_dict = {}
                    
                    for i, param in enumerate(params):
                        param_name = f"param{i}"
                        # Replace only the first occurrence of %s
                        modified_query = modified_query.replace('%s', f":{param_name}", 1)
                        param_dict[param_name] = param
                    
                    result = conn.execute(text(modified_query), param_dict)
                    if result.returns_rows:
                        return result.fetchall()  # Return results for SELECT queries
                # Handle dictionary of parameters
                elif isinstance(params, dict):
                    # Convert psycopg2 style parameters to SQLAlchemy style
                    modified_query = query.replace('%(', ':').replace(')s', '')
                    result = conn.execute(text(modified_query), params)
                    if result.returns_rows:
                        return result.fetchall()  # Return results for SELECT queries
                else:
                    raise ValueError("Parameters must be a list or dictionary")
            else:
                result = conn.execute(text(query))
                if result.returns_rows:
                    return result.fetchall()  # Return results for SELECT queries
    except SQLAlchemyError as e:
        logger.error(f"Database error in execute_query: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in execute_query: {e}")
        raise

def execute_transaction(queries_and_params):
    """
    Execute multiple queries in a single transaction.
    
    Args:
        queries_and_params (list): List of tuples (query, params)
        
    Returns:
        bool: True if transaction succeeded, False otherwise
    """
    try:
        with engine.begin() as conn:
            for query, params in queries_and_params:
                if params:
                    # Handle list of parameters for positional binding
                    if isinstance(params, list):
                        # For positional parameters, directly replace %s with named parameters
                        modified_query = query
                        param_dict = {}
                        
                        for i, param in enumerate(params):
                            param_name = f"param{i}"
                            # Replace only the first occurrence of %s
                            modified_query = modified_query.replace('%s', f":{param_name}", 1)
                            param_dict[param_name] = param
                        
                        conn.execute(text(modified_query), param_dict)
                    # Handle dictionary of parameters
                    elif isinstance(params, dict):
                        # Convert psycopg2 style parameters to SQLAlchemy style
                        modified_query = query.replace('%(', ':').replace(')s', '')
                        conn.execute(text(modified_query), params)
                    else:
                        raise ValueError("Parameters must be a list or dictionary")
                else:
                    conn.execute(text(query))
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database error in execute_transaction: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in execute_transaction: {e}")
        return False

def validate_supplier_invoice(supplier_code, invoice_number):
    """
    Validate if an invoice number is unique for a supplier.
    
    Args:
        supplier_code (str): Supplier code
        invoice_number (str): Invoice number to validate
        
    Returns:
        bool: True if valid (no duplicate), False if duplicate exists
    """
    query = """
        SELECT COUNT(*) as count 
        FROM received_products 
        WHERE supplier_code = %s AND supplier_invoice_number = %s
    """
    result = load_data(query, [supplier_code, invoice_number])
    return result['count'].iloc[0] == 0 if not result.empty else True

def get_invoice_summary(invoice_number):
    """
    Get summary information for a specific invoice.
    
    Args:
        invoice_number (str): Invoice number to get summary for
        
    Returns:
        dict: Summary information including total items, total quantity, and status
    """
    query = """
        SELECT 
            COUNT(*) as total_items,
            SUM(quantity) as total_quantity,
            MIN(quality_status) as min_status,
            MAX(quality_status) as max_status,
            MIN(received_date) as received_date,
            MAX(supplier_code) as supplier_code
        FROM received_products
        WHERE supplier_invoice_number = %s
    """
    result = load_data(query, [invoice_number])
    if result.empty:
        return None
    
    return {
        'total_items': result['total_items'].iloc[0],
        'total_quantity': result['total_quantity'].iloc[0],
        'status': result['min_status'].iloc[0] if result['min_status'].iloc[0] == result['max_status'].iloc[0] else 'MIXED',
        'received_date': result['received_date'].iloc[0],
        'supplier_code': result['supplier_code'].iloc[0]
    }
