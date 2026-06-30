import os
import json
import threading
import warnings
import requests
from dotenv import load_dotenv

load_dotenv()

_BASE_URL = os.getenv("LLM_USAGE_MONITOR_BASE_URL", "")
_APP_ID = os.getenv("LLM_USAGE_MONITOR_APP_ID", "")
_MODEL_NAME = os.getenv("LLM_USAGE_MONITOR_MODEL_NAME", "")
_API_KEY = os.getenv("LLM_USAGE_MONITOR_API_KEY", "")
_CALL_TYPE_L = os.getenv("LLM_USAGE_MONITOR_CALL_TYPE_L_INVOKE", "l_invoke")
_CALL_TYPE_A = os.getenv("LLM_USAGE_MONITOR_CALL_TYPE_A_INVOKE", "a_invoke")


def _post(call_type: str, metadata: str) -> None:
    if not _BASE_URL:
        return
    try:
        requests.post(
            f"{_BASE_URL}/log-metadata/",
            params={"app_id": _APP_ID, "call_type": call_type, "model_name": _MODEL_NAME},
            headers={"Authorization": f"Bearer {_API_KEY}"},
            json={"metadata": metadata},
            timeout=10,
        )
    except Exception as e:
        warnings.warn(f"LLM usage monitor POST failed: {e}")


def _fire(call_type: str, metadata: str) -> None:
    t = threading.Thread(target=_post, args=(call_type, metadata), daemon=True)
    t.start()


def log_llm_invoke(response) -> None:
    """Log after a direct LLM invocation (l_invoke). Fire-and-forget, never raises."""
    if not _BASE_URL:
        return
    try:
        metadata = json.dumps(response.model_dump(), default=str)
        _fire(_CALL_TYPE_L, metadata)
    except Exception as e:
        warnings.warn(f"LLM monitor serialization failed (l_invoke): {e}")


def log_agent_invoke(result) -> None:
    """Log after an agent invocation (a_invoke). Fire-and-forget, never raises."""
    if not _BASE_URL:
        return
    try:
        from langchain_core.load import dumps as lc_dumps
        metadata = lc_dumps(result)
        _fire(_CALL_TYPE_A, metadata)
    except Exception as e:
        warnings.warn(f"LLM monitor serialization failed (a_invoke): {e}")
