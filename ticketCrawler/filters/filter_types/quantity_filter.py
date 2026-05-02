# -*- coding: utf-8 -*-
"""Quantity-based ticket filter."""
from ..base_filter import BaseFilter


class QuantityFilter(BaseFilter):
    """Filter tickets by quantity available."""
    
    def __init__(self, min_quantity=None, max_quantity=None):
        """
        Initialize quantity filter.
        
        Args:
            min_quantity (int): Minimum quantity to accept
            max_quantity (int): Maximum quantity to accept
        """
        super().__init__({
            'min_quantity': min_quantity,
            'max_quantity': max_quantity
        })
        self.min_quantity = min_quantity
        self.max_quantity = max_quantity
    
    def matches(self, ticket):
        """
        Check if ticket quantity is acceptable.
        
        Args:
            ticket (dict): Ticket with 'quantity' key
            
        Returns:
            bool: True if quantity is acceptable
        """
        if 'quantity' not in ticket:
            return True  # If no quantity data, don't filter out
        
        try:
            quantity = int(ticket['quantity'])
        except (ValueError, TypeError):
            return True  # If can't parse quantity, don't filter out
        
        if self.min_quantity is not None and quantity < self.min_quantity:
            return False
        
        if self.max_quantity is not None and quantity > self.max_quantity:
            return False
        
        return True
    
    def __repr__(self):
        """Return string representation."""
        parts = []
        if self.min_quantity is not None:
            parts.append(f"min={self.min_quantity}")
        if self.max_quantity is not None:
            parts.append(f"max={self.max_quantity}")
        
        criteria = ', '.join(parts) if parts else 'any'
        return f"QuantityFilter({criteria})"
