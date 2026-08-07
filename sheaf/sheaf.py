import httpx_sse
import httpx
# import requests
import asyncio
import json

from webhooks import members
import response_functions


# on startup, subscribe to sse events
async def startup(self) -> None:
    # global API_KEY
    with open("meta/SHEAF.txt") as file:
        API_KEY = file.readline().strip()

    async with httpx.AsyncClient(timeout=30) as client:
        async with httpx_sse.aconnect_sse(
            client, "GET", "https://many.skiesatmorning.com/v1/fronts/stream",
            headers={ "Authorization": f"Bearer {API_KEY}" }
        ) as event_source:
            async for event in event_source.aiter_sse():
                # print(event)
                if not event.data:
                    # ignore heartbeat events
                    # (they still extend the asyncClient though)
                    continue
                
                data = event.json()
                # data = json.JSONDecoder().decode(event.data)
                data["event_type"] = event.event
                # print(data)
                
                fronts = []
                match data.get("event_type"):
                    case "snapshot":
                        fronts = data.get("fronting")
                        print(fronts)
                    case "front_change":
                        fronts = data.get("after")
                        print(fronts)

                custom_status = []
                for front in data.get("fronts"):
                    if front.get("custom_status", ""):
                        custom_status.append(front.get("custom_status", ""))
                self.sheaf_status["custom_status"] = ", ".join(custom_status)
                self.sheaf_status["members"] = []
                for member in fronts:
                    member = httpx.get(f"https://many.skiesatmorning.com/v1/members/{member}", headers={
                        "Authorization": f"Bearer {API_KEY}"
                    })
                    # assert isinstance(member, requests.Response)
                    if (member.is_error):
                        fronts.remove(member)
                    member = member.json().get("pluralkit_id", "_")
                    member = members.get_member(member)
                    if not member:
                        member = members.get_member("sky")
                    self.sheaf_status["members"].append(member)
                print("sheaf_status assigned")
                await response_functions.presence(self, {"type":"presence","default":True},None)