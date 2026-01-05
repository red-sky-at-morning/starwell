import re
import discord

from webhooks import members
from replacement import enable

def handle_message(text:str, message:discord.Message, user_id:int, auto:bool, curr_member:dict, default_member:dict) -> list[dict]:
    if len(text)>= 1 and text[0] == "&":
        return []
    if message.type not in (discord.MessageType.default, discord.MessageType.reply):
        return []
    if not enable.get_channel_state(message.channel.id, message.channel.guild.id):
        return []

    print(f"default_member: {default_member}")
    member_name = has_replacement(text)
    print(f"text member: {member_name}")

    if member_name is None:
        if auto:
            if curr_member == None or "no-hooks" in curr_member.get("tags", []):
                return []
            else:
                return [{"type":"message","message":text,"files":message.attachments,"embed":list(filter(lambda x: x.type == "rich", message.embeds)),"reference":message.reference},{"type":"delete","message":message.id}]
        if default_member == None or "no-hooks" in default_member.get("tags", []): 
            return []
        else:
            return [{"type":"message","message":text, "use-default":True,"files":message.attachments,"embed":list(filter(lambda x: x.type == "rich", message.embeds)),"reference":message.reference},{"type":"delete","message":message.id}]
    
    member = members.get_member(member_name)
    # print(member)
    
    if "no-hooks" in member.get("tags", []):
        return [{"type":"webhook","id":member_name}]
    if not "keep-repl" in member.get("tags", []):
        text = trim_replacement(text, member.get("replacement"))
    
    return [{"type":"webhook","id":member_name},{"type":"message","message":text,"files":message.attachments,"embed":list(filter(lambda x: x.type == "rich", message.embeds)),"reference":message.reference},{"type":"delete","message":message.id}]

def has_replacement(text:str) -> str | None:
    replacements = members.get_all_replacements()
    for key, repl in zip(replacements.keys(), replacements.values()):
        if repl is None:
            continue
        repl = re.escape(repl)
        repl = f"^{repl.replace("%text%", ".*")}$"
        repl = re.compile(repl, flags=re.DOTALL)

        match = repl.match(text)
        if match is not None:
            return key
    return None

def trim_replacement(text:str, replacement:str) -> str:
    replacement = replacement.split("%")
    idx = replacement.index("text")
    for i, fix in enumerate(replacement):
        if i < idx:
            text = text.removeprefix(fix)
        if i == idx:
            continue
        if i > idx:
            text = text.removesuffix(fix)
    return text