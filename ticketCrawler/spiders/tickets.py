# -*- coding: utf-8 -*-
"""Deprecated legacy spider.

Use `tickets_refactored` for the maintained manual-purchase workflow.
"""
import scrapy
from scrapy.exceptions import CloseSpider


class TicketsSpider(scrapy.Spider):
    """Compatibility stub for the old Python 2 spider name."""

    name = "tickets"

    def start_requests(self):
        raise CloseSpider("tickets spider is deprecated; use tickets_refactored")
