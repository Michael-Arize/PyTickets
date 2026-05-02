# -*- coding: utf-8 -*-
"""FastAPI application for PyTickets operations."""
import os
import subprocess
import sys
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ticketCrawler.config.app_config import config
from ticketCrawler.database import Database
from ticketCrawler.scheduler import CrawlerScheduler


class CrawlRequest(BaseModel):
    site: str = "dutch_tickets"
    url: str = None


class ScheduleRequest(BaseModel):
    site: str = "dutch_tickets"
    url: str = None
    interval_hours: float = 2
    job_id: str = None


class NotificationTestRequest(BaseModel):
    message: str = "PyTickets test notification"


db = Database(config.database_path)
scheduler = CrawlerScheduler(database=db)
app = FastAPI(title="PyTickets API", version="2.0.0")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
def startup():
    scheduler.load_persisted_jobs()
    scheduler.start()


@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()


@app.get("/")
def dashboard():
    return FileResponse(static_dir / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "summary": db.get_summary()}


@app.get("/api/sites")
def sites():
    config_dir = Path("configs/sites")
    return {"sites": [path.stem for path in config_dir.glob("*.json")]}


@app.get("/api/tickets")
def tickets(site: str = None, notification_status: str = None, limit: int = 100):
    return {
        "tickets": db.query_tickets(
            site=site,
            notification_status=notification_status,
            limit=limit,
        )
    }


@app.get("/api/crawl-runs")
def crawl_runs(site: str = None, limit: int = 100):
    return {"crawl_runs": db.get_crawl_runs(site=site, limit=limit)}


@app.post("/api/crawl")
def start_crawl(request: CrawlRequest):
    command = [
        sys.executable,
        "-m",
        "scrapy",
        "crawl",
        "tickets_refactored",
        "-a",
        f"site={request.site}",
    ]
    if request.url:
        command.extend(["-a", f"url={request.url}"])

    subprocess.Popen(command, env=os.environ.copy())
    return {"status": "started", "command": command}


@app.get("/api/jobs")
def jobs():
    live_jobs = []
    for job in scheduler.list_scheduled_jobs():
        live_jobs.append({
            "id": job.id,
            "next_run_time": str(job.next_run_time),
            "trigger": str(job.trigger),
        })
    return {
        "jobs": live_jobs,
        "persisted": db.list_scheduled_jobs(),
    }


@app.post("/api/jobs")
def create_job(request: ScheduleRequest):
    job = scheduler.schedule_site(
        request.site,
        url=request.url,
        interval_hours=request.interval_hours,
        job_id=request.job_id,
    )
    return {"status": "scheduled", "job_id": job.id}


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: str):
    try:
        scheduler.cancel_job(job_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"status": "deleted", "job_id": job_id}


@app.post("/api/cache/clear")
def clear_cache():
    db.clear_url_cache()
    return {"status": "cleared"}


@app.post("/api/notifications/test")
def test_notification(request: NotificationTestRequest):
    from ticketCrawler.notifications.manager import NotificationFactory, NotificationManager

    manager = NotificationManager()
    notifications_config = os.environ.get("NOTIFICATIONS_CONFIG")
    if notifications_config:
        parsed_config = json.loads(notifications_config)
        configs = parsed_config if isinstance(parsed_config, list) else [parsed_config]
        for notifier_config in configs:
            notifier_type = notifier_config.pop("type")
            manager.add_notifier_config(notifier_type, notifier_config)

    email_sender = os.environ.get("EMAIL_SENDER") or os.environ.get("email_sender")
    email_recipient = os.environ.get("EMAIL_RECIPIENT") or os.environ.get("email_recipient")
    if email_sender and email_recipient:
        manager.add_notifier_config("email", {
            "provider": os.environ.get("EMAIL_PROVIDER", os.environ.get("email_provider", "smtp")),
            "sender": email_sender,
            "recipient": email_recipient,
            "smtp_host": os.environ.get("SMTP_HOST") or os.environ.get("smtp_host"),
            "smtp_port": int(os.environ.get("SMTP_PORT", os.environ.get("smtp_port", "587"))),
            "smtp_user": os.environ.get("SMTP_USER") or os.environ.get("smtp_user") or email_sender,
            "smtp_password": os.environ.get("SMTP_PASSWORD") or os.environ.get("smtp_password"),
            "mailgun_key": os.environ.get("MAILGUN_KEY") or os.environ.get("mailgun_key"),
            "mailgun_domain": os.environ.get("MAILGUN_DOMAIN") or os.environ.get("mailgun_domain"),
        })

    token = os.environ.get("telegram_token")
    chat_id = os.environ.get("telegram_chat_id")
    if token and chat_id:
        manager.add_notifier(NotificationFactory.create_notifier(
            "telegram",
            {"token": token, "chat_id": chat_id},
        ))

    if not manager.notifiers:
        return {
            "status": "not_configured",
            "message": request.message,
            "notifiers": 0,
        }

    results = manager.notify(request.message, subject="PyTickets test notification")
    return {
        "status": "sent" if any(results.values()) else "failed",
        "message": request.message,
        "notifiers": len(manager.notifiers),
        "results": results,
    }
