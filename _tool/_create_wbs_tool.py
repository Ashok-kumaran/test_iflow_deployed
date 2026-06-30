import os
import random
import httpx
from typing import Dict, Any
from json import JSONDecodeError

CPI_BASE_URL = os.getenv("CPI_BASE_URL")
CPI_BASIC_AUTH_USERNAME = os.getenv("CPI_BASIC_AUTH_USERNAME")
CPI_BASIC_AUTH_PASSWORD = os.getenv("CPI_BASIC_AUTH_PASSWORD")

_WBS_ENDPOINT = "/http/create_wbs"
_PROJECT_EXTERNAL_ID_BASE = "14000000000000"


async def create_wbs_tool(
    planned_start_date: str,
    planned_end_date: str,
    project_profile_code: str = "ZMCRPPM"
) -> Dict[str, Any]:
    try:
        return await _create_wbs_async(planned_start_date, planned_end_date, project_profile_code)

    except Exception as e:
        print(f"===> Exception in create_wbs_tool function [Exception]: {e}")
        raise

    finally:
        pass


async def _create_wbs_async(
    planned_start_date: str,
    planned_end_date: str,
    project_profile_code: str
) -> Dict[str, Any]:
    try:
        suffix = random.randint(100, 999)
        project_external_id = f"{_PROJECT_EXTERNAL_ID_BASE}{suffix}"

        payload = {
            "ProjectProfileCode": project_profile_code,
            "ProjectExternalID": project_external_id,
            "PlannedStartDate": planned_start_date,
            "PlannedEndDate": planned_end_date
        }

        url = f"{CPI_BASE_URL}{_WBS_ENDPOINT}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                auth=(CPI_BASIC_AUTH_USERNAME, CPI_BASIC_AUTH_PASSWORD),
                json=payload,
                headers=headers
            )

        response.raise_for_status()
        content_type = response.headers.get("content-type", "")

        if "application/json" in content_type:
            response_body = response.json()
        else:
            response_body = response.text

        return {
            "status_code": response.status_code,
            "project_external_id": project_external_id,
            "response_body": response_body
        }

    except httpx.HTTPStatusError as e:
        print(f"""===> Exception in _create_wbs_async function [HTTPStatusError]: {e}
                       status code: {e.response.status_code}
                       response text: {e.response.text}""")
        raise

    except httpx.RequestError as e:
        print(f"===> Exception in _create_wbs_async function [RequestError]: {e}")
        raise

    except JSONDecodeError as e:
        print(f"===> Exception in _create_wbs_async function [JSONDecodeError]: {e}")
        raise

    except Exception as e:
        print(f"===> Exception in _create_wbs_async function [Exception]: {e}")
        raise

    finally:
        pass
