import os
import httpx
import asyncio
from dotenv import load_dotenv
from json import JSONDecodeError

load_dotenv()

API_OAUTH_CLIENT_ID = os.getenv("API_OAUTH_CLIENT_ID")
API_OAUTH_CLIENT_SECRET = os.getenv("API_OAUTH_CLIENT_SECRET")
API_OAUTH_TOKEN_URL = os.getenv("API_OAUTH_TOKEN_URL")

async def get_access_token():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                API_OAUTH_TOKEN_URL,
                data={"grant_type": "client_credentials"},
                auth=(API_OAUTH_CLIENT_ID, API_OAUTH_CLIENT_SECRET),
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

        response.raise_for_status()

        data = response.json()
        a_token = data["access_token"]
        return a_token

    except httpx.HTTPStatusError as e:
        """
            Request reached the server
            Server responded with HTTP status (401, 403, 500, etc.)
            e.response.status_code is guaranteed to exist
        """
        print(f"""===> Exception in get_access_token function [HTTPStatusError]: {e}
                       status code: {e.response.status_code}
                       response text: {e.response.text}""")
        raise 

    except httpx.RequestError as e:
        """
            Request never completed
            No HTTP response
            No status_code
            No response.text
        """
        print(f"""===> Exception in get_access_token function [RequestError]: {e}""")
        raise 

    except JSONDecodeError as e:
        """
            Parsing failed locally
            Error occurs after HTTP handling
            The problem is response format, not HTTP
        """
        print(f"""===> Exception in get_access_token function [JSONDecodeError]: {e}""")
        raise 

    except KeyError as e:
        """
            JSON exists
            HTTP succeeded (200 OK)
            Schema is wrong or unexpected
        """
        print(f"""===> Exception in get_access_token function [KeyError]: {e}""")
        raise 

    except Exception as e:
        """
            Unknown origin
        """
        print(f"""===> Exception in get_access_token function [Exception]: {e}""")
        raise 

    finally:
        pass
    
if __name__ == "__main__":
    token = asyncio.run(get_access_token())
    print(token)
