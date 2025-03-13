"""
SPATRAC - Product Traceability System
Main application entry point.
"""
import streamlit as st
import pandas as pd
import logging
import os
from datetime import datetime
from data_access.database import load_data

# Set up logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'spatrac_{pd.Timestamp.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure the page settings first, before any other imports
st.set_page_config(
    page_title="SPATRAC",
    page_icon="🏭",
    layout="wide"
)

def check_database_connection():
    """Check if database connection is working."""
    try:
        query = "SELECT 1 as connection_test"
        result = load_data(query)
        if not result.empty and result['connection_test'].iloc[0] == 1:
            logger.info("Database connection successful")
            return True
        else:
            logger.error("Database connection failed: Empty result set")
            return False
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def check_required_tables():
    """Check if all required tables exist in the database."""
    required_tables = [
        'departments', 'suppliers', 'products', 'inventory',
        'inventory_transactions', 'received_products', 'recipes',
        'recipe_ingredients', 'sales', 'sales_items', 'expired_products',
        'quality_checks'
    ]
    
    try:
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        result = load_data(query)
        
        if result.empty:
            logger.error("Failed to retrieve table list from database")
            return False
        
        existing_tables = result['table_name'].tolist()
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.warning(f"Missing required tables: {', '.join(missing_tables)}")
            return False
        else:
            logger.info("All required tables exist in the database")
            return True
    except Exception as e:
        logger.error(f"Error checking required tables: {e}")
        return False

def dashboard_home():
    """Display the main dashboard home page with key metrics and charts."""
    # Add custom CSS for Poppins font
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    </style>
    """, unsafe_allow_html=True)
    
    st.header("Overview")
    
    # Display current date and time
    st.subheader(f"{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Quality Checks metrics as the main metric
    st.markdown("### Quality Control Performance")
    
    try:
        quality_query = """
            SELECT 
                COUNT(*) as total_checks,
                COUNT(DISTINCT tracking_id) as products_checked,
                SUM(CASE WHEN status = 'PASSED' THEN 1 ELSE 0 END) as passed_checks
            FROM 
                quality_checks
            WHERE 
                checked_at >= CURRENT_DATE - INTERVAL '30 days'
        """
        quality_data = load_data(quality_query)
        
        if not quality_data.empty and quality_data['total_checks'].iloc[0] > 0:
            pass_percentage = (quality_data['passed_checks'].iloc[0] / quality_data['total_checks'].iloc[0]) * 100
            
            # Create a full-width container for the main metric
            html_content = f"""
            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #4CAF50, #2E7D32); 
                        color: white; border-radius: 15px; margin: 15px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div style="font-size: 4rem; font-weight: bold; margin-bottom: 5px;">{pass_percentage:.1f}%</div>
                <div style="font-size: 1.5rem; margin-bottom: 15px;">Quality Checks Passed</div>
                <div style="display: flex; justify-content: center; gap: 30px; font-size: 1.1rem;">
                    <div>
                        <div style="font-weight: bold;">{quality_data['total_checks'].iloc[0]:,d}</div>
                        <div>Total Checks</div>
                    </div>
                    <div>
                        <div style="font-weight: bold;">{quality_data['products_checked'].iloc[0]:,d}</div>
                        <div>Products Checked</div>
                    </div>
                </div>
                <div style="margin-top: 10px; font-size: 0.9rem;">
                    <a href="pages/03_quality_control.py" style="color: white; text-decoration: underline;">
                        View details in Quality Control
                    </a>
                </div>
            </div>
            """
            import streamlit.components.v1 as components
            components.html(html_content, height=300)
        else:
            html_content = f"""
            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #607D8B, #455A64); 
                        color: white; border-radius: 15px; margin: 15px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div style="font-size: 4rem; font-weight: bold; margin-bottom: 5px;">N/A</div>
                <div style="font-size: 1.5rem; margin-bottom: 15px;">Quality Checks Passed</div>
                <div style="font-size: 1.1rem;">No quality checks performed in the last 30 days</div>
                <div style="margin-top: 10px; font-size: 0.9rem;">
                    <a href="pages/03_quality_control.py" style="color: white; text-decoration: underline;">
                        View details in Quality Control
                    </a>
                </div>
            </div>
            """
            import streamlit.components.v1 as components
            components.html(html_content, height=300)
    except Exception as e:
        logger.error(f"Error loading quality checks metrics: {e}")
        st.error("Error loading quality checks data")
    
    # Product Expiry Status metric
    st.markdown("### Product Expiry Status")
    
    try:
        # Query for expired products
        expired_query = """
            SELECT COUNT(*) as count
            FROM inventory i
            WHERE i.quantity_remaining > 0
            AND i.expiry_date IS NOT NULL
            AND i.expiry_date < CURRENT_DATE
        """
        expired_data = load_data(expired_query)
        
        # Query for products expiring soon (within 30 days)
        expiring_soon_query = """
            SELECT 
                COUNT(*) as count,
                MIN(i.expiry_date) as earliest_expiry
            FROM 
                inventory i
            WHERE 
                i.quantity_remaining > 0
                AND i.expiry_date IS NOT NULL
                AND i.expiry_date <= CURRENT_DATE + INTERVAL '30 days'
                AND i.expiry_date >= CURRENT_DATE
        """
        expiring_soon_data = load_data(expiring_soon_query)
        
        expired_count = expired_data['count'].iloc[0] if not expired_data.empty else 0
        expiring_soon_count = expiring_soon_data['count'].iloc[0] if not expiring_soon_data.empty else 0
        
        # Get earliest expiry date if there are products expiring soon
        earliest_expiry = None
        if not expiring_soon_data.empty and expiring_soon_count > 0:
            earliest_expiry = expiring_soon_data['earliest_expiry'].iloc[0]
            days_until_earliest = (earliest_expiry - pd.Timestamp.now().date()).days
        
        # Determine the status color based on expired and expiring soon counts
        if expired_count > 0 or expiring_soon_count > 0:
            # Determine the background color gradient based on the status
            if expired_count > 0:
                # Red gradient for expired products
                bg_gradient = "linear-gradient(135deg, #FF5252, #B71C1C)"
                status_text = "Critical"
                warning_text = f"⚠️ {expired_count} products have expired and need immediate attention!"
            elif expiring_soon_count > 0:
                # Orange/yellow gradient for products expiring soon
                bg_gradient = "linear-gradient(135deg, #FFA726, #E65100)"
                status_text = "Warning"
                if earliest_expiry and days_until_earliest is not None:
                    warning_text = f"⚠️ {expiring_soon_count} products are expiring within the next 30 days. Earliest expiry in {days_until_earliest} days."
                else:
                    warning_text = f"⚠️ {expiring_soon_count} products are expiring within the next 30 days."
            else:
                # Green gradient for good status
                bg_gradient = "linear-gradient(135deg, #4CAF50, #2E7D32)"
                status_text = "Good"
                warning_text = "✅ No products expiring soon."
            
            html_content = f"""
            <div style="text-align: center; padding: 25px; background: {bg_gradient}; 
                        color: white; border-radius: 15px; margin: 15px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: bold; margin-bottom: 5px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Product Expiry Status: {status_text}</div>
                <div style="display: flex; justify-content: center; gap: 30px; font-size: 1.1rem; margin-top: 20px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">
                    <div>
                        <div style="font-size: 2.5rem; font-weight: bold; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">{expired_count}</div>
                        <div style="font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Expired Products</div>
                    </div>
                    <div>
                        <div style="font-size: 2.5rem; font-weight: bold; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">{expiring_soon_count}</div>
                        <div style="font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Expiring Within 30 Days</div>
                    </div>
                </div>
                <div style="margin-top: 15px; font-size: 1.1rem; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">{warning_text}</div>
                <div style="margin-top: 10px; font-size: 0.9rem; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">
                    <a href="pages/03_expiry_management.py" style="color: white; text-decoration: underline;">
                        View details in Expiry Management
                    </a>
                </div>
            </div>
            """
            import streamlit.components.v1 as components
            components.html(html_content, height=300)
        else:
            # Gray gradient for no data
            html_content = """
            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #607D8B, #455A64); 
                        color: white; border-radius: 15px; margin: 15px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: bold; margin-bottom: 5px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Product Expiry Status: No Data</div>
                <div style="font-size: 1.5rem; margin-bottom: 15px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">No products with expiry dates found in inventory</div>
            </div>
            """
            import streamlit.components.v1 as components
            components.html(html_content, height=300)
    except Exception as e:
        logger.error(f"Error loading product expiry metrics: {e}")
        st.error("Error loading product expiry data")

    # Create metrics for delivered products
    st.markdown("### Delivery Performance")
    
    # Received Products metrics
    try:
        # Query for delivered products
        received_query = """
            SELECT 
                COUNT(*) as count, 
                SUM(quantity) as total_quantity,
                MAX(received_date) as latest_delivery,
                COUNT(DISTINCT product_code) as unique_products
            FROM 
                received_products 
            WHERE 
                received_date >= CURRENT_DATE - INTERVAL '30 days'
        """
        received_data = load_data(received_query)
        
        # Query for total products
        products_query = "SELECT COUNT(*) as count FROM products"
        products_data = load_data(products_query)
        total_products = products_data['count'].iloc[0] if not products_data.empty else 0
        
        if not received_data.empty and received_data['count'].iloc[0] > 0:
            # Blue gradient for delivery metrics
            bg_gradient = "linear-gradient(135deg, #2196F3, #0D47A1)"
            
            # Calculate days since last delivery
            latest_delivery = received_data['latest_delivery'].iloc[0]
            days_since_delivery = None
            if latest_delivery:
                # Convert both to datetime.date for consistent comparison
                current_date = datetime.now().date()
                if isinstance(latest_delivery, pd.Timestamp):
                    latest_delivery_date = latest_delivery.date()
                else:
                    latest_delivery_date = latest_delivery
                days_since_delivery = (current_date - latest_delivery_date).days
            
            delivery_info = ""
            if days_since_delivery is not None:
                if days_since_delivery == 0:
                    delivery_info = "Last delivery: Today"
                else:
                    delivery_info = f"Last delivery: {days_since_delivery} days ago"
            
            # Calculate percentage of products that received deliveries
            unique_products = received_data['unique_products'].iloc[0]
            product_percentage = (unique_products / total_products * 100) if total_products > 0 else 0
            
            html_content = f"""
            <div style="text-align: center; padding: 25px; background: {bg_gradient}; 
                        color: white; border-radius: 15px; margin: 15px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: bold; margin-bottom: 5px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Delivery Performance</div>
                <div style="font-size: 3rem; font-weight: bold; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">{received_data['count'].iloc[0]:,d}</div>
                
                <div style="display: flex; justify-content: center; gap: 40px; font-size: 1.1rem; margin-top: 20px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">
                    <div>
                        <div style="font-size: 1.8rem; font-weight: bold; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">{received_data['total_quantity'].iloc[0]:,.2f}</div>
                        <div style="font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Total Quantity</div>
                    </div>
                    <div>
                        <div style="font-size: 1.8rem; font-weight: bold; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">{total_products:,d}</div>
                        <div style="font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Total Products</div>
                    </div>
                </div>
                
                <div style="margin-top: 10px; font-size: 0.9rem; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif; padding-bottom: 10px;">
                    <a href="pages/02_products.py" style="color: white; text-decoration: underline; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">View details in Products Management</a>
                </div>
            </div>
            """
            import streamlit.components.v1 as components
            components.html(html_content, height=320)
        else:
            # Gray gradient for no data
            html_content = f"""
            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #607D8B, #455A64); 
                        color: white; border-radius: 15px; margin: 15px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: bold; margin-bottom: 5px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Delivery Performance</div>
                <div style="font-size: 1.5rem; margin-bottom: 15px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">No Deliveries in Last 30 Days</div>
                <div style="font-size: 1.1rem; margin-top: 10px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Total Products in System: {total_products:,d}</div>
                <div style="margin-top: 10px; font-size: 0.9rem; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif; padding-bottom: 10px;">
                    <a href="pages/02_products.py" style="color: white; text-decoration: underline; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">View details in Products Management</a>
                </div>
            </div>
            """
            import streamlit.components.v1 as components
            components.html(html_content, height=320)
    except Exception as e:
        logger.error(f"Error loading received products metrics: {e}")
        st.error("Error loading delivery data")

    # Inventory Status metrics
    st.markdown("### Inventory Status")
    try:
        # Query for inventory metrics
        inventory_query = """
            SELECT 
                COUNT(*) as total_items,
                SUM(i.quantity_remaining) as total_quantity,
                COUNT(CASE WHEN i.quantity_remaining <= 10 THEN 1 END) as low_stock_items
            FROM 
                inventory i
        """
        inventory_data = load_data(inventory_query)
        
        # Query for recent sales (assuming there's a sales table)
        sales_query = """
            SELECT 
                COUNT(*) as sales_count,
                SUM(quantity) as sales_quantity
            FROM 
                inventory_transactions
            WHERE 
                transaction_type = 'OUT' AND
                transaction_date >= CURRENT_DATE - INTERVAL '30 days'
        """
        
        try:
            sales_data = load_data(sales_query)
            has_sales_data = not sales_data.empty and sales_data['sales_count'].iloc[0] > 0
        except:
            # If sales query fails (e.g., table doesn't exist), create empty data
            has_sales_data = False
            sales_data = pd.DataFrame({'sales_count': [0], 'sales_quantity': [0]})
        
        if not inventory_data.empty:
            # Calculate metrics
            total_items = inventory_data['total_items'].iloc[0]
            total_quantity = inventory_data['total_quantity'].iloc[0]
            low_stock_items = inventory_data['low_stock_items'].iloc[0]
            
            # Calculate low stock percentage
            low_stock_percentage = (low_stock_items / total_items * 100) if total_items > 0 else 0
            
            # Determine status color based on low stock percentage
            if low_stock_percentage >= 20:
                bg_gradient = "linear-gradient(135deg, #F44336, #B71C1C)"  # Red for critical
                status_text = "Critical"
            elif low_stock_percentage >= 10:
                bg_gradient = "linear-gradient(135deg, #FF9800, #E65100)"  # Orange for warning
                status_text = "Warning"
            else:
                bg_gradient = "linear-gradient(135deg, #4CAF50, #2E7D32)"  # Green for good
                status_text = "Good"
            
            # Format sales data
            sales_count = sales_data['sales_count'].iloc[0] if has_sales_data else 0
            sales_quantity = sales_data['sales_quantity'].iloc[0] if has_sales_data else 0
            
            # Create HTML content that matches the style of other metrics
            html_content = f"""
            <div style="text-align: center; padding: 25px; background: {bg_gradient}; 
                        color: white; border-radius: 15px; margin: 15px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: bold; margin-bottom: 5px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Inventory Status: {status_text}</div>
                
                <div style="display: flex; justify-content: center; gap: 40px; font-size: 1.1rem; margin-top: 20px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">
                    <div>
                        <div style="font-size: 1.8rem; font-weight: bold; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">{total_quantity:,.2f}</div>
                        <div style="font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Total Stock Quantity</div>
                    </div>
                    <div>
                        <div style="font-size: 1.8rem; font-weight: bold; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">{low_stock_items:,d}</div>
                        <div style="font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Low Stock Items</div>
                    </div>
                </div>
                
                <div style="margin-top: 10px; font-size: 0.9rem; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif; padding-bottom: 10px;">
                    <a href="pages/01_inventory.py" style="color: white; text-decoration: underline; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">View details in Inventory Management</a>
                </div>
            </div>
            """
            import streamlit.components.v1 as components
            components.html(html_content, height=320)
        else:
            # Gray gradient for no data
            html_content = """
            <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #607D8B, #455A64); 
                        color: white; border-radius: 15px; margin: 15px 0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                <div style="font-size: 2rem; font-weight: bold; margin-bottom: 5px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">Inventory Status: No Data</div>
                <div style="font-size: 1.5rem; margin-bottom: 15px; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">No inventory data available</div>
                <div style="margin-top: 10px; font-size: 0.9rem; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif; padding-bottom: 10px;">
                    <a href="pages/01_inventory.py" style="color: white; text-decoration: underline; font-family: 'Poppins', 'Segoe UI', 'Roboto', sans-serif;">View details in Inventory Management</a>
                </div>
            </div>
            """
            import streamlit.components.v1 as components
            components.html(html_content, height=320)
    except Exception as e:
        logger.error(f"Error loading inventory status metrics: {e}")
        st.error("Error loading inventory data")
    
    # Create smaller metrics row for other metrics (if needed for future metrics)
    # st.markdown("### Other Key Metrics")
    # col1, col2 = st.columns(2)

def main():
    """Main function to render the dashboard."""
    try:
        # Create sidebar
        with st.sidebar:
            st.title("SPATRAC")
            st.caption("Product Traceability System")
            
            # Main navigation section
            st.sidebar.header("Main Navigation")
            
            # Dashboard (current page)
            st.sidebar.page_link("app.py", label="📊 Dashboard")
            
            # Other pages
            st.sidebar.page_link("pages/01_inventory.py", label="📦 Inventory Management")
            st.sidebar.page_link("pages/02_products.py", label="🏭 Products Management")
            st.sidebar.page_link("pages/03_expiry_management.py", label="📅 Expiry Management")
            
            # Additional sections can be added here
            st.sidebar.header("Settings")
            st.sidebar.page_link("pages/settings.py", label="⚙️ System Settings")
            
            # Footer
            st.sidebar.markdown("---")
            st.sidebar.caption("© 2025 SPATRAC")
        
        # Check database connection
        db_connected = check_database_connection()
        if not db_connected:
            st.error("❌ Database connection failed. Please check your database configuration.")
            st.stop()
        
        # Check required tables
        tables_exist = check_required_tables()
        if not tables_exist:
            st.warning("⚠️ Some required database tables are missing. The application may not function correctly.")
        
        # Display the dashboard home
        dashboard_home()
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        st.error("Error loading dashboard")

if __name__ == "__main__":
    main()