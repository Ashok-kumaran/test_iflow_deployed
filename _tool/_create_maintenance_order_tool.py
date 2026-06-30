import os
import httpx
from typing import Dict, Any
from json import JSONDecodeError

CPI_BASE_URL = os.getenv("CPI_BASE_URL")
CPI_BASIC_AUTH_USERNAME = os.getenv("CPI_BASIC_AUTH_USERNAME")
CPI_BASIC_AUTH_PASSWORD = os.getenv("CPI_BASIC_AUTH_PASSWORD")

_MAINTENANCE_ORDER_ENDPOINT = "/http/create_maintenance_order"

_MAINTENANCE_ORDER_PAYLOAD = {
    "MaintenanceOrderType": "YBA1",
    "MaintenanceOrderDesc": "Test",
    "MaintOrdBasicStartDateTime": "2026-06-04T10:40:00+05:30",
    "MaintOrdBasicEndDateTime": "2026-07-22T07:17:00+05:30",
    "MainWorkCenter": "RES-0100",
    "MainWorkCenterPlant": "1710",
    "MaintenancePlanningPlant": "1710",
    "MaintenancePlant": "1710",
    "FunctionalLocation": "1710-SPA-SAC-PLAR1-CLR2",
    "to_MaintenanceOrderOperation": {
        "results": [
            {
                "MaintenanceOrderOperation": "0010",
                "MaintenanceOrderSubOperation": "",
                "OperationControlKey": "YBM1",
                "WorkCenter": "RES-0100",
                "Plant": "1710",
                "OperationDescription": "OP1",
                "NumberOfCapacities": 0,
                "OperationWorkPercent": 0,
                "OperationCalculationControl": "",
                "ActivityType": "",
                "DeliveryTimeInDays": "0",
                "MaintenanceObjectListItem": 0,
                "AllMaintOrdCompCmtdQtsAreKept": False,
                "to_MaintOrderOpComponent_2": {
                    "results": [
                        {
                            "Product": "SP001",
                            "BaseUnit": "PC",
                            "Plant": "1710",
                            "QuantityInUnitOfEntry": "1",
                            "MaintComponentItemCategory": "L",
                            "GoodsMovementIsAllowed": True,
                            "QuantityIsFixed": True,
                            "MatlCompIsMarkedForBackflush": False,
                            "MaintOrdOpCompIsBulkProduct": False,
                            "RqmtDateIsEnteredManually": False,
                            "SrvcSchedgIsAlignedWthOpWrkCtr": False
                        }
                    ]
                }
            }
        ]
    }
}


async def create_maintenance_order_tool() -> Dict[str, Any]:
    try:
        return await _create_maintenance_order_async()

    except Exception as e:
        print(f"===> Exception in create_maintenance_order_tool function [Exception]: {e}")
        raise

    finally:
        pass


async def _create_maintenance_order_async() -> Dict[str, Any]:
    try:
        url = f"{CPI_BASE_URL}{_MAINTENANCE_ORDER_ENDPOINT}"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                auth=(CPI_BASIC_AUTH_USERNAME, CPI_BASIC_AUTH_PASSWORD),
                json=_MAINTENANCE_ORDER_PAYLOAD,
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
            "response_body": response_body
        }

    except httpx.HTTPStatusError as e:
        print(f"""===> Exception in _create_maintenance_order_async function [HTTPStatusError]: {e}
                       status code: {e.response.status_code}
                       response text: {e.response.text}""")
        raise

    except httpx.RequestError as e:
        print(f"===> Exception in _create_maintenance_order_async function [RequestError]: {e}")
        raise

    except JSONDecodeError as e:
        print(f"===> Exception in _create_maintenance_order_async function [JSONDecodeError]: {e}")
        raise

    except Exception as e:
        print(f"===> Exception in _create_maintenance_order_async function [Exception]: {e}")
        raise

    finally:
        pass
