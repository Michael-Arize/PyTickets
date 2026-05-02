# -*- coding: utf-8 -*-
"""APScheduler-backed job manager for recurring crawler runs."""
import os
import subprocess
import sys

from ticketCrawler.database import Database


class CrawlerScheduler:
    """Schedule Scrapy crawler jobs with APScheduler."""

    def __init__(self, scheduler=None, database=None):
        if scheduler is None:
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
            except ImportError as exc:
                raise RuntimeError(
                    "APScheduler is required for scheduled crawling. "
                    "Install it with: pip install APScheduler"
                ) from exc
            scheduler = BackgroundScheduler()

        self.scheduler = scheduler
        self.database = database or Database(os.environ.get("PYTICKETS_DB_PATH", "data/pytickets.db"))
        self._running_keys = set()

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    def schedule_site(self, site_name, url=None, interval_hours=2, job_id=None):
        job_id = job_id or f"crawl_{site_name}"
        self.database.upsert_scheduled_job(job_id, site_name, url, interval_hours, enabled=True)
        return self.scheduler.add_job(
            self._run_crawler_once,
            "interval",
            hours=interval_hours,
            id=job_id,
            replace_existing=True,
            kwargs={"job_id": job_id, "site_name": site_name, "url": url},
        )

    def load_persisted_jobs(self):
        """Load enabled jobs from SQLite into APScheduler."""
        jobs = []
        for row in self.database.list_scheduled_jobs(enabled=True):
            jobs.append(
                self.schedule_site(
                    row["site"],
                    url=row.get("url"),
                    interval_hours=row["interval_hours"],
                    job_id=row["id"],
                )
            )
        return jobs

    def list_scheduled_jobs(self):
        return self.scheduler.get_jobs()

    def cancel_job(self, job_id):
        self.scheduler.remove_job(job_id)
        self.database.delete_scheduled_job(job_id)
        return True

    def pause_job(self, job_id):
        self.scheduler.pause_job(job_id)
        return True

    def resume_job(self, job_id):
        self.scheduler.resume_job(job_id)
        return True

    def get_job_status(self, job_id):
        job = self.scheduler.get_job(job_id)
        if job is None:
            return None
        return {
            "id": job.id,
            "next_run_time": job.next_run_time,
            "trigger": str(job.trigger),
        }

    def _run_crawler_once(self, job_id, site_name, url=None):
        key = (site_name, url)
        if key in self._running_keys:
            self.database.update_scheduled_job_status(job_id, "skipped_overlap")
            return 0

        self._running_keys.add(key)
        try:
            result = self._run_crawler(site_name, url=url)
            self.database.update_scheduled_job_status(
                job_id,
                "success" if result == 0 else f"failed:{result}",
            )
            return result
        finally:
            self._running_keys.discard(key)

    @staticmethod
    def _run_crawler(site_name, url=None):
        command = [
            sys.executable,
            "-m",
            "scrapy",
            "crawl",
            "tickets_refactored",
            "-a",
            f"site={site_name}",
        ]
        if url:
            command.extend(["-a", f"url={url}"])

        env = os.environ.copy()
        return subprocess.call(command, env=env)
