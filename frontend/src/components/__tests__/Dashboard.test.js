import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import Dashboard from '../Dashboard';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock child components
jest.mock('../KPICards', () => {
  return function MockKPICards({ data }) {
    return <div data-testid="kpi-cards">KPI Cards: {data.totals.total_inbound_cbm}</div>;
  };
});

jest.mock('../CBMChart', () => {
  return function MockCBMChart({ data }) {
    return <div data-testid="cbm-chart">Chart with {data.length} data points</div>;
  };
});

jest.mock('../DateRangePicker', () => {
  return function MockDateRangePicker({ dateRange, onChange }) {
    return (
      <div data-testid="date-range-picker">
        Date Range: {dateRange.from} to {dateRange.to}
      </div>
    );
  };
});

jest.mock('../ExportButtons', () => {
  return function MockExportButtons({ disabled }) {
    return <div data-testid="export-buttons">Export Buttons (disabled: {disabled.toString()})</div>;
  };
});

describe('Dashboard Component', () => {
  const mockUploadedData = {
    filename: 'test.xlsx',
    total_rows: 100,
    date_range: {
      min_date: '2023-01-01',
      max_date: '2023-01-31'
    },
    columns_detected: {
      so_date: 'SO Date',
      so_total_cbm: 'SO Total CBM',
      si_date: 'SI Date',
      si_total_cbm: 'SI Total CBM'
    }
  };

  const mockAnalysisData = {
    daily: [
      { 
        date: '2023-01-01', 
        inbound_cbm: 10.5, 
        outbound_cbm_si: 8.2, 
        net_flow_cbm: 2.3,
        inbound_qty: 15,
        outbound_qty_si: 12,
        net_flow_qty: 3
      },
      { 
        date: '2023-01-02', 
        inbound_cbm: 15.2, 
        outbound_cbm_si: 12.1, 
        net_flow_cbm: 3.1,
        inbound_qty: 20,
        outbound_qty_si: 18,
        net_flow_qty: 2
      }
    ],
    totals: {
      total_inbound_cbm: 25.7,
      total_outbound_cbm_si: 20.3,
      total_net_flow_cbm: 5.4,
      total_inbound_qty: 35,
      total_outbound_qty_si: 30,
      total_net_flow_qty: 5
    },
    kpis: {
      peak_inbound_cbm_day: { date: '2023-01-02', value: 15.2 },
      peak_outbound_cbm_day: { date: '2023-01-02', value: 12.1 },
      peak_inbound_qty_day: { date: '2023-01-02', value: 20 },
      peak_outbound_qty_day: { date: '2023-01-02', value: 18 },
      avg_daily_net_flow_cbm: 2.7,
      avg_daily_net_flow_qty: 2.5
    }
  };

  const mockSetIsLoading = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders file information correctly', () => {
    mockedAxios.post.mockResolvedValueOnce({ data: mockAnalysisData });

    render(
      <Dashboard 
        uploadedData={mockUploadedData}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    expect(screen.getByText('File Analysis: test.xlsx')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument(); // total rows
    expect(screen.getByText('2023-01-01 to 2023-01-31')).toBeInTheDocument(); // date range
    expect(screen.getByText('4')).toBeInTheDocument(); // columns detected
  });

  test('displays detected columns', () => {
    mockedAxios.post.mockResolvedValueOnce({ data: mockAnalysisData });

    render(
      <Dashboard 
        uploadedData={mockUploadedData}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    expect(screen.getByText('Detected Columns:')).toBeInTheDocument();
    expect(screen.getByText('so_date:')).toBeInTheDocument();
    expect(screen.getByText('SO Date')).toBeInTheDocument();
  });

  test('calls analyze API on mount', async () => {
    mockedAxios.post.mockResolvedValueOnce({ data: mockAnalysisData });

    render(
      <Dashboard 
        uploadedData={mockUploadedData}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    await waitFor(() => {
      expect(mockedAxios.post).toHaveBeenCalledWith('/api/analyze', {
        date_from: expect.any(String),
        date_to: expect.any(String),
        group_by: null
      });
    });
  });

  test('shows loading state', () => {
    render(
      <Dashboard 
        uploadedData={mockUploadedData}
        isLoading={true}
        setIsLoading={mockSetIsLoading}
      />
    );

    expect(screen.getByText('Analyzing data...')).toBeInTheDocument();
    expect(document.querySelector('.loading-spinner')).toBeInTheDocument();
  });

  test('displays analysis results', async () => {
    mockedAxios.post.mockResolvedValueOnce({ data: mockAnalysisData });

    render(
      <Dashboard 
        uploadedData={mockUploadedData}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('kpi-cards')).toBeInTheDocument();
      expect(screen.getByTestId('cbm-chart')).toBeInTheDocument();
    });

    expect(screen.getByText('KPI Cards: 25.7')).toBeInTheDocument();
    expect(screen.getByText('Chart with 2 data points')).toBeInTheDocument();
  });

  test('handles analysis error', async () => {
    const mockError = {
      response: {
        data: {
          detail: 'Analysis failed'
        }
      }
    };

    mockedAxios.post.mockRejectedValueOnce(mockError);

    render(
      <Dashboard 
        uploadedData={mockUploadedData}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Analysis failed')).toBeInTheDocument();
    });
  });

  test('renders controls section', async () => {
    mockedAxios.post.mockResolvedValueOnce({ data: mockAnalysisData });

    render(
      <Dashboard 
        uploadedData={mockUploadedData}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    expect(screen.getByTestId('date-range-picker')).toBeInTheDocument();
    expect(screen.getByTestId('export-buttons')).toBeInTheDocument();
  });

  test('export buttons are disabled when loading', () => {
    render(
      <Dashboard 
        uploadedData={mockUploadedData}
        isLoading={true}
        setIsLoading={mockSetIsLoading}
      />
    );

    expect(screen.getByText('Export Buttons (disabled: true)')).toBeInTheDocument();
  });

  test('export buttons are enabled when data is loaded', async () => {
    mockedAxios.post.mockResolvedValueOnce({ data: mockAnalysisData });

    render(
      <Dashboard 
        uploadedData={mockUploadedData}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Export Buttons (disabled: false)')).toBeInTheDocument();
    });
  });

  test('uses default date range when not provided', () => {
    const uploadedDataWithoutDates = {
      ...mockUploadedData,
      date_range: null
    };

    mockedAxios.post.mockResolvedValueOnce({ data: mockAnalysisData });

    render(
      <Dashboard 
        uploadedData={uploadedDataWithoutDates}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    // Should still render without errors
    expect(screen.getByText('File Analysis: test.xlsx')).toBeInTheDocument();
  });
});