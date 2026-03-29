import discord
from discord.ext import commands
from discord import app_commands
import os
from google import genai

class TranslateModal(discord.ui.Modal, title='Translate Message'):
    language = discord.ui.TextInput(
        label='Target Language',
        placeholder='e.g., English, Spanish, Japanese...',
        required=True,
        max_length=50
    )

    def __init__(self, message_to_translate: discord.Message, bot):
        super().__init__()
        self.message_to_translate = message_to_translate
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        target = self.language.value
        text = self.message_to_translate.content

        try:
            exclusion_list = await self.bot.db.smembers("translator_exclusion_keywords")
        except:
            exclusion_list = []
        exclusion_str = ""
        if exclusion_list:
            words = ", ".join([f"'{w}'" for w in exclusion_list])
            exclusion_str = f" CRITICAL INSTRUCTION: Do NOT translate or alter these specific keywords under any circumstances: {words}."

        prompt = f"Translate the following text to {target}. Be strict about literal and accurate translations. Do not use overly conversational slang if the original text is standard (e.g., translate 'hello' as 'hello', not 'sup'). Maintain gamer slang ONLY if originally present, use minimal AI flourish, and output ONLY the raw translation without preamble: \"{text}\"{exclusion_str}"
        
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            if not response.text:
                raise ValueError("Empty response from AI")
            translation = response.text.strip()
            
            # Save language to the per-server synced background translation engine
            try:
                await self.bot.db.hset(f"translator_subs:{interaction.guild_id}", str(interaction.user.id), target)
            except Exception as e:
                print(f"Failed to sync per-server setting: {e}")
            
            embed = discord.Embed(
                title=f"🌍 Translated to {target.capitalize()}",
                description=translation,
                color=discord.Color.green()
            )
            embed.set_author(name=self.message_to_translate.author.display_name, icon_url=self.message_to_translate.author.display_avatar.url if self.message_to_translate.author.display_avatar else None)
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Translation failed. ({str(e)[:50]})", ephemeral=True)

class TransChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(
            channel_types=[discord.ChannelType.text],
            placeholder="Select translation channels...",
            min_values=0,
            max_values=25
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Clear existing config
        await self.bot.db.delete(f"translation_channels:{interaction.guild_id}")
        
        if not self.values:
            await interaction.followup.send("📴 Cleared all translation channels. Auto-translation is disabled.", ephemeral=True)
            return
            
        # Add new selections
        for channel in self.values:
            await self.bot.db.sadd(f"translation_channels:{interaction.guild_id}", str(channel.id))
            
        mentions = [c.mention for c in self.values]
        await interaction.followup.send(f"✅ Auto-translation is now enabled in:\n" + "\n".join(mentions), ephemeral=True)

class TransConfigView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.add_item(TransChannelSelect(bot))

class QuickTranslator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Register the context menu command natively
        self.ctx_menu = app_commands.ContextMenu(
            name="Translate to...",
            callback=self.translate_context_menu,
        )
        self.ctx_menu.default_permissions = discord.Permissions(administrator=True)
        self.bot.tree.add_command(self.ctx_menu)

    async def translate_context_menu(self, interaction: discord.Interaction, message: discord.Message):
        # Check if user has a per-server preference
        preferred_lang = None
        try:
            preferred_lang = await self.bot.db.hget(f"translator_subs:{interaction.guild_id}", str(interaction.user.id))
        except:
            pass

        if preferred_lang:
            await interaction.response.defer(ephemeral=True)
            target = preferred_lang
            text = message.content

            try:
                exclusion_list = await self.bot.db.smembers("translator_exclusion_keywords")
            except:
                exclusion_list = []
            exclusion_str = ""
            if exclusion_list:
                words = ", ".join([f"'{w}'" for w in exclusion_list])
                exclusion_str = f" CRITICAL INSTRUCTION: Do NOT translate or alter these specific keywords under any circumstances: {words}."

            prompt = f"Translate the following text to {target}. Be strict about literal and accurate translations. Do not use overly conversational slang if the original text is standard (e.g., translate 'hello' as 'hello', not 'sup'). Maintain gamer slang ONLY if originally present, use minimal AI flourish, and output ONLY the raw translation without preamble: \"{text}\"{exclusion_str}"
            
            try:
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                response = await client.aio.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                if not response.text:
                    raise ValueError("Empty response from AI")
                translation = response.text.strip()
                
                embed = discord.Embed(
                    title=f"🌍 Translated to {target.capitalize()}",
                    description=translation,
                    color=discord.Color.green()
                )
                embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url if message.author.display_avatar else None)
                await interaction.followup.send(embed=embed, ephemeral=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                await interaction.followup.send(f"❌ Translation failed. ({str(e)[:50]})", ephemeral=True)
        else:
            # Fallback: Open a modal to ask for language
            await interaction.response.send_modal(TranslateModal(message, self.bot))

    async def cog_load(self):
        from cogs.utils.ui import PersistentLanguageView
        self.bot.add_view(PersistentLanguageView(self.bot))

    async def cog_unload(self):
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    @commands.command(aliases=['qt'])
    async def qtranslate(self, ctx, target_language: str = None, *, text_to_translate: str = None):
        """Instantly translates the provided text into the target language."""
        if not target_language or not text_to_translate:
            return await ctx.send("❌ Usage: `!qtranslate <Language> <Text...>`\nExample: `!qtranslate Spanish That clutch was insane!`")
            
        from cogs.utils.ui import LANGUAGES
        valid_langs = {}
        for key, data in LANGUAGES.items():
            if key == "Off": continue
            valid_langs[key.lower()] = key
            if "code" in data:
                valid_langs[data["code"].lower()] = key
        
        if target_language.lower() not in valid_langs:
            return await ctx.send(f"❌ \"{target_language}\" isn't a valid translation choice, unless you speak Elvish or Klingon! Please stick to Earth languages.")
        target_language = valid_langs[target_language.lower()]

        # Indicate the bot is "typing" while it fetches the API
        async with ctx.typing():
            try:
                try:
                    exclusion_list = await self.bot.db.smembers("translator_exclusion_keywords")
                except:
                    exclusion_list = []
                exclusion_str = ""
                if exclusion_list:
                    words = ", ".join([f"'{w}'" for w in exclusion_list])
                    exclusion_str = f" CRITICAL INSTRUCTION: Do NOT translate or alter these specific keywords under any circumstances: {words}."

                prompt = f"Translate the following text to {target_language}. Be strict about literal and accurate translations. Do not use overly conversational slang if the original text is standard (e.g., translate 'hello' as 'hello', not 'sup'). Maintain gamer slang ONLY if originally present, use minimal AI flourish, and output ONLY the raw translation without preamble: \"{text_to_translate}\"{exclusion_str}"
                
                try:
                    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                    response = await client.aio.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                    if not response.text:
                        raise ValueError("Empty response from AI")
                    translation = response.text.strip()
                except Exception as api_err:
                    import traceback
                    traceback.print_exc()
                    raise api_err
                
                try:
                    await self.bot.db.hset(f"translator_subs:{ctx.guild.id}", str(ctx.author.id), target_language)
                except:
                    pass
                
                
                await ctx.send(f"🌍 **{target_language.capitalize()}:** {translation}")

            except Exception as e:
                import traceback
                traceback.print_exc()
                await ctx.send(f"❌ Quick Translation failed. Please try again later. ({str(e)[:50]})")

    @app_commands.command(name="translate", description="Instantly translate text to a targeted language")
    @app_commands.describe(language="The language to translate into", text="The text you want to translate")
    @app_commands.default_permissions(administrator=True)
    async def slash_translate(self, interaction: discord.Interaction, language: str, text: str):
        """Instantly parses text via slash command and translates it into another language."""
        from cogs.utils.ui import LANGUAGES
        valid_langs = {}
        for key, data in LANGUAGES.items():
            if key == "Off": continue
            valid_langs[key.lower()] = key
            if "code" in data:
                valid_langs[data["code"].lower()] = key
                
        if language.lower() not in valid_langs:
            return await interaction.response.send_message(f"❌ \"{language}\" isn't a valid translation choice, unless you speak Elvish or Klingon! Please stick to Earth languages.", ephemeral=True)
        language = valid_langs[language.lower()]

        # Indicate the bot is "thinking" while it fetches the API natively in Discord's UI
        # We use defer without ephemeral so the result is posted publicly in the channel
        await interaction.response.defer(ephemeral=False)
        try:
            try:
                exclusion_list = await self.bot.db.smembers("translator_exclusion_keywords")
            except:
                exclusion_list = []
            exclusion_str = ""
            if exclusion_list:
                words = ", ".join([f"'{w}'" for w in exclusion_list])
                exclusion_str = f" CRITICAL INSTRUCTION: Do NOT translate or alter these specific keywords under any circumstances: {words}."

            prompt = f"Translate the following text to {language}. Be strict about literal and accurate translations. Do not use overly conversational slang if the original text is standard (e.g., translate 'hello' as 'hello', not 'sup'). Maintain gamer slang ONLY if originally present, use minimal AI flourish, and output ONLY the raw translation without preamble: \"{text}\"{exclusion_str}"
            
            try:
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                response = await client.aio.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt
                )
                if not response.text:
                    raise ValueError("Empty response from AI")
                translation = response.text.strip()
            except Exception as api_err:
                import traceback
                traceback.print_exc()
                raise api_err
            
            try:
                await self.bot.db.hset(f"translator_subs:{interaction.guild_id}", str(interaction.user.id), language)
            except:
                pass
            
            await interaction.followup.send(f"🌍 **{language.capitalize()}:** {translation}")

        except Exception as e:
            import traceback
            traceback.print_exc()
            await interaction.followup.send(f"❌ Translation failed. ({str(e)[:50]})")

    @commands.command()
    async def translate(self, ctx, member: discord.Member = None):
        """Configure per-server auto-translation directly into your DMs using a dropdown menu."""
        from cogs.utils.ui import LanguageDropdown
        
        if member and member.id != ctx.author.id:
            if not ctx.author.guild_permissions.administrator:
                return await ctx.send("❌ You need Administrator permissions to configure translations for another user.")
            target_id = member.id
            embed = discord.Embed(
                title=f"🌍 Configure Translation for {member.display_name}",
                description=f"Select the preferred language for {member.mention}.",
                color=discord.Color.blue()
            )
        else:
            target_id = ctx.author.id
            embed = discord.Embed(
                title="🌍 Translation Setup",
                description="Select your preferred language from the dropdown below to receive auto-translated DMs.\nNote: You can also use this dropdown to disable auto-translations.",
                color=discord.Color.blue()
            )
            
        view = discord.ui.View()
        # Ephemeral view doesn't necessarily need a custom id, but we supply suffix to be safe.
        view.add_item(LanguageDropdown(self.bot, target_user_id=target_id))
        
        await ctx.send(embed=embed, view=view)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def spawntranslator(self, ctx):
        """Spawns a persistent dropdown menu for users to self-assign their translation language."""
        from cogs.utils.ui import PersistentLanguageView
        
        embed = discord.Embed(
            title="🌍 Auto-Translation Setup",
            description="Select your preferred language from the dropdown below or disable auto-translations altogether.\n\nWhenever someone sends a message in a supported channel, it will be automatically translated and sent directly to your DMs!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, view=PersistentLanguageView(self.bot))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addtranschannel(self, ctx, channel: discord.TextChannel = None):
        """Allow auto-translations in a specific channel."""
        if not channel:
            return await ctx.send("❌ Usage: `!addtranschannel #channel`")
        await self.bot.db.sadd(f"translation_channels:{ctx.guild.id}", str(channel.id))
        await ctx.send(f"✅ Auto-translation has been **enabled** for {channel.mention}.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removetranschannel(self, ctx, channel: discord.TextChannel = None):
        """Disallow auto-translations in a specific channel."""
        if not channel:
            return await ctx.send("❌ Usage: `!removetranschannel #channel`")
        deleted = await self.bot.db.srem(f"translation_channels:{ctx.guild.id}", str(channel.id))
        if deleted:
            await ctx.send(f"✅ Auto-translation has been **disabled** for {channel.mention}.")
        else:
            await ctx.send(f"⚠️ {channel.mention} is not currently in the translation allowlist.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def transconfig(self, ctx):
        """Interactive dropdown menu to configure translation allowlisted channels."""
        current_channels = await self.bot.db.smembers(f"translation_channels:{ctx.guild.id}")
        desc = "Use the dropdown menu below to select which text channels should allow auto-translation! Unselecting channels implicitly removes them."
        if current_channels:
            mentions = [f"<#{c}>" for c in current_channels]
            desc += "\n\n**Currently Active Channels:**\n" + "\n".join(mentions)
            
        embed = discord.Embed(
            title="🌍 Translation Channel Configuration",
            description=desc,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=TransConfigView(self.bot))

async def setup(bot):
    await bot.add_cog(QuickTranslator(bot))
