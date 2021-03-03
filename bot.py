import discord
from discord.ext import commands
from utils import create_tables, sqlite
import os
from os import environ as env
import io
import chat_exporter

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
    embed = discord.Embed(
      title = "Ticket Started!",
      description = f"**Author:** {ctx.author.mention}\n**Reason:** ```{reason}```",
      color = discord.Colour.blue())
    await channel_msg.send(content = "@here", embed=embed)
    # TODO: mention/start message configurations.


  @commands.command()
  @commands.has_permissions(manage_channels=True)
  async def close(self, ctx: commands.Context):
   embed = discord.Embed(
     title = "Ticket Logs",
     description = f"**Closed by:** {ctx.author}", 
     color = discord.Colour.blue())
   channel = self.bot.get_channel(self.log_id(ctx.guild.id))
   transcript = await chat_exporter.export(ctx.channel, limit=1000)
   transcript_file = discord.File(io.BytesIO(transcript.encode()),
   filename=f"transcript-{ctx.channel.name}.html")
   await ctx.channel.delete()
   await channel.send(embed=embed, file=transcript_file)
   # TODO: custom checks to make sure the close command is ran in the ticket category.

  @commands.group(aliases=["configuration"])
  async def config(self, ctx: commands.Context):
    embed = discord.Embed(
      title = "Current Configurations",
      decription = "`ticket_logs <channel_ID>` - Change the channel where logs will be sent.",
      color = discord.Colour.blue()
    )
    await ctx.reply(embed=embed)

  @config.command()
  @command.has_permissions(manage_guild=True)
  async def ticket_logs(self, ctx: commands.Context, ID: int):
    self.db.execute("UPDATE Tickets SET logs=? WHERE guild_id=?", (ID, ctx.guild.id))
    await ctx.reply(f"✅ Successfully changed the logs channel to <#{self.logs(ctx.guild.id)}>.")



    





bot.add_cog(TicketBot(bot))
bot.run(env.get("TOKEN"))