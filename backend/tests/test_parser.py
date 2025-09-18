import pytest
import pandas as pd
import io
from datetime import datetime
from parser import ExcelParser

class TestExcelParser:
    
    def setup_method(self):
        self.parser = ExcelParser()
    
    def test_normalize_column_name(self):
        """Test column name normalization"""
        assert self.parser.normalize_column_name("SO Date") == "sodate"
        assert self.parser.normalize_column_name("Sales Order Total CBM") == "salesordertotalcbm"
        assert self.parser.normalize_column_name("SI_Total_CBM") == "sitotalcbm"
        assert self.parser.normalize_column_name("") == ""
        assert self.parser.normalize_column_name(None) == ""
    
    def test_find_column_match_exact(self):
        """Test exact column matching"""
        columns = ["SO Date", "SO Total CBM", "SI Date", "SI Total CBM"]
        
        match = self.parser.find_column_match(columns, ["so date"])
        assert match == "SO Date"
        
        match = self.parser.find_column_match(columns, ["so total cbm"])
        assert match == "SO Total CBM"
    
    def test_find_column_match_fuzzy(self):
        """Test fuzzy column matching"""
        columns = ["Sales Order Date", "Sales Order Total CBM", "Sales Invoice Date", "Sales Invoice Total CBM"]
        
        match = self.parser.find_column_match(columns, ["so date"])
        assert match == "Sales Order Date"
        
        match = self.parser.find_column_match(columns, ["si total cbm"])
        assert match == "Sales Invoice Total CBM"
    
    def test_find_column_match_no_match(self):
        """Test when no column matches"""
        columns = ["Random Column", "Another Column"]
        
        match = self.parser.find_column_match(columns, ["so date"])
        assert match is None
    
    def test_parse_dates_standard_format(self):
        """Test parsing standard date formats"""
        df = pd.DataFrame({
            'date_col': ['2023-01-15', '2023-02-20', '2023-03-25']
        })
        
        dates = self.parser.parse_dates(df, 'date_col')
        assert not dates.isna().any()
        assert dates[0] == pd.Timestamp('2023-01-15')
    
    def test_parse_dates_excel_serial(self):
        """Test parsing Excel serial dates"""
        df = pd.DataFrame({
            'date_col': [44927, 44958, 44986]  # Excel serial dates for 2023 dates
        })
        
        dates = self.parser.parse_dates(df, 'date_col')
        assert not dates.isna().any()
    
    def test_parse_dates_mixed_formats(self):
        """Test parsing mixed date formats"""
        df = pd.DataFrame({
            'date_col': ['2023-01-15', '20/02/2023', '25-Mar-2023']
        })
        
        dates = self.parser.parse_dates(df, 'date_col')
        # Should parse at least some dates successfully
        assert dates.notna().sum() >= 1
    
    def create_test_excel_data(self):
        """Create test Excel data"""
        data = {
            'SO Date': ['2023-01-15', '2023-01-16', '2023-01-17'],
            'SO Total CBM': [10.5, 15.2, 8.7],
            'Sales Invoice Date': ['2023-01-16', '2023-01-17', '2023-01-18'],
            'SI Total CBM': [12.3, 9.8, 11.1],
            'Per Unit CBM': [2.1, 3.8, 2.9],
            'Sales Order Qty': [5, 4, 3],
            'Sales Invoice Qty': [6, 2, 4]
        }
        
        df = pd.DataFrame(data)
        
        # Convert to Excel bytes
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        return buffer.getvalue()
    
    def test_parse_excel_success(self):
        """Test successful Excel parsing"""
        excel_data = self.create_test_excel_data()
        
        result = self.parser.parse_excel(excel_data)
        
        assert result['columns']['so_date'] == 'SO Date'
        assert result['columns']['so_total_cbm'] == 'SO Total CBM'
        assert result['columns']['si_date'] == 'Sales Invoice Date'
        assert result['columns']['si_total_cbm'] == 'SI Total CBM'
        
        assert result['date_range']['min_date'] is not None
        assert result['date_range']['max_date'] is not None
        
        assert len(result['sample_rows']) > 0
        assert isinstance(result['data'], pd.DataFrame)
    
    def test_parse_excel_missing_so_date(self):
        """Test Excel parsing with missing SO Date column"""
        data = {
            'Random Column': [1, 2, 3],
            'SO Total CBM': [10.5, 15.2, 8.7]
        }
        
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        
        with pytest.raises(ValueError, match="SO Date column not found"):
            self.parser.parse_excel(buffer.getvalue())
    
    def test_parse_excel_missing_si_date(self):
        """Test Excel parsing with missing SI Date column"""
        data = {
            'SO Date': ['2023-01-15', '2023-01-16'],
            'SO Total CBM': [10.5, 15.2],
            'Random Column': [1, 2]
        }
        
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        
        with pytest.raises(ValueError, match="Sales Invoice Date column not found"):
            self.parser.parse_excel(buffer.getvalue())
    
    def test_parse_excel_computed_cbm(self):
        """Test Excel parsing with computed CBM from per unit * quantity"""
        data = {
            'SO Date': ['2023-01-15', '2023-01-16'],
            'Per Unit CBM': [2.5, 3.0],
            'Sales Order Qty': [4, 5],
            'Sales Invoice Date': ['2023-01-16', '2023-01-17'],
            'Sales Invoice Qty': [3, 4]
        }
        
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        
        result = self.parser.parse_excel(buffer.getvalue())
        
        # Should compute CBM from per unit * quantity
        assert 'so_cbm_computed' in result['columns']
        
        # Check computed values
        data_df = result['data']
        assert data_df['so_cbm_value'].iloc[0] == 10.0  # 2.5 * 4
        assert data_df['so_cbm_value'].iloc[1] == 15.0  # 3.0 * 5
    
    def test_parse_excel_empty_file(self):
        """Test parsing empty Excel file"""
        df = pd.DataFrame()
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        
        with pytest.raises(ValueError, match="Excel file is empty"):
            self.parser.parse_excel(buffer.getvalue())