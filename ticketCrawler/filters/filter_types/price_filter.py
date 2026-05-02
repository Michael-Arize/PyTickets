# -*- coding: utf-8 -*-
"""Price-based ticket filter."""
from ..base_filter import BaseFilter


class PriceFilter(BaseFilter):
    """Filter tickets by price range."""
    
    def __init__(self, min_price=None, max_price=None):
        """
        Initialize price filter.
        
        Args:
            min_price (float): Minimum acceptable price (None = no minimum)
            max_price (float): Maximum acceptable price (None = no maximum)
        """
        super().__init__({'min_price': min_price, 'max_price': max_price})
        self.min_price = min_price
        self.max_price = max_price
    
    def matches(self, ticket):
        """
        Check if ticket price is within range.
        
        Args:
            ticket (dict): Ticket with 'price' key
            
        Returns:
            bool: True if price is acceptable
        """
        if 'price' not in ticket:
            return True  # If no price data, don't filter out
        
        price = float(ticket['price'])
        
        if self.min_price is not None and price < self.min_price:
            return False
        
        if self.max_price is not None and price > self.max_price:
            return False
        
        return True
    
    def __repr__(self):
        """Return string representation."""
        parts = []
        if self.min_price is not None:
            parts.append(f"min={self.min_price}")
        if self.max_price is not None:
            parts.append(f"max={self.max_price}")
        
        criteria = ', '.join(parts) if parts else 'any'
        return f"PriceFilter({criteria})"
