import pandas as pd
import io
from typing import Dict, List, Any, Optional
from fuzzywuzzy import fuzz
import re
from datetime import datetime

class ExcelParser:
    """Parse Excel files and detect required columns"""
    
    def __init__(self):
        self.required_columns = {
            'so_date': ['so date', 'sales order date', 'order date'],
            'so_total_cbm': ['so total cbm', 'sales order total cbm', 'total cbm', 'so cbm'],
            'si_date': ['sales invoice date', 'si date', 'invoice date'],
            'si_total_cbm': ['si total cbm', 'sales invoice total cbm', 'invoice cbm', 'si cbm'],
            'per_unit_cbm': ['per unit cbm', 'unit cbm', 'cbm per unit'],
            'so_qty': ['sales order qty', 'so qty', 'order qty', 'quantity'],
            'si_qty': ['sales invoice qty', 'si qty', 'invoice qty']
        }
    
    def normalize_column_name(self, name: str) -> str:
        """Normalize column name for matching"""
        if pd.isna(name):
            return ""
        return re.sub(r'[^a-z0-9]', '', str(name).lower())
    
    def find_column_match(self, columns: List[str], target_patterns: List[str]) -> Optional[str]:
        """Find best matching column using fuzzy matching"""
        normalized_columns = {self.normalize_column_name(col): col for col in columns}
        
        # Try exact match first
        for pattern in target_patterns:
            normalized_pattern = self.normalize_column_name(pattern)
            if normalized_pattern in normalized_columns:
                return normalized_columns[normalized_pattern]
        
        # Try fuzzy matching
        best_match = None
        best_score = 0
        
        for pattern in target_patterns:
            for norm_col, orig_col in normalized_columns.items():
                score = fuzz.ratio(self.normalize_column_name(pattern), norm_col)
                if score > best_score and score >= 80:  # 80% similarity threshold
                    best_score = score
                    best_match = orig_col
        
        return best_match
    
    def parse_dates(self, df: pd.DataFrame, date_column: str) -> pd.Series:
        """Parse dates with multiple fallback strategies"""
        if date_column not in df.columns:
            return pd.Series(dtype='datetime64[ns]')
        
        # Try pandas to_datetime with dayfirst=True
        dates = pd.to_datetime(df[date_column], errors='coerce', dayfirst=True)
        
        # If many NaT values, try without dayfirst
        if dates.isna().sum() > len(dates) * 0.5:
            dates = pd.to_datetime(df[date_column], errors='coerce', dayfirst=False)
        
        # Handle Excel serial dates
        mask = dates.isna() & df[date_column].notna()
        if mask.any():
            try:
                excel_dates = pd.to_datetime('1899-12-30') + pd.to_timedelta(df.loc[mask, date_column], 'D')
                dates.loc[mask] = excel_dates
            except:
                pass
        
        return dates
    
    def parse_excel(self, content: bytes) -> Dict[str, Any]:
        """Parse Excel file and return structured data"""
        
        try:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(content))
            
            if df.empty:
                raise ValueError("Excel file is empty")
            
            # Detect columns
            columns = list(df.columns)
            detected_columns = {}
            
            # Find required columns
            so_date_col = self.find_column_match(columns, self.required_columns['so_date'])
            so_cbm_col = self.find_column_match(columns, self.required_columns['so_total_cbm'])
            si_date_col = self.find_column_match(columns, self.required_columns['si_date'])
            si_cbm_col = self.find_column_match(columns, self.required_columns['si_total_cbm'])
            
            # Check for required columns
            if not so_date_col:
                raise ValueError("SO Date column not found. Required for inbound analysis.")
            if not so_cbm_col:
                # Try fallback with per unit CBM and quantity
                per_unit_col = self.find_column_match(columns, self.required_columns['per_unit_cbm'])
                so_qty_col = self.find_column_match(columns, self.required_columns['so_qty'])
                if not (per_unit_col and so_qty_col):
                    raise ValueError("SO Total CBM column not found and cannot compute from Per Unit CBM * Qty")
                detected_columns['so_cbm_computed'] = True
            
            if not si_date_col:
                raise ValueError("Sales Invoice Date column not found. Required for outbound analysis.")
            
            detected_columns.update({
                'so_date': so_date_col,
                'so_total_cbm': so_cbm_col,
                'si_date': si_date_col,
                'si_total_cbm': si_cbm_col
            })
            
            # Parse dates
            df['so_date_parsed'] = self.parse_dates(df, so_date_col)
            df['si_date_parsed'] = self.parse_dates(df, si_date_col)
            
            # Find quantity columns
            so_qty_col = self.find_column_match(columns, self.required_columns['so_qty'])
            si_qty_col = self.find_column_match(columns, self.required_columns['si_qty'])
            
            detected_columns.update({
                'so_qty': so_qty_col,
                'si_qty': si_qty_col
            })
            
            # Handle CBM calculations
            if so_cbm_col:
                df['so_cbm_value'] = pd.to_numeric(df[so_cbm_col], errors='coerce')
            else:
                # Compute from per unit CBM * quantity
                per_unit_col = self.find_column_match(columns, self.required_columns['per_unit_cbm'])
                if per_unit_col and so_qty_col:
                    df['so_cbm_value'] = (
                        pd.to_numeric(df[per_unit_col], errors='coerce') * 
                        pd.to_numeric(df[so_qty_col], errors='coerce')
                    )
                    detected_columns['so_cbm_computed'] = True
                else:
                    raise ValueError("SO Total CBM column not found and cannot compute from Per Unit CBM * Qty")
            
            if si_cbm_col:
                df['si_cbm_value'] = pd.to_numeric(df[si_cbm_col], errors='coerce')
            else:
                # Try fallback computation
                per_unit_col = self.find_column_match(columns, self.required_columns['per_unit_cbm'])
                if per_unit_col and si_qty_col:
                    df['si_cbm_value'] = (
                        pd.to_numeric(df[per_unit_col], errors='coerce') * 
                        pd.to_numeric(df[si_qty_col], errors='coerce')
                    )
                    detected_columns['si_cbm_computed'] = True
                else:
                    df['si_cbm_value'] = 0
            
            # Handle quantity values
            if so_qty_col:
                df['so_qty_value'] = pd.to_numeric(df[so_qty_col], errors='coerce')
            else:
                df['so_qty_value'] = 0
                
            if si_qty_col:
                df['si_qty_value'] = pd.to_numeric(df[si_qty_col], errors='coerce')
            else:
                df['si_qty_value'] = 0
            
            # Filter out rows with invalid dates or values
            valid_so = df['so_date_parsed'].notna() & df['so_cbm_value'].notna() & df['so_qty_value'].notna()
            valid_si = df['si_date_parsed'].notna() & df['si_cbm_value'].notna() & df['si_qty_value'].notna()
            
            # Determine date range
            all_dates = pd.concat([
                df.loc[valid_so, 'so_date_parsed'],
                df.loc[valid_si, 'si_date_parsed']
            ]).dropna()
            
            date_range = {
                'min_date': all_dates.min().strftime('%Y-%m-%d') if not all_dates.empty else None,
                'max_date': all_dates.max().strftime('%Y-%m-%d') if not all_dates.empty else None
            }
            
            # Sample rows for preview
            sample_rows = df.head(5).fillna('').to_dict('records')
            
            return {
                'data': df,
                'columns': detected_columns,
                'date_range': date_range,
                'sample_rows': sample_rows
            }
            
        except Exception as e:
            raise ValueError(f"Error parsing Excel file: {str(e)}")