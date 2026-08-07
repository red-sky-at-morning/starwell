import discord
import httpx
import json
import datetime
import random

from webhooks import members

# sheaf [command]
# command in (STATUS, MODE)
# status: no parameters
# mode: no parameters -> returns sheaf mode
# mode: parameter -> check for permissions, set self.sheaf_mode
# these are async functions because we need to check values at '''compile''' time

with open("meta/params.json", "r") as params:
    params_json = json.load(params)
    trusted_ids = params_json.get("dev_ids")
    self_id = params_json.get("id")

with open("meta/SHEAF.txt") as file:
        API_KEY = file.readline().strip()

def handle(command: list[str], user_id, message):
    match command[1].lower():
        case "status":
            return [{"type":"call","call":get_sheaf_status,"wait_type":None,"message":message}]
        case "mode":
            if len(command) <= 3:
                return [{"type":"call","call":get_sheaf_mode,"wait_type":None,"message":message}]
            else:
                if not check_user_id(user_id):
                    return [{"type":"message","message":"You cannot change sheaf integration modes!","except":True}]
                else:
                    return set_sheaf_mode(command[2])
        case "disabled" | "default" | "full":
            if not check_user_id(user_id):
                return [{"type":"message","message":"You cannot change sheaf integration modes!","except":True}]
            else:
                return set_sheaf_mode(command[1])
        case "_":
            return [{"type":"message","message":"I don't know how to do that! Try `&sheaf status`","except":True}]

def check_user_id(id):
    return (id in trusted_ids)

def set_sheaf_mode(mode) -> list[dict]:
    return [{"type":"special","action":"set_sheaf_mode","mode":mode.upper()}]

async def get_sheaf_mode(self, id, message):
    return {"type":"message","message":f"Sheaf integration mode is currently set to {self.sheaf_mode}", "except":True}

async def get_sheaf_status(self, id, message) -> list[dict]:
    if self.sheaf_mode == "DISABLED":
        embed = discord.Embed(title="many skies at morning",description="Sheaf integration is currently disabled. Check back later!")
        return {"type":"message","message":"","embed":[embed],"except":True}
    
    curr = httpx.get(f"https://many.skiesatmorning.com/v1/fronts/current", headers={
        "Authorization": f"Bearer {API_KEY}"
    }).raise_for_status().json()
    
    # for each current front:
    fronts = []
    for front in curr:
        # get the current members        
        fronting_members = front.get("member_ids", [])
        member_timestamps = front.get("member_since")
        
        data = {}
        # add their ids to a list of dicts,
        # along with their `member_since` property
        for member_id in fronting_members:
            if member_timestamps.get(member_id):
                time = datetime.datetime.fromisoformat(member_timestamps.get(member_id))
            else:
                time = None
            data[member_id] = time
        
        # then, set `status` to either None or the front's custom status
        data["status"] = front.get("custom_status", None)
        fronts.append(data)
    
    # construct an embed
    embed = discord.Embed(title="many skies at morning",description=f"There {"is" if len(fronts) == 1 else "are"} {len(fronts)} current front{"" if len(fronts) == 1 else "s"}")
    # then, for each current front:
    now = datetime.datetime.now(datetime.timezone.utc)
    colors = []
    
    for i, front in enumerate(fronts):
        # get the status
        status = front.get("status")
        del front["status"]
        
        # then, for each member:
        members_txt = []
        for member_id, timestamp in front.items():
            member_data = httpx.get(f"https://many.skiesatmorning.com/v1/members/{member_id}", headers={
                "Authorization": f"Bearer {API_KEY}"
            }).raise_for_status().json()

            # get the starwell member associated
            member_key = member_data.get("pluralkit_id")
            member = members.get_member(member_key)
            
            # get their name, pronouns, and short description
            initial = member.get("names", [])[member.get("name")][0].upper()
            # {emoji} {name}/{nickname} ({pronouns})
            # {desc_short}
            colors.append(member.get("color"))
            
            # calculate the time theyve been fronting
            time = (now-timestamp).total_seconds()
            time = time // 3600
            if time == 0:
                time = "just now"
            else:
                time = f"{int(time)}h"
            
            # add them to a bulleted list
            list_txt = f"- {member.get("emoji", initial)} "
            list_txt +=  f"{member.get("names", [])[member.get("name")]}/{members.get_nickname_by_id(member_key, message.guild)} "
            list_txt += f"({member.get("pronouns")})"
            if self.sheaf_mode == "FULL":
                list_txt += f" for {time}"
            # list_txt += f"\n*{member.get("desc-short")}*"
            members_txt.append(list_txt)
        
        # then add a new field corresponding to the front
        members_txt = "\n".join(members_txt)
        if (status is not None) and (self.sheaf_mode == "FULL"):
            members_txt = f"This front is currently {status}\n" + members_txt
        
        embed.add_field(name=f"Front {i+1}",value=members_txt)
    
    embed.color = discord.Color.from_str(colors[random.randint(0, len(colors)-1)])
    # return the message with the embed
    return [{"type":"message","message":"","embed":[embed],"except":True}]