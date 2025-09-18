import pytest
import pandas as pd
import io
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestIntegration:
    
    def create_sample_excel(self):
        """Create a sample Excel file for testing"""
        data = {
            'SO Date': ['2025-09-15', '2025-09-16', '2025-09-17'],
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
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_upload_success(self):
        """Test successful file upload"""
        excel_data = self.create_sample_excel()
        
        response = client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "success"
        assert data["filename"] == "test.xlsx"
        assert "columns_detected" in data
        assert "sample_rows" in data
        assert "date_range" in data
        assert data["total_rows"] == 3
    
    def test_upload_wrong_file_type(self):
        """Test upload with wrong file type"""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"some text", "text/plain")}
        )
        
        assert response.status_code == 400
        assert "Only .xlsx files are supported" in response.json()["detail"]
    
    def test_analyze_without_upload(self):
        """Test analyze endpoint without uploading file first"""
        response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-17"
            }
        )
        
        assert response.status_code == 400
        assert "No data uploaded" in response.json()["detail"]
    
    def test_full_workflow(self):
        """Test complete workflow: upload -> analyze -> export"""
        # Step 1: Upload file
        excel_data = self.create_sample_excel()
        
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        assert upload_response.status_code == 200
        
        # Step 2: Analyze data
        analyze_response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-18"
            }
        )
        
        assert analyze_response.status_code == 200
        analysis_data = analyze_response.json()
        
        # Verify analysis structure
        assert "daily" in analysis_data
        assert "totals" in analysis_data
        assert "kpis" in analysis_data
        
        # Verify totals match expected values from sample data
        totals = analysis_data["totals"]
        expected_inbound = 22.123456 + 33.456789 + 10.437627  # 66.017872
        expected_outbound = 25.123456 + 30.456789 + 10.437627  # 66.017872
        
        assert abs(totals["total_inbound_cbm"] - expected_inbound) < 0.000001
        assert abs(totals["total_outbound_cbm_si"] - expected_outbound) < 0.000001
        
        # Step 3: Export CSV
        csv_response = client.get(
            "/api/download/csv",
            params={
                "date_from": "2025-09-15",
                "date_to": "2025-09-18"
            }
        )
        
        assert csv_response.status_code == 200
        assert csv_response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # Step 4: Export PDF
        pdf_response = client.post(
            "/api/download/pdf",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-18"
            }
        )
        
        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"] == "application/pdf"
    
    def test_analyze_specific_date_range(self):
        """Test analysis with specific date range"""
        # Upload file first
        excel_data = self.create_sample_excel()
        
        client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        # Analyze only one day
        response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-15"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have only one day of data
        assert len(data["daily"]) == 1
        
        day_data = data["daily"][0]
        assert day_data["date"] == "2025-09-15"
        assert day_data["inbound_cbm"] == 22.123456
        assert day_data["outbound_cbm_si"] == 0  # No SI data for this date
    
    def test_kpi_calculations(self):
        """Test KPI calculations with known data"""
        # Upload file first
        excel_data = self.create_sample_excel()
        
        client.post(
            "/api/upload",
            files={"file": ("test.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
        
        # Analyze full range
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
        
        # Peak inbound day should be 2025-09-16 (33.456789)
        assert kpis["peak_inbound_day"]["date"] == "2025-09-16"
        assert abs(kpis["peak_inbound_day"]["value"] - 33.456789) < 0.000001
        
        # Peak outbound day should be 2025-09-17 (30.456789)
        assert kpis["peak_outbound_day"]["date"] == "2025-09-17"
        assert abs(kpis["peak_outbound_day"]["value"] - 30.456789) < 0.000001
    
    def test_missing_required_columns(self):
        """Test upload with missing required columns"""
        # Create Excel with missing SI Date column
        data = {
            'SO Date': ['2025-09-15', '2025-09-16'],
            'SO Total CBM': [22.123456, 33.456789],
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
        assert "Sales Invoice Date column not found" in response.json()["detail"]
    
    def test_computed_cbm_fallback(self):
        """Test CBM computation from per unit CBM and quantity"""
        # Create Excel without SO Total CBM but with per unit and quantity
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
        
        # Analyze to verify computed CBM
        analyze_response = client.post(
            "/api/analyze",
            json={
                "date_from": "2025-09-15",
                "date_to": "2025-09-17"
            }
        )
        
        assert analyze_response.status_code == 200
        data = analyze_response.json()
        
        # Total inbound should be 10.0 + 15.0 = 25.0 (2.5*4 + 3.0*5)
        assert abs(data["totals"]["total_inbound_cbm"] - 25.0) < 0.000001