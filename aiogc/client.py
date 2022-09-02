import functools
import aiohttp

from typing import Generator, Literal, Optional

from . import GOOGLEAPIS_BASE_URL
from .models import Credentials, Event


def fresh_credentials(func):
    "a decorator to make sure credentials stay fresh, `self` argument is required"
    @functools.wraps(func)
    async def wrapper(self: "EventsManager", *args, **kwargs):
        if not self.creds.is_fresh():
            await self.creds.refresh(self.session)
        return await func(self, *args, **kwargs)

    return wrapper


class EventsManager:
    "a wrapper class for making stuff possible in a simpler way"

    def __init__(
        self,
        credentials: Credentials,
        timezone: str,
        calendar_id: str = "primary",
        session: Optional[aiohttp.ClientSession] = None,
        version: str = "v3",
    ):
        """
        a shared state holder for unchanging variables in events managing

        Args:
            credentials (Credentials): aiogc.Credentials instance
            timezone (str): `Europe/London` for example
            calendar_id (str, optional): id of the calendar to work with. Defaults to "primary".
            session (aiohttp.ClientSession, optional): Session instance if you need something special. Defaults to None.
            version (str, optional): api version. not recommended to change. Defaults to "v3".
        """
        self.creds = credentials
        self.tz = timezone
        self.calendar_id = calendar_id
        self.session = session
        self.version = version

    @property
    def header(self) -> dict[str, str]:
        "a dict to pass as a header"
        return {"Authorization": f"Bearer {self.creds.access_token}"}

    @property
    def api_url(self):
        "general url used for the requests"
        return f"{GOOGLEAPIS_BASE_URL}/calendar/{self.version}/calendars/{self.calendar_id}/events"

    async def start(self):
        "for using instead of async with block"
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self

    async def stop(self):
        "for using instead of async with block"
        await self.session.close()

    async def __aenter__(self):
        return await self.start()

    async def __aexit__(self, *args, **kwargs):
        await self.stop()

    @fresh_credentials
    async def list(
        self,
        *,
        maxResults: Optional[int] = None,
        orderBy: Literal["startTime", "updated", None] = None,
        q: Optional[str] = None,
        singleEvents: Literal["true", "false", None] = None,
        syncToken: Optional[str] = None,
        timeMax: Optional[str] = None,
        timeMin: Optional[str] = None,
        updatedMin: Optional[str] = None,
        **params,
    ) -> Generator[Event, None, None]:
        """
        refer to https://developers.google.com/calendar/api/v3/reference/events/list
        """
        extra_params = {
            "maxResults": maxResults,
            "orderBy": orderBy,
            "q": q,
            "singleEvents": singleEvents,
            "syncToken": syncToken,
            "timeMax": timeMax,
            "timeMin": timeMin,
            "updatedMin": updatedMin,
            "timeZone": self.tz,
        }
        for key, value in extra_params.items():
            if value:
                params[key] = value
        async with self.session.get(
            url=self.api_url,
            params=params,
            headers=self.header,
            raise_for_status=True,
        ) as r:
            return (Event(**item) for item in (await r.json())["items"])

    @fresh_credentials
    async def insert(
        self, event: Event, sendUpdates: Literal["all", "externalOnly", "none"] = None
    ) -> Event:
        """
        refer to https://developers.google.com/calendar/api/v3/reference/events/insert
        """
        async with self.session.post(
            url=self.api_url,
            json=event.dict(),
            headers=self.header,
            params={"sendUpdates": sendUpdates} if sendUpdates else {},
            raise_for_status=True,
        ) as r:
            return Event(**(await r.json()))

    @fresh_credentials
    async def update(
        self, event: Event, sendUpdates: Literal["all", "externalOnly", "none"] = None
    ) -> Event:
        """
        refer to https://developers.google.com/calendar/api/v3/reference/events/update
        """
        async with self.session.put(
            url=f"{self.api_url}/{event.id}",
            json=event.dict(),
            headers=self.header,
            params={"sendUpdates": sendUpdates} if sendUpdates else {},
            raise_for_status=True,
        ) as r:
            return Event(**(await r.json()))

    @fresh_credentials
    async def delete(
        self, evend_id: str, sendUpdates: Literal["all", "externalOnly", "none"] = None
    ) -> None:
        """
        refer to https://developers.google.com/calendar/api/v3/reference/events/delete
        """
        await self.session.delete(
            url=f"{self.api_url}/{evend_id}",
            headers=self.header,
            params={"sendUpdates": sendUpdates} if sendUpdates else {},
            raise_for_status=True,
        )

    @fresh_credentials
    async def get(self, evend_id: str, timezone: Optional[str] = None) -> None:
        """
        refer to https://developers.google.com/calendar/api/v3/reference/events/get
        """
        await self.session.get(
            url=f"{self.api_url}/{evend_id}",
            headers=self.header,
            params={"timeZone": timezone or self.tz},
            raise_for_status=True,
        )
