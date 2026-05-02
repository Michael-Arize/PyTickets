# -*- coding: utf-8 -*-
"""Tests for Phase 2 API, proxy, and configuration helpers."""
import os

from ticketCrawler.config.app_config import AppConfig
from ticketCrawler.database import Database
from ticketCrawler.proxies import ProxyManager
from ticketCrawler.scheduler import CrawlerScheduler


def test_app_config_loads_dotenv_without_overriding(tmp_path, monkeypatch):
    env_path = tmp_path / ".env"
    env_path.write_text("PYTICKETS_NOTIFY_MODE=batch\nEXISTING=from-file\n", encoding="utf-8")
    monkeypatch.setenv("EXISTING", "from-env")

    cfg = AppConfig(env_path=env_path)

    assert cfg.notify_mode == "batch"
    assert os.environ["EXISTING"] == "from-env"


def test_database_query_helpers_and_scheduled_jobs(tmp_path):
    db = Database(tmp_path / "tickets.db")
    db.save_ticket({"site": "Dutch Tickets", "url": "https://example.com/1"})
    db.mark_ticket_notified("https://example.com/1", "sent")
    db.upsert_scheduled_job("job-1", "dutch_tickets", "https://example.com", 2)

    assert db.query_tickets(notification_status="sent")[0]["url"] == "https://example.com/1"
    assert db.get_summary()["tickets"] == 1
    assert db.list_scheduled_jobs()[0]["id"] == "job-1"

    db.clear_url_cache()
    db.delete_scheduled_job("job-1")
    assert db.list_scheduled_jobs() == []


def test_proxy_manager_round_robin_and_health():
    manager = ProxyManager(["http://p1", "http://p2"], max_failures=2)

    assert manager.get_next_proxy() == "http://p1"
    assert manager.get_next_proxy() == "http://p2"

    manager.mark_failed("http://p1")
    manager.mark_failed("http://p1")

    health = manager.get_health_status()
    p1 = [proxy for proxy in health if proxy["url"] == "http://p1"][0]
    assert not p1["enabled"]


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


def test_scheduler_persists_and_loads_jobs(tmp_path):
    db = Database(tmp_path / "tickets.db")
    scheduler = CrawlerScheduler(scheduler=FakeScheduler(), database=db)

    scheduler.schedule_site("dutch_tickets", url="https://example.com", job_id="job-1")
    assert db.list_scheduled_jobs()[0]["id"] == "job-1"

    scheduler_two = CrawlerScheduler(scheduler=FakeScheduler(), database=db)
    scheduler_two.load_persisted_jobs()
    assert scheduler_two.get_job_status("job-1")["id"] == "job-1"
