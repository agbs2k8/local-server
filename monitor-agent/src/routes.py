import json
import fastapi
import datetime
from typing import Optional, List
from src.models import PodList, Pod, JobList, Job, CronJobList, CronJob
from src.kube_client import v1, apps_v1, get_pod_failure_events
import logging

logger = logging.getLogger(__name__)

router = fastapi.APIRouter()

@router.get("/liveness")
async def liveness():
    return {"message": "ok"}

@router.get("/readiness")
async def readiness():
    return {"message": "ok"}


@router.get("/jobs", 
            response_model=None, 
            summary="List all jobs",
            description="Returns a list of all k8s jobs")
async def list_jobs():
    """
    Return a list of all jobs
    """
    logger.info("retrieving_jobs")
    #all_jobs = apps_v1.list_job_for_all_namespaces()
    jobs = JobList.from_kubectl(apps_v1.list_job_for_all_namespaces())
    return jobs


@router.get("/cronjobs", 
            response_model=CronJobList, 
            summary="List all cronjobs",
            description="Returns a list of all k8s cronjobs")
async def list_cronjobs():
    """
    Return a list of all cronjobs
    """
    logger.info("retrieving_cronjobs")
    cronjobs = CronJobList.from_kubectl(apps_v1.list_cron_job_for_all_namespaces())
    return cronjobs

@router.get("/pods", 
            response_model=PodList, 
            summary="List all jobs",
            description="Returns a list of all k8s jobs")
async def list_pods():
    """
    Return a list of all pods
    """
    logger.info("retrieving_pods")
    pods = PodList.from_kubectl(apps_v1.list_pod_for_all_namespaces())
    return pods#{"date": datetime.datetime.now(), "pods": [x.to_dict() for x in all_pods.items]}