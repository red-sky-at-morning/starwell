import json
import discord
# from discord.ext import commands
import asyncio
import responses

from webhooks import members

class Bot(discord.Client):
    def __init__(self, intents:discord.Intents):
        super().__init__(intents=intents)
        self.starting_mode = "HYBRID"        
        self.starting_server = None
        self.starting_channel = None

        self.modes:tuple = ("ACTIVE", "STANDBY", "TESTING")
        self.mode:str = self.starting_mode
        if not self.mode in self.modes:
            self.mode = "ACTIVE"

        self.ignore_errors:bool = True

        self.author:discord.User
        self.last_sent_message:discord.Message = None

        self.curr_member = None
        self.ap = False
        self.default_member = self.curr_member

    async def on_ready(self):
        with open("meta/params.json", "r") as params:
            params_json = json.load(params)
            self.author = await self.fetch_user(params_json.get("dev_ids")[0])
        if self.mode == "TESTING":
            self.ignore_errors = True
        await self.change_presence(activity=discord.CustomActivity(name="🔴 | watching the stars"))
        print(f"{self.user} is now running!")

    async def send_dm(self, user:discord.User, content:str) -> None:
        channel = await user.create_dm()
        await channel.send(content)
    
    async def on_error(self, event:str, *args, **kwargs):
        import sys, traceback
        extype, ex, _ = sys.exc_info()
        print(f"{extype.__name__} exception in {event}: {ex}\n{traceback.format_exc()}")
        await self.send_dm(self.author, f"{extype.__name__} exception in {event}: ```{ex}\n{traceback.format_exc()}```")
        if self.ignore_errors:
            return
        await self.switch_mode("STANDBY")
        await self.send_dm(self.author, "Entering Standby mode...")
        self.mode = self.modes[2]
    
    async def switch_mode(self, mode) -> None:
        if mode not in self.modes:
            raise TypeError(f"Mode not found in mode list: {mode}")
        print(f"Switching to mode {mode}")
        await self.change_presence(activity=discord.Game(f"in {mode} mode"))
        self.mode = mode
    
    def verify_mode(self, server:int, channel:int, user:int) -> bool:
        restricted:bool = channel == 1041508830279905280 or server == 677632068041310208 or user == 630837649963483179
        match self.mode:
            case "ACTIVE":
                return True
            case "CONSOLE":
                return restricted
            case "HYBRID":
                return True
            case "STANDBY":
                return restricted
            case "TESTING":
                return restricted
    
    async def handle_response(self, response:list[dict]|None, channel:discord.TextChannel) -> None:
        if response is None:
            return
        for item in response:
            if not item or item is None:
                continue
            match item.get("type", None):
                case "message":
                    # send messages as bot
                    if self.curr_member is None or item.get("except", False):
                        self.last_sent_message = await channel.send(item.get("message","No message provided"), embeds=item.get("embed", []), reference=item.get("reference"))
                    else:
                        hook = await members.get_or_make_webhook(channel)
                        # replying
                        if item.get("reference") is not None:
                            resolve = item.get("reference").resolved
                            if resolve != None:
                                embed = discord.Embed(description=f"[Reply to]({resolve.jump_url}): {resolve.content}")
                                print(resolve.author.display_avatar.url)
                                embed.set_author(name=resolve.author.name, icon_url=resolve.author.display_avatar.url)
                                if item.get("embed") != None:
                                    item["embed"].insert(0, embed)
                                else:
                                    item["embed"] = [embed]
                        # files
                        if item.get("files") is not None:
                            for i, file in enumerate(item.get("files")):
                                item["files"][i] = await file.to_file()
                        # send the message
                        if item.get("use-default", False):
                            self.last_sent_message = await hook.send(item.get("message",""), username=self.default_member.get("username", None), avatar_url=self.default_member.get("avatar", None), files=item.get("files",[]), embeds=item.get("embed", []))
                            continue
                        self.last_sent_message = await hook.send(item.get("message",""), username=self.curr_member.get("username", None), avatar_url=self.curr_member.get("avatar", None), files=item.get("files",[]), embeds=item.get("embed", []))
                    print(f"Said {item.get('message','No message provided')}{' (with embed)' if item.get("embed", []) else ""} in {channel.name} in {channel.guild.name}")
                case "reply":
                    await channel.send(item.get("message","No message provided"), reference=item.get("reply", self.last_sent_message), embed=item.get("embed", None))
                    print(f"Said {item.get('message','No message provided')} {'(with embed)' if item.get("embed", []) else ""} in {channel.name} in {channel.guild.name}")
                case "react":
                    message:discord.Message = item.get("message", self.last_sent_message)
                    if type(item.get("react")) == discord.PartialEmoji:
                        await message.add_reaction(item.get("react"))
                    else:
                        for char in item.get("react"):
                            await message.add_reaction(char)
                    print(f"Reacted to {message.content} (by {message.author}) in {message.channel} in {message.channel.guild} with {item.get('react')}")
                case "delete":
                    try:
                        message = await channel.fetch_message(item.get("message"))
                        await message.delete()
                    except discord.errors.PrivilegedIntentsRequired:
                        await channel.send("We do not have permission to delete messages")
                case "wait":
                    print(f"Sleeping for {item.get('time', 0)} seconds...")
                    await asyncio.sleep(item.get("time"))
                case "webhook":
                    if item.get("id", "_") != None:
                        self.curr_member = members.get_member(item.get("id", "_"))
                    if self.ap:
                        await self.change_presence(activity=discord.CustomActivity(name=f"🟢 | {self.curr_member.get("presence", "watching the stars")}"))
                    if item.get("default", False):
                        self.default_member = self.curr_member
                        print(self.default_member)
                        await self.change_presence(activity=discord.CustomActivity(name=f"🔴 | {self.curr_member.get("presence", "watching the stars")}"))
                case "error":
                    error = item.get("error")
                    print(f"Raising error {error}")
                    raise error
                case "input":
                    msg = await self.wait_for(item.get("wait_type"), check=item.get("check"))
                    func = item.get("call", lambda x:None)
                    response.append(await func(msg.author.id, msg))
                case "special":
                    match item.get("action"):
                        case "toggle_ap":
                            self.ap = not self.ap
                            await self.change_presence(activity=discord.CustomActivity(name=f"{"🟢" if self.ap else "🔴"} | {self.curr_member.get("presence", "watching the stars")}"))
                        case _:
                            raise TypeError("Unexpected action in response")
                case None:
                    raise TypeError("No type provided for response")
                case _:
                    raise TypeError("Unexpected type for response")
    
    async def on_raw_reaction_add(self, payload:discord.RawReactionActionEvent):

        server:discord.Guild = await self.fetch_guild(payload.guild_id)
        channel = await self.fetch_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user:discord.User = await server.fetch_member(int(payload.user_id))

        # Don't respond to bots
        if message.author.bot:
            return False
        # don't respond to webhook messages
        if message.webhook_id is not None:
            return False

        character:discord.PartialEmoji = payload.emoji
        try:
            count = discord.utils.get(message.reactions, emoji=character.name).count
        except AttributeError:
            return False
        username = user.name
        
        # Print to console
        print(f"{username} ({user.id}) reacted to {message.content} (by {message.author}) with {character.name} in #{channel} in {server}")

        if not self.verify_mode(server.id, channel.id, user.id):
            return False

        response = responses.handle_react(message, character, count, channel.id, user.id, server.id)
        await self.handle_response(response, channel)
        return True

    async def on_message(self, message:discord.Message):
        # Don't respond to bots
        if message.author.bot:
            return False
        # don't respond to webhook messages
        if message.webhook_id is not None:
            return False

        # Get data from the message
        username = str(message.author)
        content = str(message.content)
        channel = message.channel
        channel_id = channel.id
        server = message.guild
        if server is not None:
            server_id = int(message.guild.id)
        else:
            server_id = -1
        user_id = int(message.author.id)

        # Print to console
        print(f"{username}{f' / {message.author.nick}' if type(message.author) == discord.Member else ""} ({user_id}) said {content} in #{channel} in {server}")

        if not self.verify_mode(server_id, channel_id, user_id):
            return False

        response = responses.handle_message(message, content, channel_id, user_id, server_id, mentioned=self.user.mentioned_in(message), ap=self.ap, curr=self.curr_member, default=self.default_member)
        await self.handle_response(response, channel)

        return True

    def startup(self) -> None:
        try:
            with open("meta/TOKEN.txt", "r") as token:
                TOKEN = token.readline().strip()
        except (FileNotFoundError, EOFError) as e:
            print(f"Bad token: {e}")
        async def run():
            discord.utils.setup_logging(root=False)
            await asyncio.gather(
                self.start(TOKEN)
            )
        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            print("\nGoodbye!")

if __name__ == "__main__":
    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True
    starwell = Bot(intents=intents)
    starwell.startup()