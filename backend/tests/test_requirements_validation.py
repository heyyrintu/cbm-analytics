"""
Test suite to validate specific requirements from the original prompt.
This ensures the application meets all specified criteria.
"""

import pytest
import pandas as pd
import io
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestRequirementsValidation:
    """Validate specific requirements from the prompt"""
    
    def create_exact_test_data(self):
        """Create test data matching the prompt's expected values"""
        data = {
            'SO Date': ['2025-09-15', '2025-09-15', '2025-09-15'],
            'SO Total CBM': [22.123456, 33.456789, 10.437627],
            'Sales Invoice Date': ['2025-09-16', '2025-09-17', '2025-09-18'],
            'SI Total CBM': [25.123456, 30.456789, 10.437627],
            'Per Unit CBM': [2.5, 3.0, 2.1],
            'Sales Order Qty': [8, 11, 5],
            'Sales Invoice Qty': [10, 10, 5]
        }
        
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        return buffer.getvalue()
    
    def test_api_endpoints_exist(self):
        """Test that all required API endpoints exist"""
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        # Test upload endpoint (without file - should fail gracefully)
        response = client.post("/api/upload")
        assert response.status_code == 422  # Validation error for missing file
        
        # Test analyze endpoint (without data - should fail gracefully)
        response = client.post("/api/analyze", json={
            "date_from": "2025-09-15",
            "date_to": "2025-09-15"
        })
        assert response.status_code == 400  # No data uploaded
        
        # Test CSV download endpoint (without data - should fail gracefully)
        response = client.get("/api/download/csv?date_from=2025-09-15&date_to=2025-09-15")
        assert response.status_code == 400  # No data uploaded
        
        # Test PDF download endpoint (without data - should fail gracefully)
        response = client.post("/api/download/pdf", json={
            "date_from": "2025-09-15",
            "date_to": "2025-09-15"
        })
        assert response.status_code == 400  # No data uploaded
    
    def test_column_detection_fuzzy_matching(self):
        """Test fuzzy matching for column names as specified in prompt"""
        
        # Create data with variations of column names
        data = {
            'so date': ['2025-09-15'],  # lowercase
            'SO_Total_CBM': [10.5],     # underscores
            'Sales Invoice DATE': ['2025-09-16'],  # mixed case with space
            'SI Total CBM': [8.2]       # standard format
        }
        
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.xlsx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should detect columns despite variations
        assert data["columns_detected"]["so_date"] == "so date"
        assert data["columns_detected"]["so_total_cbm"] == "SO_Total_CBM"
        assert data["columns_detected"]["si_date"] == "Sales Invoice DATE"
        assert data["columns_detected"]["si_total_cbm"] == "SI Total CBM"
    
    def test_exact_cbm_totals_from_prompt(self):
        """Test exact CBM totals mentioned in the prompt: 66.017872"""
        
        excel_data = self.create_exact_test_data()
        
        # Upload file
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        assert upload_response.status_code == 200
        
        # Analyze for 2025-09-15 (should have inbound but no outbound SI)
        analyze_response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-15"
            }
        )
        
        assert analyze_response.status_code == 200
        analysis_data = analyze_response.json()
        
        # Verify exact totals from prompt
        expected_inbound_cbm = 22.123456 + 33.456789 + 10.437627  # 66.017872
        expected_inbound_qty = 8 + 11 + 5  # 24
        assert abs(analysis_data["totals"]["total_inbound_cbm"] - expected_inbound_cbm) < 0.000001
        assert analysis_data["totals"]["total_inbound_qty"] == expected_inbound_qty
        assert analysis_data["totals"]["total_outbound_cbm_si"] == 0.0  # No SI on 2025-09-15
        assert analysis_data["totals"]["total_outbound_qty_si"] == 0  # No SI on 2025-09-15
        
        # Test full date range
        full_range_response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-18"
            }
        )
        
        assert full_range_response.status_code == 200
        full_data = full_range_response.json()
        
        expected_outbound_cbm = 25.123456 + 30.456789 + 10.437627  # 66.017872
        expected_outbound_qty = 10 + 10 + 5  # 25
        assert abs(full_data["totals"]["total_outbound_cbm_si"] - expected_outbound_cbm) < 0.000001
        assert full_data["totals"]["total_outbound_qty_si"] == expected_outbound_qty
    
    def test_si_only_outbound_emphasis(self):
        """Test that outbound is explicitly SI-only as specified in prompt"""
        
        excel_data = self.create_exact_test_data()
        
        # Upload and analyze
        client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-18"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check that outbound fields are named with _si suffix
        for daily_record in data["daily"]:
            assert "outbound_cbm_si" in daily_record
            assert "outbound_qty_si" in daily_record
            assert "net_flow_cbm" in daily_record
            assert "net_flow_qty" in daily_record
            assert "outbound_cbm" not in daily_record  # Should not have generic outbound
        
        assert "total_outbound_cbm_si" in data["totals"]
        assert "total_outbound_qty_si" in data["totals"]
        assert "total_net_flow_cbm" in data["totals"]
        assert "total_net_flow_qty" in data["totals"]
    
    def test_fallback_cbm_calculation(self):
        """Test fallback CBM calculation from Per Unit CBM * Qty"""
        
        # Create data without SO Total CBM but with per unit and quantity
        data = {
            'SO Date': ['2025-09-15', '2025-09-16'],
            'Per Unit CBM': [2.5, 3.0],
            'Sales Order Qty': [4, 5],
            'Sales Invoice Date': ['2025-09-16', '2025-09-17'],
            'SI Total CBM': [10.0, 12.0]
        }
        
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.xlsx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        
        # Should indicate CBM was computed
        assert "so_cbm_computed" in upload_data["columns_detected"]
        
        # Analyze to verify computed values
        analyze_response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-17"
            }
        )
        
        assert analyze_response.status_code == 200
        analysis_data = analyze_response.json()
        
        # Total inbound should be 10.0 + 15.0 = 25.0 (2.5*4 + 3.0*5)
        assert abs(analysis_data["totals"]["total_inbound_cbm"] - 25.0) < 0.000001
    
    def test_date_parsing_flexibility(self):
        """Test date parsing with various formats as specified"""
        
        # Create data with different date formats
        data = {
            'SO Date': ['2025-09-15', '15/09/2025', '15-Sep-2025'],
            'SO Total CBM': [10.0, 15.0, 20.0],
            'Sales Invoice Date': ['2025-09-16', '16/09/2025', '16-Sep-2025'],
            'SI Total CBM': [8.0, 12.0, 18.0]
        }
        
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.xlsx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should successfully parse dates and provide date range
        assert data["date_range"]["min_date"] is not None
        assert data["date_range"]["max_date"] is not None
    
    def test_kpi_calculations_as_specified(self):
        """Test KPI calculations match prompt requirements"""
        
        excel_data = self.create_exact_test_data()
        
        client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-18"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        kpis = data["kpis"]
        
        # Should have all required KPIs
        assert "peak_inbound_day" in kpis
        assert "peak_outbound_day" in kpis
        assert "avg_daily_net_flow" in kpis
        
        # Peak inbound should be 2025-09-15 with 66.017872
        assert kpis["peak_inbound_day"]["date"] == "2025-09-15"
        assert abs(kpis["peak_inbound_day"]["value"] - 66.017872) < 0.000001
    
    def test_export_functionality(self):
        """Test CSV and PDF export as specified in prompt"""
        
        excel_data = self.create_exact_test_data()
        
        client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        # Test CSV export
        csv_response = client.get(
            "/api/download/csv",
            params={
                "date_from": "2025-09-15",
                "date_to": "2025-09-18"
            }
        )
        
        assert csv_response.status_code == 200
        assert csv_response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # CSV should contain all required columns
        csv_content = csv_response.content.decode('utf-8')
        assert "outbound_cbm_si" in csv_content
        assert "outbound_qty_si" in csv_content
        assert "date" in csv_content
        assert "inbound_cbm" in csv_content
        assert "inbound_qty" in csv_content
        assert "net_flow_cbm" in csv_content
        assert "net_flow_qty" in csv_content
        
        # Test PDF export
        pdf_response = client.post(
            "/api/download/pdf",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-18"
            }
        )
        
        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"] == "application/pdf"
        assert len(pdf_response.content) > 1000  # Should be a substantial PDF
    
    def test_error_handling_for_missing_si_data(self):
        """Test clear error when SI data is missing entirely"""
        
        # Create data without SI Date column
        data = {
            'SO Date': ['2025-09-15', '2025-09-16'],
            'SO Total CBM': [10.0, 15.0],
            'Random Column': [1, 2]
        }
        
        df = pd.DataFrame(data)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.xlsx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        assert response.status_code == 400
        error_detail = response.json()["detail"]
        
        # Should provide clear error about missing invoice dates
        assert "Sales Invoice Date" in error_detail
        assert "outbound" in error_detail.lower() or "invoice" in error_detail.lower()
    
    def test_file_size_and_type_validation(self):
        """Test file upload validation as specified"""
        
        # Test wrong file type
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"some text", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Only .xlsx files are supported" in response.json()["detail"]
        
        # Test file size limit (this would need a very large file in practice)
        # For now, just verify the endpoint exists and validates
        response = client.post("/api/upload")
        assert response.status_code == 422  # Missing file validation    
 
   def test_quantity_calculations_per_date(self):
        """Test that quantity calculations are correct for each date"""
        
        excel_data = self.create_exact_test_data()
        
        client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        # Test specific date with known quantities
        response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-15"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # For 2025-09-15: SO Qty = 8 + 11 + 5 = 24, SI Qty = 0
        daily_data = data["daily"][0]  # Only one day
        assert daily_data["date"] == "2025-09-15"
        assert daily_data["inbound_qty"] == 24
        assert daily_data["outbound_qty_si"] == 0
        assert daily_data["net_flow_qty"] == 24
        
        # Test full range
        full_response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-18"
            }
        )
        
        assert full_response.status_code == 200
        full_data = full_response.json()
        
        # Total quantities should match
        assert full_data["totals"]["total_inbound_qty"] == 24  # 8 + 11 + 5
        assert full_data["totals"]["total_outbound_qty_si"] == 25  # 10 + 10 + 5
        assert full_data["totals"]["total_net_flow_qty"] == -1  # 24 - 25
    
    def test_net_flow_quantity_calculation(self):
        """Test that Net Flow Quantity = Inbound Quantity - Outbound Quantity"""
        
        excel_data = self.create_exact_test_data()
        
        client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-18"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify net flow calculation for each day
        for daily_record in data["daily"]:
            expected_net_flow_qty = daily_record["inbound_qty"] - daily_record["outbound_qty_si"]
            assert daily_record["net_flow_qty"] == expected_net_flow_qty
            
            expected_net_flow_cbm = daily_record["inbound_cbm"] - daily_record["outbound_cbm_si"]
            assert abs(daily_record["net_flow_cbm"] - expected_net_flow_cbm) < 0.000001