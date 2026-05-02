# -*- coding: utf-8 -*-
"""Deprecated legacy single-run spider.

Use `tickets_refactored` for the maintained manual-purchase workflow.
"""
import scrapy
from scrapy.exceptions import CloseSpider


class singleRunSpider(scrapy.Spider):
    """Compatibility stub for the old Python 2 spider name."""

    name = "singleRun"

    def start_requests(self):
        raise CloseSpider("singleRun spider is deprecated; use tickets_refactored")
