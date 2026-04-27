# -*- coding: utf-8 -*-
"""Adapter for Dutch ticket website."""
from ..base_adapter import BaseAdapter


class DutchTicketsAdapter(BaseAdapter):
    """Adapter for the Dutch ticket trading website."""
    
    def __init__(self, config):
        """Initialize Dutch Tickets adapter."""
        super().__init__(config)
        self.selectors = config.get('selectors', {})
    
    def authenticate(self, browser):
        """
        Authenticate using Facebook login.
        
        Args:
            browser: Selenium WebDriver instance
            
        Raises:
            Exception: If authentication fails
        """
        try:
            browser.get(self.base_url)
            
            # Click login link
            login_link_text = self.selectors.get('login_link_text', 'Inloggen')
            browser.find_element_by_link_text(login_link_text).click()
            
            # Switch to Facebook login window if needed
            for handle in browser.window_handles:
                browser.switch_to_window(handle)
            
            # Fill in credentials
            email_input = self.selectors.get('email_input_name', 'email')
            password_input = self.selectors.get('password_input_name', 'pass')
            login_button = self.selectors.get('login_button_name', 'login')
            
            email_elem = browser.find_element_by_name(email_input)
            email_elem.send_keys(self.config['auth']['credentials']['email'])
            
            pass_elem = browser.find_element_by_name(password_input)
            pass_elem.send_keys(self.config['auth']['credentials']['password'])
            
            browser.find_element_by_name(login_button).click()
            
            # Switch back to main window
            for handle in browser.window_handles:
                browser.switch_to_window(handle)
        
        except Exception as e:
            raise Exception(f"Facebook authentication failed: {str(e)}")
    
    def check_tickets_available(self, response):
        """
        Check if any tickets are available.
        
        Returns:
            bool: True if tickets available, False if no tickets or rate limited
        """
        body = response.body if hasattr(response, 'body') else response
        
        # Check for no tickets text
        no_tickets_text = self.selectors.get('no_tickets_text', [])
        other_available = self.selectors.get('other_available_text', 'Andere beschikbare tickets')
        
        for text in no_tickets_text:
            if text in body:
                # Check if there are other available tickets
                if other_available not in body:
                    return False
        
        return True
    
    def get_first_sold_ticket_url(self, response):
        """
        Extract URL of first sold ticket listing.
        
        Returns:
            str: Full URL of first sold ticket
        """
        body = response.text if hasattr(response, 'text') else response
        
        # Check which section contains sold tickets
        offered_xpath = self.selectors.get('sold_tickets_link_xpath_offered')
        sold_xpath = self.selectors.get('sold_tickets_link_xpath_sold')
        
        if 'Aangeboden' in response.xpath('//section[1]/h2').extract_first() or '':
            link = response.xpath(offered_xpath).extract_first()
        elif 'Verkocht' in response.xpath('//section[1]/h2').extract_first() or '':
            link = response.xpath(sold_xpath).extract_first()
        else:
            return None
        
        if link:
            return self.base_url + link
        return None
    
    def extract_tickets(self, response):
        """
        Extract ticket elements from response.
        
        Returns:
            list: List of ticket elements
        """
        xpath = self.selectors.get('ticket_array_xpath', '//body/div[4]/div/div[2]/article')
        return response.xpath(xpath)
    
    def get_ticket_url(self, ticket_element):
        """
        Extract URL from a ticket element.
        
        Args:
            ticket_element: Scrapy selector for individual ticket
            
        Returns:
            str: Full URL of the ticket
        """
        xpath = self.selectors.get('ticket_link_xpath', 'div[1]/h3/a/@href')
        link = ticket_element.xpath(xpath).extract_first()
        
        if link:
            return self.base_url + link
        return None
    
    def check_ticket_available(self, browser):
        """
        Check if a specific ticket is still available.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if available, False if reserved
        """
        ticket_text = self.selectors.get('ticket_already_reserved_text', 'Koop e-ticket')
        return ticket_text in browser.page_source
    
    def buy_ticket(self, browser):
        """
        Click the buy button to reserve ticket.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if button clicked successfully
        """
        import time
        try:
            button_class = self.selectors.get('buy_button_class', 'btn-buy')
            browser.find_element_by_class_name(button_class).click()
            time.sleep(5)  # Wait for payment page to load
            return True
        except Exception as e:
            print(f"Error clicking buy button: {str(e)}")
            return False
    
    def check_reservation_success(self, browser):
        """
        Check if ticket was successfully reserved.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if payment page is shown
        """
        success_indicators = self.selectors.get('success_indicators', [])
        page_source = browser.page_source
        
        for indicator in success_indicators:
            if indicator in page_source:
                return True
        
        return False
    
    def is_rate_limited(self, response):
        """
        Check if we've been rate limited.
        
        Args:
            response: Page content
            
        Returns:
            bool: True if rate limited
        """
        rate_limit_text = self.selectors.get('rate_limit_text', 'Oeps, iets te vaak vernieuwd')
        body = response.body if hasattr(response, 'body') else response
        return rate_limit_text in body
    
    def has_facebook_error(self, browser):
        """
        Check for Facebook authentication errors.
        
        Args:
            browser: Selenium WebDriver instance
            
        Returns:
            bool: True if Facebook error present
        """
        error_text = self.selectors.get('facebook_error_text', 'Je hebt ons geen toegang gegeven tot je Facebook account')
        return error_text in browser.page_source
