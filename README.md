# SPATRAC - Supply Chain and Product Traceability System

SPATRAC is a comprehensive inventory and traceability system designed to help businesses track products, manage inventory, analyze sales, and ensure quality control throughout the supply chain.

## Project Overview

This is a rebuilt version of the SPATRAC system, focusing on a solid foundation with the database at its core. The system is designed to be modular, maintainable, and scalable.

## Key Features

- **Inventory Management**: Track current inventory levels, transactions, and expiring products
- **Product Management**: Manage product information, suppliers, and departments
- **Recipe Management**: Define and track recipes and their ingredients
- **Sales Analytics**: Analyze sales data and its impact on inventory
- **Traceability**: Track products from receipt to sale
- **Reporting**: Generate comprehensive reports on inventory, sales, and more
- **Expired Products Management**: Track and manage expired products

## Project Structure

- **components/**: UI components for the Streamlit application
- **data_access/**: Database access layer
- **config/**: Configuration settings
- **utils/**: Utility functions
- **business_logic/**: Business logic layer
- **migrations/**: Database migration scripts
- **scripts/**: Utility scripts
- **docs/**: Documentation
- **assets/**: Static assets
- **logs/**: Log files
- **backups/**: Database backups

## Database Structure

The system uses a PostgreSQL database with the following main tables:
- departments
- expired_products
- ingredients
- inventory
- inventory_transactions
- packaging
- product_report
- products
- quality_check_types
- quality_checks
- received_products
- recipe_ingredients
- recipe_productions
- recipes
- sales
- sales_items
- supplier_departments
- suppliers
- users

## Getting Started

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure the database connection in the `.env` file

3. Run the application:
   ```
   streamlit run dashboard.py
   ```

## Development Roadmap

1. Database Connection Layer
2. Core Data Access Functions
3. Basic UI Components
4. Authentication System
5. Inventory Management
6. Product Management
7. Recipe Management
8. Sales Analytics
9. Reporting System
10. Traceability Features
11. Quality Control
12. Expired Products Management
