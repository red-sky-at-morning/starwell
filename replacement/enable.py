import discord
import json

with open("replacement/meta/servers.json", "r") as file:
    data:dict = json.load(file)

# WHAT IS THE FUCKING THING
# when disabled, return False.
# when enabled, return True.
# default: disabled -> False

def handle(type:str, command:list, channel:discord.TextChannel, server:discord.Guild) -> list[dict]:
    if len(command) <= 2:
        return []
    # expect_len = 4

    # match command[1].lower():
        # case "enable" | "disable":
    state = bool(command[1].lower() == "enable")
    reason = None
    if len(command) >= 4:
        reason = command[-1].removeprefix(f"&{type} {command[1]} ")
    match type:
        case "chmod":
            set_channel_val(channel.id, server.id, state, reason)
        case "svmod":            
            set_server_val(server.id, state, reason)
    return get_formatted_channel(channel, server)

def get_server_val(server:int) -> bool:
    sv = data.get(server.__str__(), data.get("_"))
    return sv.get("enabled")

def get_channel_val(channel:int, server:int) -> bool:
    sv = data.get(server.__str__(), data.get("_"))
    invert = get_server_val(server)
    if invert:
        return (channel.__str__() not in sv.get("blacklist", {}).keys())
    else:
        return (channel.__str__() in sv.get("whitelist", []))

def get_channel_state(channel:int, server:int) -> bool:    
    if not get_channel_val(channel, server):
        return False
    
    return True

def get_channel_reason(channel:int, server:int) -> str | None:
    if not get_server_val(server):
        return data.get(server.__str__(), data.get("_")).get("reason", None)
    else:
        return data.get(server.__str__(), data.get("_")).get("blacklist",{}).get(channel.__str__(), None)

def get_formatted_channel(channel:discord.TextChannel, server:discord.Guild) -> list[dict]:
    # (channel_name) is (state) because of (reason:server>channel)
    state = get_channel_state(channel.id, server.id)
    reason = get_channel_reason(channel.id, server.id)

    desc = f"<#{channel.id}> is **{"enabled" if state else "disabled"}**"
    if not state:
        desc += f" because of: {reason if reason is not None else "(no reason provided)"}"
    elif (channel.id.__str__() in data.get(server.id.__str__(), {}).get("whitelist", [])):
        desc += f" (whitelist)"
    embed = discord.Embed(color=discord.Color.random(),description=desc)
    
    return [{"type":"message","message":"","embed":[embed],"except":True}]

def set_channel_val(channel:int, server:int, state:bool, reason: str | None) -> None:
    if data.get(server.__str__(), None) is None:
        data[server.__str__()] = {"enabled":True,"reason":None,"blacklist":{},"whitelist":[]}

    if state:
        data[server.__str__()]["whitelist"].append(channel.__str__())
        if (channel.__str__() in data[server.__str__()]["blacklist"].keys()):
            del data[server.__str__()]["blacklist"][channel.__str__()]
    else:
        if (channel.__str__() in data[server.__str__()]["whitelist"]):
            data[server.__str__()]["whitelist"].remove(channel.__str__())
        data[server.__str__()]["blacklist"][channel.__str__()] = reason
    with open("replacement/meta/servers.json", "w") as file:
        json.dump(data, file)

def set_server_val(server:int, state:bool, reason: str | None) -> None:
    if data.get(server.__str__(), None) is None:
        data[server.__str__()] = {"enabled":True,"reason":None,"blacklist":{},"whitelist":[]}

    data[server.__str__()]["enabled"] = state
    data[server.__str__()]["reason"] = reason
    with open("replacement/meta/servers.json", "w") as file:
        json.dump(data, file)