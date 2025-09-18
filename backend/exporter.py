import csv
import io
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime

class CSVExporter:
    """Export data to CSV format"""
    
    def export(self, daily_data: List[Dict[str, Any]]) -> str:
        """Export daily data to CSV string"""
        
        output = io.StringIO()
        
        if not daily_data:
            return ""
        
        # Get field names from first record
        fieldnames = list(daily_data[0].keys())
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in daily_data:
            # Round numeric values for cleaner output
            clean_row = {}
            for key, value in row.items():
                if isinstance(value, (int, float)) and key != 'date':
                    clean_row[key] = round(value, 6)
                else:
                    clean_row[key] = value
            writer.writerow(clean_row)
        
        return output.getvalue()

class PDFExporter:
    """Export data to PDF format"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
    def export(self, analysis_result: Dict[str, Any]) -> bytes:
        """Export analysis result to PDF"""
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        
        # Title
        title = Paragraph("CBM Analysis Report", self.title_style)
        story.append(title)
        story.append(Spacer(1, 20))
        
        # Summary section
        story.append(Paragraph("Summary", self.styles['Heading2']))
        
        totals = analysis_result.get('totals', {})
        kpis = analysis_result.get('kpis', {})
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Inbound CBM', f"{totals.get('total_inbound_cbm', 0):.6f}"],
            ['Total Outbound CBM (SI)', f"{totals.get('total_outbound_cbm_si', 0):.6f}"],
            ['Total Net Flow CBM', f"{totals.get('total_net_flow_cbm', 0):.6f}"],
            ['Total Inbound Quantity', f"{totals.get('total_inbound_qty', 0):.0f}"],
            ['Total Outbound Quantity (SI)', f"{totals.get('total_outbound_qty_si', 0):.0f}"],
            ['Total Net Flow Quantity', f"{totals.get('total_net_flow_qty', 0):.0f}"],
            ['Average Daily Net Flow CBM', f"{kpis.get('avg_daily_net_flow_cbm', 0):.6f}"],
            ['Average Daily Net Flow Quantity', f"{kpis.get('avg_daily_net_flow_qty', 0):.0f}"]
        ]
        
        # Add peak days if available
        peak_inbound_cbm = kpis.get('peak_inbound_cbm_day', {})
        if peak_inbound_cbm.get('date'):
            summary_data.append([
                'Peak Inbound CBM Day', 
                f"{peak_inbound_cbm['date']} ({peak_inbound_cbm.get('value', 0):.6f} CBM)"
            ])
        
        peak_outbound_cbm = kpis.get('peak_outbound_cbm_day', {})
        if peak_outbound_cbm.get('date'):
            summary_data.append([
                'Peak Outbound CBM Day (SI)', 
                f"{peak_outbound_cbm['date']} ({peak_outbound_cbm.get('value', 0):.6f} CBM)"
            ])
            
        peak_inbound_qty = kpis.get('peak_inbound_qty_day', {})
        if peak_inbound_qty.get('date'):
            summary_data.append([
                'Peak Inbound Quantity Day', 
                f"{peak_inbound_qty['date']} ({peak_inbound_qty.get('value', 0):.0f} units)"
            ])
        
        peak_outbound_qty = kpis.get('peak_outbound_qty_day', {})
        if peak_outbound_qty.get('date'):
            summary_data.append([
                'Peak Outbound Quantity Day (SI)', 
                f"{peak_outbound_qty['date']} ({peak_outbound_qty.get('value', 0):.0f} units)"
            ])
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Daily data section
        story.append(Paragraph("Daily Data", self.styles['Heading2']))
        
        daily_data = analysis_result.get('daily', [])
        if daily_data:
            # Limit to first 20 rows for PDF readability
            display_data = daily_data[:20]
            
            table_data = [['Date', 'Inbound CBM', 'Outbound CBM (SI)', 'Net Flow CBM', 'Inbound Qty', 'Outbound Qty (SI)', 'Net Flow Qty']]
            
            for row in display_data:
                table_data.append([
                    row.get('date', ''),
                    f"{row.get('inbound_cbm', 0):.6f}",
                    f"{row.get('outbound_cbm_si', 0):.6f}",
                    f"{row.get('net_flow_cbm', 0):.6f}",
                    f"{row.get('inbound_qty', 0):.0f}",
                    f"{row.get('outbound_qty_si', 0):.0f}",
                    f"{row.get('net_flow_qty', 0):.0f}"
                ])
            
            daily_table = Table(table_data)
            daily_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(daily_table)
            
            if len(daily_data) > 20:
                story.append(Spacer(1, 12))
                story.append(Paragraph(
                    f"Note: Showing first 20 rows of {len(daily_data)} total rows. "
                    "Download CSV for complete data.",
                    self.styles['Normal']
                ))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            self.styles['Normal']
        ))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()