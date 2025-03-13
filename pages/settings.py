import streamlit as st
import sys
import os
import logging
import pandas as pd

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_access.database import load_data, execute_query

# Configure logging
logger = logging.getLogger(__name__)

# Page title
st.title("System Settings")

def system_settings():
    """Main function for the System Settings page."""
    
    # Create tabs for different settings categories
    tab1, tab2, tab3, tab4 = st.tabs(["General Settings", "Notification Settings", "User Management", "System Info"])
    
    # Tab 1: General Settings
    with tab1:
        st.header("General Settings")
        
        # Company Information
        st.subheader("Company Information")
        with st.form("company_info_form"):
            col1, col2 = st.columns(2)
            with col1:
                company_name = st.text_input("Company Name", value="SPATRAC Inc.")
                company_email = st.text_input("Company Email", value="info@spatrac.com")
            with col2:
                company_phone = st.text_input("Company Phone", value="+1 (555) 123-4567")
                company_address = st.text_area("Company Address", value="123 Main St, San Francisco, CA 94105")
            
            submitted = st.form_submit_button("Save Company Information")
            if submitted:
                st.success("Company information saved successfully! (Functionality to be implemented)")
        
        # Application Settings
        st.subheader("Application Settings")
        with st.form("app_settings_form"):
            col1, col2 = st.columns(2)
            with col1:
                default_warning_days = st.number_input("Default Expiry Warning Days", min_value=1, max_value=365, value=90)
                critical_threshold = st.number_input("Critical Expiry Threshold (days)", min_value=1, max_value=90, value=30)
            with col2:
                low_stock_threshold = st.number_input("Low Stock Threshold", min_value=1, max_value=100, value=10)
                default_view = st.selectbox("Default Dashboard View", options=["Summary", "Detailed"])
            
            submitted = st.form_submit_button("Save Application Settings")
            if submitted:
                st.success("Application settings saved successfully! (Functionality to be implemented)")
    
    # Tab 2: Notification Settings
    with tab2:
        st.header("Notification Settings")
        
        # Email Notifications
        st.subheader("Email Notifications")
        with st.form("email_settings_form"):
            enable_email = st.checkbox("Enable Email Notifications", value=True)
            
            if enable_email:
                col1, col2 = st.columns(2)
                with col1:
                    smtp_server = st.text_input("SMTP Server", value="smtp.example.com")
                    smtp_port = st.number_input("SMTP Port", min_value=1, max_value=65535, value=587)
                with col2:
                    smtp_username = st.text_input("SMTP Username", value="notifications@spatrac.com")
                    smtp_password = st.text_input("SMTP Password", type="password", value="password")
            
            st.subheader("Notification Events")
            col1, col2 = st.columns(2)
            with col1:
                notify_expiry = st.checkbox("Product Expiry Warnings", value=True)
                notify_low_stock = st.checkbox("Low Stock Alerts", value=True)
            with col2:
                notify_deliveries = st.checkbox("New Deliveries", value=True)
                notify_quality_issues = st.checkbox("Quality Control Issues", value=True)
            
            submitted = st.form_submit_button("Save Notification Settings")
            if submitted:
                st.success("Notification settings saved successfully! (Functionality to be implemented)")
    
    # Tab 3: User Management
    with tab3:
        st.header("User Management")
        
        # User List
        st.subheader("System Users")
        
        # Placeholder for user list
        user_data = {
            "username": ["admin", "manager", "inventory", "quality"],
            "full_name": ["Admin User", "Department Manager", "Inventory Clerk", "Quality Control"],
            "role": ["Administrator", "Manager", "Staff", "Staff"],
            "last_login": ["2025-03-13 08:15", "2025-03-12 17:30", "2025-03-13 07:45", "2025-03-11 16:20"]
        }
        users_df = pd.DataFrame(user_data)
        st.dataframe(users_df, use_container_width=True)
        
        # Add/Edit User Form
        st.subheader("Add/Edit User")
        with st.form("user_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username")
                full_name = st.text_input("Full Name")
            with col2:
                role = st.selectbox("Role", options=["Administrator", "Manager", "Staff"])
                password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Save User")
            if submitted:
                st.success("User saved successfully! (Functionality to be implemented)")
    
    # Tab 4: System Info
    with tab4:
        st.header("System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Application Information")
            st.info("""
            **SPATRAC Product Traceability System**
            Version: 1.0.0
            Build Date: March 2025
            """)
            
            st.subheader("Database Status")
            try:
                # Check database connection
                db_query = "SELECT version();"
                db_version = load_data(db_query)
                if not db_version.empty:
                    st.success("Database Connection: Active")
                    st.code(f"Database Version: {db_version.iloc[0, 0]}")
                else:
                    st.error("Database Connection: Inactive")
            except Exception as e:
                logger.error(f"Error checking database status: {e}")
                st.error(f"Database Connection Error: {e}")
        
        with col2:
            st.subheader("System Statistics")
            try:
                # Get some system statistics
                stats_queries = {
                    "Total Products": "SELECT COUNT(*) FROM products",
                    "Total Inventory Items": "SELECT COUNT(*) FROM inventory",
                    "Transactions (30 days)": "SELECT COUNT(*) FROM inventory_transactions WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'",
                    "Expiring Products (90 days)": "SELECT COUNT(*) FROM inventory WHERE expiry_date <= CURRENT_DATE + INTERVAL '90 days'"
                }
                
                for label, query in stats_queries.items():
                    try:
                        result = load_data(query)
                        if not result.empty:
                            st.metric(label, result.iloc[0, 0])
                        else:
                            st.metric(label, "N/A")
                    except:
                        st.metric(label, "Error")
            except Exception as e:
                logger.error(f"Error loading system statistics: {e}")
                st.error("Error loading system statistics")
            
            st.subheader("Maintenance")
            if st.button("Backup Database"):
                st.info("Database backup initiated! (Functionality to be implemented)")
            
            if st.button("Clear Cache"):
                st.cache_data.clear()
                st.success("Cache cleared successfully!")

if __name__ == "__main__":
    system_settings()
