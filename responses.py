import json
import random
import discord

from webhooks import members
from replacement import replacement

with open("meta/params.json", "r") as params:
    params_json = json.load(params)
    cmd_prefix:str = params_json.get("cmd_prefix")
    trusted_ids = params_json.get("dev_ids")

def handle_message(message: discord.Message, content:str, channel_id, user_id:int, server:int, **kwargs) -> list[dict]:
    if not content:
        return None
    m_list:list = content.split()
    m_list[0] = m_list[0].lower()
    m_list.append(content)
    response:list = []
    response += message_replacement(content, message, channel_id, user_id, server, kwargs.get("ap"), kwargs.get("curr"))
    response += commands(m_list, message, channel_id, user_id, server, kwargs.get("ap"))
    return response

def commands(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int, ap:bool) -> list[dict]:
    response:list = []
    if command[0][0] != cmd_prefix:
        return response
    # public commands
    match command[0][1:]:
        case "member":
            response += members.member_info(command[1].lower())
    # private commands
    if user_id not in trusted_ids:
        return response
    match command[0][1:]:
        # case "test":
        #     response += [{"type":"message","message":"Hello world!","except":True}]
        # case "test2":
        #     response += [{"type":"message","message":"Next message should be from a webhook...","except":True},{"type":"webhook","id":"_"},{"type":"message","message":"test"}]
        case "ap":
            response += [{"type":"special","action":"toggle_ap"},{"type":"react","react":"🔴" if ap else "🟢","message":message}]
        case "useradd":
            response += members.handle_usermod(command[1], [], "add")
        case "usermod":
            response += members.handle_usermod(command[1], [command[2], command[-1].split(command[2])[-1].strip()], "edit")
    return response

def message_replacement(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int, ap:bool, curr:dict) -> list[dict]:
    response:list = []
    response += replacement.handle_message(command, message, user_id, ap, curr)
    return response

def handle_react(message:discord.Message, emoji:discord.PartialEmoji, count, channel_id:int, user_id:int, server:int) -> list[dict]:
    return []