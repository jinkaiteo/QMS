# PDF Report Generator - Phase B Sprint 2 Day 1
# Professional PDF report generation with ReportLab integration

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import Color, HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import io
import base64

class PDFReportGenerator:
    """
    Professional PDF report generation service with charts and formatting
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for professional reports"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=20,
            spaceAfter=30,
            textColor=HexColor('#1976d2'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=18,
            textColor=HexColor('#333333'),
            fontName='Helvetica-Bold',
            borderWidth=1,
            borderColor=HexColor('#e0e0e0'),
            borderPadding=5
        ))
        
        # KPI style
        self.styles.add(ParagraphStyle(
            name='KPIValue',
            fontSize=24,
            alignment=TA_CENTER,
            textColor=HexColor('#4caf50'),
            fontName='Helvetica-Bold',
            spaceAfter=6
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            fontSize=10,
            alignment=TA_CENTER,
            textColor=HexColor('#666666'),
            spaceAfter=20
        ))
    
    def generate_report(self, template_data: Dict[str, Any], 
                       report_data: Dict[str, Any], 
                       output_path: str) -> Dict[str, Any]:
        """
        Generate a PDF report based on template and data
        
        Args:
            template_data: Report template configuration
            report_data: Data to populate the report
            output_path: Output file path
            
        Returns:
            Dict with generation results and metadata
        """
        start_time = datetime.now()
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=template_data.get('page_size', A4),
                rightMargin=template_data.get('margin_right', 72),
                leftMargin=template_data.get('margin_left', 72),
                topMargin=template_data.get('margin_top', 72),
                bottomMargin=template_data.get('margin_bottom', 72)
            )
            
            # Build report content
            story = []
            
            # Add header
            if template_data.get('header'):
                story.extend(self._build_header(template_data['header'], report_data))
            
            # Add title
            if template_data.get('title'):
                story.append(Paragraph(template_data['title'], self.styles['ReportTitle']))
                story.append(Spacer(1, 20))
            
            # Add metadata section
            if template_data.get('show_metadata', True):
                story.extend(self._build_metadata_section(report_data.get('metadata', {})))
            
            # Add executive summary
            if template_data.get('executive_summary'):
                story.extend(self._build_executive_summary(report_data.get('summary', {})))
            
            # Add sections based on template configuration
            for section in template_data.get('sections', []):
                story.extend(self._build_section(section, report_data))
            
            # Add footer
            if template_data.get('footer'):
                story.extend(self._build_footer(template_data['footer'], report_data))
            
            # Generate PDF
            doc.build(story)
            
            # Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Get file size
            import os
            file_size = os.path.getsize(output_path)
            
            return {
                'success': True,
                'file_path': output_path,
                'file_size': file_size,
                'generation_time_ms': int(generation_time),
                'page_count': len(story) // 10,  # Rough estimate
                'format': 'pdf'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'generation_time_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }
    
    def _build_header(self, header_config: Dict, report_data: Dict) -> List:
        """Build report header section"""
        elements = []
        
        # Company logo and information
        if header_config.get('show_logo'):
            # Add logo if available
            elements.append(Spacer(1, 12))
        
        # Report metadata in header
        if header_config.get('show_date'):
            date_text = f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
            elements.append(Paragraph(date_text, self.styles['Normal']))
        
        elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e0e0e0')))
        elements.append(Spacer(1, 20))
        
        return elements
    
    def _build_metadata_section(self, metadata: Dict) -> List:
        """Build metadata information section"""
        elements = []
        
        if not metadata:
            return elements
        
        elements.append(Paragraph("Report Information", self.styles['SectionHeader']))
        
        # Create metadata table
        data = []
        if metadata.get('department'):
            data.append(['Department:', metadata['department']])
        if metadata.get('period'):
            data.append(['Period:', metadata['period']])
        if metadata.get('generated_by'):
            data.append(['Generated by:', metadata['generated_by']])
        
        if data:
            table = Table(data, colWidths=[2*inch, 4*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), HexColor('#f5f5f5')),
                ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#333333')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, HexColor('#e0e0e0'))
            ]))
            elements.append(table)
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _build_executive_summary(self, summary_data: Dict) -> List:
        """Build executive summary section with KPIs"""
        elements = []
        
        if not summary_data:
            return elements
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # KPI grid
        if summary_data.get('kpis'):
            kpi_data = []
            kpis = summary_data['kpis']
            
            # Arrange KPIs in rows of 3
            for i in range(0, len(kpis), 3):
                row = []
                for j in range(3):
                    if i + j < len(kpis):
                        kpi = kpis[i + j]
                        kpi_cell = [
                            Paragraph(f"{kpi['value']}{kpi.get('unit', '')}", self.styles['KPIValue']),
                            Paragraph(kpi['title'], self.styles['Subtitle'])
                        ]
                        row.append(kpi_cell)
                    else:
                        row.append(['', ''])
                kpi_data.append(row)
            
            if kpi_data:
                kpi_table = Table(kpi_data, colWidths=[2*inch, 2*inch, 2*inch])
                kpi_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('GRID', (0, 0), (-1, -1), 1, HexColor('#e0e0e0')),
                    ('BACKGROUND', (0, 0), (-1, -1), HexColor('#fafafa'))
                ]))
                elements.append(kpi_table)
        
        # Summary text
        if summary_data.get('text'):
            elements.append(Spacer(1, 15))
            elements.append(Paragraph(summary_data['text'], self.styles['Normal']))
        
        elements.append(Spacer(1, 20))
        return elements
    
    def _build_section(self, section_config: Dict, report_data: Dict) -> List:
        """Build a report section based on configuration"""
        elements = []
        section_data = report_data.get(section_config['data_key'], {})
        
        # Section title
        if section_config.get('title'):
            elements.append(Paragraph(section_config['title'], self.styles['SectionHeader']))
        
        # Section content based on type
        section_type = section_config.get('type', 'text')
        
        if section_type == 'table':
            elements.extend(self._build_table_section(section_config, section_data))
        elif section_type == 'chart':
            elements.extend(self._build_chart_section(section_config, section_data))
        elif section_type == 'text':
            elements.extend(self._build_text_section(section_config, section_data))
        elif section_type == 'kpi_grid':
            elements.extend(self._build_kpi_grid_section(section_config, section_data))
        
        elements.append(Spacer(1, 15))
        return elements
    
    def _build_table_section(self, config: Dict, data: Dict) -> List:
        """Build a table section"""
        elements = []
        
        if not data.get('rows'):
            elements.append(Paragraph("No data available", self.styles['Normal']))
            return elements
        
        # Prepare table data
        table_data = []
        
        # Add headers if specified
        if config.get('headers'):
            table_data.append(config['headers'])
        
        # Add data rows
        table_data.extend(data['rows'])
        
        # Create table
        table = Table(table_data)
        
        # Apply styling
        style_commands = [
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f9f9f9')),
            ('GRID', (0, 0), (-1, -1), 1, HexColor('#e0e0e0'))
        ]
        
        table.setStyle(TableStyle(style_commands))
        elements.append(table)
        
        return elements
    
    def _build_chart_section(self, config: Dict, data: Dict) -> List:
        """Build a chart section"""
        elements = []
        
        # For now, add placeholder for chart
        # In production, this would generate actual charts using reportlab graphics
        chart_type = config.get('chart_type', 'line')
        elements.append(Paragraph(f"[{chart_type.title()} Chart - Data visualization]", self.styles['Normal']))
        
        # Add chart data summary
        if data.get('summary'):
            elements.append(Spacer(1, 10))
            elements.append(Paragraph(data['summary'], self.styles['Normal']))
        
        return elements
    
    def _build_text_section(self, config: Dict, data: Dict) -> List:
        """Build a text section"""
        elements = []
        
        if data.get('content'):
            elements.append(Paragraph(data['content'], self.styles['Normal']))
        
        return elements
    
    def _build_kpi_grid_section(self, config: Dict, data: Dict) -> List:
        """Build a KPI grid section"""
        elements = []
        
        if not data.get('kpis'):
            return elements
        
        # Similar to executive summary KPIs but with section-specific styling
        return self._build_executive_summary(data)
    
    def _build_footer(self, footer_config: Dict, report_data: Dict) -> List:
        """Build report footer"""
        elements = []
        
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(width="100%", thickness=1, color=HexColor('#e0e0e0')))
        
        # Footer text
        footer_text = footer_config.get('text', 'QMS Analytics Report')
        elements.append(Paragraph(footer_text, self.styles['Normal']))
        
        # Page numbers and timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        elements.append(Paragraph(f"Generated on {timestamp}", self.styles['Normal']))
        
        return elements