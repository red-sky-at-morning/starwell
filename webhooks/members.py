import json
import discord

with open("webhooks/meta/members.json", "r") as file:
    members:dict = json.load(file)

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
    if id == "list":
        member_list = [f"{key}: {members[key].get("names", "")[members[key].get("name")]} ({members[key].get("pronouns", "none set")})" if key != "_" else "" for key in members.keys()]
        member_list.sort()
        member_list = "\n".join(member_list)
        embed = discord.Embed(color=discord.Color.from_str("#cb2956"), title=f"Members of the Daybreak System",description=member_list)
        return [{"type":"message","message":"","embed":[embed],"except":True}]

    member = members.get(id, None)
    if not member:
        return[{"type":"message","message":"That member does not exist (yet?)! Sorry!", "except": True}]

    names_l = member.get("names").copy()
    del names_l[member.get("name", 0)]
    embed_desc = f"{member.get("names")[member.get("name", 0)]}{f' ({member.get("pronouns")})' if member.get("pronouns") else ""}"
    embed_desc += f"\n{member.get("desc")}"
    
    embed = discord.Embed(color=discord.Color.from_str(member.get("color", "#181926")),title=f"@{member.get("username")}",description=embed_desc)
    embed.set_thumbnail(url=member.get("avatar", None))

    if names_l:
        embed.add_field(name="Aka", value=", ".join(names_l), inline=False)
    if member.get("presence"):
        embed.add_field(name="Status", value=member.get("presence"), inline=False)
    if member.get("replacement"):
        embed.add_field(name="Text", value=member.get("replacement"), inline=False)
    if member.get("tags"):
        embed.set_footer(text=str(member.get("tags")).strip("[]").replace("'", ""))
    return [{"type":"message","message":"","embed":[embed], "except":True}]

def get_member(id:str) -> dict:
    return members.get(id, members.get("_"))

def get_member_by_username(username:str) -> str:
    filtered = list(filter(lambda x: x.get("username") == username, list(members.copy().values())))
    return [key for key, value in members.items() if value == filtered[0]][0]

def get_all_replacements() -> dict:
    return {name:item.get("replacement", None) for name,item in zip(members.keys(), members.values())}

def handle_usermod(id:str, args:list[str], type:str, curr:str):
    if type not in ("add", "edit"):
        return [{"type":"message", "message":"Sorry, I don't know how to perform that action!","except":True}]
    match type:
        case "add":
            if add_member(id):
                out = [{"type":"message","message":f"Added a new member with id {id}","except":True}]
                return out
            return [{"type":"message", "message":"Sorry, I don't know how to add that user!","except":True}]
        case "edit":
            match edit_member(id, args[0], args[1]):
                case 1:
                    out = [{"type":"message","message":f"Editied member {id}'s {args[0]}: {args[1]}", "except":True}]
                case 2:
                    out = [{"type":"message","message":f"Editied member {id}'s {args[0]}: {args[1]}", "except":True},{"type":"presence","default":True}]
                case _:
                    return [{"type":"message", "message":"Sorry, I don't know how to edit that value!", "except":True}]
            return out

def add_member(id:str) -> bool:
    members[id] = {"name":0, "names":[id.capitalize()], "username":id}
    with open("webhooks/meta/members.json", "w") as file:
        json.dump(members, file)
    return True

valid_keys:tuple = ("name", "names", "username", "pronouns", "avatar", "color", "desc", "replacement", "tags", "presence", "emoji")
def edit_member(id:str, key:str, val:any) -> int:
    if key not in valid_keys:
        return 0
    if id not in members.keys():
        return 0
    out = 1
    match key:
        case "name":
            if val in members[id]["names"]:
                members[id][key] = members[id]["names"].index(val)
            else:
                members[id]["names"].append(val)
                members[id][key] = members[id]["names"].index(val)
        case "tags" | "names":
            tags = members[id].get(key, [])
            if val in tags:
                tags.remove(val)
            else:
                tags.append(val)
            members[id][key] = tags
        case "presence":
            members[id][key] = val
            out = 2
        case _:
            members[id][key] = val
    with open("webhooks/meta/members.json", "w") as file:
        json.dump(members, file)
    return out