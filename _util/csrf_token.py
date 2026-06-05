import os
import httpx
import asyncio
from dotenv import load_dotenv
from json import JSONDecodeError
# from _util.token_gen import get_access_token
from _util.token_manager import TokenManager

API_BASE_URL = os.getenv("API_BASE_URL")

async def get_csrf_token():
    try:
        # access_token = await get_access_token()
        access_token = await TokenManager.get_token()
        url = (
            f"{API_BASE_URL}"
            f"/"
        )

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json", # "application/xml|json"
            "X-CSRF-Token": "Fetch"
        }

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, headers=headers)

        response.raise_for_status()
        csrf_token = response.headers.get("x-csrf-token", "")
        return csrf_token

    except httpx.HTTPStatusError as e:
        print(f"""===> Exception in get_csrf_token function [HTTPStatusError]: {e}
                       status code: {e.response.status_code}
                       response text: {e.response.text}""")
        raise 

    except httpx.RequestError as e:
        print(f"""===> Exception in get_csrf_token function [RequestError]: {e}""")
        raise 

    except JSONDecodeError as e:
        print(f"""===> Exception in get_csrf_token function [JSONDecodeError]: {e}""")
        raise 

    except KeyError as e:
        print(f"""===> Exception in get_csrf_token function [KeyError]: {e}""")
        raise 

    except Exception as e:
        print(f"""===> Exception in get_csrf_token function [Exception]: {e}""")
        raise 
    
    finally:
        pass

