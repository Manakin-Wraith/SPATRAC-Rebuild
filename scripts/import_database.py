"""
Import database schema and data from production to test database.
"""
import sys
import os
import subprocess
import logging
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logging_utils import setup_logger

# Set up logger
logger = setup_logger('import_database')

def run_command(command):
    """Run a shell command and return the output."""
    logger.info(f"Running command: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Command completed successfully")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")
        return False, e.stderr

def export_production_schema():
    """Export schema from production database."""
    logger.info("Exporting schema from production database...")
    command = "pg_dump -U postgres -h localhost -d traceability_db --schema-only -f /tmp/spatrac_schema.sql"
    success, output = run_command(command)
    if success:
        logger.info("✅ Schema exported successfully")
        return True
    else:
        logger.error("❌ Failed to export schema")
        return False

def export_production_data():
    """Export data from production database."""
    logger.info("Exporting data from production database...")
    command = "pg_dump -U postgres -h localhost -d traceability_db --data-only -f /tmp/spatrac_data.sql"
    success, output = run_command(command)
    if success:
        logger.info("✅ Data exported successfully")
        return True
    else:
        logger.error("❌ Failed to export data")
        return False

def import_schema_to_test():
    """Import schema to test database."""
    logger.info("Importing schema to test database...")
    command = "psql -U postgres -h localhost -d spatrac_test_db -f /tmp/spatrac_schema.sql"
    success, output = run_command(command)
    if success:
        logger.info("✅ Schema imported successfully")
        return True
    else:
        logger.error("❌ Failed to import schema")
        return False

def import_data_to_test():
    """Import data to test database."""
    logger.info("Importing data to test database...")
    command = "psql -U postgres -h localhost -d spatrac_test_db -f /tmp/spatrac_data.sql"
    success, output = run_command(command)
    if success:
        logger.info("✅ Data imported successfully")
        return True
    else:
        logger.error("❌ Failed to import data")
        return False

def main():
    """Run the database import process."""
    logger.info("Starting database import process...")
    
    # Export schema and data from production
    schema_exported = export_production_schema()
    if not schema_exported:
        logger.error("❌ Schema export failed. Stopping import process.")
        return False
    
    data_exported = export_production_data()
    if not data_exported:
        logger.error("❌ Data export failed. Stopping import process.")
        return False
    
    # Import schema and data to test database
    schema_imported = import_schema_to_test()
    if not schema_imported:
        logger.error("❌ Schema import failed. Stopping import process.")
        return False
    
    data_imported = import_data_to_test()
    if not data_imported:
        logger.error("❌ Data import failed.")
        return False
    
    # Clean up temporary files
    logger.info("Cleaning up temporary files...")
    os.remove("/tmp/spatrac_schema.sql")
    os.remove("/tmp/spatrac_data.sql")
    
    logger.info("✅ Database import process completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    print(f"Database import {'completed successfully' if success else 'failed'}. See log for details.")
    sys.exit(0 if success else 1)
