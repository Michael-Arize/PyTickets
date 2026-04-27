# -*- coding: utf-8 -*-
"""Base adapter class for site implementations."""
from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """Abstract base class for ticket site adapters."""
    
    def __init__(self, config):
        """
        Initialize the adapter with a site configuration.
        
        Args:
            config (dict): Site configuration from ConfigLoader
        """
        self.config = config
        self.base_url = config.get('base_url')
    
    @abstractmethod
    def authenticate(self, browser):
        """
        Authenticate with the ticket site.
        
        Args:
            browser: Selenium WebDriver instance
            
        Raises:
            Exception: If authentication fails
        """
        pass
    
    @abstractmethod
    def check_tickets_available(self, response):
        """
        Check if tickets are available on the page.
        
        Args:
            response: Scrapy response object
            
        Returns:
            bool: True if tickets available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_first_sold_ticket_url(self, response):
        """
        Extract URL of first sold ticket listing.
        
        Args:
            response: Scrapy response object
            
        Returns:
            str: URL of first sold ticket or None if not found
        """
        pass
    
    @abstractmethod
    def extract_tickets(self, response):
        """
        Extract ticket elements from response.
        
        Args:
            response: Scrapy response object
            
        Returns:
            list: List of ticket elements
        """
        pass
    
    @abstractmethod
    def get_ticket_url(self, ticket_element):
        """
        Extract URL from a ticket element.
        
        Args:
            ticket_element: Individual ticket element
            
        Returns:
            str: URL of the ticket
        """
        pass
    
    @abstractmethod
    def check_ticket_available(self, browser):
        """
        Check if a specific ticket is still available.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if ticket available, False if already reserved
        """
        pass
    
    @abstractmethod
    def buy_ticket(self, browser):
        """
        Attempt to buy/reserve a ticket.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def check_reservation_success(self, browser):
        """
        Check if ticket reservation was successful.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if reservation successful
        """
        pass
    
    def get_rate_limits(self):
        """
        Get rate limiting configuration.
        
        Returns:
            dict: {'min_delay': float, 'max_delay': float}
        """
        rate_limit = self.config.get('rate_limit', {})
        return {
            'min_delay': rate_limit.get('min_delay', 2.5),
            'max_delay': rate_limit.get('max_delay', 4.3)
        }
    
    def is_proxy_required(self):
        """
        Check if proxy rotation is required for this site.
        
        Returns:
            bool: True if proxy required
        """
        return self.config.get('proxy_required', False)
