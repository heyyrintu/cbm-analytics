import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const CBMChart = ({ data }) => {
  const formatTooltip = (value, name) => {
    const formattedValue = new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(value);

    const nameMap = {
      inbound_cbm: 'Inbound CBM',
      outbound_cbm_si: 'Outbound CBM (SI)',
      net_flow_cbm: 'Net Flow CBM'
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
        Daily CBM Flow Analysis
      </h3>
      
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
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
                  maximumFractionDigits: 1
                }).format(value)
              }
            />
            <Tooltip 
              formatter={formatTooltip}
              labelFormatter={(label) => `Date: ${label}`}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="inbound_cbm"
              stroke="#3B82F6"
              strokeWidth={2}
              name="inbound_cbm"
              dot={{ r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="outbound_cbm_si"
              stroke="#10B981"
              strokeWidth={2}
              name="outbound_cbm_si"
              dot={{ r: 3 }}
            />
            <Line
              type="monotone"
              dataKey="net_flow_cbm"
              stroke="#F59E0B"
              strokeWidth={2}
              name="net_flow_cbm"
              dot={{ r: 3 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
          <span>Inbound CBM (Sales Orders)</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
          <span>Outbound CBM (Sales Invoices Only)</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
          <span>Net Flow CBM (Inbound - Outbound)</span>
        </div>
      </div>
    </div>
  );
};

export default CBMChart;