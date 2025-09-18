import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import axios from 'axios';
import FileUpload from '../FileUpload';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

describe('FileUpload Component', () => {
  const mockOnUploadSuccess = jest.fn();
  const mockSetIsLoading = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders upload area correctly', () => {
    render(
      <FileUpload 
        onUploadSuccess={mockOnUploadSuccess}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    expect(screen.getByText('Upload Excel File for CBM Analysis')).toBeInTheDocument();
    expect(screen.getByText('Drag & drop an Excel file here, or click to select')).toBeInTheDocument();
    expect(screen.getByText('Required Columns')).toBeInTheDocument();
  });

  test('shows loading state when uploading', () => {
    render(
      <FileUpload 
        onUploadSuccess={mockOnUploadSuccess}
        isLoading={true}
        setIsLoading={mockSetIsLoading}
      />
    );

    expect(screen.getByText('Processing file...')).toBeInTheDocument();
    expect(document.querySelector('.loading-spinner')).toBeInTheDocument();
  });

  test('handles successful file upload', async () => {
    const mockResponse = {
      data: {
        status: 'success',
        filename: 'test.xlsx',
        columns_detected: { so_date: 'SO Date' },
        sample_rows: [],
        date_range: { min_date: '2023-01-01', max_date: '2023-01-31' },
        total_rows: 100
      }
    };

    mockedAxios.post.mockResolvedValueOnce(mockResponse);

    render(
      <FileUpload 
        onUploadSuccess={mockOnUploadSuccess}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    // Create a mock file
    const file = new File(['test content'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });

    // Get the file input
    const fileInput = screen.getByRole('button').querySelector('input[type="file"]');
    
    // Simulate file drop
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockSetIsLoading).toHaveBeenCalledWith(true);
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/upload',
        expect.any(FormData),
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
    });

    await waitFor(() => {
      expect(mockOnUploadSuccess).toHaveBeenCalledWith(mockResponse.data);
      expect(mockSetIsLoading).toHaveBeenCalledWith(false);
    });
  });

  test('handles upload error', async () => {
    const mockError = {
      response: {
        data: {
          detail: 'Upload failed'
        }
      }
    };

    mockedAxios.post.mockRejectedValueOnce(mockError);

    render(
      <FileUpload 
        onUploadSuccess={mockOnUploadSuccess}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    // Create a mock file
    const file = new File(['test content'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });

    const fileInput = screen.getByRole('button').querySelector('input[type="file"]');
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('Upload failed')).toBeInTheDocument();
      expect(mockSetIsLoading).toHaveBeenCalledWith(false);
    });
  });

  test('validates file type', async () => {
    render(
      <FileUpload 
        onUploadSuccess={mockOnUploadSuccess}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    // Create a non-Excel file
    const file = new File(['test content'], 'test.txt', { type: 'text/plain' });

    const fileInput = screen.getByRole('button').querySelector('input[type="file"]');
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('Please upload an Excel (.xlsx) file')).toBeInTheDocument();
    });

    // Should not call axios
    expect(mockedAxios.post).not.toHaveBeenCalled();
  });

  test('shows drag active state', () => {
    render(
      <FileUpload 
        onUploadSuccess={mockOnUploadSuccess}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    const dropzone = screen.getByRole('button');
    
    // Simulate drag enter
    fireEvent.dragEnter(dropzone);
    
    expect(screen.getByText('Drop the Excel file here...')).toBeInTheDocument();
  });

  test('displays required columns information', () => {
    render(
      <FileUpload 
        onUploadSuccess={mockOnUploadSuccess}
        isLoading={false}
        setIsLoading={mockSetIsLoading}
      />
    );

    expect(screen.getByText('Inbound (Sales Orders)')).toBeInTheDocument();
    expect(screen.getByText('Outbound (Sales Invoices)')).toBeInTheDocument();
    expect(screen.getByText('• SO Date / Sales Order Date')).toBeInTheDocument();
    expect(screen.getByText('• SI Total CBM / Sales Invoice Total CBM')).toBeInTheDocument();
  });
});