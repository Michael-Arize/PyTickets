# -*- coding: utf-8 -*-
"""Run PyTickets on a recurring schedule."""
import os
import time

from ticketCrawler.scheduler import CrawlerScheduler


def main():
    site = os.environ.get("PYTICKETS_SCHEDULE_SITE", "dutch_tickets")
    url = os.environ.get("PYTICKETS_SCHEDULE_URL")
    interval_hours = float(os.environ.get("PYTICKETS_SCHEDULE_INTERVAL_HOURS", "2"))

    scheduler = CrawlerScheduler()
    scheduler.schedule_site(site, url=url, interval_hours=interval_hours)
    scheduler.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()


if __name__ == "__main__":
    main()
