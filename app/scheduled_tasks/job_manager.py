import logging
from datetime import datetime
from uuid import uuid4
import asyncio
from queue import Queue
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models.database.scheduled_jobs_models import ScheduledJob
from app.models.database.tenant_models import TenantMetadata
from app.models.database.schema_models import User
from app.scheduled_tasks.invoice_processor import process_xero_invoices_wrapper
from app.scheduled_tasks.statement_processor import process_bank_statements_wrapper
from app.utils.xero.tenant_utils import get_tenant_metadata

logger = logging.getLogger(__name__)

# Initialize the scheduler
jobstores = {
    'default': SQLAlchemyJobStore(url=settings.database_url)
}
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    job_defaults={
        'coalesce': True,  # Combine multiple missed runs into a single run
        'max_instances': 1  # Prevent concurrent execution of the same job
    }
)
scheduler.start()

# Create a job queue for sequential processing
job_queue = Queue()
job_queue_running = False
job_queue_lock = threading.Lock()
job_parameters = {}

def process_job_queue():
    """Process jobs in the queue sequentially"""
    global job_queue_running
    
    with job_queue_lock:
        if job_queue_running:
            return
        job_queue_running = True
    
    try:
        while not job_queue.empty():
            job_func, args = job_queue.get()
            try:
                job_func(*args)
            except Exception as e:
                logger.error(f"Error executing job from queue: {str(e)}", exc_info=True)
            finally:
                job_queue.task_done()
                # Small delay between jobs to ensure clean event loop cleanup
                time.sleep(0.5)
    finally:
        with job_queue_lock:
            job_queue_running = False

def queue_job(func, *args):
    """Add a job to the queue and start processing if not already running"""
    job_queue.put((func, args))
    
    # Start processing the queue in a separate thread if not already running
    with job_queue_lock:
        if not job_queue_running:
            threading.Thread(target=process_job_queue, daemon=True).start()

def execute_queued_job(job_id):
    """Execute a job from the stored parameters"""
    if job_id in job_parameters:
        func, args = job_parameters[job_id]
        queue_job(func, *args)
    else:
        logger.error(f"Job parameters not found for job_id: {job_id}")

def get_schedule_description(
    hour: str, minute: str, second: str, day: str, month: str, day_of_week: str
) -> str:
    """
    Constructs a human-readable description of the schedule interval based on cron components.
    """
    if hour.startswith("*/"):
        interval = int(hour[2:])
        return f"every {interval} hours"
    elif day.startswith("*/"):
        interval = int(day[2:])
        return f"every {interval} days"
    elif minute.startswith("*/"):
        interval = int(minute[2:])
        return f"every {interval} minutes"
    elif second.startswith("*/"):
        interval = int(second[2:])
        return f"every {interval} seconds"
    else:
        return "on a custom schedule"


async def start_job_for_user(
    db: Session, user_id: str, tenant_id: str, job_type: str
) -> dict:
    """Start a scheduled job for a user"""
    try:
        # Get user and their brain_id
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if not user.brain_id:
            raise HTTPException(
                status_code=400, detail="User has no brain_id configured"
            )

        # Get tenant metadata
        tenant_metadata = await get_tenant_metadata(db, tenant_id, user_id)
        if not tenant_metadata:
            raise HTTPException(status_code=404, detail="Tenant metadata not found")

        # Check if job already exists
        existing_job = (
            db.query(ScheduledJob)
            .filter(
                ScheduledJob.user_id == user_id,
                ScheduledJob.tenant_id == tenant_id,
                ScheduledJob.job_type == job_type,
                ScheduledJob.is_active == True,
            )
            .first()
        )

        if existing_job:
            logger.info(
                f"Job {existing_job.id} already exists and running for user {user_id} and type {job_type}"
            )
            return {
                "status": "success",
                "message": f"{job_type.capitalize()} processing is already scheduled",
                "job_id": existing_job.id,
            }

        # Create new job record
        job_id = str(uuid4())
        db_job = ScheduledJob(
            id=job_id,
            user_id=user_id,
            tenant_id=tenant_id,
            brain_id=user.brain_id,
            job_type=job_type,
        )
        db.add(db_job)
        db.commit()

        logger.info(f"Created new {job_type} job {job_id} for user {user_id}")

        # Schedule the job
        if job_type == "invoice":
            func = process_xero_invoices_wrapper
            args = [user.brain_id, tenant_id]
        else:  # statement
            func = process_bank_statements_wrapper
            args = [user.brain_id, tenant_id, db]

        # Get schedule description
        schedule_description = get_schedule_description(
            settings.schedule_hour,
            settings.schedule_minute,
            settings.schedule_second,
            settings.schedule_day,
            settings.schedule_month,
            settings.schedule_day_of_week,
        )

        job_parameters[job_id] = (func, args)
        scheduler.add_job(
            func=execute_queued_job,
            args=[job_id],
            trigger=CronTrigger(
                hour=settings.schedule_hour,
                minute=settings.schedule_minute,
                second=settings.schedule_second,
                day=settings.schedule_day,
                month=settings.schedule_month,
                day_of_week=settings.schedule_day_of_week,
            ),
            id=job_id,
            name=f"{job_type.capitalize()} Processing for User {user_id}",
            replace_existing=True,
        )

        logger.info(
            f"Scheduled {job_type} job {job_id} to run {schedule_description}"
        )

        # Run immediately in a non-blocking way by adding to the queue
        queue_job(func, *args)
        logger.info(f"Initial run of {job_type} job {job_id} queued for processing")

        next_run = scheduler.get_job(job_id).next_run_time
        logger.info(f"Next run of {job_type} job {job_id} scheduled for {next_run}")

        return {
            "status": "success",
            "message": f"{job_type.capitalize()} processing started and will run {schedule_description}",
            "job_id": job_id,
            "processed_at": datetime.now().isoformat(),
            "next_run": next_run.isoformat() if next_run else None,
        }

    except Exception as e:
        logger.error(f"Error starting {job_type} job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to start {job_type} processing: {str(e)}"
        )


async def stop_job(
    db: Session,
    job_id: str,
) -> dict:
    """Stop a scheduled job"""
    try:
        # Get job from database
        job = db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Mark as inactive
        job.is_active = False
        db.commit()

        # Remove from scheduler if it exists
        try:
            scheduler.remove_job(job_id)
        except JobLookupError:
            # Job exists in DB but not in scheduler - this is fine
            logger.warning(f"Job {job_id} not found in scheduler, but marked as inactive in database")

        return {
            "message": f"{job.job_type.capitalize()} processing stopped successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stop job: {str(e)}")


def start_jobs_on_startup(db: Session):
    """Start all active jobs when application starts"""
    try:
        tenant_metadata_records = db.query(TenantMetadata).all()
        logger.info(f"Found {len(tenant_metadata_records)} tenant metadata records to check for required jobs")
        job_types = ["invoice", "statement"]
        jobs_created = 0
        for tenant in tenant_metadata_records:
            user = db.query(User).filter(User.id == tenant.user_id).first()
            if not user or not user.brain_id:
                logger.warning(f"Skipping tenant {tenant.tenant_id} - user {tenant.user_id} not found or has no brain_id")
                continue
            for job_type in job_types:
                user_id = str(tenant.user_id)
                existing_job = (
                    db.query(ScheduledJob)
                    .filter(
                        ScheduledJob.user_id == user_id,
                        ScheduledJob.tenant_id == tenant.tenant_id,
                        ScheduledJob.job_type == job_type,
                        ScheduledJob.is_active == True,
                    )
                    .first()
                )
                if existing_job:
                    logger.debug(f"Job {existing_job.id} already exists for user {tenant.user_id}, tenant {tenant.tenant_id}, type {job_type}")
                else:
                    # Create new job record
                    job_id = str(uuid4())
                    db_job = ScheduledJob(
                        id=job_id,
                        user_id=user_id,
                        tenant_id=tenant.tenant_id,
                        brain_id=user.brain_id,
                        job_type=job_type,
                        is_active=True
                    )
                    db.add(db_job)
                    jobs_created += 1
                    logger.info(f"Created and scheduled new {job_type} job {job_id} for user {tenant.user_id}, tenant {tenant.tenant_id}")
        
        if jobs_created > 0:
            db.commit()
            logger.info(f"Created {jobs_created} new jobs for users with active tenants")

        active_jobs = (
            db.query(ScheduledJob).filter(ScheduledJob.is_active == True).all()
        )
        logger.info(f"Found {len(active_jobs)} active jobs to restore on startup")

        for job in active_jobs:
            if job.job_type == "invoice":
                func = process_xero_invoices_wrapper
                args = [job.brain_id, job.tenant_id]
            else:  # statement
                func = process_bank_statements_wrapper
                args = [job.brain_id, job.tenant_id, db]

            job_parameters[job.id] = (func, args)
            scheduler.add_job(
                func=execute_queued_job,
                args=[job.id],
                trigger=CronTrigger(
                    hour=settings.schedule_hour,
                    minute=settings.schedule_minute,
                    second=settings.schedule_second,
                    day=settings.schedule_day,
                    month=settings.schedule_month,
                    day_of_week=settings.schedule_day_of_week,
                ),
                id=job.id,
                name=f"{job.job_type.capitalize()} Processing for User {job.user_id}",
                replace_existing=True,
            )

            queue_job(func, *args)
            logger.info(f"Initial run of {job.job_type} job {job.id} queued for processing")

            next_run = scheduler.get_job(job.id).next_run_time
            logger.info(
                f"Restored {job.job_type} job {job.id} for user {job.user_id}. "
                f"Next run scheduled for {next_run}"
            )

    except Exception as e:
        logger.error(f"Error starting jobs on startup: {str(e)}", exc_info=True)
