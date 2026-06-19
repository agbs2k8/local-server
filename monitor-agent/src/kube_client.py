import re
import logging
import itertools
from functools import lru_cache
from config import cfg
from kubernetes import client, config

logger = logging.getLogger(__name__)

DEFAULT_POD_LOG_LINES = cfg.DEFAULT_POD_LOG_LINES


# ANSI escape sequences start with ESC (0x1B) followed by a CSI sequence like [32m.
# This regex matches the full sequence so it can be removed cleanly before
# control character stripping (which would only remove the ESC, leaving `[32m` behind).
_ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

# Unicode defines two blocks of control characters:
#   C0 (0x00–0x1F): includes null, bell, backspace, ESC, etc.
#   C1 (0x7F–0x9F): includes DEL and the C1 supplement block
# We exclude \t (0x09), \n (0x0A), and \r (0x0D) since they're legitimate in log output.
_CONTROL_CHARS = "".join(
    chr(c)
    for c in itertools.chain(
        range(0x00, 0x09),   # C0: before \t
        range(0x0B, 0x0D),   # C0: between \n and \r
        range(0x0E, 0x20),   # C0: after \r up to space
        range(0x7F, 0xA0),   # DEL + C1 controls
    )
)
_CONTROL_CHAR_RE = re.compile("[%s]" % re.escape(_CONTROL_CHARS))


def strip_log_output(s: str) -> str:
    """Strip ANSI escape sequences and control characters from log output.
    
    Preserves \\t, \\n, and \\r since these are meaningful in log formatting.
    """
    s = _ANSI_ESCAPE_RE.sub("", s)
    return _CONTROL_CHAR_RE.sub("", s)


@lru_cache(maxsize=1)
def get_core_v1() -> client.CoreV1Api:
    """
    Return a cached CoreV1Api client. Attempts in-cluster config first, then falls back
    to local kubeconfig for development/testing. Raises on complete failure.
    """
    try:
        config.load_incluster_config()
        logger.debug("Loaded in-cluster Kubernetes config")
        return client.CoreV1Api()
    except Exception as incluster_err:
        logger.info(
            f"In-cluster config not available, attempting kubeconfig fallback: {incluster_err}"
        )
        try:
            logger.debug("Loaded local kubeconfig from %s", cfg.KUBE_CONFIG_PATH)
            config.load_kube_config(config_file=cfg.KUBE_CONFIG_PATH)
            return client.CoreV1Api()
        except Exception as kubeconfig_err:
            logger.error(
                "Failed to configure Kubernetes client using both in-cluster and kubeconfig: "
                f"{kubeconfig_err}"
            )
            raise


@lru_cache(maxsize=1)
def get_apps_v1() -> client.AppsV1Api:
    """
    Return a cached AppsV1Api client. Reuses the same config loaded by get_core_v1().
    """
    get_core_v1()
    return client.AppsV1Api()


@lru_cache(maxsize=1)
def get_batch_v1() -> client.BatchV1Api:
    """
    Return a cached BatchV1Api client. Reuses the same config loaded by get_core_v1().
    """
    get_core_v1()
    return client.BatchV1Api()


class _CoreV1Proxy:
    """Proxy exposing CoreV1Api methods while being easy to patch in tests.

    Methods are defined explicitly to avoid resolving the underlying client during
    attribute patching in tests, allowing `mocker.patch("utils.kube_client.v1.<method>")`
    to work without a live cluster or kubeconfig.
    """

    def list_namespaced_event(self, *args, **kwargs):
        return get_core_v1().list_namespaced_event(*args, **kwargs)

    def read_namespaced_pod_log(self, *args, **kwargs):
        return get_core_v1().read_namespaced_pod_log(*args, **kwargs)

    def list_namespaced_pod(self, *args, **kwargs):
        return get_core_v1().list_namespaced_pod(*args, **kwargs)

    def read_namespaced_pod(self, *args, **kwargs):
        return get_core_v1().read_namespaced_pod(*args, **kwargs)


# Public proxy used by module functions and tests
v1 = _CoreV1Proxy()


class _AppsV1Proxy:
    """Proxy exposing AppsV1Api methods while being easy to patch in tests."""

    def list_pod_for_all_namespaces(self, *args, **kwargs):
        return get_core_v1().list_pod_for_all_namespaces(*args, **kwargs)

    def list_job_for_all_namespaces(self, *args, **kwargs):
        return get_batch_v1().list_job_for_all_namespaces(*args, **kwargs)

    def list_cron_job_for_all_namespaces(self, *args, **kwargs):
        return get_batch_v1().list_cron_job_for_all_namespaces(*args, **kwargs)

    def list_stateful_set_for_all_namespaces(self, *args, **kwargs):
        return get_apps_v1().list_stateful_set_for_all_namespaces(*args, **kwargs)

    def list_deployment_for_all_namespaces(self, *args, **kwargs):
        return get_apps_v1().list_deployment_for_all_namespaces(*args, **kwargs)

    def read_namespaced_stateful_set(self, *args, **kwargs):
        return get_apps_v1().read_namespaced_stateful_set(*args, **kwargs)

    def read_namespaced_deployment(self, *args, **kwargs):
        return get_apps_v1().read_namespaced_deployment(*args, **kwargs)

    def patch_namespaced_deployment(self, *args, **kwargs):
        return get_apps_v1().patch_namespaced_deployment(*args, **kwargs)

    def patch_namespaced_stateful_set(self, *args, **kwargs):
        return get_apps_v1().patch_namespaced_stateful_set(*args, **kwargs)


apps_v1 = _AppsV1Proxy()


def get_pod_failure_events(namespace: str, pod_name: str) -> list:
    """
    Retrieve events for a specific pod in a given namespace.

    Args:
        namespace (str): The namespace of the pod.
        pod_name (str): The name of the pod.
    """
    try:
        field_selector = (
            f"involvedObject.name={pod_name},involvedObject.namespace={namespace}"
        )
        events = v1.list_namespaced_event(
            namespace=namespace, field_selector=field_selector
        )
        return events.items
    except Exception as e:
        logger.error(
            f"Exception when retrieving events for pod {pod_name} in namespace {namespace}: {e}"
        )
        return []


def get_pod_logs(
    namespace: str,
    pod_name: str,
    tail_lines: int = DEFAULT_POD_LOG_LINES,
    timestamps=True,
    previous=False,
) -> str:
    """
    Retrieve logs for a specific pod in a given namespace.

    Args:
        namespace (str): The namespace of the pod.
        pod_name (str): The name of the pod.
        tail_lines (int): Number of lines from the end of the logs to retrieve. Default is 100.
        timestamps (bool): Whether to include timestamps in the logs. Default is True.
        previous (bool): Whether to retrieve logs from the previous instance of the container. Default is False.
    """
    try:
        log_response = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines,
            timestamps=timestamps,
            previous=previous,
        )
        return strip_log_output(log_response)
    except Exception as e:
        logger.error(
            f"Exception when retrieving logs for pod {pod_name} in namespace {namespace}: {e}"
        )
        return ""
