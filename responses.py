import json
import random
import discord

from webhooks import members
from replacement import replacement
from replacement import enable

with open("meta/params.json", "r") as params:
    params_json = json.load(params)
    cmd_prefix:str = params_json.get("cmd_prefix")
    trusted_ids = params_json.get("dev_ids")
    hook_id = 0

def handle_message(message: discord.Message, content:str, channel_id, user_id:int, server:int, **kwargs) -> list[dict]:
    if not content:
        return message_replacement(content, message, channel_id, user_id, server, kwargs.get("ap"), kwargs.get("curr"), kwargs.get("default"))
    m_list:list = content.split()
    m_list[0] = m_list[0].lower()
    m_list.append(content)
    response:list = []
    response += message_replacement(content, message, channel_id, user_id, server, kwargs.get("ap"), kwargs.get("curr"), kwargs.get("default"))
    response += public_commands(m_list, message, channel_id, user_id, server, kwargs.get("ap"))
    response += member_commands(m_list, message, channel_id, user_id, server, kwargs.get("ap"), kwargs.get("curr"))
    response += reply_commands(m_list, message, channel_id, user_id, server, kwargs.get("ap"))
    return response

def public_commands(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int, ap:bool) -> list[dict]:
    response:list = []
    if command[0][0] != cmd_prefix:
        return response
    # public commands
    match command[0][1:]:
        case "member":
            response += members.member_info(command[1].lower())
        case "chinfo":
            response += enable.get_formatted_channel(message.channel, message.channel.guild)
        case "test1":
            response += [{"type":"react","message":message,"react":discord.PartialEmoji.from_str("<:fuwaaa:1458680563375411375>")}]

    return response

def member_commands(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int, ap:bool, curr:dict):
    response:list = []
    if user_id not in trusted_ids:
        return response
    match command[0][1:]:
        case "ap":
            response += [{"type":"special","action":"toggle_ap"},{"type":"react","react":"🔴" if ap else "🟢","message":message}]
        case "setfront":
            if len(command) <= 2:
                response += [{"type": "webhook", "id":None, "default":True}]
            else:
                response += [{"type":"webhook", "id":command[1], "default":True}]
        case "useradd":
            response += members.handle_usermod(command[1], [], "add", curr.get("name", "_"))
        case "usermod":
            response += members.handle_usermod(command[1], [command[2], command[-1].split(command[2])[-1].strip()], "edit", curr.get("username", "_"))
        case "chmod" | "svmod":
            response += enable.handle(command[0][1:], command, message.channel, message.channel.guild)
    return response

def reply_commands(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int, ap:bool):
    response:list = []
    if user_id not in trusted_ids:
        return response
    if not message.reference:
        return response
    if message.reference.resolved is None:
        return response
    rp_message = message.reference.resolved

    async def check_resp(self, id, message) -> bool:
        if id in trusted_ids:
            return True
        hook = await members.get_or_make_webhook(message.channel)
        try:
            await hook.fetch_message(message.id)
            return True
        except (discord.errors.NotFound, discord.errors.HTTPException):
            return False
    
    response += [{"type":"call", "call":check_resp, "message":rp_message, "kill":True}]

    match command[0][1:]:
        case "rp":
            if len(command) > 2:
                response += [{"type":"webhook", "id": command[1]}]
            response += [{"type":"message","message":rp_message.content,"files":rp_message.attachments,"embed":list(filter(lambda x: x.type == "rich", rp_message.embeds)),"reference":rp_message.reference}]
            response += [{"type":"delete","message":message.id}, {"type":"delete","message":rp_message.id}]
        case "edit":
            response += [{"type":"edit", "id":rp_message.id, "message":command[-1].removeprefix("&edit "), "embeds":message.embeds}]
            response += [{"type":"delete","message":message.id}]
        case "del":
            response += [{"type":"delete","message":message.id}, {"type":"delete","message":rp_message.id}]
    return response

def message_replacement(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int, ap:bool, curr:dict, default:dict) -> list[dict]:
    response:list = []
    if user_id not in trusted_ids:
        return response
    response += replacement.handle_message(command, message, user_id, ap, curr, default)
    return response

def handle_react(message:discord.Message, emoji:discord.PartialEmoji, count, channel_id:int, user_id:int, server:int) -> list[dict]:
    return []
