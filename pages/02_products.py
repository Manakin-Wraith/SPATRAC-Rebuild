import streamlit as st
import pandas as pd
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
st.title("Products Management")

def products_management():
    """Main function for the Products Management page."""
    
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
                department_filter = f"AND department IN ({', '.join(['%s' for _ in selected_departments])})"
                
        else:
            department_filter = ""
            selected_departments = []
    except Exception as e:
        logger.error(f"Error loading departments: {e}")
        department_filter = ""
        selected_departments = []
        st.sidebar.error("Error loading departments")
    
    # Supplier filter
    try:
        supplier_query = "SELECT DISTINCT supplier FROM products WHERE supplier IS NOT NULL ORDER BY supplier"
        suppliers = load_data(supplier_query)
        if not suppliers.empty:
            all_suppliers = suppliers['supplier'].tolist()
            selected_suppliers = st.sidebar.multiselect(
                "Filter by Supplier:",
                options=["All"] + all_suppliers,
                default="All"
            )
            
            if "All" in selected_suppliers or not selected_suppliers:
                supplier_filter = ""
            else:
                supplier_filter = f"AND supplier IN ({', '.join(['%s' for _ in selected_suppliers])})"
                
        else:
            supplier_filter = ""
            selected_suppliers = []
    except Exception as e:
        logger.error(f"Error loading suppliers: {e}")
        supplier_filter = ""
        selected_suppliers = []
        st.sidebar.error("Error loading suppliers")
    
    # Status filter (assuming there's a status column)
    status_options = ["All", "Active", "Inactive"]
    selected_status = st.sidebar.selectbox(
        "Status:",
        options=status_options,
        index=0
    )
    
    if selected_status == "All":
        status_filter = ""
    else:
        status_filter = f"AND status = %s"
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["Products List", "Add/Edit Product", "Analytics"])
    
    # Tab 1: Products List
    with tab1:
        st.header("Products List")
        
        # Search box
        search_term = st.text_input("Search by Product Code or Name:")
        
        # Query for products
        try:
            products_query = f"""
                SELECT 
                    product_code,
                    product_name,
                    department,
                    supplier,
                    unit_of_measure,
                    COALESCE(status, 'Active') as status,
                    created_date
                FROM 
                    products
                WHERE 
                    (product_code ILIKE %s OR product_name ILIKE %s)
                    {department_filter}
                    {supplier_filter}
                    {status_filter}
                ORDER BY 
                    department, product_name
            """
            
            search_param = f"%{search_term}%" if search_term else "%%"
            query_params = [search_param, search_param]
            
            if department_filter and "All" not in selected_departments:
                query_params.extend(selected_departments)
                
            if supplier_filter and "All" not in selected_suppliers:
                query_params.extend(selected_suppliers)
                
            if status_filter:
                query_params.append(selected_status)
                
            products_data = load_data(products_query, query_params)
            
            if not products_data.empty:
                # Format the date column
                if 'created_date' in products_data.columns:
                    products_data['created_date'] = pd.to_datetime(products_data['created_date']).dt.strftime('%Y-%m-%d')
                
                # Display the table
                st.dataframe(products_data, use_container_width=True)
                
                # Add action buttons
                st.subheader("Actions")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Add New Product", type="primary"):
                        st.info("This would open an add product form (functionality to be implemented)")
                
                with col2:
                    if st.button("Edit Selected Product"):
                        st.info("This would open an edit product form (functionality to be implemented)")
                
                with col3:
                    if st.button("Export to CSV"):
                        st.info("This would export the data to CSV (functionality to be implemented)")
            else:
                st.info("No products found matching your criteria")
        except Exception as e:
            logger.error(f"Error loading products data: {e}")
            st.error(f"Error loading products data: {e}")
    
    # Tab 2: Add/Edit Product
    with tab2:
        st.header("Add/Edit Product")
        
        # Product form
        with st.form("product_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                product_code = st.text_input("Product Code*")
                product_name = st.text_input("Product Name*")
                department = st.selectbox(
                    "Department*", 
                    options=all_departments if 'all_departments' in locals() and all_departments else [""]
                )
                
            with col2:
                supplier = st.selectbox(
                    "Supplier", 
                    options=[""] + (all_suppliers if 'all_suppliers' in locals() and all_suppliers else [])
                )
                unit_of_measure = st.text_input("Unit of Measure*")
                status = st.selectbox("Status", options=["Active", "Inactive"])
            
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("Save Product")
            if submitted:
                st.success("Product saved successfully! (Functionality to be implemented)")
    
    # Tab 3: Analytics
    with tab3:
        st.header("Product Analytics")
        
        col1, col2 = st.columns(2)
        
        # Chart 1: Products by Department
        with col1:
            try:
                dept_products_query = """
                    SELECT 
                        department,
                        COUNT(*) as count
                    FROM 
                        products
                    GROUP BY 
                        department
                    ORDER BY 
                        count DESC
                """
                
                dept_products_data = load_data(dept_products_query)
                
                if not dept_products_data.empty:
                    fig = px.pie(
                        dept_products_data,
                        names='department',
                        values='count',
                        title="Products by Department",
                        color_discrete_sequence=px.colors.qualitative.Pastel
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for department products chart")
            except Exception as e:
                logger.error(f"Error loading department products data: {e}")
                st.error("Error loading department products chart")
        
        # Chart 2: Products by Status
        with col2:
            try:
                status_query = """
                    SELECT 
                        COALESCE(status, 'Active') as status,
                        COUNT(*) as count
                    FROM 
                        products
                    GROUP BY 
                        status
                    ORDER BY 
                        count DESC
                """
                
                status_data = load_data(status_query)
                
                if not status_data.empty:
                    colors = {'Active': '#4CAF50', 'Inactive': '#F44336'}
                    fig = px.bar(
                        status_data,
                        x='status',
                        y='count',
                        title="Products by Status",
                        color='status',
                        color_discrete_map=colors
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data available for status chart")
            except Exception as e:
                logger.error(f"Error loading status data: {e}")
                st.error("Error loading status chart")
        
        # Chart 3: Recent Deliveries
        st.subheader("Recent Deliveries")
        try:
            deliveries_query = """
                SELECT 
                    DATE_TRUNC('day', received_date) as date,
                    COUNT(*) as delivery_count,
                    SUM(quantity) as total_quantity
                FROM 
                    received_products
                WHERE 
                    received_date >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY 
                    DATE_TRUNC('day', received_date)
                ORDER BY 
                    date
            """
            
            deliveries_data = load_data(deliveries_query)
            
            if not deliveries_data.empty:
                deliveries_data['date'] = pd.to_datetime(deliveries_data['date']).dt.strftime('%Y-%m-%d')
                fig = px.bar(
                    deliveries_data,
                    x='date',
                    y='total_quantity',
                    title="Product Deliveries (Last 30 Days)",
                    labels={'total_quantity': 'Total Quantity', 'date': 'Date'},
                    color_discrete_sequence=['#2196F3']
                )
                fig.add_scatter(
                    x=deliveries_data['date'], 
                    y=deliveries_data['delivery_count'],
                    mode='lines+markers',
                    name='Delivery Count',
                    yaxis='y2'
                )
                fig.update_layout(
                    yaxis2=dict(
                        title='Delivery Count',
                        overlaying='y',
                        side='right'
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for deliveries chart")
        except Exception as e:
            logger.error(f"Error loading deliveries data: {e}")
            st.error("Error loading deliveries chart")

if __name__ == "__main__":
    products_management()
