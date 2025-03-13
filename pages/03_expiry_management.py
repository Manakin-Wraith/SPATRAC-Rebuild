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
st.title("Expiry Management")

# Initialize session state for filters
if 'expiry_days_filter' not in st.session_state:
    st.session_state.expiry_days_filter = 90  # Default to 90 days

def expiry_management():
    """Main function for the Expiry Management page."""
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Filter for expiry days
    expiry_days = st.sidebar.slider(
        "Show products expiring within (days):",
        min_value=7,
        max_value=365,
        value=st.session_state.expiry_days_filter,
        step=7
    )
    st.session_state.expiry_days_filter = expiry_days
    
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
    
    # Calculate the expiry date threshold
    expiry_threshold = datetime.now().date() + timedelta(days=expiry_days)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Products Expiring Soon")
        try:
            # Query for expiring products
            expiry_query = f"""
                SELECT 
                    p.product_code,
                    p.product_name,
                    p.department,
                    i.batch_number,
                    i.expiry_date,
                    i.quantity,
                    p.unit_of_measure,
                    EXTRACT(DAY FROM (i.expiry_date - CURRENT_DATE)) as days_until_expiry
                FROM 
                    inventory i
                JOIN 
                    products p ON i.product_code = p.product_code
                WHERE 
                    i.expiry_date <= %s
                    {department_filter}
                ORDER BY 
                    i.expiry_date ASC
            """
            
            query_params = [expiry_threshold]
            if department_filter and "All" not in selected_departments:
                query_params.extend(selected_departments)
                
            expiring_products = load_data(expiry_query, query_params)
            
            if not expiring_products.empty:
                # Add status column
                def get_status(days):
                    if days < 0:
                        return "Expired"
                    elif days <= 30:
                        return "Critical"
                    elif days <= 60:
                        return "Warning"
                    else:
                        return "OK"
                
                expiring_products['status'] = expiring_products['days_until_expiry'].apply(get_status)
                
                # Add styling
                def highlight_status(row):
                    if row['status'] == 'Expired':
                        return ['background-color: #FFCDD2'] * len(row)
                    elif row['status'] == 'Critical':
                        return ['background-color: #FFECB3'] * len(row)
                    elif row['status'] == 'Warning':
                        return ['background-color: #E8F5E9'] * len(row)
                    else:
                        return [''] * len(row)
                
                # Format the date column
                expiring_products['expiry_date'] = pd.to_datetime(expiring_products['expiry_date']).dt.strftime('%Y-%m-%d')
                
                # Display the table with styling
                st.dataframe(
                    expiring_products.style.apply(highlight_status, axis=1),
                    use_container_width=True,
                    height=400
                )
                
                # Add action buttons for batch operations
                st.subheader("Batch Actions")
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    if st.button("Mark Selected as Disposed", type="primary"):
                        st.info("This would mark selected items as disposed (functionality to be implemented)")
                
                with col_b:
                    if st.button("Generate Disposal Report"):
                        st.info("This would generate a disposal report (functionality to be implemented)")
                
                with col_c:
                    if st.button("Export to CSV"):
                        st.info("This would export the data to CSV (functionality to be implemented)")
                
            else:
                st.info(f"No products expiring within {expiry_days} days")
        except Exception as e:
            logger.error(f"Error loading expiring products: {e}")
            st.error(f"Error loading expiring products: {e}")
    
    with col2:
        st.header("Expiry Summary")
        try:
            # Summary metrics
            summary_query = f"""
                SELECT 
                    COUNT(*) as total_expiring,
                    COUNT(CASE WHEN expiry_date <= CURRENT_DATE THEN 1 END) as expired,
                    COUNT(CASE WHEN expiry_date > CURRENT_DATE AND expiry_date <= CURRENT_DATE + INTERVAL '30 days' THEN 1 END) as critical,
                    COUNT(CASE WHEN expiry_date > CURRENT_DATE + INTERVAL '30 days' AND expiry_date <= CURRENT_DATE + INTERVAL '60 days' THEN 1 END) as warning,
                    COUNT(CASE WHEN expiry_date > CURRENT_DATE + INTERVAL '60 days' AND expiry_date <= %s THEN 1 END) as ok
                FROM 
                    inventory
                WHERE 
                    expiry_date <= %s
            """
            
            summary_data = load_data(summary_query, [expiry_threshold, expiry_threshold])
            
            if not summary_data.empty:
                # Display metrics
                col_x, col_y = st.columns(2)
                with col_x:
                    st.metric("Total Expiring", summary_data['total_expiring'].iloc[0])
                with col_y:
                    st.metric("Already Expired", summary_data['expired'].iloc[0], 
                             delta=-summary_data['expired'].iloc[0], delta_color="inverse")
                
                col_x, col_y = st.columns(2)
                with col_x:
                    st.metric("Critical (30 days)", summary_data['critical'].iloc[0], 
                             delta=-summary_data['critical'].iloc[0], delta_color="inverse")
                with col_y:
                    st.metric("Warning (60 days)", summary_data['warning'].iloc[0], 
                             delta=-summary_data['warning'].iloc[0], delta_color="inverse")
                
                # Create data for pie chart
                labels = ['Expired', 'Critical (30 days)', 'Warning (60 days)', 'OK (>60 days)']
                values = [
                    summary_data['expired'].iloc[0],
                    summary_data['critical'].iloc[0],
                    summary_data['warning'].iloc[0],
                    summary_data['ok'].iloc[0]
                ]
                colors = ['#F44336', '#FF9800', '#FFEB3B', '#4CAF50']
                
                # Create pie chart
                fig = px.pie(
                    names=labels,
                    values=values,
                    color_discrete_sequence=colors,
                    title="Expiry Status Distribution"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
                # Add expiry timeline chart
                st.subheader("Expiry Timeline")
                timeline_query = f"""
                    SELECT 
                        DATE_TRUNC('month', expiry_date) as month,
                        COUNT(*) as count
                    FROM 
                        inventory
                    WHERE 
                        expiry_date <= %s
                    GROUP BY 
                        DATE_TRUNC('month', expiry_date)
                    ORDER BY 
                        month
                """
                
                timeline_data = load_data(timeline_query, [expiry_threshold])
                
                if not timeline_data.empty:
                    timeline_data['month'] = pd.to_datetime(timeline_data['month']).dt.strftime('%Y-%m')
                    fig = px.bar(
                        timeline_data,
                        x='month',
                        y='count',
                        title="Products Expiring by Month",
                        color_discrete_sequence=['#2196F3']
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"No products expiring within {expiry_days} days")
        except Exception as e:
            logger.error(f"Error loading expiry summary: {e}")
            st.error(f"Error loading expiry summary: {e}")

    # Add section for expiry management settings
    st.header("Expiry Management Settings")
    with st.expander("Configure Notification Settings"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.number_input("Critical threshold (days)", min_value=1, max_value=90, value=30)
            st.number_input("Warning threshold (days)", min_value=30, max_value=180, value=60)
        with col_b:
            st.checkbox("Enable email notifications", value=True)
            st.multiselect("Notify departments", options=["All"] + (all_departments if 'all_departments' in locals() else []), default="All")
        
        if st.button("Save Settings"):
            st.success("Settings saved successfully (functionality to be implemented)")

if __name__ == "__main__":
    expiry_management()
