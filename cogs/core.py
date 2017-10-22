import sys
import discord

from discord.ext import commands

class Core:

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def reload(self, ctx, *, cog=''):
        '''Reloads an extension'''
        try:
            ctx.bot.unload_extension(cog)
            ctx.bot.load_extension(cog)
        except Exception as e:
            await ctx.send('Failed to load: `{}`\n```py\n{}\n```'.format(cog, e))
        else:
            await ctx.send('\N{OK HAND SIGN} Reloaded cog {} successfully'.format(cog))

    @reload.group(name='all', invoke_without_command=True)
    async def reload_all(self, ctx):
        '''Reloads all extensions'''
        if 'cogs.util' in sys.modules:
            import importlib
            importlib.reload(sys.modules['cogs.util'])

        for extension in ctx.bot.extensions.copy():
            ctx.bot.unload_extension(extension)
            try:
                ctx.bot.load_extension(extension)
            except Exception as e:
                await ctx.send('Failed to load `{}`:\n```py\n{}\n```'.format(extension, e))

        await ctx.send('\N{OK HAND SIGN} Reloaded {} cogs successfully'.format(len(ctx.bot.extensions)))

    @reload_all.group()
    async def lolol(self, ctx):
        pass

    @commands.command(aliases=['exception'])
    async def error(self, ctx, *, text: str = None):
        '''Raises an error. Testing purposes only, please don't use.'''
        raise Exception(text or 'Woo! Errors!')

    @commands.command()
    async def setname(self, ctx, *, name):
        '''Change the bot's username'''
        try:
            await self.bot.user.edit(username=name)
        except discord.HTTPException:
            await ctx.send('Changing the name failed.')

    @commands.command()
    async def setnick(self, ctx, *, name):
        '''Change the bot's nickname'''
        try:
            await ctx.guild.get_member(self.bot.user.id).edit(nick=name)
        except discord.HTTPException:
            await ctx.send('Changing the name failed.')

    @commands.command()
    async def setavatar(self, ctx):
        '''Change the bot's profile picture'''
        attachment = ctx.message.attachments[0]
        await attachment.save(attachment.filename)
        try:
            with open(attachment.filename, 'rb') as avatar:
                await self.bot.user.edit(avatar=avatar.read())
        except discord.HTTPException:
            await ctx.send('Changing the avatar failed.')
        except discord.InvalidArgument:
            await ctx.send('You did not upload an image.')

    @commands.command(aliases=['shutdown'])
    async def die(self, ctx):
        """Shuts down the bot"""
        ctx.bot.dying = True
        await ctx.send(':wave:')
        await ctx.bot.logout()

def setup(bot):
    bot.add_cog(Core(bot))