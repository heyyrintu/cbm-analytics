import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format, subDays, startOfMonth, endOfMonth } from 'date-fns';
import KPICards from './KPICards';
import CBMChart from './CBMChart';
import QuantityChart from './QuantityChart';
import DataTable from './DataTable';
import DateRangePicker from './DateRangePicker';
import ExportButtons from './ExportButtons';

const Dashboard = ({ uploadedData, isLoading, setIsLoading }) => {
  const [analysisData, setAnalysisData] = useState(null);
  const [dateRange, setDateRange] = useState({
    from: uploadedData.date_range?.min_date || format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    to: uploadedData.date_range?.max_date || format(new Date(), 'yyyy-MM-dd')
  });
  const [groupBy, setGroupBy] = useState(null);
  const [error, setError] = useState(null);

  const analyzeData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.post('/api/analyze', {
        date_from: dateRange.from,
        date_to: dateRange.to,
        group_by: groupBy
      });

      setAnalysisData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    analyzeData();
  }, [dateRange, groupBy]);

  const handleDateRangeChange = (newRange) => {
    setDateRange(newRange);
  };

  const handleQuickDateSelect = (preset) => {
    const today = new Date();
    let from, to;

    switch (preset) {
      case 'last7days':
        from = format(subDays(today, 7), 'yyyy-MM-dd');
        to = format(today, 'yyyy-MM-dd');
        break;
      case 'last30days':
        from = format(subDays(today, 30), 'yyyy-MM-dd');
        to = format(today, 'yyyy-MM-dd');
        break;
      case 'thisMonth':
        from = format(startOfMonth(today), 'yyyy-MM-dd');
        to = format(endOfMonth(today), 'yyyy-MM-dd');
        break;
      case 'all':
        from = uploadedData.date_range?.min_date || format(subDays(today, 365), 'yyyy-MM-dd');
        to = uploadedData.date_range?.max_date || format(today, 'yyyy-MM-dd');
        break;
      default:
        return;
    }

    setDateRange({ from, to });
  };

  return (
    <div className="space-y-6">
      {/* File Info */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              File Analysis: {uploadedData.filename}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
              <div>
                <span className="font-medium">Total Rows:</span> {uploadedData.total_rows}
              </div>
              <div>
                <span className="font-medium">Date Range:</span>{' '}
                {uploadedData.date_range?.min_date} to {uploadedData.date_range?.max_date}
              </div>
              <div>
                <span className="font-medium">Columns Detected:</span>{' '}
                {Object.keys(uploadedData.columns_detected).length}
              </div>
            </div>
          </div>
        </div>

        {/* Detected Columns */}
        <div className="mt-4 p-4 bg-gray-50 rounded-md">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Detected Columns:</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs text-gray-600">
            {Object.entries(uploadedData.columns_detected).map(([key, value]) => (
              <div key={key}>
                <span className="font-medium">{key}:</span> {value || 'Not found'}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <DateRangePicker
            dateRange={dateRange}
            onChange={handleDateRangeChange}
            onQuickSelect={handleQuickDateSelect}
          />
          
          <ExportButtons
            dateRange={dateRange}
            groupBy={groupBy}
            disabled={isLoading || !analysisData}
          />
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-12">
          <div className="loading-spinner"></div>
          <p className="text-gray-600 mt-4">Analyzing data...</p>
        </div>
      ) : analysisData ? (
        <>
          <KPICards data={analysisData} />
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CBMChart data={analysisData.daily} />
            <QuantityChart data={analysisData.daily} />
          </div>
          
          <DataTable data={analysisData.daily} />
        </>
      ) : null}
    </div>
  );
};

export default Dashboard;