# -*- coding: utf-8 -*-
"""Combined filter applying multiple filters."""
from .base_filter import BaseFilter


class CombinedFilter(BaseFilter):
    """Apply multiple filters to tickets."""
    
    def __init__(self, filters=None, require_all=True):
        """
        Initialize combined filter.
        
        Args:
            filters (list): List of filter objects to combine
            require_all (bool): If True, ALL filters must match. 
                               If False, ANY filter can match.
        """
        super().__init__({'filters': filters, 'require_all': require_all})
        self.filters = filters or []
        self.require_all = require_all
    
    def add_filter(self, filter_obj):
        """
        Add a filter to the combination.
        
        Args:
            filter_obj: Filter object to add
        """
        self.filters.append(filter_obj)
    
    def remove_filter(self, filter_obj):
        """
        Remove a filter from the combination.
        
        Args:
            filter_obj: Filter object to remove
        """
        if filter_obj in self.filters:
            self.filters.remove(filter_obj)
    
    def matches(self, ticket):
        """
        Apply all filters to ticket.
        
        Args:
            ticket (dict): Ticket data to filter
            
        Returns:
            bool: True if ticket passes filter criteria
        """
        if not self.filters:
            return True  # No filters = accept all
        
        if self.require_all:
            # ALL filters must match
            return all(f.matches(ticket) for f in self.filters)
        else:
            # ANY filter can match
            return any(f.matches(ticket) for f in self.filters)
    
    def filter_tickets(self, tickets):
        """
        Apply filters to a list of tickets.
        
        Args:
            tickets (list): List of ticket dictionaries
            
        Returns:
            list: Filtered list of tickets
        """
        return [t for t in tickets if self.matches(t)]
    
    def __repr__(self):
        """Return string representation."""
        if not self.filters:
            return "CombinedFilter(empty)"
        
        mode = "ALL" if self.require_all else "ANY"
        filter_strs = [repr(f) for f in self.filters]
        return f"CombinedFilter({mode}): [{', '.join(filter_strs)}]"
