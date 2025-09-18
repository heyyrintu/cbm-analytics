import pytest
import pandas as pd
from datetime import datetime, date
from analyzer import DataAnalyzer

class TestDataAnalyzer:
    
    def create_test_data(self):
        """Create test DataFrame for analysis"""
        data = {
            'so_date_parsed': [
                pd.Timestamp('2023-01-15'),
                pd.Timestamp('2023-01-16'),
                pd.Timestamp('2023-01-17'),
                pd.Timestamp('2023-01-18')
            ],
            'so_cbm_value': [10.5, 15.2, 8.7, 12.3],
            'si_date_parsed': [
                pd.Timestamp('2023-01-16'),
                pd.Timestamp('2023-01-17'),
                pd.Timestamp('2023-01-18'),
                pd.Timestamp('2023-01-19')
            ],
            'si_cbm_value': [12.3, 9.8, 11.1, 7.5]
        }
        
        return pd.DataFrame(data)
    
    def setup_method(self):
        self.test_data = self.create_test_data()
        self.analyzer = DataAnalyzer(self.test_data)
    
    def test_analyze_basic(self):
        """Test basic analysis functionality"""
        result = self.analyzer.analyze('2023-01-15', '2023-01-19')
        
        # Check structure
        assert 'daily' in result
        assert 'totals' in result
        assert 'kpis' in result
        
        # Check daily data
        daily = result['daily']
        assert len(daily) == 5  # 5 days from 15th to 19th
        
        # Check totals
        totals = result['totals']
        assert totals['total_inbound_cbm'] == 46.7  # Sum of SO CBM
        assert totals['total_outbound_cbm_si'] == 40.7  # Sum of SI CBM
        assert totals['total_net_flow'] == 6.0  # 46.7 - 40.7
    
    def test_analyze_date_filtering(self):
        """Test date range filtering"""
        # Analyze only 2 days
        result = self.analyzer.analyze('2023-01-16', '2023-01-17')
        
        daily = result['daily']
        assert len(daily) == 2  # Only 2 days
        
        # Check that only data within range is included
        totals = result['totals']
        assert totals['total_inbound_cbm'] == 23.9  # 15.2 + 8.7
        assert totals['total_outbound_cbm_si'] == 22.1  # 12.3 + 9.8
    
    def test_analyze_kpis(self):
        """Test KPI calculations"""
        result = self.analyzer.analyze('2023-01-15', '2023-01-19')
        
        kpis = result['kpis']
        
        # Check peak inbound day
        peak_inbound = kpis['peak_inbound_day']
        assert peak_inbound['date'] == '2023-01-16'
        assert peak_inbound['value'] == 15.2
        
        # Check peak outbound day
        peak_outbound = kpis['peak_outbound_day']
        assert peak_outbound['date'] == '2023-01-16'
        assert peak_outbound['value'] == 12.3
        
        # Check average daily net flow
        assert 'avg_daily_net_flow' in kpis
    
    def test_analyze_empty_date_range(self):
        """Test analysis with date range that has no data"""
        result = self.analyzer.analyze('2023-02-01', '2023-02-05')
        
        daily = result['daily']
        assert len(daily) == 5  # 5 days in range
        
        # All values should be 0
        for day in daily:
            assert day['inbound_cbm'] == 0
            assert day['outbound_cbm_si'] == 0
            assert day['net_flow'] == 0
        
        totals = result['totals']
        assert totals['total_inbound_cbm'] == 0
        assert totals['total_outbound_cbm_si'] == 0
        assert totals['total_net_flow'] == 0
    
    def test_analyze_single_day(self):
        """Test analysis for a single day"""
        result = self.analyzer.analyze('2023-01-16', '2023-01-16')
        
        daily = result['daily']
        assert len(daily) == 1
        
        day_data = daily[0]
        assert day_data['date'] == '2023-01-16'
        assert day_data['inbound_cbm'] == 15.2
        assert day_data['outbound_cbm_si'] == 12.3
        assert day_data['net_flow'] == 2.9
    
    def test_analyze_net_flow_calculation(self):
        """Test net flow calculation"""
        result = self.analyzer.analyze('2023-01-15', '2023-01-19')
        
        daily = result['daily']
        
        for day in daily:
            expected_net_flow = day['inbound_cbm'] - day['outbound_cbm_si']
            assert abs(day['net_flow'] - expected_net_flow) < 0.001
    
    def test_analyze_with_missing_data(self):
        """Test analysis with missing data points"""
        # Create data with some NaN values
        data = self.test_data.copy()
        data.loc[1, 'so_cbm_value'] = None
        data.loc[2, 'si_cbm_value'] = None
        
        analyzer = DataAnalyzer(data)
        result = analyzer.analyze('2023-01-15', '2023-01-19')
        
        # Should handle NaN values gracefully
        assert 'daily' in result
        assert 'totals' in result
    
    def test_group_by_column_not_found(self):
        """Test grouping when column doesn't exist"""
        result = self.analyzer.analyze('2023-01-15', '2023-01-19', group_by='warehouse')
        
        # Should return None for grouped data when column not found
        assert result['grouped'] is None
    
    def test_group_by_column_exists(self):
        """Test grouping when column exists"""
        # Add warehouse column to test data
        data = self.test_data.copy()
        data['Warehouse A'] = ['WH1', 'WH2', 'WH1', 'WH2']
        
        analyzer = DataAnalyzer(data)
        result = analyzer.analyze('2023-01-15', '2023-01-19', group_by='warehouse')
        
        # Should return grouped data
        assert result['grouped'] is not None
        assert result['grouped']['group_by'] == 'warehouse'
        assert 'data' in result['grouped']
    
    def test_rounding_precision(self):
        """Test that values are properly rounded"""
        result = self.analyzer.analyze('2023-01-15', '2023-01-19')
        
        # Check that totals are rounded to 6 decimal places
        totals = result['totals']
        for key, value in totals.items():
            # Should not have more than 6 decimal places
            str_value = str(value)
            if '.' in str_value:
                decimal_places = len(str_value.split('.')[1])
                assert decimal_places <= 6
    
    def test_date_string_format(self):
        """Test that dates are returned as strings in correct format"""
        result = self.analyzer.analyze('2023-01-15', '2023-01-19')
        
        daily = result['daily']
        for day in daily:
            date_str = day['date']
            # Should be in YYYY-MM-DD format
            assert len(date_str) == 10
            assert date_str[4] == '-'
            assert date_str[7] == '-'
            
            # Should be parseable as date
            datetime.strptime(date_str, '%Y-%m-%d')