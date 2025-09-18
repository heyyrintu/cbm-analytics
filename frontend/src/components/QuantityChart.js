import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const QuantityChart = ({ data }) => {
  const formatTooltip = (value, name) => {
    const formattedValue = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);

    const nameMap = {
      inbound_qty: 'Inbound Quantity',
      outbound_qty_si: 'Outbound Quantity (SI)',
      net_flow_qty: 'Net Flow Quantity'
    };

    return [formattedValue, nameMap[name] || name];
  };

  const formatXAxisLabel = (tickItem) => {
    const date = new Date(tickItem);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-6">
        Daily Quantity Flow Analysis
      </h3>
      
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{
              top: 5,
              right: 30,
              left: 20,
              bottom: 5,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tickFormatter={formatXAxisLabel}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis 
              tickFormatter={(value) => 
                new Intl.NumberFormat('en-US', {
                  notation: 'compact',
                  maximumFractionDigits: 0
                }).format(value)
              }
            />
            <Tooltip 
              formatter={formatTooltip}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Legend />
            <Bar
              dataKey="inbound_qty"
              fill="#3B82F6"
              name="inbound_qty"
            />
            <Bar
              dataKey="outbound_qty_si"
              fill="#10B981"
              name="outbound_qty_si"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-blue-500 rounded-sm mr-2"></div>
          <span>Inbound Quantity (Sales Orders)</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-green-500 rounded-sm mr-2"></div>
          <span>Outbound Quantity (Sales Invoices Only)</span>
        </div>
      </div>
    </div>
  );
};

export default QuantityChart;