"""
Inventory data access functions.
"""
import pandas as pd
import logging
from datetime import datetime, timedelta
from .database import load_data, execute_query, execute_transaction
from config.settings import DATE_FORMAT, EXPIRY_WARNING_DAYS

# Configure logging
logger = logging.getLogger(__name__)

def get_current_inventory():
    """
    Get current inventory levels.
    
    Returns:
        pandas.DataFrame: Current inventory data
    """
    query = """
        SELECT 
            i.product_code,
            p.product_name,
            d.department_name,
            s.supplier_name,
            i.quantity,
            i.unit,
            i.last_updated,
            i.storage_location,
            i.expiry_date,
            i.best_before_date
        FROM 
            inventory i
        JOIN 
            products p ON i.product_code = p.product_code
        JOIN 
            departments d ON p.department_code = d.department_code
        JOIN 
            suppliers s ON p.supplier_code = s.supplier_code
        WHERE 
            i.quantity > 0
        ORDER BY 
            d.department_name, p.product_name
    """
    try:
        inventory_data = load_data(query)
        
        # Format dates
        if not inventory_data.empty:
            for date_col in ['expiry_date', 'best_before_date']:
                if date_col in inventory_data.columns:
                    inventory_data[date_col] = pd.to_datetime(inventory_data[date_col]).dt.strftime(DATE_FORMAT)
            
            inventory_data['last_updated'] = pd.to_datetime(inventory_data['last_updated'])
        
        logger.info(f"Retrieved current inventory: {len(inventory_data)} items")
        return inventory_data
    except Exception as e:
        logger.error(f"Error retrieving current inventory: {e}")
        return pd.DataFrame()

def get_inventory_transactions(start_date=None, end_date=None, product_code=None, transaction_type=None):
    """
    Get inventory transactions with optional filters.
    
    Args:
        start_date (datetime, optional): Start date for filtering
        end_date (datetime, optional): End date for filtering
        product_code (str, optional): Product code for filtering
        transaction_type (str, optional): Transaction type for filtering
        
    Returns:
        pandas.DataFrame: Inventory transactions
    """
    # Build query with conditions
    conditions = []
    params = {}
    
    query = """
        SELECT 
            it.transaction_id,
            it.product_code,
            p.product_name,
            d.department_name,
            s.supplier_name,
            it.transaction_type,
            it.quantity,
            it.unit,
            it.transaction_date,
            it.reference_id,
            it.notes
        FROM 
            inventory_transactions it
        JOIN 
            products p ON it.product_code = p.product_code
        JOIN 
            departments d ON p.department_code = d.department_code
        JOIN 
            suppliers s ON p.supplier_code = s.supplier_code
        WHERE 1=1
    """
    
    if start_date:
        conditions.append("it.transaction_date >= %(start_date)s")
        params['start_date'] = start_date
    
    if end_date:
        conditions.append("it.transaction_date <= %(end_date)s")
        params['end_date'] = end_date
    
    if product_code:
        conditions.append("it.product_code = %(product_code)s")
        params['product_code'] = product_code
    
    if transaction_type:
        conditions.append("it.transaction_type = %(transaction_type)s")
        params['transaction_type'] = transaction_type
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    query += " ORDER BY it.transaction_date DESC"
    
    try:
        transactions = load_data(query, params)
        
        # Format dates
        if not transactions.empty:
            transactions['transaction_date'] = pd.to_datetime(transactions['transaction_date'])
        
        logger.info(f"Retrieved inventory transactions: {len(transactions)} records")
        return transactions
    except Exception as e:
        logger.error(f"Error retrieving inventory transactions: {e}")
        return pd.DataFrame()

def get_expiring_soon(days=None):
    """
    Get products that are expiring soon.
    
    Args:
        days (int, optional): Number of days to consider for expiry warning
        
    Returns:
        pandas.DataFrame: Products expiring soon
    """
    if days is None:
        days = EXPIRY_WARNING_DAYS
    
    warning_date = datetime.now().date() + timedelta(days=days)
    
    query = """
        SELECT 
            i.product_code,
            p.product_name,
            d.department_name,
            s.supplier_name,
            i.quantity,
            i.unit,
            i.storage_location,
            i.expiry_date,
            i.best_before_date,
            i.last_updated
        FROM 
            inventory i
        JOIN 
            products p ON i.product_code = p.product_code
        JOIN 
            departments d ON p.department_code = d.department_code
        JOIN 
            suppliers s ON p.supplier_code = s.supplier_code
        WHERE 
            i.quantity > 0
            AND i.expiry_date IS NOT NULL
            AND i.expiry_date <= %(warning_date)s
            AND i.expiry_date >= CURRENT_DATE
        ORDER BY 
            i.expiry_date, d.department_name, p.product_name
    """
    
    try:
        expiring_soon = load_data(query, {'warning_date': warning_date})
        
        # Format dates
        if not expiring_soon.empty:
            for date_col in ['expiry_date', 'best_before_date']:
                if date_col in expiring_soon.columns:
                    expiring_soon[date_col] = pd.to_datetime(expiring_soon[date_col]).dt.strftime(DATE_FORMAT)
            
            expiring_soon['last_updated'] = pd.to_datetime(expiring_soon['last_updated'])
            
            # Calculate days until expiry
            expiring_soon['days_until_expiry'] = (pd.to_datetime(expiring_soon['expiry_date']) - 
                                                pd.Timestamp.now().normalize()).dt.days
        
        logger.info(f"Retrieved products expiring soon: {len(expiring_soon)} items")
        return expiring_soon
    except Exception as e:
        logger.error(f"Error retrieving products expiring soon: {e}")
        return pd.DataFrame()

def get_expired_products():
    """
    Get expired products from the expired_products table.
    
    Returns:
        pandas.DataFrame: Expired products
    """
    query = """
        SELECT 
            ep.id,
            ep.product_code,
            p.product_name,
            d.department_name,
            s.supplier_name,
            ep.quantity,
            ep.unit,
            ep.expiry_date,
            ep.removed_date,
            ep.removed_by,
            ep.notes,
            ep.category
        FROM 
            expired_products ep
        JOIN 
            products p ON ep.product_code = p.product_code
        JOIN 
            departments d ON p.department_code = d.department_code
        JOIN 
            suppliers s ON p.supplier_code = s.supplier_code
        ORDER BY 
            ep.removed_date DESC, d.department_name, p.product_name
    """
    
    try:
        expired_products = load_data(query)
        
        # Format dates
        if not expired_products.empty:
            for date_col in ['expiry_date', 'removed_date']:
                if date_col in expired_products.columns:
                    expired_products[date_col] = pd.to_datetime(expired_products[date_col]).dt.strftime(DATE_FORMAT)
        
        logger.info(f"Retrieved expired products: {len(expired_products)} items")
        return expired_products
    except Exception as e:
        logger.error(f"Error retrieving expired products: {e}")
        return pd.DataFrame()

def update_inventory(product_code, quantity_change, transaction_type, reference_id=None, notes=None):
    """
    Update inventory and record the transaction.
    
    Args:
        product_code (str): Product code
        quantity_change (float): Quantity change (positive for additions, negative for removals)
        transaction_type (str): Type of transaction
        reference_id (str, optional): Reference ID for the transaction
        notes (str, optional): Notes for the transaction
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Start a transaction
        queries_and_params = []
        
        # Get current quantity
        check_query = "SELECT quantity, unit FROM inventory WHERE product_code = %(product_code)s"
        current = load_data(check_query, {'product_code': product_code})
        
        if current.empty:
            # Product not in inventory yet, insert new record
            insert_query = """
                INSERT INTO inventory (
                    product_code, 
                    quantity, 
                    unit, 
                    last_updated
                )
                SELECT 
                    %(product_code)s, 
                    %(quantity)s, 
                    (SELECT unit FROM products WHERE product_code = %(product_code)s),
                    CURRENT_TIMESTAMP
                WHERE 
                    EXISTS (SELECT 1 FROM products WHERE product_code = %(product_code)s)
            """
            queries_and_params.append((insert_query, {
                'product_code': product_code,
                'quantity': quantity_change
            }))
        else:
            # Update existing inventory
            update_query = """
                UPDATE inventory 
                SET 
                    quantity = quantity + %(quantity_change)s,
                    last_updated = CURRENT_TIMESTAMP
                WHERE 
                    product_code = %(product_code)s
            """
            queries_and_params.append((update_query, {
                'product_code': product_code,
                'quantity_change': quantity_change
            }))
        
        # Record transaction
        transaction_query = """
            INSERT INTO inventory_transactions (
                product_code,
                transaction_type,
                quantity,
                unit,
                transaction_date,
                reference_id,
                notes
            ) VALUES (
                %(product_code)s,
                %(transaction_type)s,
                %(quantity)s,
                (SELECT unit FROM products WHERE product_code = %(product_code)s),
                CURRENT_TIMESTAMP,
                %(reference_id)s,
                %(notes)s
            )
        """
        queries_and_params.append((transaction_query, {
            'product_code': product_code,
            'transaction_type': transaction_type,
            'quantity': quantity_change,
            'reference_id': reference_id,
            'notes': notes
        }))
        
        # Execute transaction
        success = execute_transaction(queries_and_params)
        
        if success:
            logger.info(f"Updated inventory for product {product_code}: {quantity_change} units ({transaction_type})")
        else:
            logger.error(f"Failed to update inventory for product {product_code}")
        
        return success
    except Exception as e:
        logger.error(f"Error updating inventory: {e}")
        return False

def mark_as_expired(product_code, quantity, expiry_date, removed_by, category=None, notes=None):
    """
    Mark a product as expired and move it from inventory to expired_products.
    
    Args:
        product_code (str): Product code
        quantity (float): Quantity to mark as expired
        expiry_date (date): Expiry date
        removed_by (str): User who removed the product
        category (str, optional): Category of expiry
        notes (str, optional): Notes
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Start a transaction
        queries_and_params = []
        
        # Get current quantity and unit
        check_query = "SELECT quantity, unit FROM inventory WHERE product_code = %(product_code)s"
        current = load_data(check_query, {'product_code': product_code})
        
        if current.empty or current['quantity'].iloc[0] < quantity:
            logger.error(f"Insufficient inventory for product {product_code} to mark as expired")
            return False
        
        unit = current['unit'].iloc[0]
        
        # Update inventory
        update_query = """
            UPDATE inventory 
            SET 
                quantity = quantity - %(quantity)s,
                last_updated = CURRENT_TIMESTAMP
            WHERE 
                product_code = %(product_code)s
        """
        queries_and_params.append((update_query, {
            'product_code': product_code,
            'quantity': quantity
        }))
        
        # Record transaction
        transaction_query = """
            INSERT INTO inventory_transactions (
                product_code,
                transaction_type,
                quantity,
                unit,
                transaction_date,
                reference_id,
                notes
            ) VALUES (
                %(product_code)s,
                'EXPIRED',
                %(quantity)s,
                %(unit)s,
                CURRENT_TIMESTAMP,
                NULL,
                %(notes)s
            )
        """
        queries_and_params.append((transaction_query, {
            'product_code': product_code,
            'quantity': -quantity,  # Negative because it's a removal
            'unit': unit,
            'notes': notes
        }))
        
        # Add to expired_products
        expired_query = """
            INSERT INTO expired_products (
                product_code,
                quantity,
                unit,
                expiry_date,
                removed_date,
                removed_by,
                category,
                notes
            ) VALUES (
                %(product_code)s,
                %(quantity)s,
                %(unit)s,
                %(expiry_date)s,
                CURRENT_TIMESTAMP,
                %(removed_by)s,
                %(category)s,
                %(notes)s
            )
        """
        queries_and_params.append((expired_query, {
            'product_code': product_code,
            'quantity': quantity,
            'unit': unit,
            'expiry_date': expiry_date,
            'removed_by': removed_by,
            'category': category,
            'notes': notes
        }))
        
        # Execute transaction
        success = execute_transaction(queries_and_params)
        
        if success:
            logger.info(f"Marked {quantity} {unit} of product {product_code} as expired")
        else:
            logger.error(f"Failed to mark product {product_code} as expired")
        
        return success
    except Exception as e:
        logger.error(f"Error marking product as expired: {e}")
        return False
