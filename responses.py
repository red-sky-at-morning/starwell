import json
import random
import discord

from webhooks import members

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
    # response += dev_commands(m_list, message, channel_id, user_id, server)
    response += commands(m_list, message, channel_id, user_id, server)
    # response += single_args_m(m_list[0], message, channel_id, user_id, server)
    response += message_replacement(m_list, message, channel_id, user_id, server, kwargs.get("mentioned"))
    return response

def commands(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int) -> list[dict]:
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
        case "test":
            response += [{"type":"message","message":"Hello world!","except":True}]
        case "test2":
            response += [{"type":"message","message":"Next message should be from a webhook...","except":True},{"type":"webhook","id":"_"},{"type":"message","message":"test"}]
        case "useradd":
            response += members.add_member()
        case "usermod":
            response += members.edit_user()
    return response

def message_replacement(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int, mentioned:bool) -> list[dict]:
    response:list = []
    return response