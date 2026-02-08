import builtins
import json
import discord
# from discord.ext import commands
import asyncio
import responses
import response_functions

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

        self.curr_member = members.get_member("byte")
        self.ap = True
        self.default_member = self.curr_member

    async def on_ready(self):
        with open("meta/params.json", "r") as params:
            params_json = json.load(params)
            self.author = await self.fetch_user(params_json.get("dev_ids")[0])
        if self.mode == "TESTING":
            self.ignore_errors = True
        await self.change_presence(activity=discord.CustomActivity(name=f"{"🟢" if self.ap else "🔴"}{self.curr_member.get("emoji")} | {self.curr_member.get("presence")}"))
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

    async def handle_response(self, response:list[dict]|None, channel:discord.TextChannel|discord.Thread) -> None:
        if response is None:
            return
        for item in response:
            if not item or item is None:
                continue
            match item.get("type", None):
                case "message":
                    await response_functions.message(self, item, channel)
                
                case "edit":
                    await response_functions.edit(self, item, channel)
                
                case "react":
                    await response_functions.react(self, item, channel)
                
                case "delete":
                    await response_functions.delete(self, item, channel)
                
                case "wait":
                    await response_functions.wait(self, item, channel)
                
                case "webhook":
                    resp = await response_functions.webhook(self, item, channel)
                    if type(resp) is dict:
                        response.append(resp)
                
                case "error":
                    error = item.get("error")
                    print(f"Raising error {error}")
                    raise error
                
                case "call":
                    resp = await response_functions.call(self, item, channel)
                    if (item.get("kill") and not resp):
                        return
                    match type(resp):
                        case builtins.dict:
                            response.append(resp)
                        case builtins.list:
                            response += resp
                        case _:
                            continue

                case "presence":
                    await response_functions.presence(self, item, channel)
                
                case "special":
                    match item.get("action"):
                        case "toggle_ap":
                            self.ap = not self.ap
                            self.default_member = self.curr_member
                            response.append({"type":"presence", "default":True})
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