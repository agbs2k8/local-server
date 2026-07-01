import config as cfg
import datetime
from app.load_events import run_download
from app.publish import run_upload
from app.load_schedule import get_schedules


if __name__ == "__main__":
    _now = datetime.datetime.now()
    if _now.day==1 and _now.hour < 6:
        get_schedules(cfg)
    run_download(cfg)
    run_upload(cfg)
