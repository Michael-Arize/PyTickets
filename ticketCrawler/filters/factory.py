# -*- coding: utf-8 -*-
"""Factory for creating filters."""
from .filter_types.price_filter import PriceFilter
from .filter_types.seat_filter import SeatTypeFilter
from .filter_types.date_filter import DateFilter
from .filter_types.quantity_filter import QuantityFilter
from .combined_filter import CombinedFilter


class FilterFactory:
    """Factory for creating ticket filters."""
    
    FILTERS = {
        'price': PriceFilter,
        'seat_type': SeatTypeFilter,
        'date': DateFilter,
        'quantity': QuantityFilter,
    }
    
    @classmethod
    def create_filter(cls, filter_type, **kwargs):
        """
        Create a filter instance.
        
        Args:
            filter_type (str): Type of filter
            **kwargs: Arguments to pass to filter constructor
            
        Returns:
            BaseFilter: Filter instance
            
        Raises:
            ValueError: If filter type not found
        """
        if filter_type not in cls.FILTERS:
            available = ', '.join(cls.FILTERS.keys())
            raise ValueError(f"Unknown filter type: {filter_type}. Available: {available}")
        
        filter_class = cls.FILTERS[filter_type]
        return filter_class(**kwargs)
    
    @classmethod
    def create_combined_filter(cls, filters_config, require_all=True):
        """
        Create a combined filter from configuration.
        
        Args:
            filters_config (list): List of filter configs
                E.g., [
                    {'type': 'price', 'min_price': 10, 'max_price': 50},
                    {'type': 'seat_type', 'seat_types': ['floor', 'vip']}
                ]
            require_all (bool): If True, all filters must match
            
        Returns:
            CombinedFilter: Combined filter instance
        """
        combined = CombinedFilter(require_all=require_all)
        
        for filter_config in filters_config:
            filter_type = filter_config.pop('type', None)
            if not filter_type:
                continue
            
            filter_obj = cls.create_filter(filter_type, **filter_config)
            combined.add_filter(filter_obj)
        
        return combined
    
    @classmethod
    def register_filter(cls, filter_type, filter_class):
        """
        Register a new filter type.
        
        Args:
            filter_type (str): Type name
            filter_class: Filter class (must inherit from BaseFilter)
        """
        cls.FILTERS[filter_type] = filter_class
    
    @classmethod
    def list_filters(cls):
        """List all available filter types."""
        return list(cls.FILTERS.keys())
