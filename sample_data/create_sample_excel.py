#!/usr/bin/env python3
"""
Create a sample Excel file for testing the CBM Analytics application.
This script generates realistic test data with the expected column structure.
"""

import pandas as pd
from datetime import datetime, timedelta
import random
import numpy as np

def create_sample_data():
    """Create sample CBM data"""
    
    # Generate date range
    start_date = datetime(2025, 9, 1)
    end_date = datetime(2025, 9, 30)
    
    # Generate sample data
    data = []
    
    for i in range(100):  # 100 sample rows
        # Sales Order data
        so_date = start_date + timedelta(days=random.randint(0, 29))
        so_cbm = round(random.uniform(5.0, 50.0), 6)
        
        # Sales Invoice data (usually 1-3 days after SO)
        si_date = so_date + timedelta(days=random.randint(1, 3))
        si_cbm = round(random.uniform(3.0, 45.0), 6)
        
        # Additional fields
        per_unit_cbm = round(random.uniform(1.0, 5.0), 6)
        so_qty = random.randint(1, 20)
        si_qty = random.randint(1, 15)
        
        # Customer and warehouse (optional grouping fields)
        customers = ['Customer A', 'Customer B', 'Customer C', 'Customer D']
        warehouses = ['Warehouse North', 'Warehouse South', 'Warehouse East']
        
        row = {
            'SO Date': so_date.strftime('%Y-%m-%d'),
            'SO Total CBM': so_cbm,
            'Sales Invoice Date': si_date.strftime('%Y-%m-%d'),
            'SI Total CBM': si_cbm,
            'Per Unit CBM': per_unit_cbm,
            'Sales Order Qty': so_qty,
            'Sales Invoice Qty': si_qty,
            'Customer': random.choice(customers),
            'Warehouse': random.choice(warehouses),
            'Product Code': f'PROD-{i+1:03d}',
            'Description': f'Sample Product {i+1}'
        }
        
        data.append(row)
    
    return pd.DataFrame(data)

def create_test_cases():
    """Create specific test cases for validation"""
    
    # Test case 1: Known totals for 2025-09-15
    test_data = [
        {
            'SO Date': '2025-09-15',
            'SO Total CBM': 22.123456,
            'Sales Invoice Date': '2025-09-16',
            'SI Total CBM': 25.123456,
            'Per Unit CBM': 2.5,
            'Sales Order Qty': 8,
            'Sales Invoice Qty': 10,
            'Customer': 'Test Customer A',
            'Warehouse': 'Test Warehouse',
            'Product Code': 'TEST-001',
            'Description': 'Test Product 1'
        },
        {
            'SO Date': '2025-09-15',
            'SO Total CBM': 33.456789,
            'Sales Invoice Date': '2025-09-17',
            'SI Total CBM': 30.456789,
            'Per Unit CBM': 3.0,
            'Sales Order Qty': 11,
            'Sales Invoice Qty': 10,
            'Customer': 'Test Customer B',
            'Warehouse': 'Test Warehouse',
            'Product Code': 'TEST-002',
            'Description': 'Test Product 2'
        },
        {
            'SO Date': '2025-09-15',
            'SO Total CBM': 10.437627,
            'Sales Invoice Date': '2025-09-18',
            'SI Total CBM': 10.437627,
            'Per Unit CBM': 2.1,
            'Sales Order Qty': 5,
            'Sales Invoice Qty': 5,
            'Customer': 'Test Customer C',
            'Warehouse': 'Test Warehouse',
            'Product Code': 'TEST-003',
            'Description': 'Test Product 3'
        }
    ]
    
    # Expected totals for 2025-09-15:
    # Inbound CBM: 22.123456 + 33.456789 + 10.437627 = 66.017872
    # Inbound Quantity: 8 + 11 + 5 = 24
    # Outbound CBM (SI): 0 (no SI on 2025-09-15)
    # Outbound Quantity (SI): 0 (no SI on 2025-09-15)
    
    return pd.DataFrame(test_data)

def main():
    """Generate sample Excel files"""
    
    print("Creating sample Excel files...")
    
    # Create main sample file
    sample_data = create_sample_data()
    sample_data.to_excel('sample_cbm_data.xlsx', index=False)
    print(f"Created sample_cbm_data.xlsx with {len(sample_data)} rows")
    
    # Create test case file
    test_data = create_test_cases()
    test_data.to_excel('test_cbm_data.xlsx', index=False)
    print(f"Created test_cbm_data.xlsx with {len(test_data)} rows")
    
    # Print expected test results
    print("\nExpected test results for test_cbm_data.xlsx:")
    print("Date: 2025-09-15")
    print(f"Total Inbound CBM: {test_data['SO Total CBM'].sum():.6f}")
    print(f"Total Inbound Quantity: {test_data['Sales Order Qty'].sum()}")
    print("Total Outbound CBM (SI): 0.000000 (no SI data for this date)")
    print("Total Outbound Quantity (SI): 0 (no SI data for this date)")
    
    print("\nDate range: 2025-09-15 to 2025-09-18")
    print(f"Total Inbound CBM: {test_data['SO Total CBM'].sum():.6f}")
    print(f"Total Inbound Quantity: {test_data['Sales Order Qty'].sum()}")
    print(f"Total Outbound CBM (SI): {test_data['SI Total CBM'].sum():.6f}")
    print(f"Total Outbound Quantity (SI): {test_data['Sales Invoice Qty'].sum()}")
    
    print("\nFiles created successfully!")

if __name__ == "__main__":
    main()