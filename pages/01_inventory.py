import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import sys
import os
import logging

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_access.database import load_data, execute_query

# Configure logging
logger = logging.getLogger(__name__)

# Page title
st.title("Inventory Management")

def inventory_management():
    """Main function for the Inventory Management page."""
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Department filter
    try:
        dept_query = "SELECT DISTINCT department FROM products ORDER BY department"
        departments = load_data(dept_query)
        if not departments.empty:
            all_departments = departments['department'].tolist()
            selected_departments = st.sidebar.multiselect(
                "Filter by Department:",
                options=["All"] + all_departments,
                default="All"
            )
            
            if "All" in selected_departments or not selected_departments:
                department_filter = ""
            else:
                department_filter = f"AND p.department IN ({', '.join(['%s' for _ in selected_departments])})"
                
        else:
            department_filter = ""
            selected_departments = []
    except Exception as e:
        logger.error(f"Error loading departments: {e}")
        department_filter = ""
        selected_departments = []
        st.sidebar.error("Error loading departments")
    
    # Date range filter for transactions
    st.sidebar.subheader("Transaction Date Range")
    start_date = st.sidebar.date_input(
        "Start Date",
        datetime.now().date() - timedelta(days=30)
    )
    end_date = st.sidebar.date_input(
        "End Date",
        datetime.now().date()
    )
    
    # Transaction type filter
    transaction_types = ["All", "IN", "OUT", "ADJUSTMENT"]
    selected_transaction_type = st.sidebar.selectbox(
        "Transaction Type:",
        options=transaction_types,
        index=0
    )
    
    if selected_transaction_type == "All":
        transaction_type_filter = ""
    else:
        transaction_type_filter = f"AND transaction_type = %s"
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["Current Inventory", "Inventory Transactions", "Analytics"])
    
    # Tab 1: Current Inventory
    with tab1:
        st.header("Current Inventory")
        
        # Search box
        search_term = st.text_input("Search by Product Code or Name:")
        
        # Query for current inventory
        try:
            inventory_query = f"""
                SELECT 
                    i.product_code,
                    p.product_name,
                    p.department,
                    i.batch_number,
                    i.quantity_remaining as quantity,
                    p.unit_of_measure,
                    i.expiry_date,
                    EXTRACT(DAY FROM (i.expiry_date - CURRENT_DATE)) as days_until_expiry
                FROM 
                    inventory i
                JOIN 
                    products p ON i.product_code = p.product_code
                WHERE 
                    (i.product_code ILIKE %s OR p.product_name ILIKE %s)
                    {department_filter}
                ORDER BY 
                    p.department, p.product_name
            """
            
            search_param = f"%{search_term}%" if search_term else "%%"
            query_params = [search_param, search_param]
            
            if department_filter and "All" not in selected_departments:
                query_params.extend(selected_departments)
                
            inventory_data = load_data(inventory_query, query_params)
            
            if not inventory_data.empty:
                # Add status column based on days until expiry
                def get_expiry_status(days):
                    if days < 0:
                        return "Expired"
                    elif days <= 30:
                        return "Critical"
                    elif days <= 90:
                        return "Warning"
                    else:
                        return "OK"
                
                inventory_data['expiry_status'] = inventory_data['days_until_expiry'].apply(get_expiry_status)
                
                # Format the date column
                inventory_data['expiry_date'] = pd.to_datetime(inventory_data['expiry_date']).dt.strftime('%Y-%m-%d')
                
                # Display the table
                st.dataframe(inventory_data, use_container_width=True)
                
                # Add action buttons
                st.subheader("Actions")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Add Inventory", type="primary"):
                        st.info("This would open an add inventory form (functionality to be implemented)")
                
                with col2:
                    if st.button("Record Transaction"):
                        st.info("This would open a transaction form (functionality to be implemented)")
                
                with col3:
                    if st.button("Export to CSV"):
                        st.info("This would export the data to CSV (functionality to be implemented)")
            else:
                st.info("No inventory items found matching your criteria")
        except Exception as e:
            logger.error(f"Error loading inventory data: {e}")
            st.error(f"Error loading inventory data: {e}")
    
    # Tab 2: Inventory Transactions
    with tab2:
        st.header("Inventory Transactions")
        
        # Query for inventory transactions
        try:
            transactions_query = f"""
                SELECT 
                    t.transaction_id,
                    t.transaction_date,
                    t.product_code,
                    p.product_name,
                    t.transaction_type,
                    t.quantity,
                    p.unit_of_measure,
                    t.batch_number,
                    t.notes
                FROM 
                    inventory_transactions t
                JOIN 
                    products p ON t.product_code = p.product_code
                WHERE 
                    t.transaction_date BETWEEN %s AND %s
                    {transaction_type_filter}
                    {department_filter}
                ORDER BY 
                    t.transaction_date DESC
            """
            
            query_params = [start_date, end_date]
            
            if transaction_type_filter:
                query_params.append(selected_transaction_type)
                
            if department_filter and "All" not in selected_departments:
                query_params.extend(selected_departments)
                
            transactions_data = load_data(transactions_query, query_params)
            
            if not transactions_data.empty:
                # Format the date column
                transactions_data['transaction_date'] = pd.to_datetime(transactions_data['transaction_date']).dt.strftime('%Y-%m-%d %H:%M')
                
                # Display the table
                st.dataframe(transactions_data, use_container_width=True)
                
                # Add action buttons
                st.subheader("Actions")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("New Transaction", type="primary"):
                        st.info("This would open a new transaction form (functionality to be implemented)")
                
                with col2:
                    if st.button("Generate Transaction Report"):
                        st.info("This would generate a transaction report (functionality to be implemented)")
            else:
                st.info("No transactions found matching your criteria")
        except Exception as e:
            logger.error(f"Error loading transaction data: {e}")
            st.error(f"Error loading transaction data: {e}")
    
    # Tab 3: Analytics
    with tab3:
        st.header("Inventory Analytics")
        
        col1, col2 = st.columns(2)
        
        # Chart 1: Inventory by Department
        with col1:
            try:
                dept_inventory_query = """
                    SELECT 
                        p.department,
                        SUM(i.quantity) as total_quantity
                    FROM 
                        inventory i
                    JOIN 
                        products p ON i.product_code = p.product_code
                    GROUP BY 
                        p.department
                    ORDER BY 
                        total_quantity DESC
                """
                
                dept_inventory_data = load_data(dept_inventory_query)
                
                if not dept_inventory_data.empty:
                    fig = px.bar(
                        dept_inventory_data,
                        x='department',
                        y='total_quantity',
                        title="Inventory by Department",
                        color='department',
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for department inventory chart")
            except Exception as e:
                logger.error(f"Error loading department inventory data: {e}")
                st.error("Error loading department inventory chart")
        
        # Chart 2: Expiry Timeline
        with col2:
            try:
                expiry_query = """
                    SELECT 
                        DATE_TRUNC('month', expiry_date) as month,
                        COUNT(*) as count
                    FROM 
                        inventory
                    WHERE 
                        expiry_date <= CURRENT_DATE + INTERVAL '180 days'
                    GROUP BY 
                        DATE_TRUNC('month', expiry_date)
                    ORDER BY 
                        month
                """
                
                expiry_data = load_data(expiry_query)
                
                if not expiry_data.empty:
                    expiry_data['month'] = pd.to_datetime(expiry_data['month']).dt.strftime('%Y-%m')
                    fig = px.line(
                        expiry_data,
                        x='month',
                        y='count',
                        title="Products Expiring by Month (Next 6 Months)",
                        markers=True,
                        color_discrete_sequence=['#FF9800']
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for expiry timeline chart")
            except Exception as e:
                logger.error(f"Error loading expiry timeline data: {e}")
                st.error("Error loading expiry timeline chart")
        
        # Chart 3: Transaction History
        st.subheader("Transaction History")
        try:
            transaction_history_query = """
                SELECT 
                    DATE_TRUNC('day', transaction_date) as date,
                    transaction_type,
                    COUNT(*) as count
                FROM 
                    inventory_transactions
                WHERE 
                    transaction_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY 
                    DATE_TRUNC('day', transaction_date), transaction_type
                ORDER BY 
                    date
            """
            
            transaction_history_data = load_data(transaction_history_query)
            
            if not transaction_history_data.empty:
                transaction_history_data['date'] = pd.to_datetime(transaction_history_data['date']).dt.strftime('%Y-%m-%d')
                fig = px.line(
                    transaction_history_data,
                    x='date',
                    y='count',
                    color='transaction_type',
                    title="Transaction History (Last 30 Days)",
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for transaction history chart")
        except Exception as e:
            logger.error(f"Error loading transaction history data: {e}")
            st.error("Error loading transaction history chart")

if __name__ == "__main__":
    inventory_management()
