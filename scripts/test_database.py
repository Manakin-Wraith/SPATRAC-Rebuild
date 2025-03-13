"""
Test database connection and basic functionality.
"""
import sys
import os
import pandas as pd
import logging
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_access.database import load_data, execute_query
from utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger('test_database')

def test_connection():
    """Test database connection."""
    try:
        query = "SELECT 1 as connection_test"
        result = load_data(query)
        
        if not result.empty and result['connection_test'].iloc[0] == 1:
            logger.info("✅ Database connection successful")
            return True
        else:
            logger.error("❌ Database connection failed: Empty result set")
            return False
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def test_tables():
    """Test if required tables exist."""
    required_tables = [
        'departments', 'suppliers', 'products', 'inventory',
        'inventory_transactions', 'received_products', 'recipes',
        'recipe_ingredients', 'sales', 'sales_items', 'expired_products'
    ]
    
    try:
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        result = load_data(query)
        
        if result.empty:
            logger.error("❌ Failed to retrieve table list from database")
            return False
        
        existing_tables = result['table_name'].tolist()
        logger.info(f"Found {len(existing_tables)} tables in the database")
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.warning(f"⚠️ Missing required tables: {', '.join(missing_tables)}")
            return False
        else:
            logger.info("✅ All required tables exist in the database")
            return True
    except Exception as e:
        logger.error(f"❌ Error checking required tables: {e}")
        return False

def test_basic_queries():
    """Test basic queries to ensure data access is working."""
    tests = [
        {
            "name": "Products Count",
            "query": "SELECT COUNT(*) as count FROM products",
            "success_condition": lambda df: not df.empty and 'count' in df.columns
        },
        {
            "name": "Departments List",
            "query": "SELECT * FROM departments",
            "success_condition": lambda df: not df.empty and 'department_code' in df.columns
        },
        {
            "name": "Suppliers List",
            "query": "SELECT * FROM suppliers",
            "success_condition": lambda df: not df.empty and 'supplier_code' in df.columns
        },
        {
            "name": "Current Inventory",
            "query": "SELECT * FROM inventory WHERE quantity_remaining > 0",
            "success_condition": lambda df: 'product_code' in df.columns
        }
    ]
    
    all_passed = True
    
    for test in tests:
        try:
            result = load_data(test["query"])
            if test["success_condition"](result):
                logger.info(f"✅ Test '{test['name']}' passed: {len(result)} rows returned")
            else:
                logger.warning(f"⚠️ Test '{test['name']}' failed: Unexpected result format")
                all_passed = False
        except Exception as e:
            logger.error(f"❌ Test '{test['name']}' failed with error: {e}")
            all_passed = False
    
    return all_passed

def main():
    """Run all tests."""
    logger.info("Starting database tests...")
    
    # Test connection
    connection_ok = test_connection()
    if not connection_ok:
        logger.error("❌ Database connection test failed. Stopping further tests.")
        return False
    
    # Test tables
    tables_ok = test_tables()
    if not tables_ok:
        logger.warning("⚠️ Table check failed. Some functionality may not work correctly.")
    
    # Test basic queries
    queries_ok = test_basic_queries()
    if not queries_ok:
        logger.warning("⚠️ Some basic query tests failed. Data access may be limited.")
    
    # Overall status
    if connection_ok and tables_ok and queries_ok:
        logger.info("✅ All tests passed successfully!")
        return True
    else:
        logger.warning("⚠️ Some tests failed. See log for details.")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Database tests {'passed' if success else 'failed'}. See log for details.")
    sys.exit(0 if success else 1)
