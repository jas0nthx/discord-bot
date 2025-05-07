import discord
from discord.ext import commands
import time
import platform
import logging

class BasicCommands(commands.Cog):
    """Basic commands for the Discord bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('discord.basic_commands')
    
    @commands.command(name="hello")
    async def hello(self, ctx):
        """Say hello to the user."""
        await ctx.send(f"Hello {ctx.author.mention}! How can I help you today?")
    
    @commands.command(name="info")
    async def info(self, ctx):
        """Display information about the bot."""
        embed = discord.Embed(
            title="Bot Information",
            description="Information about this Discord bot",
            color=discord.Color.blue()
        )
        
        # Add bot information
        embed.add_field(name="Bot Name", value=self.bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="Platform", value=platform.system(), inline=True)
        embed.add_field(name="Prefix", value=self.bot.command_prefix, inline=True)
        
        # Calculate uptime
        uptime = int(time.time() - self.bot.uptime) if hasattr(self.bot, 'uptime') else 0
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        embed.add_field(name="Uptime", value=f"{hours}h {minutes}m {seconds}s", inline=True)
        
        # Add server count
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        
        # Set footer
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="serverinfo")
    async def server_info(self, ctx):
        """Display information about the current server."""
        guild = ctx.guild
        
        # Skip if not in a guild
        if not guild:
            await ctx.send("This command can only be used in a server.")
            return
        
        embed = discord.Embed(
            title=f"{guild.name} Information",
            description=guild.description or "No description",
            color=discord.Color.green()
        )
        
        # Add server icon if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Add basic information
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        
        # Add member information
        total_members = guild.member_count
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_members - bot_count
        
        embed.add_field(name="Total Members", value=total_members, inline=True)
        embed.add_field(name="Humans", value=human_count, inline=True)
        embed.add_field(name="Bots", value=bot_count, inline=True)
        
        # Add channel information
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        embed.add_field(name="Text Channels", value=text_channels, inline=True)
        embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
        embed.add_field(name="Categories", value=categories, inline=True)
        
        # Set footer
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="help")
    async def custom_help(self, ctx, command=None):
        """Display custom help information for commands."""
        if command:
            # Get help for a specific command
            cmd = self.bot.get_command(command)
            if cmd:
                embed = discord.Embed(
                    title=f"Help: {cmd.name}",
                    description=cmd.help or "No description available",
                    color=discord.Color.blue()
                )
                
                # Add usage information if available
                if cmd.signature:
                    embed.add_field(name="Usage", value=f"{self.bot.command_prefix}{cmd.name} {cmd.signature}", inline=False)
                else:
                    embed.add_field(name="Usage", value=f"{self.bot.command_prefix}{cmd.name}", inline=False)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Command '{command}' not found.")
        else:
            # General help - list all commands by cog
            embed = discord.Embed(
                title="Bot Commands",
                description=f"Use `{self.bot.command_prefix}help <command>` for detailed help",
                color=discord.Color.blue()
            )
            
            # Organize commands by cog
            for cog_name, cog in self.bot.cogs.items():
                # Get commands that are not hidden
                commands_list = [f"`{self.bot.command_prefix}{cmd.name}`" for cmd in cog.get_commands() if not cmd.hidden]
                
                if commands_list:
                    embed.add_field(name=cog_name, value=", ".join(commands_list), inline=False)
            
            # Add uncategorized commands
            uncategorized = [f"`{self.bot.command_prefix}{cmd.name}`" for cmd in self.bot.commands if not cmd.cog and not cmd.hidden]
            if uncategorized:
                embed.add_field(name="Uncategorized", value=", ".join(uncategorized), inline=False)
            
            # Set footer
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            
            await ctx.send(embed=embed)

async def setup(bot):
    """Add the cog to the bot."""
    # Store start time for uptime command
    bot.uptime = time.time()
    await bot.add_cog(BasicCommands(bot))
