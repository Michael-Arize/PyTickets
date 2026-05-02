# -*- coding: utf-8 -*-
"""APScheduler-backed job manager for recurring crawler runs."""
import os
import subprocess
import sys


class CrawlerScheduler:
    """Schedule Scrapy crawler jobs with APScheduler."""

    def __init__(self, scheduler=None):
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

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    def schedule_site(self, site_name, url=None, interval_hours=2, job_id=None):
        job_id = job_id or f"crawl_{site_name}"
        return self.scheduler.add_job(
            self._run_crawler,
            "interval",
            hours=interval_hours,
            id=job_id,
            replace_existing=True,
            kwargs={"site_name": site_name, "url": url},
        )

    def list_scheduled_jobs(self):
        return self.scheduler.get_jobs()

    def cancel_job(self, job_id):
        self.scheduler.remove_job(job_id)
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
