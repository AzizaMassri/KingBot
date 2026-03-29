import discord
from discord.ext import commands

class Aliases(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def alias(self, ctx, original_command: str = None, new_alias: str = None):
        """Creates a custom shortcut/alias for an existing command."""
        if not original_command or not new_alias:
            return await ctx.send("❌ Usage: `!alias <OriginalCommand> <NewAlias>`\nExample: `!alias rank profile`")
            
        original_command = original_command.lower().lstrip(ctx.prefix).replace('<@!', '<@')
        new_alias = new_alias.lower().lstrip(ctx.prefix).replace('<@!', '<@')

        is_mention = original_command.startswith('<@') and original_command.endswith('>')

        # Basic Check: Does the original command even exist?
        if not is_mention and not self.bot.get_command(original_command):
            return await ctx.send(f"❌ The command `{original_command}` does not exist!")

        # Basic Check: Is the alias already a core command?
        if self.bot.get_command(new_alias):
            return await ctx.send(f"❌ You cannot use `{new_alias}` as an alias because it is already a real command.")

        # Save to Database hash `aliases:{guild_id}`
        await self.db.hset(f"aliases:{ctx.guild.id}", new_alias, original_command)
        
        display_alias = new_alias if new_alias.startswith('<@') else f"!{new_alias}"
        await ctx.send(f"✅ Created alias! Typing `{display_alias}` will now execute `!{original_command}`.")

    @commands.command(name="aliases")
    async def list_aliases(self, ctx):
        """Displays all active aliases for this server in two columns."""
        aliases_data = await self.db.hgetall(f"aliases:{ctx.guild.id}")
        
        if not aliases_data:
            return await ctx.send("There are currently no aliases set for this server.")

        embed = discord.Embed(
            title="🔗 Server Command Aliases",
            description="Here are all the custom shortcuts set up for this server:",
            color=discord.Color.purple()
        )

        alias_column = ""
        original_column = ""

        # Database returns bytes if not decoded, but python-database decode_responses=True is active in bot.py
        for alias, original in aliases_data.items():
            if alias.startswith('<@'):
                alias_column += f"`{alias}`\n"
            else:
                alias_column += f"`!{alias}`\n"
                
            if original.startswith('<@'):
                original_column += f"`{original}`\n"
            else:
                original_column += f"`!{original}`\n"

        embed.add_field(name="Alias", value=alias_column, inline=True)
        embed.add_field(name="Original Command", value=original_column, inline=True)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # Check if the message is potentially a command
        # bot.command_prefix could be a string, a list, or a callable. 
        # For simplicity in this bot, we assume it's "!" globally as defined in bot.py. 
        prefix = '!'
        parts = message.content.split()
        if not parts:
            return
            
        first_word = parts[0].lower()
        invoked_alias = None
        
        if first_word.startswith(prefix):
            invoked_alias = first_word[len(prefix):]
        elif first_word.startswith('<@') and first_word.endswith('>'):
            invoked_alias = first_word.replace('<@!', '<@')
            
        if invoked_alias:
            original_command = await self.db.hget(f"aliases:{message.guild.id}", invoked_alias)
            
            if original_command:
                # Replace the alias with the original command name in the message content
                if original_command.startswith('<@') and original_command.endswith('>'):
                    new_content = message.content.replace(parts[0], original_command, 1)
                else:
                    new_content = message.content.replace(parts[0], f"{prefix}{original_command}", 1)
                message.content = new_content
                
                # We definitively found an alias. We need to manually construct the context
                # and invoke the original command because simply changing message.content
                # does not re-trigger the discord.py event pipeline natively.
                ctx = await self.bot.get_context(message)
                command = self.bot.get_command(original_command)
                
                if command:
                    await command.invoke(ctx)
                elif original_command.startswith('<@') and original_command.endswith('>'):
                    # The user is triggering an alias to ping another bot/user.
                    # We impersonate them using a webhook so it looks seamless!
                    try:
                        await message.delete()
                    except:
                        pass
                        
                    try:
                        webhooks = await message.channel.webhooks()
                        webhook = discord.utils.get(webhooks, name="KingBot Alias")
                        if not webhook:
                            webhook = await message.channel.create_webhook(name="KingBot Alias")
                            
                        await webhook.send(
                            content=message.content,
                            username=message.author.display_name,
                            avatar_url=message.author.display_avatar.url
                        )
                    except discord.Forbidden:
                        await message.channel.send(message.content)


async def setup(bot):
    await bot.add_cog(Aliases(bot))
