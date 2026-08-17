from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def fetch_assessments_job():
    """
    Runs the fetch_assessments management command as a background job.
    Fetches new assessment payloads from Unity Cloud Save and
    triggers the CQ-DSF engine for each new session found.
    """
    try:
        from api.management.commands.fetch_assessments import Command
        cmd = Command()
        cmd.handle()
        logger.info("fetch_assessments job completed successfully.")
    except Exception as e:
        logger.error(f"fetch_assessments job failed: {e}")


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        fetch_assessments_job,
        trigger=IntervalTrigger(minutes=2),
        id="fetch_assessments",
        name="Fetch assessments from Unity Cloud Save",
        replace_existing=True,
        misfire_grace_time=60,
    )

    scheduler.start()
    logger.info("Scheduler started. Fetching assessments every 2 minutes.")