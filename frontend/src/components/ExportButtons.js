import React, { useState } from 'react';
import axios from 'axios';

const ExportButtons = ({ dateRange, groupBy, disabled }) => {
  const [isExporting, setIsExporting] = useState({ csv: false, pdf: false });

  const downloadFile = (blob, filename) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const exportCSV = async () => {
    setIsExporting(prev => ({ ...prev, csv: true }));
    
    try {
      const params = new URLSearchParams({
        date_from: dateRange.from,
        date_to: dateRange.to,
        ...(groupBy && { group_by: groupBy })
      });

      const response = await axios.get(`/api/download/csv?${params}`, {
        responseType: 'blob'
      });

      downloadFile(response.data, 'cbm_analysis.csv');
    } catch (error) {
      console.error('CSV export failed:', error);
      alert('CSV export failed. Please try again.');
    } finally {
      setIsExporting(prev => ({ ...prev, csv: false }));
    }
  };

  const exportPDF = async () => {
    setIsExporting(prev => ({ ...prev, pdf: true }));
    
    try {
      const response = await axios.post('/api/download/pdf', {
        date_from: dateRange.from,
        date_to: dateRange.to,
        group_by: groupBy
      }, {
        responseType: 'blob'
      });

      downloadFile(response.data, 'cbm_summary.pdf');
    } catch (error) {
      console.error('PDF export failed:', error);
      alert('PDF export failed. Please try again.');
    } finally {
      setIsExporting(prev => ({ ...prev, pdf: false }));
    }
  };

  return (
    <div className="flex gap-3">
      <button
        onClick={exportCSV}
        disabled={disabled || isExporting.csv}
        className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isExporting.csv ? (
          <>
            <div className="animate-spin -ml-1 mr-2 h-4 w-4 border-2 border-gray-300 border-t-gray-600 rounded-full"></div>
            Exporting...
          </>
        ) : (
          <>
            <svg className="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export CSV
          </>
        )}
      </button>

      <button
        onClick={exportPDF}
        disabled={disabled || isExporting.pdf}
        className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isExporting.pdf ? (
          <>
            <div className="animate-spin -ml-1 mr-2 h-4 w-4 border-2 border-blue-300 border-t-white rounded-full"></div>
            Exporting...
          </>
        ) : (
          <>
            <svg className="-ml-1 mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            Export PDF
          </>
        )}
      </button>
    </div>
  );
};

export default ExportButtons;