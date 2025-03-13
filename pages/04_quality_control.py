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
st.title("Quality Control")

def quality_control():
    """Main function for the Quality Control page."""
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range filter
    st.sidebar.subheader("Date Range")
    start_date = st.sidebar.date_input(
        "Start Date",
        datetime.now().date() - timedelta(days=30)
    )
    end_date = st.sidebar.date_input(
        "End Date",
        datetime.now().date()
    )
    
    # Status filter
    status_options = ["All", "PASSED", "FAILED", "PENDING", "N/A"]
    selected_status = st.sidebar.selectbox(
        "Quality Check Status:",
        options=status_options,
        index=0
    )
    
    if selected_status == "All":
        status_filter = ""
    else:
        status_filter = f"AND qc.status = %s"
    
    # Department filter
    try:
        dept_query = "SELECT DISTINCT department FROM quality_check_types WHERE department IS NOT NULL ORDER BY department"
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
                department_filter = f"AND qct.department IN ({', '.join(['%s' for _ in selected_departments])})"
                
        else:
            department_filter = ""
            selected_departments = []
    except Exception as e:
        logger.error(f"Error loading departments: {e}")
        department_filter = ""
        selected_departments = []
        st.sidebar.error("Error loading departments")
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["Quality Checks", "Check Types", "Analytics"])
    
    # Tab 1: Quality Checks
    with tab1:
        st.header("Quality Checks")
        
        # Search box
        search_term = st.text_input("Search by Tracking ID or Product:")
        
        # Query for quality checks
        try:
            quality_checks_query = f"""
                SELECT 
                    qc.check_id,
                    qct.check_name,
                    qc.tracking_id,
                    rp.product_code,
                    p.product_name,
                    qc.status,
                    qc.notes,
                    qc.checked_by,
                    qc.checked_at,
                    qct.department
                FROM 
                    quality_checks qc
                JOIN 
                    quality_check_types qct ON qc.check_id = qct.check_id
                JOIN 
                    received_products rp ON qc.tracking_id = rp.tracking_id
                JOIN 
                    products p ON rp.product_code = p.product_code
                WHERE 
                    qc.checked_at BETWEEN %s AND %s
                    AND (qc.tracking_id ILIKE %s OR p.product_name ILIKE %s OR p.product_code ILIKE %s)
                    {status_filter}
                    {department_filter}
                ORDER BY 
                    qc.checked_at DESC
            """
            
            search_param = f"%{search_term}%" if search_term else "%%"
            query_params = [
                start_date, 
                end_date, 
                search_param, 
                search_param,
                search_param
            ]
            
            if status_filter:
                query_params.append(selected_status)
                
            if department_filter and "All" not in selected_departments:
                query_params.extend(selected_departments)
                
            quality_checks_data = load_data(quality_checks_query, query_params)
            
            if not quality_checks_data.empty:
                # Format the date column
                quality_checks_data['checked_at'] = pd.to_datetime(quality_checks_data['checked_at']).dt.strftime('%Y-%m-%d %H:%M')
                
                # Add styling
                def highlight_status(val):
                    if val == 'PASSED':
                        return 'background-color: #C8E6C9; color: #2E7D32'
                    elif val == 'FAILED':
                        return 'background-color: #FFCDD2; color: #C62828'
                    elif val == 'PENDING':
                        return 'background-color: #FFF9C4; color: #F57F17'
                    return ''
                
                # Apply styling to the status column
                styled_df = quality_checks_data.style.applymap(
                    highlight_status, 
                    subset=['status']
                )
                
                # Display the table
                st.dataframe(styled_df, use_container_width=True)
                
                # Add action buttons
                st.subheader("Actions")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("Add Quality Check", type="primary"):
                        st.info("This would open a form to add a new quality check (functionality to be implemented)")
                
                with col2:
                    if st.button("Generate Quality Report"):
                        st.info("This would generate a quality report (functionality to be implemented)")
                
                with col3:
                    if st.button("Export to CSV"):
                        st.info("This would export the data to CSV (functionality to be implemented)")
            else:
                st.info("No quality checks found matching your criteria")
        except Exception as e:
            logger.error(f"Error loading quality checks: {e}")
            st.error(f"Error loading quality checks: {e}")
    
    # Tab 2: Check Types
    with tab2:
        st.header("Quality Check Types")
        
        # Query for check types
        try:
            check_types_query = f"""
                SELECT 
                    check_id,
                    check_name,
                    department,
                    required,
                    created_at
                FROM 
                    quality_check_types
                WHERE 
                    1=1
                    {department_filter}
                ORDER BY 
                    department, check_name
            """
            
            query_params = []
            if department_filter and "All" not in selected_departments:
                query_params.extend(selected_departments)
                
            check_types_data = load_data(check_types_query, query_params)
            
            if not check_types_data.empty:
                # Format the date column
                check_types_data['created_at'] = pd.to_datetime(check_types_data['created_at']).dt.strftime('%Y-%m-%d')
                
                # Display the table
                st.dataframe(check_types_data, use_container_width=True)
                
                # Add action buttons
                st.subheader("Actions")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Add Check Type", type="primary"):
                        st.info("This would open a form to add a new check type (functionality to be implemented)")
                
                with col2:
                    if st.button("Edit Selected Check Type"):
                        st.info("This would open a form to edit the selected check type (functionality to be implemented)")
            else:
                st.info("No check types found matching your criteria")
        except Exception as e:
            logger.error(f"Error loading check types: {e}")
            st.error(f"Error loading check types: {e}")
    
    # Tab 3: Analytics
    with tab3:
        st.header("Quality Control Analytics")
        
        # Quality pass rate over time
        try:
            pass_rate_query = f"""
                SELECT 
                    DATE_TRUNC('day', checked_at) as check_date,
                    COUNT(*) as total_checks,
                    SUM(CASE WHEN status = 'PASSED' THEN 1 ELSE 0 END) as passed_checks
                FROM 
                    quality_checks qc
                JOIN 
                    quality_check_types qct ON qc.check_id = qct.check_id
                WHERE 
                    checked_at BETWEEN %s AND %s
                    {department_filter}
                GROUP BY 
                    DATE_TRUNC('day', checked_at)
                ORDER BY 
                    check_date
            """
            
            query_params = [start_date, end_date]
            if department_filter and "All" not in selected_departments:
                query_params.extend(selected_departments)
                
            pass_rate_data = load_data(pass_rate_query, query_params)
            
            if not pass_rate_data.empty and pass_rate_data['total_checks'].sum() > 0:
                # Calculate pass rate
                pass_rate_data['pass_rate'] = (pass_rate_data['passed_checks'] / pass_rate_data['total_checks']) * 100
                pass_rate_data['check_date'] = pd.to_datetime(pass_rate_data['check_date']).dt.strftime('%Y-%m-%d')
                
                # Create line chart
                fig = px.line(
                    pass_rate_data, 
                    x='check_date', 
                    y='pass_rate',
                    title='Quality Check Pass Rate Over Time',
                    labels={'check_date': 'Date', 'pass_rate': 'Pass Rate (%)'},
                    markers=True
                )
                
                fig.update_layout(
                    xaxis_title='Date',
                    yaxis_title='Pass Rate (%)',
                    yaxis=dict(range=[0, 100])
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Overall metrics
                total_checks = pass_rate_data['total_checks'].sum()
                total_passed = pass_rate_data['passed_checks'].sum()
                overall_pass_rate = (total_passed / total_checks) * 100 if total_checks > 0 else 0
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Checks", f"{total_checks:,d}")
                with col2:
                    st.metric("Passed Checks", f"{total_passed:,d}")
                with col3:
                    st.metric("Overall Pass Rate", f"{overall_pass_rate:.1f}%")
                
                # Quality issues by department
                dept_query = f"""
                    SELECT 
                        qct.department,
                        COUNT(*) as total_checks,
                        SUM(CASE WHEN qc.status = 'PASSED' THEN 1 ELSE 0 END) as passed_checks,
                        SUM(CASE WHEN qc.status = 'FAILED' THEN 1 ELSE 0 END) as failed_checks
                    FROM 
                        quality_checks qc
                    JOIN 
                        quality_check_types qct ON qc.check_id = qct.check_id
                    WHERE 
                        qc.checked_at BETWEEN %s AND %s
                        {department_filter}
                    GROUP BY 
                        qct.department
                    ORDER BY 
                        failed_checks DESC
                """
                
                dept_data = load_data(dept_query, query_params)
                
                if not dept_data.empty:
                    # Calculate failure rate
                    dept_data['failure_rate'] = (dept_data['failed_checks'] / dept_data['total_checks']) * 100
                    
                    # Create bar chart
                    fig2 = px.bar(
                        dept_data,
                        x='department',
                        y='failure_rate',
                        title='Quality Check Failure Rate by Department',
                        labels={'department': 'Department', 'failure_rate': 'Failure Rate (%)'},
                        color='failure_rate',
                        color_continuous_scale='Reds'
                    )
                    
                    fig2.update_layout(
                        xaxis_title='Department',
                        yaxis_title='Failure Rate (%)',
                        yaxis=dict(range=[0, 100])
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No quality check data available for the selected period")
        except Exception as e:
            logger.error(f"Error loading quality analytics: {e}")
            st.error(f"Error loading quality analytics: {e}")

if __name__ == "__main__":
    quality_control()
