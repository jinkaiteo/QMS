# Chart Generation Service - Phase B Sprint 2 Day 2
# Professional chart generation for PDF and Excel reports

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.textlabels import Label

from openpyxl.chart import LineChart, BarChart, PieChart, Reference, Series
from openpyxl.chart.axis import DateAxis, ValuesAxis
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.legend import Legend as ExcelLegend

from typing import Dict, List, Any, Optional, Union, Tuple
import io
import base64
from datetime import datetime

class ChartConfiguration:
    """Configuration class for chart generation"""
    
    def __init__(self, 
                 chart_type: str,
                 title: str,
                 width: int = 400,
                 height: int = 300,
                 x_axis_title: str = "",
                 y_axis_title: str = "",
                 colors: List[str] = None,
                 show_legend: bool = True,
                 show_values: bool = False):
        self.chart_type = chart_type
        self.title = title
        self.width = width
        self.height = height
        self.x_axis_title = x_axis_title
        self.y_axis_title = y_axis_title
        self.colors = colors or self._get_default_colors()
        self.show_legend = show_legend
        self.show_values = show_values
    
    def _get_default_colors(self) -> List[str]:
        """Get default color palette"""
        return [
            '#1976d2', '#388e3c', '#f57c00', '#d32f2f',
            '#7b1fa2', '#0288d1', '#689f38', '#fbc02d',
            '#c2185b', '#5d4037', '#455a64', '#e64a19'
        ]

class PDFChartGenerator:
    """Generate charts for PDF reports using ReportLab graphics"""
    
    def __init__(self):
        self.default_width = 4 * inch
        self.default_height = 3 * inch
    
    def generate_chart(self, 
                      config: ChartConfiguration,
                      data: Dict[str, Any]) -> Drawing:
        """
        Generate a chart for PDF inclusion
        
        Args:
            config: Chart configuration
            data: Chart data with labels and datasets
            
        Returns:
            ReportLab Drawing object
        """
        if config.chart_type == 'line':
            return self._create_line_chart(config, data)
        elif config.chart_type == 'bar':
            return self._create_bar_chart(config, data)
        elif config.chart_type == 'pie':
            return self._create_pie_chart(config, data)
        else:
            return self._create_placeholder_chart(config)
    
    def _create_line_chart(self, config: ChartConfiguration, data: Dict[str, Any]) -> Drawing:
        """Create a line chart for PDF"""
        drawing = Drawing(config.width, config.height)
        
        chart = HorizontalLineChart()
        chart.x = 50
        chart.y = 50
        chart.width = config.width - 100
        chart.height = config.height - 100
        
        # Set data
        labels = data.get('labels', [])
        datasets = data.get('datasets', [])
        
        if datasets:
            chart_data = []
            for dataset in datasets:
                chart_data.append(dataset.get('data', []))
            
            chart.data = chart_data
            chart.categoryAxis.categoryNames = labels
            
            # Styling
            chart.lines[0].strokeColor = colors.toColor(config.colors[0])
            chart.lines[0].strokeWidth = 2
            
            # Axes
            chart.categoryAxis.title = config.x_axis_title
            chart.valueAxis.title = config.y_axis_title
            
            # Legend
            if config.show_legend and len(datasets) > 1:
                legend = Legend()
                legend.x = config.width - 150
                legend.y = config.height - 50
                legend.columnMaximum = 1
                items = []
                for i, dataset in enumerate(datasets):
                    items.append((config.colors[i % len(config.colors)], dataset.get('label', f'Series {i+1}')))
                legend.colorNamePairs = items
                drawing.add(legend)
        
        # Title
        if config.title:
            title = Label()
            title.setText(config.title)
            title.x = config.width / 2
            title.y = config.height - 25
            title.textAnchor = 'middle'
            title.fontName = 'Helvetica-Bold'
            title.fontSize = 12
            drawing.add(title)
        
        drawing.add(chart)
        return drawing
    
    def _create_bar_chart(self, config: ChartConfiguration, data: Dict[str, Any]) -> Drawing:
        """Create a bar chart for PDF"""
        drawing = Drawing(config.width, config.height)
        
        chart = VerticalBarChart()
        chart.x = 50
        chart.y = 50
        chart.width = config.width - 100
        chart.height = config.height - 100
        
        # Set data
        labels = data.get('labels', [])
        datasets = data.get('datasets', [])
        
        if datasets:
            chart_data = []
            for dataset in datasets:
                chart_data.append(dataset.get('data', []))
            
            chart.data = chart_data
            chart.categoryAxis.categoryNames = labels
            
            # Styling
            for i, dataset in enumerate(datasets):
                color_index = i % len(config.colors)
                chart.bars[i].fillColor = colors.toColor(config.colors[color_index])
            
            # Axes
            chart.categoryAxis.title = config.x_axis_title
            chart.valueAxis.title = config.y_axis_title
            
            # Show values on bars
            if config.show_values:
                chart.barLabels.visible = 1
                chart.barLabels.fontSize = 8
        
        # Title
        if config.title:
            title = Label()
            title.setText(config.title)
            title.x = config.width / 2
            title.y = config.height - 25
            title.textAnchor = 'middle'
            title.fontName = 'Helvetica-Bold'
            title.fontSize = 12
            drawing.add(title)
        
        drawing.add(chart)
        return drawing
    
    def _create_pie_chart(self, config: ChartConfiguration, data: Dict[str, Any]) -> Drawing:
        """Create a pie chart for PDF"""
        drawing = Drawing(config.width, config.height)
        
        chart = Pie()
        chart.x = 50
        chart.y = 50
        chart.width = min(config.width, config.height) - 100
        chart.height = chart.width
        
        # Set data
        labels = data.get('labels', [])
        datasets = data.get('datasets', [])
        
        if datasets and len(datasets) > 0:
            pie_data = datasets[0].get('data', [])
            chart.data = pie_data
            
            # Colors
            chart.slices.strokeColor = colors.white
            chart.slices.strokeWidth = 1
            
            for i, value in enumerate(pie_data):
                color_index = i % len(config.colors)
                chart.slices[i].fillColor = colors.toColor(config.colors[color_index])
                if config.show_values:
                    chart.slices[i].labelRadius = 1.2
                    chart.slices[i].fontName = 'Helvetica'
                    chart.slices[i].fontSize = 8
            
            # Legend
            if config.show_legend:
                legend = Legend()
                legend.x = config.width - 150
                legend.y = config.height / 2
                legend.columnMaximum = len(labels)
                items = []
                for i, label in enumerate(labels):
                    color_index = i % len(config.colors)
                    items.append((config.colors[color_index], label))
                legend.colorNamePairs = items
                drawing.add(legend)
        
        # Title
        if config.title:
            title = Label()
            title.setText(config.title)
            title.x = config.width / 2
            title.y = config.height - 25
            title.textAnchor = 'middle'
            title.fontName = 'Helvetica-Bold'
            title.fontSize = 12
            drawing.add(title)
        
        drawing.add(chart)
        return drawing
    
    def _create_placeholder_chart(self, config: ChartConfiguration) -> Drawing:
        """Create a placeholder chart for unsupported types"""
        drawing = Drawing(config.width, config.height)
        
        # Add placeholder text
        title = Label()
        title.setText(f"{config.title}\n[{config.chart_type.title()} Chart]")
        title.x = config.width / 2
        title.y = config.height / 2
        title.textAnchor = 'middle'
        title.fontName = 'Helvetica'
        title.fontSize = 14
        drawing.add(title)
        
        return drawing

class ExcelChartGenerator:
    """Generate charts for Excel reports using OpenPyXL"""
    
    def add_chart_to_worksheet(self, 
                              worksheet,
                              config: ChartConfiguration,
                              data: Dict[str, Any],
                              data_range: str,
                              position: str = "A1") -> bool:
        """
        Add a chart to an Excel worksheet
        
        Args:
            worksheet: OpenPyXL worksheet object
            config: Chart configuration
            data: Chart data
            data_range: Excel range containing the data
            position: Cell position for chart placement
            
        Returns:
            Success status
        """
        try:
            if config.chart_type == 'line':
                chart = self._create_excel_line_chart(config, data, data_range, worksheet)
            elif config.chart_type == 'bar':
                chart = self._create_excel_bar_chart(config, data, data_range, worksheet)
            elif config.chart_type == 'pie':
                chart = self._create_excel_pie_chart(config, data, data_range, worksheet)
            else:
                return False
            
            # Add chart to worksheet
            worksheet.add_chart(chart, position)
            return True
            
        except Exception as e:
            print(f"Error adding chart to Excel: {e}")
            return False
    
    def _create_excel_line_chart(self, config: ChartConfiguration, data: Dict[str, Any], 
                                data_range: str, worksheet) -> LineChart:
        """Create a line chart for Excel"""
        chart = LineChart()
        chart.title = config.title
        chart.style = 10
        chart.x_axis.title = config.x_axis_title
        chart.y_axis.title = config.y_axis_title
        chart.width = config.width / 10  # Convert pixels to Excel units
        chart.height = config.height / 10
        
        # Add data series
        datasets = data.get('datasets', [])
        labels = data.get('labels', [])
        
        if datasets:
            # Assuming data is arranged with labels in first column, data in subsequent columns
            data_ref = Reference(worksheet, min_col=2, min_row=1, max_col=1+len(datasets), max_row=len(labels)+1)
            cats_ref = Reference(worksheet, min_col=1, min_row=2, max_row=len(labels)+1)
            
            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats_ref)
            
            # Apply colors
            for i, series in enumerate(chart.series):
                if i < len(config.colors):
                    # Note: OpenPyXL color setting is more complex and may require RGB conversion
                    pass
        
        if not config.show_legend:
            chart.legend = None
        
        return chart
    
    def _create_excel_bar_chart(self, config: ChartConfiguration, data: Dict[str, Any],
                               data_range: str, worksheet) -> BarChart:
        """Create a bar chart for Excel"""
        chart = BarChart()
        chart.type = "col"  # Column chart
        chart.title = config.title
        chart.style = 10
        chart.x_axis.title = config.x_axis_title
        chart.y_axis.title = config.y_axis_title
        chart.width = config.width / 10
        chart.height = config.height / 10
        
        # Add data series
        datasets = data.get('datasets', [])
        labels = data.get('labels', [])
        
        if datasets:
            data_ref = Reference(worksheet, min_col=2, min_row=1, max_col=1+len(datasets), max_row=len(labels)+1)
            cats_ref = Reference(worksheet, min_col=1, min_row=2, max_row=len(labels)+1)
            
            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats_ref)
        
        if not config.show_legend:
            chart.legend = None
        
        return chart
    
    def _create_excel_pie_chart(self, config: ChartConfiguration, data: Dict[str, Any],
                               data_range: str, worksheet) -> PieChart:
        """Create a pie chart for Excel"""
        chart = PieChart()
        chart.title = config.title
        chart.width = config.width / 10
        chart.height = config.height / 10
        
        # Add data series
        datasets = data.get('datasets', [])
        labels = data.get('labels', [])
        
        if datasets and len(datasets) > 0:
            # For pie charts, we use the first dataset
            data_ref = Reference(worksheet, min_col=2, min_row=2, max_row=len(labels)+1)
            cats_ref = Reference(worksheet, min_col=1, min_row=2, max_row=len(labels)+1)
            
            chart.add_data(data_ref)
            chart.set_categories(cats_ref)
        
        if not config.show_legend:
            chart.legend = None
        
        return chart

class ChartDataProcessor:
    """Process and validate chart data"""
    
    @staticmethod
    def process_chart_data(raw_data: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
        """
        Process raw data into chart-ready format
        
        Args:
            raw_data: Raw data from aggregation service
            chart_type: Type of chart to generate
            
        Returns:
            Processed chart data
        """
        if chart_type in ['line', 'bar']:
            return ChartDataProcessor._process_xy_data(raw_data)
        elif chart_type == 'pie':
            return ChartDataProcessor._process_pie_data(raw_data)
        else:
            return {'labels': [], 'datasets': []}
    
    @staticmethod
    def _process_xy_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for line and bar charts"""
        # Extract time series or categorical data
        if 'trend_data' in raw_data:
            trend_data = raw_data['trend_data']
            labels = [item.get('period', '') for item in trend_data]
            datasets = [{
                'label': 'Values',
                'data': [item.get('average_value', 0) for item in trend_data]
            }]
        elif 'departments' in raw_data:
            departments = raw_data['departments']
            labels = [dept.get('name', '') for dept in departments]
            datasets = [{
                'label': 'Performance Score',
                'data': [dept.get('performance_score', 0) for dept in departments]
            }]
        else:
            # Fallback to KPI data
            kpis = raw_data.get('kpis', [])
            labels = [kpi.get('name', '') for kpi in kpis[:6]]
            datasets = [{
                'label': 'Values',
                'data': [kpi.get('value', 0) for kpi in kpis[:6]]
            }]
        
        return {'labels': labels, 'datasets': datasets}
    
    @staticmethod
    def _process_pie_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for pie charts"""
        # Look for status distribution or categorical breakdown
        if 'status_distribution' in raw_data:
            status_data = raw_data['status_distribution']
            labels = list(status_data.keys())
            data = list(status_data.values())
        elif 'compliance_breakdown' in raw_data:
            compliance_data = raw_data['compliance_breakdown']
            labels = list(compliance_data.keys())
            data = list(compliance_data.values())
        else:
            # Use top departments or categories
            kpis = raw_data.get('kpis', [])[:5]  # Top 5 for pie chart
            labels = [kpi.get('name', '') for kpi in kpis]
            data = [kpi.get('value', 0) for kpi in kpis]
        
        return {
            'labels': labels,
            'datasets': [{'data': data}]
        }
    
    @staticmethod
    def validate_chart_data(data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate chart data structure
        
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, "Chart data must be a dictionary"
        
        if 'labels' not in data:
            return False, "Chart data must include 'labels'"
        
        if 'datasets' not in data:
            return False, "Chart data must include 'datasets'"
        
        labels = data['labels']
        datasets = data['datasets']
        
        if not isinstance(labels, list):
            return False, "'labels' must be a list"
        
        if not isinstance(datasets, list):
            return False, "'datasets' must be a list"
        
        if len(datasets) == 0:
            return False, "At least one dataset is required"
        
        # Validate each dataset
        for i, dataset in enumerate(datasets):
            if not isinstance(dataset, dict):
                return False, f"Dataset {i} must be a dictionary"
            
            if 'data' not in dataset:
                return False, f"Dataset {i} must include 'data'"
            
            if not isinstance(dataset['data'], list):
                return False, f"Dataset {i} 'data' must be a list"
            
            if len(dataset['data']) != len(labels):
                return False, f"Dataset {i} data length ({len(dataset['data'])}) must match labels length ({len(labels)})"
        
        return True, "Chart data is valid"