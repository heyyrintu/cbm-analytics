import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from './App';

// Mock child components to avoid complex dependencies in unit tests
jest.mock('./components/FileUpload', () => {
  return function MockFileUpload() {
    return <div data-testid="file-upload">File Upload Component</div>;
  };
});

jest.mock('./components/Dashboard', () => {
  return function MockDashboard() {
    return <div data-testid="dashboard">Dashboard Component</div>;
  };
});

describe('App Component', () => {
  test('renders app header', () => {
    render(<App />);
    
    expect(screen.getByText('CBM Analytics')).toBeInTheDocument();
    expect(screen.getByText('Inbound & Outbound CBM Analysis')).toBeInTheDocument();
  });

  test('renders file upload component initially', () => {
    render(<App />);
    
    expect(screen.getByTestId('file-upload')).toBeInTheDocument();
    expect(screen.queryByTestId('dashboard')).not.toBeInTheDocument();
  });

  test('does not show upload new file button initially', () => {
    render(<App />);
    
    expect(screen.queryByText('Upload New File')).not.toBeInTheDocument();
  });
});