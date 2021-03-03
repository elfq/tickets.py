import discord
from discord.ext import commands
from utils import create_tables, sqlite
from os import environ as env

tables = create_tables.creation(debug=True)
if not tables:
    sys.exit(1)

bot = commands.Bot(command_prefix="t!")

class TicketBot(commands.Cog):
  def __init__(self, bot: commands.Bot):
    self.bot = bot
    self.db = sqlite.Database()
  
  @commands.command(name = "setup")
  @commands.has_permissions(manage_guild=True)
  async def setup(self, ctx: commands.Context):
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
        ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    logs = await ctx.guild.create_text_channel('ticket-logs', overwrites=overwrites)
    category = await ctx.guild.create_category("Tickets", overwrites=overwrites)
    self.db.execute("INSERT INTO Tickets VALUES (?, ?, ?)", (ctx.guild.id, logs.id, category.id))
    await ctx.reply(f"👋 **Hello, there!**\n\nThis server has now been setup, if you would like to relocate your ticket logs, please use `{bot.command_prefix}config ticket_logs <channel_ID>`.")
  



bot.add_cog(TicketBot(bot))
bot.run(env.get("TOKEN"))