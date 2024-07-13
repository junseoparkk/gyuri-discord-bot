import discord
import random

def number_to_emoji(number):
    """
    숫자를 이모지로 변환합니다.
    """
    num_to_emoji = {
        '0': ':zero:', '1': ':one:', '2': ':two:', '3': ':three:', '4': ':four:',
        '5': ':five:', '6': ':six:', '7': ':seven:', '8': ':eight:', '9': ':nine:'
    }
    return ''.join(num_to_emoji[digit] for digit in str(number))

def setup_roll_command(bot):
    @bot.tree.command(name='굴려')
    async def roll_command(interaction: discord.Interaction):
        """🍊규리가 주사위를 굴려요!"""
        await roll_dice(interaction)

async def roll_dice(interaction: discord.Interaction):
    """🍊규리가 1부터 100까지의 숫자 중 하나를 무작위로 골라줘요!"""
    roll = random.randint(1, 100)
    roll_emoji = number_to_emoji(roll)
    await interaction.response.send_message(f'🎲 {interaction.user.mention} : {roll_emoji}', ephemeral=False)