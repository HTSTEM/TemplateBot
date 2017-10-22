import traceback
import logging
import os
import re
import sys

import discord

from ruamel.yaml import YAML
from discord.ext import commands

class Bot(commands.AutoShardedBot):
    def __init__(self, command_prefix='!', *args, **kwargs):
        logging.basicConfig(level=logging.INFO, format='[%(name)s %(levelname)s] %(message)s')
        self.logger = logging.getLogger('bot')

        self.yaml = YAML(typ='safe')
        with open('config/config.yml') as conf_file:
            self.config = self.yaml.load(conf_file)

        if 'command_prefix' in self.config:
            command_prefix = self.config['command_prefix']

        super().__init__(command_prefix=command_prefix, *args, **kwargs)

    # Async methods
    async def close(self):
        await super().close()

    async def notify_devs(self, info, ctx=None):
        with open('error.txt', 'w') as error_file:
            error_file.write(info)

        for dev_id in self.config['developers']:
            dev = self.get_user(dev_id)
            if dev is None:
                self.logger.warning(f'Could not get developer with an ID of {dev.id}, skipping.')
                continue
            try:
                with open('error.txt', 'r') as error_file:
                    if ctx is None:
                        await dev.send(file=discord.File(error_file))
                    else:
                        await dev.send(f'{ctx.author}: {ctx.message.content}',file=discord.File(error_file))
            except Exception as e:
                self.logger.error('Couldn\'t send error embed to developer {0.id}. {1}'
                                .format(dev, type(e).__name__ + ': ' + str(e)))

        os.remove('error.txt')

    # Client events
    async def on_command_error(self, ctx: commands.Context, exception: Exception):
        if isinstance(exception, commands.CommandInvokeError):
            if isinstance(exception.original, discord.Forbidden):
                try: await ctx.send(f'Permissions error: `{exception}`')
                except discord.Forbidden: pass
                return

            lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
            self.logger.error(''.join(lines))
            await ctx.send(f'{exception.original}, the devs have been notified.')
            await self.notify_devs(''.join(lines), ctx)
        elif isinstance(exception, commands.CheckFailure):
            await ctx.send('You can\'t do that.')
        elif isinstance(exception, commands.CommandNotFound):
            pass
        elif isinstance(exception, commands.UserInputError):
            error = ' '.join(exception.args)
            error_data = re.findall('Converting to \"(.*)\" failed for parameter \"(.*)\"\.', error)
            if not error_data:
                await ctx.send('Error: {}'.format(' '.join(exception.args)))
            else:
                await ctx.send('Got to say, I *was* expecting `{1}` to be an `{0}`..'.format(*error_data[0]))
        else:
            info = traceback.format_exception(type(exception), exception, exception.__traceback__, chain=False)
            self.logger.error('Unhandled command exception - {}'.format(''.join(info)))
            await ctx.send(f'{exception}, the devs have been notified.')
            await self.notify_devs(''.join(info), ctx)

    async def on_error(self, event_method, *args, **kwargs):
        info = sys.exc_info()
        info = traceback.format_exception(*info, chain=False)
        self.logger.error('Unhandled exception - {}'.format(''.join(info)))
        await self.notify_devs(''.join(info))

    async def on_message(self, message):
        await self.process_commands(message)

    async def on_ready(self):
        self.logger.info(f'Connected to Discord')
        self.logger.info(f'Guilds  : {len(self.guilds)}')
        self.logger.info(f'Users   : {len(set(self.get_all_members()))}')
        self.logger.info(f'Channels: {len(list(self.get_all_channels()))}')

    def run(self, token):
        cogs = self.config['cogs']
        self.remove_command("help")
        for cog in cogs:
            try:
                self.load_extension(cog)
            except Exception as e:
                self.logger.exception(f'Failed to load cog {cog}:')
                self.logger.exception(e)
            else:
                self.logger.info(f'Loaded cog {cog}.')

        self.logger.info(f'Loaded {len(self.cogs)} cogs')
        super().run(token)

if __name__ == '__main__':
    bot = MusicBot()
    token = open(bot.config['token_file'], 'r').read().split('\n')[0]
    bot.run(token)
