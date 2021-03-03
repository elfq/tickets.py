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
    self.db.execute("INSERT INTO Tickets VALUES (?, ?, ?, ?)", (ctx.guild.id, logs.id, category.id, 1))
    await ctx.reply(f"👋 **Hello, there!**\n\nThis server has now been setup, if you would like to relocate your ticket logs, please use `{bot.command_prefix}config ticket_logs <channel_ID>`.")

  def category_id(self, guild_id):
   data = self.db.fetchrow("SELECT * FROM Tickets WHERE guild_id=?", (guild_id,))
   if data:
     return data["category"]
   else:
     return None

  def log_id(self, guild_id):
   data = self.db.fetchrow("SELECT * FROM Tickets WHERE guild_id=?", (guild_id,))
   if data:
     return data["logs"]
   else:
     return None

  def ticket_amt(self, guild_id):
   data = self.db.fetchrow("SELECT * FROM Tickets WHERE guild_id=?", (guild_id,))
   if data:
     return data["tickets"]
   else:
     return None

  @commands.command(aliases = ["ticket"])
  async def new(self, ctx: commands.Context, *, reason="No reason inputted."):
    overwrites = {
     ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
     ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    self.db.execute("UPDATE Tickets SET tickets=? WHERE guild_id=?", (self.ticket_amt(ctx.guild.id) + 1, ctx.guild.id))
    ticket_channel_id = await ctx.guild.create_text_channel(f'ticket-{self.ticket_amt(ctx.guild.id)}', overwrites=overwrites)
    await ticket_channel_id.edit(category=discord.utils.get(ctx.guild.channels, name="Tickets"))
    embed = discord.Embed(
      title = "Thread Created!",
      description = f"<#{ticket_channel_id.id}>",
      color = discord.Colour.blue()
    )
    await ctx.author.send(embed=embed)
    channel_msg = self.bot.get_channel(ticket_channel_id.id)
    await channel_msg.send(f"A ticket has been started by {ctx.author}, reason: `{reason}`.")

  @commands.command()
  async def close(self, ctx: commands.Context):
    





bot.add_cog(TicketBot(bot))
bot.run(env.get("TOKEN"))