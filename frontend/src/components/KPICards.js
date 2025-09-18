import React from 'react';

const KPICards = ({ data }) => {
  const { totals, kpis } = data;

  const formatNumber = (num) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 6
    }).format(num || 0);
  };

  const formatQuantity = (num) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(num || 0);
  };

  const cards = [
    {
      title: 'Total Inbound CBM',
      value: formatNumber(totals?.total_inbound_cbm),
      subtitle: 'Sales Orders',
      color: 'bg-blue-500',
      icon: '📦'
    },
    {
      title: 'Total Outbound CBM (SI)',
      value: formatNumber(totals?.total_outbound_cbm_si),
      subtitle: 'Sales Invoices Only',
      color: 'bg-green-500',
      icon: '🚚'
    },
    {
      title: 'Net Flow CBM',
      value: formatNumber(totals?.total_net_flow_cbm),
      subtitle: 'Inbound - Outbound',
      color: totals?.total_net_flow_cbm >= 0 ? 'bg-emerald-500' : 'bg-red-500',
      icon: '⚖️'
    },
    {
      title: 'Total Inbound Quantity',
      value: formatQuantity(totals?.total_inbound_qty),
      subtitle: 'Sales Orders',
      color: 'bg-cyan-500',
      icon: '📊'
    },
    {
      title: 'Total Outbound Quantity (SI)',
      value: formatQuantity(totals?.total_outbound_qty_si),
      subtitle: 'Sales Invoices Only',
      color: 'bg-teal-500',
      icon: '📈'
    },
    {
      title: 'Net Flow Quantity',
      value: formatQuantity(totals?.total_net_flow_qty),
      subtitle: 'Inbound - Outbound',
      color: totals?.total_net_flow_qty >= 0 ? 'bg-lime-500' : 'bg-red-500',
      icon: '🔢'
    }
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {cards.map((card, index) => (
        <div key={index} className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="p-6">
            <div className="flex items-center">
              <div className={`flex-shrink-0 ${card.color} rounded-md p-3`}>
                <span className="text-white text-xl">{card.icon}</span>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {card.title}
                  </dt>
                  <dd className="text-lg font-semibold text-gray-900">
                    {card.value}
                  </dd>
                  <dd className="text-sm text-gray-600">
                    {card.subtitle}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default KPICards;