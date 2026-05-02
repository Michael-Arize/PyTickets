# -*- coding: utf-8 -*-
"""Seat type-based ticket filter."""
from ..base_filter import BaseFilter


class SeatTypeFilter(BaseFilter):
    """Filter tickets by seat type/location."""
    
    def __init__(self, seat_types=None, exclude_seat_types=None):
        """
        Initialize seat type filter.
        
        Args:
            seat_types (list): Accepted seat types (e.g., ['floor', 'vip'])
                              If None, all types accepted
            exclude_seat_types (list): Seat types to exclude
        """
        super().__init__({
            'seat_types': seat_types,
            'exclude_seat_types': exclude_seat_types
        })
        self.seat_types = seat_types or []
        self.exclude_seat_types = exclude_seat_types or []
    
    def matches(self, ticket):
        """
        Check if ticket seat type is acceptable.
        
        Args:
            ticket (dict): Ticket with 'seat_type' key
            
        Returns:
            bool: True if seat type is acceptable
        """
        if 'seat_type' not in ticket:
            return True  # If no seat type data, don't filter out
        
        seat_type = str(ticket['seat_type']).lower()
        
        # Check exclusions first
        for excluded in self.exclude_seat_types:
            if excluded.lower() in seat_type:
                return False
        
        # If specific types requested, check if ticket matches
        if self.seat_types:
            for accepted in self.seat_types:
                if accepted.lower() in seat_type:
                    return True
            return False
        
        return True
    
    def __repr__(self):
        """Return string representation."""
        parts = []
        if self.seat_types:
            parts.append(f"allowed={self.seat_types}")
        if self.exclude_seat_types:
            parts.append(f"excluded={self.exclude_seat_types}")
        
        criteria = ', '.join(parts) if parts else 'any'
        return f"SeatTypeFilter({criteria})"
