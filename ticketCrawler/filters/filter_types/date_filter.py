# -*- coding: utf-8 -*-
"""Date-based ticket filter."""
from datetime import datetime
from .base_filter import BaseFilter


class DateFilter(BaseFilter):
    """Filter tickets by event date."""
    
    def __init__(self, start_date=None, end_date=None, date_format='%Y-%m-%d'):
        """
        Initialize date filter.
        
        Args:
            start_date (str or datetime): Earliest acceptable date
            end_date (str or datetime): Latest acceptable date
            date_format (str): Date format string for parsing
        """
        super().__init__({
            'start_date': start_date,
            'end_date': end_date,
            'date_format': date_format
        })
        self.start_date = self._parse_date(start_date, date_format)
        self.end_date = self._parse_date(end_date, date_format)
        self.date_format = date_format
    
    def _parse_date(self, date_val, date_format):
        """Parse date string or return datetime object."""
        if date_val is None:
            return None
        
        if isinstance(date_val, datetime):
            return date_val
        
        return datetime.strptime(date_val, date_format)
    
    def matches(self, ticket):
        """
        Check if ticket event date is within range.
        
        Args:
            ticket (dict): Ticket with 'date' key
            
        Returns:
            bool: True if date is acceptable
        """
        if 'date' not in ticket:
            return True  # If no date data, don't filter out
        
        try:
            ticket_date = self._parse_date(ticket['date'], self.date_format)
        except (ValueError, TypeError):
            return True  # If can't parse date, don't filter out
        
        if self.start_date and ticket_date < self.start_date:
            return False
        
        if self.end_date and ticket_date > self.end_date:
            return False
        
        return True
    
    def __repr__(self):
        """Return string representation."""
        parts = []
        if self.start_date:
            parts.append(f"from={self.start_date.strftime(self.date_format)}")
        if self.end_date:
            parts.append(f"to={self.end_date.strftime(self.date_format)}")
        
        criteria = ', '.join(parts) if parts else 'any'
        return f"DateFilter({criteria})"
