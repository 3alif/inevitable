import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import datetime
import random


class Games(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.active_games = {}
    
    @app_commands.command(name = 'dice', description = 'Gives you a random number from 1 to 6.')
    async def dice(self, interaction: discord.Interaction):
        number = ['1', '2', '3', '4', '5', '6']
        await interaction.response.send_message('🎲 You have got ' + random.choice(number))
    
    hotpotato_group = app_commands.Group(name="hotpotato", description="Commands for the hot potato game")

    @hotpotato_group.command(name='start', description='Starts a hotpotato game.')
    @app_commands.describe(time = 'Time in seconds (Default: 30)')
    async def hotpotato_start(self, interaction: discord.Interaction, time: int = 30):
        guild_id = interaction.guild.id
        
        if self.active_games.get(guild_id) is not None:
            current_holder = self.active_games[guild_id]
            await interaction.response.send_message(f'Hotpotato is already in progress. {current_holder.mention} is holding the potato.')
            return
        
        self.active_games[guild_id] = interaction.user
        await interaction.response.send_message(f'🥔 {interaction.user.mention} pulled the pin! The hot potato is live! {time} seconds to pass.')
        
        await asyncio.sleep(time)
        
        loser = self.active_games.get(guild_id)
        if loser is not None:
            self.active_games[guild_id] = None
            
            try:
                duration = datetime.timedelta(minutes=1)
                await loser.timeout(duration, reason="Lost Hot Potato")
                await interaction.channel.send(f'💥 BOOM! The potato exploded! {loser.mention} lost and has been timed out for 1 minute!')
            except discord.Forbidden:
                await interaction.channel.send(f'💥 BOOM! The potato exploded on {loser.mention}! (I tried to time them out, but I lack permissions to do so!)')
    
    @hotpotato_group.command(name='pass', description='Pass the potato to someone else.')
    @app_commands.describe(user = 'Who do you want to pass the potato to?')
    async def hotpotato_pass(self, interaction: discord.Interaction, user: discord.Member):
        guild_id = interaction.guild.id
        current_holder = self.active_games.get(guild_id)
        
        if current_holder is None:
            await interaction.response.send_message(f'There is no hotpotato game going on right now. Use `/hotpotato start` to begin one.')
            return
            
        if interaction.user != current_holder:
            await interaction.response.send_message(f'You are not the one holding the potato. {current_holder.mention} is.')
            return
            
        if user.bot:
            await interaction.response.send_message(f'You cannot pass the potato to a bot! Throw it to a real person!')
            return
            
        if user == interaction.user:
            await interaction.response.send_message(f'You cannot pass the potato to yourself!')
            return
        
        self.active_games[guild_id] = user
        await interaction.response.send_message(f'🥔 {interaction.user.mention} passed the hot potato to {user.mention}!')

    @hotpotato_group.command(name='help', description='How to play hot potato.')
    async def hotpotato_help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🥔 How to play Hot Potato",
            description=(
                "**The classic game of hot potato!**\n\n"
                "1️⃣ Start the game using `/hotpotato start`. A timer will begin.\n"
                "2️⃣ The person holding the potato must quickly pass it using `/hotpotato pass @user`.\n"
                "3️⃣ Keep passing it! If the timer runs out while you are holding it, it explodes! 💥"
            ),
            color=discord.Color.orange()
        )
        embed.add_field(name="/hotpotato start", value="Start a new game of hot potato.", inline=False)
        embed.add_field(name="/hotpotato pass <user>", value="Pass the potato to another user.", inline=False)
        embed.add_field(name="Penalty", value="The loser gets timed out for 1 minute! 💥", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(client):
    await client.add_cog(Games(client))