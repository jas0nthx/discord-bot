import discord
from discord.ext import commands
import datetime
import logging
import random

class UtilityCommands(commands.Cog):
    """Utility commands for the Discord bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger('discord.utility_commands')
    
    @commands.command(name="echo")
    async def echo(self, ctx, *, message=None):
        """Repeat the user's message."""
        if message:
            await ctx.send(message)
        else:
            await ctx.send("You need to provide a message for me to echo.")
    
    @commands.command(name="roll")
    async def roll(self, ctx, dice: str = "1d6"):
        """Roll dice in NdN format."""
        try:
            # Parse the dice notation
            rolls, limit = map(int, dice.split('d'))
            
            # Validate input
            if rolls <= 0 or limit <= 0:
                await ctx.send("Number of dice and sides must be positive numbers.")
                return
            
            if rolls > 100:
                await ctx.send("You can't roll more than 100 dice at once.")
                return
            
            # Roll the dice
            results = [random.randint(1, limit) for _ in range(rolls)]
            total = sum(results)
            
            # Format the response
            if len(results) == 1:
                await ctx.send(f"🎲 You rolled a **{results[0]}**")
            else:
                await ctx.send(f"🎲 You rolled: {', '.join(str(r) for r in results)}\nTotal: **{total}**")
        
        except ValueError:
            await ctx.send("Invalid dice format. Use NdN format (e.g., 1d6, 2d20).")
    
    @commands.command(name="choose")
    async def choose(self, ctx, *, options=None):
        """Choose between multiple options separated by commas."""
        if not options:
            await ctx.send("You need to provide options for me to choose from, separated by commas.")
            return
        
        # Split the options by commas and strip whitespace
        choices = [choice.strip() for choice in options.split(',') if choice.strip()]
        
        if not choices:
            await ctx.send("I couldn't find any valid options to choose from.")
            return
        
        if len(choices) == 1:
            await ctx.send(f"You only gave me one option: **{choices[0]}**")
            return
        
        # Select a random choice
        selected = random.choice(choices)
        await ctx.send(f"🤔 I choose: **{selected}**")
    
    @commands.command(name="userinfo")
    async def user_info(self, ctx, member: discord.Member = None):
        """Display information about a user."""
        # If no member is specified, use the command author
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"User Information: {member.name}",
            color=member.color
        )
        
        # Add user avatar
        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        
        # Add user information
        embed.add_field(name="Username", value=member.name, inline=True)
        embed.add_field(name="Discriminator", value=member.discriminator, inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        
        # Add join dates
        embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        
        # Add roles (excluding @everyone)
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        if roles:
            embed.add_field(name=f"Roles [{len(roles)}]", value=", ".join(roles), inline=False)
        else:
            embed.add_field(name="Roles", value="No roles", inline=False)
        
        # Set footer
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="poll")
    async def poll(self, ctx, question=None, *options):
        """Create a simple poll with reactions."""
        if not question:
            await ctx.send("You need to provide a question for the poll.")
            return
        
        if len(options) < 2:
            # If not enough options are provided, use yes/no poll
            embed = discord.Embed(
                title="📊 Poll",
                description=question,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Poll by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            
            message = await ctx.send(embed=embed)
            await message.add_reaction("👍")  # Thumbs up
            await message.add_reaction("👎")  # Thumbs down
        else:
            # Multiple choice poll
            if len(options) > 10:
                await ctx.send("You can only have up to 10 options in a poll.")
                return
            
            # Emoji options (numbers 1-10)
            emoji_options = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            
            embed = discord.Embed(
                title="📊 Poll",
                description=question,
                color=discord.Color.blue()
            )
            
            # Add options to the embed
            for i, option in enumerate(options):
                embed.add_field(name=f"Option {i+1}", value=f"{emoji_options[i]} {option}", inline=False)
            
            embed.set_footer(text=f"Poll by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            
            message = await ctx.send(embed=embed)
            
            # Add reactions for each option
            for i in range(len(options)):
                await message.add_reaction(emoji_options[i])

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(UtilityCommands(bot))
