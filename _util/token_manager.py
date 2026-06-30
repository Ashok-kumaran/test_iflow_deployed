import os
import time
import httpx
import asyncio
from dotenv import load_dotenv
from json import JSONDecodeError

load_dotenv()

API_OAUTH_CLIENT_ID = os.getenv("API_OAUTH_CLIENT_ID")
API_OAUTH_CLIENT_SECRET = os.getenv("API_OAUTH_CLIENT_SECRET")
API_OAUTH_TOKEN_URL = os.getenv("API_OAUTH_TOKEN_URL")

CPI_OAUTH_CLIENT_ID = os.getenv("CPI_OAUTH_CLIENT_ID")
CPI_OAUTH_CLIENT_SECRET = os.getenv("CPI_OAUTH_CLIENT_SECRET")
CPI_OAUTH_TOKEN_URL = os.getenv("CPI_OAUTH_TOKEN_URL")

AICORE_CLIENT_ID = os.getenv("AICORE_CLIENT_ID")
AICORE_CLIENT_SECRET = os.getenv("AICORE_CLIENT_SECRET")
AICORE_AUTH_URL = os.getenv("AICORE_AUTH_URL")

class TokenManager:
    # these are like global variables that are shared across the server untill server stops
    # so only one application level token, not like an user level token or new token for each tool
    # so only one application level token, not like an user level token or new token for each tool
    _access_token: str | None = None
    _expires_at: float = 0.0
    '''
    - without Lock(), TOCTOU (Time Of Check → Time Of Use) bug will raise
    - with Lock(), [get_token Coroutine A] enters lock and [get_token Coroutine B] waits
    - without Lock(), [get_token Coroutine A] enters, then awaited, then [get_token Coroutine B] enters. Which means
      two OAuth calls.
    - This Lock(), definitely needed because variables like _access_token & _expires_at are shared state varaibles or like 
      global variables across the servers. So without Lock() last couroutine may overwrite it.
    '''
    _lock = asyncio.Lock()

    @classmethod
    async def get_token(cls) -> str:
        async with cls._lock:
            now = time.time()
            print(f'===> now: {now} seconds | t0 (sec) is the specific point in timeline elapsed since 00:00:00 UTC on January 1, 1970.')
            
            # Reuse token if still valid
            if cls._access_token and now < cls._expires_at:
                print(f'===> {now} < {cls._expires_at}')
                return cls._access_token

            # Else fetch a new one
            token, expires_in = await cls._fetch_new_token()
            print(f'===> expires_in: {expires_in} seconds | Delta t (sec) is a duration, not a point. So token expires in Delta t from t0')
            
            # Refresh a bit earlier than actual expiry (safety margin)
            cls._access_token = token
            cls._expires_at = now + expires_in - 60
            print(f'===> _expires_at: {cls._expires_at} seconds | this gives the expected specific point in timeline for the token expiration with safety margin of 60 seconds')

            return cls._access_token

    @staticmethod
    async def _fetch_new_token() -> tuple[str, int]:
        if not API_OAUTH_TOKEN_URL or not API_OAUTH_CLIENT_ID or not API_OAUTH_CLIENT_SECRET:
            raise ValueError("API OAuth configuration is missing")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    API_OAUTH_TOKEN_URL,
                    data={"grant_type": "client_credentials"},
                    auth=(API_OAUTH_CLIENT_ID, API_OAUTH_CLIENT_SECRET),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

            response.raise_for_status()
            data = response.json()

            return data["access_token"], data["expires_in"]
        
        except httpx.HTTPStatusError as e:
            print(f"""===> Exception in get_access_token function [HTTPStatusError]: {e}
                        status code: {e.response.status_code}
                        response text: {e.response.text}""")
            raise 

        except httpx.RequestError as e:
            print(f"""===> Exception in get_access_token function [RequestError]: {e}""")
            raise 

        except JSONDecodeError as e:
            print(f"""===> Exception in get_access_token function [JSONDecodeError]: {e}""")
            raise 

        except KeyError as e:
            print(f"""===> Exception in get_access_token function [KeyError]: {e}""")
            raise 

        except Exception as e:
            print(f"""===> Exception in get_access_token function [Exception]: {e}""")
            raise 

        finally:
            pass


class CPITokenManager:
    # Separate token manager for CPI runtime calls
    _access_token: str | None = None
    _expires_at: float = 0.0
    _lock = asyncio.Lock()

    @classmethod
    async def get_token(cls) -> str:
        async with cls._lock:
            now = time.time()
            print(f'===> CPI now: {now} seconds | t0 (sec) is the specific point in timeline elapsed since 00:00:00 UTC on January 1, 1970.')
            
            # Reuse token if still valid
            if cls._access_token and now < cls._expires_at:
                print(f'===> {now} < {cls._expires_at}')
                return cls._access_token

            # Else fetch a new one
            token, expires_in = await cls._fetch_new_token()
            print(f'===> CPI expires_in: {expires_in} seconds | Delta t (sec) is a duration, not a point. So token expires in Delta t from t0')
            
            # Refresh a bit earlier than actual expiry (safety margin)
            cls._access_token = token
            cls._expires_at = now + expires_in - 60
            print(f'===> CPI _expires_at: {cls._expires_at} seconds | this gives the expected specific point in timeline for the token expiration with safety margin of 60 seconds')

            return cls._access_token

    @staticmethod
    async def _fetch_new_token() -> tuple[str, int]:
        if not CPI_OAUTH_TOKEN_URL or not CPI_OAUTH_CLIENT_ID or not CPI_OAUTH_CLIENT_SECRET:
            raise ValueError("CPI OAuth configuration is missing")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    CPI_OAUTH_TOKEN_URL,
                    data={"grant_type": "client_credentials"},
                    auth=(CPI_OAUTH_CLIENT_ID, CPI_OAUTH_CLIENT_SECRET),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )

            response.raise_for_status()
            data = response.json()

            return data["access_token"], data["expires_in"]
        
        except httpx.HTTPStatusError as e:
            print(f"""===> Exception in CPI get_access_token function [HTTPStatusError]: {e}
                        status code: {e.response.status_code}
                        response text: {e.response.text}""")
            raise 

        except httpx.RequestError as e:
            print(f"""===> Exception in CPI get_access_token function [RequestError]: {e}""")
            raise 

        except JSONDecodeError as e:
            print(f"""===> Exception in CPI get_access_token function [JSONDecodeError]: {e}""")
            raise 

        except KeyError as e:
            print(f"""===> Exception in CPI get_access_token function [KeyError]: {e}""")
            raise 

        except Exception as e:
            print(f"""===> Exception in CPI get_access_token function [Exception]: {e}""")
            raise 

        finally:
            pass


class AICoreTokenManager:
    _access_token: str | None = None
    _expires_at: float = 0.0
    _lock = asyncio.Lock()

    @classmethod
    async def get_token(cls) -> str:
        async with cls._lock:
            now = time.time()
            if cls._access_token and now < cls._expires_at:
                return cls._access_token
            token, expires_in = await cls._fetch_new_token()
            cls._access_token = token
            cls._expires_at = now + expires_in - 60
            return cls._access_token

    @staticmethod
    async def _fetch_new_token() -> tuple[str, int]:
        if not AICORE_AUTH_URL or not AICORE_CLIENT_ID or not AICORE_CLIENT_SECRET:
            raise ValueError("SAP AI Core OAuth configuration is missing")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    AICORE_AUTH_URL,
                    data={"grant_type": "client_credentials"},
                    auth=(AICORE_CLIENT_ID, AICORE_CLIENT_SECRET),
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            response.raise_for_status()
            data = response.json()
            return data["access_token"], data["expires_in"]

        except httpx.HTTPStatusError as e:
            print(f"""===> Exception in AiCore get_access_token function [HTTPStatusError]: {e}
                        status code: {e.response.status_code}
                        response text: {e.response.text}""")
            raise

        except httpx.RequestError as e:
            print(f"===> Exception in AiCore get_access_token function [RequestError]: {e}")
            raise

        except JSONDecodeError as e:
            print(f"===> Exception in AiCore get_access_token function [JSONDecodeError]: {e}")
            raise

        except KeyError as e:
            print(f"===> Exception in AiCore get_access_token function [KeyError]: {e}")
            raise

        except Exception as e:
            print(f"===> Exception in AiCore get_access_token function [Exception]: {e}")
            raise


if __name__ == "__main__":
    token = asyncio.run(TokenManager.get_token())
    print(token)