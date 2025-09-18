# CBM Analytics Dashboard

A Dockerized React + FastAPI application for analyzing Excel data to track inbound (Sales Orders) and outbound (Sales Invoices) CBM with interactive dashboards and export capabilities.

## Features

- Excel file upload with drag & drop support
- Auto-detection of SO (inbound) and SI (outbound) CBM and quantity data
- Daily aggregation of inbound/outbound CBM and quantities
- Interactive charts for both CBM and quantity analysis
- Comprehensive KPIs and data table with extended columns
- CSV and PDF export functionality with both CBM and quantity data
- Comprehensive test coverage

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Running Locally

1. Clone the repository:
```bash
git clone <repository-url>
cd cbm-analytics
```

2. Start the application:
```bash
docker-compose up --build
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Running Tests

```bash
# Backend tests
docker-compose exec backend pytest tests/ -v

# Frontend tests
docker-compose exec frontend npm test
```

## API Endpoints

- `POST /api/upload` - Upload Excel file for analysis
- `POST /api/analyze` - Analyze data with date range and grouping options
- `GET /api/download/csv` - Export data as CSV
- `POST /api/download/pdf` - Export summary as PDF

## Project Structure

```
cbm-analytics/
├── frontend/          # React application
├── backend/           # FastAPI application
├── tests/            # Test files
├── docker-compose.yml
└── README.md
```

## Testing

### Backend Tests

The backend includes comprehensive unit and integration tests:

```bash
# Run all backend tests
docker-compose run --rm test-backend

# Run specific test files
docker-compose exec backend pytest tests/test_parser.py -v
docker-compose exec backend pytest tests/test_analyzer.py -v
docker-compose exec backend pytest tests/test_integration.py -v
```

### Frontend Tests

```bash
# Run frontend tests
docker-compose run --rm test-frontend

# Run tests in watch mode during development
docker-compose exec frontend npm test
```

### Test Data

Sample Excel files are provided in the `sample_data/` directory:
- `sample_cbm_data.xlsx` - 100 rows of realistic test data
- `test_cbm_data.xlsx` - 3 rows with known expected results for validation

Expected results for `test_cbm_data.xlsx`:
- Date 2025-09-15: Inbound CBM = 66.017872, Inbound Qty = 24, Outbound CBM (SI) = 0.000000, Outbound Qty (SI) = 0
- Date range 2025-09-15 to 2025-09-18: Total Inbound CBM = 66.017872, Total Inbound Qty = 24, Total Outbound CBM = 66.017872, Total Outbound Qty = 25

## Architecture

### Backend (FastAPI)
- `main.py` - API endpoints and request handling
- `parser.py` - Excel file parsing with fuzzy column matching
- `analyzer.py` - Data analysis and aggregation logic
- `exporter.py` - CSV and PDF export functionality

### Frontend (React)
- `FileUpload.js` - Drag & drop file upload with validation
- `Dashboard.js` - Main dashboard with controls and data display
- `KPICards.js` - Key performance indicators display
- `CBMChart.js` - Interactive line chart using Recharts
- `DateRangePicker.js` - Date range selection with presets
- `ExportButtons.js` - CSV and PDF export functionality

### Key Features

1. **Fuzzy Column Matching**: Automatically detects columns with variations in naming
2. **Date Parsing**: Handles multiple date formats including Excel serial dates
3. **CBM Computation**: Falls back to Per Unit CBM × Quantity when Total CBM is missing
4. **SI-Only Outbound**: Explicitly focuses on Sales Invoice data for outbound analysis
5. **Quantity Tracking**: Parallel tracking of quantities alongside CBM data
6. **Interactive Charts**: Real-time visualization of both CBM and quantity flows
7. **Extended Data Table**: Shows Date | Inbound CBM | Outbound CBM | Net Flow CBM | Inbound Qty | Outbound Qty | Net Flow Qty
8. **Export Options**: Both CSV (raw data) and PDF (summary report) exports with CBM and quantity data

## Deployment

### Development
```bash
docker-compose up --build
```

### Production

1. Update environment variables in `docker-compose.yml`:
```yaml
environment:
  - PYTHONPATH=/app
  - MAX_UPLOAD_SIZE=52428800  # 50MB for production
  - CORS_ORIGINS=https://yourdomain.com
```

2. Use production-ready web server:
```yaml
command: gunicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

3. Add reverse proxy (nginx) configuration:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. Enable HTTPS with SSL certificates
5. Set up monitoring and logging
6. Configure backup for uploaded files (if persistent storage is needed)

### Security Considerations

- File upload size limits (configurable via MAX_UPLOAD_SIZE)
- File type validation (only .xlsx files accepted)
- CORS configuration for production domains
- Input sanitization and validation
- No persistent file storage by default (files processed in memory)
- Rate limiting (recommended for production)