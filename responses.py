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
    self_id = params_json.get("id")

def handle_message(message: discord.Message, content:str, channel_id, user_id:int, server:int, **kwargs) -> list[dict]:
    if not content:
        return message_replacement(content, message, channel_id, user_id, server, kwargs.get("ap"), kwargs.get("curr"), kwargs.get("default"))
    m_list:list = content.split()
    m_list[0] = m_list[0].lower()
    m_list.append(content)
    response:list = []
    response += message_replacement(content, message, channel_id, user_id, server, kwargs.get("ap"), kwargs.get("curr"), kwargs.get("default"))
    response += public_commands(m_list, message, channel_id, user_id, server, kwargs.get("ap"), kwargs.get("curr"), kwargs.get("default"), kwargs.get("mentioned"))
    response += member_commands(m_list, message, channel_id, user_id, server, kwargs.get("ap"), kwargs.get("curr"))
    response += reply_commands(m_list, message, channel_id, user_id, server, kwargs.get("ap"))
    return response

def public_commands(command:list[str], message:discord.Message, channel_id:int, user_id:int, server:int, ap:bool, curr:dict, default:dict, mentioned: bool) -> list[dict]:
    response:list = []

    if mentioned and (f"<@{self_id}>" in command[0]):
        response += [{"type":"message","message":"Hi! It sounds like you have questions! What can we help with? (Answer bot, commands, daybreak, front, or plurality)","except":True}]
        response += [{"type":"call","call":info_tree,"wait_type":"message","check":lambda x: x.author.id == message.author.id}]
    
    if command[0][0] != cmd_prefix:
        return response
    # public commands
    match command[0][1:]:
        case "help":         
            response += [{"type":"message","message":"Hi! It sounds like you have questions! What can we help with? (Answer bot, commands, daybreak, front, or plurality)","except":True}]
            response += [{"type":"call","call":info_tree,"wait_type":"message","check":lambda x: x.author.id == message.author.id}]
        case "member":
            if len(command) > 2:
                response += members.member_info(command[1].lower())
            else:
                response += members.member_info(members.get_front(curr, default, ap))
        case "chinfo":
            response += enable.get_formatted_channel(message.channel, message.channel.guild)

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

# ASYNC FUNCTIONS FOR CALL COMMANDS

# Info tree, for ping
async def info_tree(self, id, message) -> dict:
    content = message.content.split()
    match content[0].lower():
        case "commands":
            return {"type":"call","call":create_help,"message":message}
        case "plurality":
            return [{"type":"message","except":True,"message":"Plurality is when multiple people or entities, usually called headmates, share the same body. A group of headmates is often reffered to as a system or collective. Headmates usually have differing personalities, names, pronouns, and preferences."},{"type":"message","except":True,"message":"For more information on systems in general, [morethanone.info](https://morethanone.info/), [healthymultiplicity](https://healthymultiplicity.com/#i), or [pluralpedia](https://pluralpedia.org/w/Main_Page) are good resources. For more information about us, try the `daybreak` option."}]
        case "daybreak":
            return members.member_info("list")
        case "front":
            return members.member_info(members.get_front(self.curr_member, self.default_member, self.ap))
        case "bot":
            return [{"type":"message","except":True,"message":"STARWELL is a custom-made and hosted bot built using discord.py and hosted on a server running headless linux mint. It is based on [EclipseBot V2's code](https://github.com/red-sky-at-morning/discord_bot), with custom modules to support webhooks."},{"type":"message","except":True,"message":"STARWELL's code is available publicly [on github](https://github.com/red-sky-at-morning/starwell). If you're looking for information about how to use the bot, try the `commands` option."}]
        case _:
            return {"type":"message","message":"Sorry, I don't know how to answer that question!", "except":True}

# Help command
async def create_help(self, id, message) -> dict:
    embed = discord.Embed(title="STARWELL commands")
    embed.add_field(name="&help", value="*Shows this message. Hi!*")
    embed.add_field(name="&member", value="*Shows information about the current member.*\nSubcommands:\n- &member list: *Lists all members*\n- &member <id>: *Shows information about a specific member*")
    embed.add_field(name="&chinfo", value="*Shows whether STARWELL will proxy in the current channel, and the reason, if any.*")
    footer_text = "Commands prefixed with a * can only be used by members. Commands prefixed with a ↑ only work when replying to a message. You are%1 a member."
    if id not in trusted_ids:
        embed.set_footer(text=footer_text.replace("%1", " not"))
    else:
        embed.set_footer(text=footer_text.replace("%1", ""))
        # Member-only commands
        embed.add_field(name="*&ap", value="*Toggles Autoproxy. Reacts with the new state of Autoproxy.*")
        embed.add_field(name="*&setfront", value="*Sets the default user to the last member speaking.*\nSubcommands:\n- &setfront <id>: *Sets the default member to a specific user.*")
        embed.add_field(name="*&useradd <id>", value="*Adds a new user. <id> is a required argument.*")
        embed.add_field(name="*&usermod <id> <key> <val>", value="*Changes a value of a user. <id>, <key>, and <val> are required.*\nAllowed keys:\n- name\n- names\n- username\n- pronouns\n- avatar\n- color\n- desc\n- replacement\n- tags\n- presence\n- emoji*")
        embed.add_field(name="*&chmod <enable|disable>", value="*Enables or disables proxying in a channel.*\nSubcommands:\n- &chmod <enable|disable> <reason>: *Enables or disables proxying in a channel, and sets a reason.*")
        embed.add_field(name="*&svmod <enable|disable>", value="*Enables or disables proxying in a server.*\nSubcommands:\n- &svmod <enable|disable> <reason>: *Enables or disables proxying in a server, and sets a reason.*")
        # Member reply-only commands
        embed.add_field(name="*↑&rp", value="*Deletes a message sent by a webhook, and sends it as the current user.*\nSubcommands:\n- &rp <id>: *Deletes a message sent by a webhook, and sends it as a specific user.*")
        embed.add_field(name="*↑&edit <text>", value="*Edits a message sent by a webhook to say <text>.*")
        embed.add_field(name="*↑&del", value="*Deletes a message sent by a webhook.*")
    return {"type":"message","message":"","embed":[embed],"except":True}

# Response checker for replies
async def check_resp(self, id, message) -> bool:
    if id in trusted_ids:
        return True
    hook = await members.get_or_make_webhook(message.channel)
    try:
        await hook.fetch_message(message.id)
        return True
    except (discord.errors.NotFound, discord.errors.HTTPException):
        return False