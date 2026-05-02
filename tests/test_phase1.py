# -*- coding: utf-8 -*-
"""Tests for Phase 1 persistence and scheduling helpers."""
from datetime import UTC, datetime, timedelta

from ticketCrawler.database import Database
from ticketCrawler.scheduler import CrawlerScheduler
from ticketCrawler.utils.error_handler import ErrorHandler, ErrorType
from ticketCrawler.utils.url_cache import URLCache


class TestURLCache:
    def test_mark_save_and_reload(self, tmp_path):
        cache_path = tmp_path / "url_cache.json"
        cache = URLCache(cache_path=cache_path)

        cache.mark_visited("https://example.com/ticket/1", {"price": 25})
        cache.save_to_disk()

        reloaded = URLCache(cache_path=cache_path)
        assert reloaded.is_visited("https://example.com/ticket/1")
        assert reloaded.get_metadata("https://example.com/ticket/1")["price"] == 25

    def test_clear_old_entries(self, tmp_path):
        cache = URLCache(cache_path=tmp_path / "url_cache.json", ttl_days=1)
        cache._entries["https://example.com/old"] = {
            "visited_at": (datetime.now(UTC) - timedelta(days=3)).isoformat(),
            "metadata": {},
        }

        cache.clear_old_entries()

        assert not cache.is_visited("https://example.com/old")


class TestDatabase:
    def test_save_ticket_and_mark_notified(self, tmp_path):
        db = Database(tmp_path / "tickets.db")
        ticket = {
            "site": "Dutch Tickets",
            "url": "https://example.com/ticket/1",
            "price": 42.5,
            "seat_type": "floor",
            "quantity": 2,
        }

        db.save_ticket(ticket)
        assert db.ticket_exists(ticket["url"])

        db.mark_ticket_notified(ticket["url"], status="sent")
        saved = db.get_recent_tickets(limit=1)[0]

        assert saved["url"] == ticket["url"]
        assert saved["notification_status"] == "sent"

    def test_crawl_run_lifecycle(self, tmp_path):
        db = Database(tmp_path / "tickets.db")
        run_id = db.start_crawl_run("dutch_tickets")

        db.finish_crawl_run(run_id, tickets_found=1, tickets_notified=1)

        assert run_id


class TestErrorHandler:
    def test_classifies_rate_limit(self):
        assert ErrorHandler.classify_error("429 too many requests") == ErrorType.RATE_LIMITED
        assert ErrorHandler.is_retryable("429 too many requests")

    def test_classifies_parse_error(self):
        assert ErrorHandler.classify_error("xpath selector missing") == ErrorType.PARSE
        assert not ErrorHandler.is_retryable("xpath selector missing")


class FakeJob:
    def __init__(self, job_id, trigger):
        self.id = job_id
        self.trigger = trigger
        self.next_run_time = None


class FakeScheduler:
    def __init__(self):
        self.running = False
        self.jobs = {}

    def start(self):
        self.running = True

    def shutdown(self):
        self.running = False

    def add_job(self, func, trigger, hours, id, replace_existing, kwargs):
        job = FakeJob(id, trigger)
        self.jobs[id] = job
        return job

    def get_jobs(self):
        return list(self.jobs.values())

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def remove_job(self, job_id):
        self.jobs.pop(job_id)

    def pause_job(self, job_id):
        return self.jobs[job_id]

    def resume_job(self, job_id):
        return self.jobs[job_id]


class TestCrawlerScheduler:
    def test_schedule_site_with_injected_scheduler(self):
        scheduler = CrawlerScheduler(scheduler=FakeScheduler())

        job = scheduler.schedule_site("dutch_tickets", interval_hours=3)
        scheduler.start()

        assert scheduler.scheduler.running
        assert job.id == "crawl_dutch_tickets"
        assert len(scheduler.list_scheduled_jobs()) == 1
