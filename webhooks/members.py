import json
import discord

with open("webhooks/meta/members.json", "r") as file:
    members = json.load(file)

with open("meta/params.json", "r") as params:
    params_json = json.load(params)
    self_id = params_json.get("id")

async def get_or_make_webhook(channel:discord.TextChannel) -> discord.Webhook:
    hooks = await channel.webhooks()
    hooks = list([item for item in hooks if item.user.id == self_id])
    if hooks:
        return hooks[0]
    hook = await channel.create_webhook(name="STARWELL member webhook",reason="initial creation. if there are more than one of these, something is wrong.")
    return hook

def member_info(id:str) -> list[dict]:
    member = members.get(id, None)
    if not member:
        return[{"type":"message","message":"That member does not exist (yet?)! Sorry!"}]

    embed = discord.Embed(color=discord.Color.from_str(member.get("color", "#181926")),title=member.get("username"),description=f"@{member.get("name")} {f'({member.get("pronouns")})' if member.get("pronouns") else ""}")
    embed.set_thumbnail(url=member.get("avatar", None))
    if member.get("desc"):
        embed.add_field(name="Description", value=member.get("desc"))
    return [{"type":"message","message":"","embed":embed}]

def get_member(id:str) -> dict:
    return members.get(id, None)

def add_member(id:str) -> bool:
    members[id] = {"name":id, "username":id}
    with open("webhooks/meta/members.json", "w") as file:
        json.dump(members, file)

def edit_member(id:str, key:str, val:any) -> bool:
    pass