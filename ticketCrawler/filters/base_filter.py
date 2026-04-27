# -*- coding: utf-8 -*-
"""Base filter class."""
from abc import ABC, abstractmethod


class BaseFilter(ABC):
    """Abstract base class for ticket filters."""
    
    def __init__(self, config=None):
        """
        Initialize filter.
        
        Args:
            config (dict): Filter configuration
        """
        self.config = config or {}
    
    @abstractmethod
    def matches(self, ticket):
        """
        Check if ticket matches filter criteria.
        
        Args:
            ticket (dict): Ticket data with keys like 'price', 'seat_type', 'date', etc.
            
        Returns:
            bool: True if ticket matches, False otherwise
        """
        pass
    
    @abstractmethod
    def __repr__(self):
        """Return string representation of filter."""
        pass
