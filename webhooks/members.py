import json
import discord

with open("webhooks/meta/members.json", "r") as file:
    members:dict = json.load(file)

with open("meta/params.json", "r") as params:
    params_json = json.load(params)
    self_id = params_json.get("id")

async def get_or_make_webhook(channel:discord.TextChannel) -> discord.Webhook:
    if not type(channel) is discord.TextChannel:
        match type(channel):
            case discord.Thread:
                channel = channel.parent
            case _:
                raise TypeError("get_or_make_webhook(channel): channel was not isntanceOf textChannel or textChannel-like")
    hooks = await channel.webhooks()
    hooks = list([item for item in hooks if item.user.id == self_id])
    if hooks:
        return hooks[0]
    hook = await channel.create_webhook(name="STARWELL member webhook",reason="initial creation. if there are more than one of these, something is wrong.")
    return hook

def system_info() -> list[dict]:
    embed = discord.Embed(color=discord.Color.from_str("#cb2956"), title=f"The Daybreak System",description=members["_"].get("about"))
    
    member_list = [f"`{key}`: {members[key].get("names", "")[members[key].get("name")]} ({members[key].get("pronouns", "none set")}){f'\n- *{members[key].get("desc", "")}*' if members[key].get("desc", None) is not None else ""}" if key != "_" else "" for key in members.keys()]
    member_list.sort()
    member_list = "\n".join(member_list)
    embed.add_field(name="Members", value=member_list)
    
    embed.set_footer(text="To see more information about a member, use &member <id>")

    return [{"type":"message","message":"","embed":[embed],"except":True}]

def member_info(id:str, server:int) -> list[dict]:
    if id == "list":
        return system_info()

    member = members.get(id, None)
    if not member:
        return[{"type":"message","message":"That member does not exist (yet?)! Sorry!", "except": True}]

    names_l = member.get("names").copy()
    del names_l[member.get("name", 0)]
    embed_desc = f"{member.get("names")[member.get("name", 0)]}{f' ({member.get("pronouns")})' if member.get("pronouns") else ""}"
    embed_desc += f"\n*{member.get("desc", "")}*"
    embed_desc += f"\n{member.get("about", "")}"
    
    embed_title = f"@{member.get("username")}"
    nick = get_nickname_by_id(id, server)
    if nick is not None:
        embed_title = f"{nick} ({embed_title})"

    embed = discord.Embed(color=discord.Color.from_str(member.get("color", "#181926")),title=f"{embed_title}",description=embed_desc)
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

def get_nickname_by_id(id:str, server:int):
    member = members.get(id)
    return member.get("nick", {}).get(server.__str__(), None)

def get_nickname(member:dict, server:id):
    return member.get("nick", {}).get(server.__str__(), None)

def get_member(id:str) -> dict:
    return members.get(id, members.get("_"))

def get_member_by_username(username:str) -> str:
    filtered = list(filter(lambda x: x.get("username") == username, list(members.copy().values())))
    return [key for key, value in members.items() if value == filtered[0]][0]

def get_front(curr:dict, default:dict, ap:bool) -> str:
    if ap:
        return get_member_by_username(curr.get("username", "nullrefexception"))
    else:
        return get_member_by_username(default.get("username", "nullrefexception"))

def get_all_replacements() -> dict:
    return {name:item.get("replacement", None) for name,item in zip(members.keys(), members.values())}

def handle_usermod(id:str, args:list[str], type:str, server:int):
    if type not in ("add", "edit"):
        return [{"type":"message", "message":"Sorry, I don't know how to perform that action!","except":True}]
    match type:
        case "add":
            if add_member(id):
                out = [{"type":"message","message":f"Added a new member with id {id}","except":True}]
                return out
            return [{"type":"message", "message":"Sorry, I don't know how to add that user!","except":True}]
        case "edit":
            match edit_member(id, args[0], args[1], server=server):
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

valid_keys:tuple = ("name", "names", "username", "pronouns", "avatar", "color", "desc", "about", "replacement", "tags", "presence", "status", "emoji", "nick", "id")
def edit_member(id:str, key:str, val:any, **kwargs) -> int:
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
        case "presence" | "status":
            members[id]["presence"] = val
            out = 2
        case "nick":
            server_id = kwargs.get("server")
            if server_id is None:
                return 0
            if members.get(id).get("nick", None) is None:
                members[id]["nick"] = {}
            if not val:
                del members[id]["nick"][server_id.__str__()]
            else:
                members[id]["nick"][server_id.__str__()] = val
        case "id":
            member_data = members[id]
            del members[id]
            members[val] = member_data
        case _:
            members[id][key] = val
    with open("webhooks/meta/members.json", "w") as file:
        json.dump(members, file)
    return out