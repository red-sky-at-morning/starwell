from aiohttp_sse_client2 import client as sse_client
import requests
import asyncio
import json

from webhooks import members
import response_functions

# on startup, subscribe to sse events
def startup(self) -> None:
    global API_KEY
    with open("meta/SHEAF.txt") as file:
        API_KEY = file.readline().strip()

    global sse_events
    sse_events = sse_client.EventSource("https://many.skiesatmorning.com/v1/fronts/stream", headers={
        "Authorization": f"Bearer {API_KEY}"
    })

# then on heartbeat check for events
# if events change status according to self.sheaf_status
async def heartbeat(self) -> None:
    try:
        async with sse_events:
            async for event in sse_events:
                assert isinstance(event, sse_client.MessageEvent)
                data = json.JSONDecoder().decode(event.data)
                data["event_type"] = event.type
                print(data)
                
                fronts = []
                match data.get("event_type"):
                    case "snapshot":
                        fronts = data.get("fronting")
                        print(fronts)
                    case "front_change":
                        fronts = data.get("after")
                        print(fronts)
                    case "ping":
                        return

                custom_status = []
                for front in data.get("fronts"):
                    if front.get("custom_status", ""):
                        custom_status.append(front.get("custom_status", ""))
                self.sheaf_status["custom_status"] = ", ".join(custom_status)
                self.sheaf_status["members"] = []
                for member in fronts:
                    member = requests.get(f"https://many.skiesatmorning.com/v1/members/{member}", headers={
                        "Authorization": f"Bearer {API_KEY}"
                    })
                    assert isinstance(member, requests.Response)
                    if (not member.ok):
                        fronts.remove(member)
                    member = member.json().get("pluralkit_id", "_")
                    member = members.get_member(member)
                    self.sheaf_status["members"].append(member)
                print("sheaf_status assigned")
                await response_functions.presence(self, {"type":"presence","default":True},None)

    except asyncio.exceptions.CancelledError:
        startup(self)