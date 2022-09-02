# aiogc
> Async Google Calendar API Client for Python 3

## Installation

Run this in your terminal:
```commandLine
pip install git+https://github.com/MarsBatya/aiogc.git
```

## Usage
Basic usage is displayed below. Event.to_str() requires ujson, so if you don't have it installed, just `pip install ujson`.
```python
import asyncio
import arrow

from aiogc.client import EventsManager
from aiogc.models import Time, Credentials, Event


async def main():
    credentials = Credentials(
        client_id="<your_client_id>",
        client_secret="<your_client_secret>",
        scopes=["https://www.googleapis.com/auth/calendar"],
        refresh_token="<refresh token obtained w/ oauth>",
    )
    client = EventsManager(
        credentials=credentials,
        timezone="<your timezone>",
        calendar_id="<your email>",
    )
    await client.start()
    try:
        es = await client.list(maxResults=1)
        event = es.send(None)
        print(event.to_str())

        result = await client.insert(
            event=Event(
                summary="testing",
                start=Time(dateTime=arrow.now(client.tz).shift(hours=6).isoformat()),
                end=Time(dateTime=arrow.now(client.tz).shift(hours=7).isoformat()),
            )
        )
        print("created %s (%s)" % (result.id, result.summary))

        result = await client.update(
            event=Event(
                id=result.id,
                summary="testing updated",
                start=Time(dateTime=arrow.now(client.tz).shift(hours=7).isoformat()),
                end=Time(dateTime=arrow.now(client.tz).shift(hours=8).isoformat()),
            )
        )
        print("updated %s (%s)" % (result.id, result.summary))

        await client.delete(result.id)
        print("deleted %s" % result.id)
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())

```