from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import pandas as pd
import io
import os
import tempfile
from datetime import datetime, date
import json

from parser import ExcelParser
from analyzer import DataAnalyzer
from exporter import CSVExporter, PDFExporter

app = FastAPI(title="CBM Analytics API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for uploaded data
uploaded_data = {}

class AnalyzeRequest(BaseModel):
    date_from: str
    date_to: str
    group_by: Optional[str] = None

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and parse Excel file"""
    
    # Validate file type
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    
    # Check file size
    max_size = int(os.getenv('MAX_UPLOAD_SIZE', 20971520))  # 20MB default
    
    try:
        # Read file content
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Parse Excel file
        parser = ExcelParser()
        result = parser.parse_excel(content)
        
        # Store parsed data globally (in production, use proper storage)
        uploaded_data['data'] = result['data']
        uploaded_data['columns'] = result['columns']
        uploaded_data['date_range'] = result['date_range']
        
        return {
            "status": "success",
            "filename": file.filename,
            "columns_detected": result['columns'],
            "sample_rows": result['sample_rows'],
            "date_range": result['date_range'],
            "total_rows": len(result['data'])
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/analyze")
async def analyze_data(request: AnalyzeRequest):
    """Analyze uploaded data with date filtering and grouping"""
    
    if 'data' not in uploaded_data:
        raise HTTPException(status_code=400, detail="No data uploaded. Please upload a file first.")
    
    try:
        analyzer = DataAnalyzer(uploaded_data['data'])
        result = analyzer.analyze(
            date_from=request.date_from,
            date_to=request.date_to,
            group_by=request.group_by
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/download/csv")
async def download_csv(
    date_from: str = Query(...),
    date_to: str = Query(...),
    group_by: Optional[str] = Query(None)
):
    """Export data as CSV"""
    
    if 'data' not in uploaded_data:
        raise HTTPException(status_code=400, detail="No data uploaded")
    
    try:
        analyzer = DataAnalyzer(uploaded_data['data'])
        result = analyzer.analyze(date_from, date_to, group_by)
        
        exporter = CSVExporter()
        csv_content = exporter.export(result['daily'])
        
        return StreamingResponse(
            io.StringIO(csv_content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=cbm_analysis.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/download/pdf")
async def download_pdf(request: AnalyzeRequest):
    """Export summary as PDF"""
    
    if 'data' not in uploaded_data:
        raise HTTPException(status_code=400, detail="No data uploaded")
    
    try:
        analyzer = DataAnalyzer(uploaded_data['data'])
        result = analyzer.analyze(request.date_from, request.date_to, request.group_by)
        
        exporter = PDFExporter()
        pdf_content = exporter.export(result)
        
        return StreamingResponse(
            io.BytesIO(pdf_content),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cbm_summary.pdf"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)