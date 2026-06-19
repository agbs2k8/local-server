import datetime
from pydantic import (BaseModel, 
                      Field,
                      conlist, 
                      GetJsonSchemaHandler, 
                      model_validator, 
                      GetCoreSchemaHandler)
from typing import Optional, List, Literal, Annotated


class Pod(BaseModel):
    name: str
    namespace: str
    creation_timestamp: Optional[datetime.datetime]
    uid: str
    node_name: Optional[str]
    service_account: Optional[str]
    phase: Optional[str]
    start_time: Optional[datetime.datetime]

    @staticmethod
    def from_kubectl(pod_dict: dict) -> "Pod":
        metadata = pod_dict.get("metadata", {})
        spec = pod_dict.get("spec", {})
        status = pod_dict.get("status", {})
        
        return Pod(
            name=metadata.get("name"),
            namespace=metadata.get("namespace"),
            creation_timestamp=metadata.get("creation_timestamp"),
            uid=metadata.get("uid"),
            node_name=spec.get("node_name", None),
            service_account=spec.get("service_account", None),
            phase=status.get("phase", None),
            start_time=status.get("start_time")
        )
    
class PodList(BaseModel):
    data: List[Pod]

    @staticmethod
    def from_kubectl(pod_list) -> "PodList":
        return PodList(data=[Pod.from_kubectl(pod.to_dict()) for pod in pod_list.items])
    

class Job(BaseModel):
    name: str
    namespace: str
    creation_timestamp: Optional[datetime.datetime]
    uid: str
    start_time: Optional[datetime.datetime]
    completion_time: Optional[datetime.datetime]
    active: Optional[int]
    succeeded: Optional[int]
    failed: Optional[int]

    @staticmethod
    def from_kubectl(job_dict: dict) -> "Job":
        metadata = job_dict.get("metadata", {})
        status = job_dict.get("status", {})
        
        return Job(
            name=metadata.get("name"),
            namespace=metadata.get("namespace"),
            creation_timestamp=metadata.get("creation_timestamp"),
            uid=metadata.get("uid"),
            start_time=status.get("start_time"),
            completion_time=status.get("completion_time"),
            active=status.get("active") if status.get("active") is not None else 0,
            succeeded=status.get("succeeded") if status.get("succeeded") is not None else 0,
            failed=status.get("failed") if status.get("failed") is not None else 0
        )
    

class JobList(BaseModel):
    data: List[Job]

    @staticmethod
    def from_kubectl(job_list) -> "PodList":
        return JobList(data=[Job.from_kubectl(job.to_dict()) for job in job_list.items])


class CronJob(BaseModel):
    name: str
    namespace: str
    creation_timestamp: Optional[datetime.datetime]
    uid: str
    schedule: Optional[str]
    suspend: Optional[bool]
    active: int
    last_schedule_time: Optional[datetime.datetime]
    last_successful_time: Optional[datetime.datetime]

    @staticmethod
    def from_kubectl(cronjob_dict: dict) -> "CronJob":
        metadata = cronjob_dict.get("metadata", {})
        spec = cronjob_dict.get("spec", {})
        status = cronjob_dict.get("status", {})
        active_jobs = status.get("active") or []

        return CronJob(
            name=metadata.get("name"),
            namespace=metadata.get("namespace"),
            creation_timestamp=metadata.get("creation_timestamp"),
            uid=metadata.get("uid"),
            schedule=spec.get("schedule"),
            suspend=spec.get("suspend"),
            active=len(active_jobs),
            last_schedule_time=status.get("last_schedule_time"),
            last_successful_time=status.get("last_successful_time"),
        )


class CronJobList(BaseModel):
    data: List[CronJob]

    @staticmethod
    def from_kubectl(cronjob_list) -> "CronJobList":
        return CronJobList(
            data=[CronJob.from_kubectl(cronjob.to_dict()) for cronjob in cronjob_list.items]
        )
    