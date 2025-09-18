import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, date

class DataAnalyzer:
    """Analyze parsed Excel data and generate insights"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data
    
    def analyze(self, date_from: str, date_to: str, group_by: Optional[str] = None) -> Dict[str, Any]:
        """Analyze data within date range with optional grouping"""
        
        # Convert date strings to datetime
        start_date = pd.to_datetime(date_from)
        end_date = pd.to_datetime(date_to)
        
        # Filter data by date range
        so_mask = (
            self.data['so_date_parsed'].notna() & 
            (self.data['so_date_parsed'] >= start_date) & 
            (self.data['so_date_parsed'] <= end_date)
        )
        
        si_mask = (
            self.data['si_date_parsed'].notna() & 
            (self.data['si_date_parsed'] >= start_date) & 
            (self.data['si_date_parsed'] <= end_date)
        )
        
        # Aggregate inbound (SO) data by date
        so_data = self.data[so_mask].copy()
        so_daily_cbm = so_data.groupby(so_data['so_date_parsed'].dt.date)['so_cbm_value'].sum().reset_index()
        so_daily_qty = so_data.groupby(so_data['so_date_parsed'].dt.date)['so_qty_value'].sum().reset_index()
        
        so_daily = so_daily_cbm.merge(so_daily_qty, on='so_date_parsed', how='outer')
        so_daily.columns = ['date', 'inbound_cbm', 'inbound_qty']
        so_daily['date'] = so_daily['date'].astype(str)
        
        # Aggregate outbound (SI) data by date
        si_data = self.data[si_mask].copy()
        si_daily_cbm = si_data.groupby(si_data['si_date_parsed'].dt.date)['si_cbm_value'].sum().reset_index()
        si_daily_qty = si_data.groupby(si_data['si_date_parsed'].dt.date)['si_qty_value'].sum().reset_index()
        
        si_daily = si_daily_cbm.merge(si_daily_qty, on='si_date_parsed', how='outer')
        si_daily.columns = ['date', 'outbound_cbm_si', 'outbound_qty_si']
        si_daily['date'] = si_daily['date'].astype(str)
        
        # Create complete date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        daily_df = pd.DataFrame({'date': date_range.strftime('%Y-%m-%d')})
        
        # Merge inbound and outbound data
        daily_df = daily_df.merge(so_daily, on='date', how='left')
        daily_df = daily_df.merge(si_daily, on='date', how='left')
        
        # Fill NaN values with 0
        daily_df['inbound_cbm'] = daily_df['inbound_cbm'].fillna(0)
        daily_df['outbound_cbm_si'] = daily_df['outbound_cbm_si'].fillna(0)
        daily_df['inbound_qty'] = daily_df['inbound_qty'].fillna(0)
        daily_df['outbound_qty_si'] = daily_df['outbound_qty_si'].fillna(0)
        
        # Calculate net flows
        daily_df['net_flow_cbm'] = daily_df['inbound_cbm'] - daily_df['outbound_cbm_si']
        daily_df['net_flow_qty'] = daily_df['inbound_qty'] - daily_df['outbound_qty_si']
        
        # Calculate totals and KPIs
        total_inbound_cbm = daily_df['inbound_cbm'].sum()
        total_outbound_cbm = daily_df['outbound_cbm_si'].sum()
        total_net_flow_cbm = total_inbound_cbm - total_outbound_cbm
        
        total_inbound_qty = daily_df['inbound_qty'].sum()
        total_outbound_qty = daily_df['outbound_qty_si'].sum()
        total_net_flow_qty = total_inbound_qty - total_outbound_qty
        
        # Find peak days
        peak_inbound_cbm_day = daily_df.loc[daily_df['inbound_cbm'].idxmax()] if total_inbound_cbm > 0 else None
        peak_outbound_cbm_day = daily_df.loc[daily_df['outbound_cbm_si'].idxmax()] if total_outbound_cbm > 0 else None
        peak_inbound_qty_day = daily_df.loc[daily_df['inbound_qty'].idxmax()] if total_inbound_qty > 0 else None
        peak_outbound_qty_day = daily_df.loc[daily_df['outbound_qty_si'].idxmax()] if total_outbound_qty > 0 else None
        
        # Calculate average daily net flows
        non_zero_cbm_days = daily_df[daily_df['net_flow_cbm'] != 0]
        avg_daily_net_flow_cbm = non_zero_cbm_days['net_flow_cbm'].mean() if len(non_zero_cbm_days) > 0 else 0
        
        non_zero_qty_days = daily_df[daily_df['net_flow_qty'] != 0]
        avg_daily_net_flow_qty = non_zero_qty_days['net_flow_qty'].mean() if len(non_zero_qty_days) > 0 else 0
        
        # Handle grouping if requested
        grouped_data = None
        if group_by and group_by in ['warehouse', 'customer']:
            # This would require additional columns in the Excel file
            # For now, return None to indicate grouping not available
            grouped_data = self._group_by_column(group_by, start_date, end_date)
        
        return {
            'daily': daily_df.to_dict('records'),
            'totals': {
                'total_inbound_cbm': round(total_inbound_cbm, 6),
                'total_outbound_cbm_si': round(total_outbound_cbm, 6),
                'total_net_flow_cbm': round(total_net_flow_cbm, 6),
                'total_inbound_qty': round(total_inbound_qty, 0),
                'total_outbound_qty_si': round(total_outbound_qty, 0),
                'total_net_flow_qty': round(total_net_flow_qty, 0)
            },
            'kpis': {
                'peak_inbound_cbm_day': {
                    'date': peak_inbound_cbm_day['date'] if peak_inbound_cbm_day is not None else None,
                    'value': round(peak_inbound_cbm_day['inbound_cbm'], 6) if peak_inbound_cbm_day is not None else 0
                },
                'peak_outbound_cbm_day': {
                    'date': peak_outbound_cbm_day['date'] if peak_outbound_cbm_day is not None else None,
                    'value': round(peak_outbound_cbm_day['outbound_cbm_si'], 6) if peak_outbound_cbm_day is not None else 0
                },
                'peak_inbound_qty_day': {
                    'date': peak_inbound_qty_day['date'] if peak_inbound_qty_day is not None else None,
                    'value': round(peak_inbound_qty_day['inbound_qty'], 0) if peak_inbound_qty_day is not None else 0
                },
                'peak_outbound_qty_day': {
                    'date': peak_outbound_qty_day['date'] if peak_outbound_qty_day is not None else None,
                    'value': round(peak_outbound_qty_day['outbound_qty_si'], 0) if peak_outbound_qty_day is not None else 0
                },
                'avg_daily_net_flow_cbm': round(avg_daily_net_flow_cbm, 6),
                'avg_daily_net_flow_qty': round(avg_daily_net_flow_qty, 0)
            },
            'grouped': grouped_data
        }
    
    def _group_by_column(self, group_by: str, start_date: pd.Timestamp, end_date: pd.Timestamp) -> Optional[Dict]:
        """Group data by specified column if available"""
        
        # Look for warehouse or customer columns
        potential_columns = []
        for col in self.data.columns:
            col_lower = str(col).lower()
            if group_by.lower() in col_lower:
                potential_columns.append(col)
        
        if not potential_columns:
            return None
        
        # Use the first matching column
        group_column = potential_columns[0]
        
        # Filter data by date range
        so_mask = (
            self.data['so_date_parsed'].notna() & 
            (self.data['so_date_parsed'] >= start_date) & 
            (self.data['so_date_parsed'] <= end_date)
        )
        
        si_mask = (
            self.data['si_date_parsed'].notna() & 
            (self.data['si_date_parsed'] >= start_date) & 
            (self.data['si_date_parsed'] <= end_date)
        )
        
        # Group inbound data
        so_grouped_cbm = self.data[so_mask].groupby(group_column)['so_cbm_value'].sum().reset_index()
        so_grouped_qty = self.data[so_mask].groupby(group_column)['so_qty_value'].sum().reset_index()
        so_grouped = so_grouped_cbm.merge(so_grouped_qty, on=group_column, how='outer')
        so_grouped.columns = [group_by, 'inbound_cbm', 'inbound_qty']
        
        # Group outbound data
        si_grouped_cbm = self.data[si_mask].groupby(group_column)['si_cbm_value'].sum().reset_index()
        si_grouped_qty = self.data[si_mask].groupby(group_column)['si_qty_value'].sum().reset_index()
        si_grouped = si_grouped_cbm.merge(si_grouped_qty, on=group_column, how='outer')
        si_grouped.columns = [group_by, 'outbound_cbm_si', 'outbound_qty_si']
        
        # Merge grouped data
        grouped = so_grouped.merge(si_grouped, on=group_by, how='outer').fillna(0)
        grouped['net_flow_cbm'] = grouped['inbound_cbm'] - grouped['outbound_cbm_si']
        grouped['net_flow_qty'] = grouped['inbound_qty'] - grouped['outbound_qty_si']
        
        return {
            'group_by': group_by,
            'data': grouped.to_dict('records')
        }