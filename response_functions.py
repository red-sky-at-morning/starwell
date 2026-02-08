import discord
import asyncio
from webhooks import members

async def message(self: discord.Client, item:list[dict]|None, channel:discord.TextChannel):
    # send messages as bot
    # if len(item.get("message")) <= 0:
    #     if len(item.get("files", [])) + len(item.get("embeds", [])) <= 0:
    #         continue
    if self.curr_member is None or item.get("except", False):
        self.last_sent_message = await channel.send(item.get("message","No message provided"), embeds=item.get("embed", []), reference=item.get("reference"))
    else:
        hook = await members.get_or_make_webhook(channel)
        if type(channel) == discord.Thread:
            thread = channel
            channel = channel.parent
        else:
            thread = discord.utils.MISSING
        # replying
        if item.get("reference") is not None:
            resolve = item.get("reference").resolved
            if resolve != None:
                attachment_len = len(resolve.attachments) + len(resolve.embeds)
                embed = discord.Embed(description=f"[Reply to]({resolve.jump_url}): {resolve.content if len(resolve.content) >= 1 else "[no content]"} {"(includes attatchment)" if attachment_len > 0 else ""}")
                embed.set_author(name=resolve.author.name, icon_url=resolve.author.display_avatar.url)
                if item.get("embed") != None:
                    item["embed"].insert(0, embed)
                else:
                    item["embed"] = [embed]
        # files
        if item.get("files") is not None:
            for i, file in enumerate(item.get("files")):
                item["files"][i] = await file.to_file()
        
        # join the thread (technically not necessary, but courtesy)
        if type(thread) is discord.Thread:
            await thread.join()
        
        # send the message
        if item.get("use-default", False):
            self.last_sent_message = await hook.send(item.get("message",""), thread=(thread), username=self.default_member.get("username", None), avatar_url=self.default_member.get("avatar", None), files=item.get("files",[]), embeds=item.get("embed", []))
            return
        self.last_sent_message = await hook.send(item.get("message",""), thread=(thread), username=self.curr_member.get("username", None), avatar_url=self.curr_member.get("avatar", None), files=item.get("files",[]), embeds=item.get("embed", []))
    print(f"Said {item.get('message','No message provided')}{' (with embed)' if item.get("embed", []) else ""} in {channel.name} in {channel.guild.name}")

async def edit(self:discord.Client, item:list[dict]|None, channel:discord.TextChannel):
        # id: message id, message:content, embed:embeds (append to message embeds) file:files (append to message files)
    hook:discord.Webhook = await members.get_or_make_webhook(channel)
    message:discord.WebhookMessage = await hook.fetch_message(item.get("id"))
    old_content = message.content
    content:str = item.get("message", message.content)
    embeds:list = message.embeds.copy()
    embeds += item.get("embeds")
    
    await message.edit(content=content, embeds=embeds)
    print(f"Edited message in {channel.name} in {channel.guild.name} from {old_content} to {content}")

async def react(self:discord.Client, item:list[dict]|None, channel:discord.TextChannel):
    message:discord.Message = item.get("message", self.last_sent_message)
    if type(item.get("react")) == discord.PartialEmoji:
        await message.add_reaction(item.get("react"))
    else:
        for char in item.get("react"):
            await message.add_reaction(char)
    print(f"Reacted to {message.content} (by {message.author}) in {message.channel} in {message.channel.guild} with {item.get('react')}")

async def delete(self:discord.Client, item:list[dict]|None, channel:discord.TextChannel):
    try:
        message = item.get("message")
        if type(message) is int:
            message = await channel.fetch_message(item.get("message"))
        await message.delete()
    except discord.errors.PrivilegedIntentsRequired:
        await channel.send("We do not have permission to delete messages")

async def wait(self:discord.Client, item:list[dict]|None, channel:discord.TextChannel):
    print(f"Sleeping for {item.get('time', 0)} seconds...")
    await asyncio.sleep(item.get("time"))

async def webhook(self:discord.Client, item:list[dict]|None, channel:discord.TextChannel):
    if item.get("id", "_") != None:
        self.curr_member = members.get_member(item.get("id", "_"))
    if self.ap:
        return({"type":"presence", "default":True})
    if item.get("default", False):
        self.default_member = self.curr_member
        return({"type":"presence", "default":True})

async def call(self:discord.Client, item:list[dict]|None, channel:discord.TextChannel):
    wait_type = item.get("wait_type", None)
    if wait_type is not None:
        msg = await self.wait_for(wait_type, check=item.get("check", lambda x: True))
    else:
        msg = item.get("message")

    func = item.get("call", lambda x:None)
    return await func(self, msg.author.id, msg)

async def presence(self:discord.Client, item:list[dict]|None, channel:discord.TextChannel):
    if item.get("default", False):
        presence = f"{self.curr_member.get("presence", "watching the stars")}"
    else:
        presence = item.get("presence", f"{self.curr_member.get("presence", "watching the stars")}")
    
    emoji = "🟢" if self.ap else "🔴"
    if self.curr_member.get("emoji", None) is not None:
        emoji += self.curr_member.get("emoji")
    
    presence = f"{emoji} | {presence}"
    await self.change_presence(activity=discord.CustomActivity(name=presence))