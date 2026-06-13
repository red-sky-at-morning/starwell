import json
import random
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

def handle(command:list[str], curr:dict, default:dict, ap:bool, message:discord.Message) -> list[dict]:
    # member (list <all|tags|none>)(show <all|tags|none>)(id|none)
    
    # show front if just the command is sent
    if len(command) <= 2:
        return member_info(get_front(curr, default, ap), message.guild)
    
    match command[1].lower():
        case "list":
            if len(command) <= 3:
                return list_all(message.guild)
            if command[2] == "all":
                return list_all(message.guild)
            else:
                return list_by_tag(command[2].lower(), message.guild)
        case "show":
            if len(command) <= 3:
                return member_info(get_front(curr, default, ap), message.guild)
            if command[2] == "all":
                return show_all(message.guild)
            else:
                if command[2].lower() in members.keys():
                    return member_info(command[2].lower(), message.guild)
                else:
                    return show_by_tag(message.guild, command[2].lower())
        case _:
            return member_info(command[1].lower(), message.guild)

# funcs for listing

def filter_members(func) -> dict:
    out = {}
    for key, member in members["members"].items():
        if func(key, member):
            out[key] = member
    return out

def list_all(server:discord.Guild) -> list[dict]:
    member_list = []
    for key, member in sorted(filter_members(lambda x, y: not "no-list" in y.get("tags-util", [])).items()):
        username = f"@{member.get("username")}"
        nick = get_nickname_by_id(key, server)
        if nick is not None:
            username = f"@{nick}"
        member_list.append(f"`{key}`: {member.get("names", "")[member.get("name")]} ({member.get("pronouns", "none set")}) {username} {f'\n- *{member.get("desc-short", "")}*' if member.get("desc-short", None) is not None else ""}")

    hidden_members = filter_members(lambda x, y: ("no-list" in y.get("tags-util", [])))

    count = f"{str(len(member_list))}"
    if len(hidden_members):
        count += f" (+{str(len(hidden_members))} hidden for {str(len(hidden_members) + len(member_list))} total)"
    desc = members["meta"].get("desc-long").replace("$count", count)
    # desc += f"\n\nCurrent count: {len(members)-1} (+{len(members)-len(member_list)-1} hidden member(s), no we won't show you :p)"
    
    colors = list(member.get("color", "#5b6078") for member in filter_members(lambda x, y: not "no-list" in y.get("tags-util", [])).values())
    color = random.randint(0, len(colors)-1)
    embed = discord.Embed(color=discord.Color.from_str(colors[color]), title=f"The Daybreak System",description=desc)
    
    member_list = "\n".join(member_list)
    embed.add_field(name="Members", value=member_list)
    
    embed.set_footer(text="To see more information about a member, use &member <id>. \nIds are listed before information about a member.")

    return [{"type":"message","message":"","embed":[embed],"except":True}]

def list_by_tag(tag:str, server:discord.Guild):
    member_list = []
    for key, member in sorted(filter_members(lambda x, y: (not "no-list" in y.get("tags-util", [])) and (tag in y.get("tags-util", []) + y.get("tags-desc", []))).items()):
        username = f"@{member.get("username")}"
        nick = get_nickname_by_id(key, server)
        if nick is not None:
            username = f"@{nick}"
        member_list.append(f"`{key}`: {member.get("names", "")[member.get("name")]} ({member.get("pronouns", "none set")}) {username} {f'\n- *{member.get("desc-short", "")}*' if member.get("desc-short", None) is not None else ""}")

    hidden_members = filter_members(lambda x, y: ("no-list" in y.get("tags-util", [])) and (tag in y.get("tags-util", []) + y.get("tags-desc", [])))

    count = f"{str(len(member_list))}"
    if len(hidden_members):
        count += f" (+{str(len(hidden_members))} hidden for {str(len(hidden_members) + len(member_list))} total)"
    desc = members["meta"].get("desc-long").replace("$count", count)
    # desc += f"\n\nCurrent count: {len(member_list)+len(hidden_members)} (+{len(hidden_members)} hidden member(s), no we won't show you :p)"
    
    colors = list(member.get("color", "#5b6078") for member in filter_members(lambda x, y: (not "no-list" in y.get("tags-util", [])) and (tag in y.get("tags-util", []) + y.get("tags-desc", []))).values())
    color = random.randint(0, len(colors)-1)
    if len(colors) == 0:
        colors = ["#cb2956"]
        color = 0
    embed = discord.Embed(color=discord.Color.from_str(colors[color]), title=f"Members with tag `{tag}`",description=desc)

    member_list = "\n".join(member_list)
    if member_list != '':
        embed.add_field(name="Members", value=member_list)
    else:
        embed.add_field(name="Members", value=f"No members with tag `{tag}`. Sorry!")

    embed.set_footer(text="To see more information about a member, use &member <id>")

    return [{"type":"message","message":"","embed":[embed],"except":True}]

# funcs for showing

def show_all(server:discord.Guild) -> list[dict]:
    response = []
    for key in sorted(filter_members(lambda x, y: not "no-list" in y.get("tags-util", [])).keys()):
        response += member_info(key, server)
    return response

def show_by_tag(server:discord.Guild, tag:str) -> list[dict]:
    response = []
    for key in sorted(filter_members(lambda x, y: (not "no-list" in y.get("tags-util", [])) and (tag in y.get("tags-desc", []))).keys()):
        response += member_info(key, server)
    return response

# helpers

def member_info(id:str, server:discord.Guild) -> list[dict]:
    member = members["members"].get(id, None)
    if not member:
        return[{"type":"message","message":"That member does not exist (yet?)! Sorry!", "except": True}]

    names_l = member.get("names").copy()
    del names_l[member.get("name", 0)]
    embed_desc = f"{member.get("names")[member.get("name", 0)]}{f' ({member.get("pronouns")})' if member.get("pronouns") else ""}"
    member_desc = member.get("desc-short", None)
    if member_desc is not None:
        embed_desc += f"\n *{member_desc}*"
    embed_desc += f"\n\n{member.get("desc-long", "")}"
    
    embed_title = f"@{member.get("username")}"
    nick = get_nickname_by_id(id, server)
    if nick is not None and nick != member.get("username"):
        embed_title = f"{nick} ({embed_title})"

    embed = discord.Embed(color=discord.Color.from_str(member.get("color", "#5b6078")),title=f"{embed_title}",description=embed_desc)
    embed.set_thumbnail(url=member.get("avatar", None))

    if names_l:
        embed.add_field(name="Aka", value=", ".join(names_l), inline=False)
    if member.get("presence"):
        embed.add_field(name="Status", value=member.get("presence"), inline=False)
    if member.get("replacement"):
        embed.add_field(name="Text", value=member.get("replacement"), inline=False)
    desc = ""
    if member.get("tags-util"):
        desc += f"Util: {str(member.get("tags-util")).strip("[]").replace("'", "")}"
    
    if member.get("tags-desc"):
        if (member.get("tags-util")):
            desc += " | "
        desc += f"Desc: {str(member.get("tags-desc")).strip("[]").replace("'", "")}"

    if desc:
        embed.set_footer(text=desc)

    return [{"type":"message","message":"","embed":[embed], "except":True}]

def get_nickname_by_id(id:str, server:discord.Guild):
    member = members["members"].get(id)
    return get_nickname(member, server)

def get_nickname(member:dict, server:discord.Guild):
    if "copy-nick" in member.get("tags-util", []):
        print(server)
        id = members["meta"].get("user_id", -1)
        user = server.get_member(id)
        print(server.members)
        return user.nick if user.nick is not None else user.global_name
    
    return member.get("nick", {}).get(server.id.__str__(), member.get("username"))

def get_member(id:str) -> dict | None:
    return members["members"].get(id, None)

def get_member_by_username(username:str) -> str:
    for key, val in members["members"].items():
        if val.get("username", "") == username:
            return key

def get_front(curr:dict, default:dict, ap:bool) -> str:
    if ap:
        return get_member_by_username(curr.get("username"))
    else:
        return get_member_by_username(default.get("username"))

def get_all_replacements() -> dict:
    return {name:item.get("replacement", None) for name, item in members["members"].items()}

# usermods

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
                case "invalid key":
                    out = [{"type":"message","message":f"That is not a field that you can edit!", "except":True}]
                case "invalid id":
                    out = [{"type":"message","message":f"That member does not exist!", "except":True}]
                case "presence changed":
                    out = [{"type":"message","message":f"Edited member {id}'s {args[0]}: {args[1]}", "except":True},{"type":"presence","default":True}]
                case _:
                    out = [{"type":"message","message":f"Edited member {id}'s {args[0]}: {args[1]}", "except":True}]
            return out

def add_member(id:str) -> bool:
    members["members"][id] = {"name":0, "names":[id.capitalize()], "username":id}
    with open("webhooks/meta/members.json", "w") as file:
        json.dump(members, file)
    return True

valid_keys:tuple = ("name", "names", "username", "pronouns", "avatar", "color", "desc", "about", "replacement", "tags", "presence", "status", "emoji", "nick", "id")
def edit_member(id:str, key:str, val:any, **kwargs) -> str:
    if key not in valid_keys:
        return "invalid key"
    if id not in members["members"].keys():
        return "invalid id"
    out = 1
    match key:
        case "name":
            if val in members["members"][id]["names"]:
                members["members"][id][key] = members["members"][id]["names"].index(val)
            else:
                members["members"][id]["names"].append(val)
                members["members"][id][key] = members["members"][id]["names"].index(val)
        case "tags":
            tagtype = "tags-desc"
            if val in members["meta"].get("tags-util"):
                tagtype = "tags-util"
            tags = members["members"][id].get(tagtype, [])
            if val in tags:
                tags.remove(val)
            else:
                tags.append(val)
            members["members"][id][tagtype] = tags
        case "names":
            tags = members["members"][id].get(key, [])
            if val in tags:
                tags.remove(val)
            else:
                tags.append(val)
            members["members"][id][key] = tags
        case "presence" | "status":
            members["members"][id]["presence"] = val
            out = "presence changed"
        case "nick" | "nickname":
            server_id = kwargs.get("server")
            if server_id is None:
                return 0
            if members["members"].get(id).get("nick", None) is None:
                members["members"][id]["nick"] = {}
            if not val:
                del members["members"][id]["nick"][server_id.__str__()]
            else:
                members["members"][id]["nick"][server_id.__str__()] = val
        case "id":
            member_data = members["members"][id]
            del members["members"][id]
            members["members"][val] = member_data
        case _:
            members["members"][id][key] = val
    with open("webhooks/meta/members.json", "w") as file:
        json.dump(members, file)
    return out