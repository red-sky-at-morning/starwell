import re
import json
import discord

from webhooks import members

with open("meta/params.json", "r") as params:
    params_json = json.load(params)
    trusted_ids = params_json.get("dev_ids")

def handle_message(text:str, message:discord.Message, user_id:int, auto:bool) -> list[dict]:
    if user_id not in trusted_ids:
        return []
    member_name = has_replacement(text)
    if member_name is None:
        return [{"type":"delete","message":message.id},{"type":"message","message":text}] if auto else []
    member = members.get_member(member_name)
    print(member)
    if "no-hooks" in member.get("tags", []):
        return []
    if not "keep-repl" in member.get("tags", []):
        text = trim_replacement(text, member.get("replacement"))
    return [{"type":"delete","message":message.id},{"type":"webhook","id":member_name},{"type":"message","message":text}]
    return []

def has_replacement(text:str) -> str | None:
    replacements = members.get_all_replacements()
    for key, repl in zip(replacements.keys(), replacements.values()):
        if repl is None:
            continue
        repl = re.escape(repl)
        repl = f"^{repl.replace("%text%", ".*")}$"
        repl = re.compile(repl)

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