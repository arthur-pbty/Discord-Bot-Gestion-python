import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import os
import sys
import pytz
from datetime import datetime, timedelta
import sqlite3
from random import randint, sample, choice
import aiohttp
import inspect
import wikipedia
from collections import defaultdict
import asyncio
from typing import Literal
import re


load_dotenv()
roles_perm = ["perm 5", "perm 4", "perm 3", "perm 2", "perm 1"]
sniped_messages = {}
link_regex = re.compile(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")



def redemarrer_script():
   python = sys.executable
   os.execl(python, python, *sys.argv)

def choose_db(guild_id):
   con = sqlite3.connect(f"db/{guild_id}.db")
   cur = con.cursor()
   return con, cur


intents = discord.Intents().all()
bot = commands.Bot(command_prefix='?', intents=intents, help_command=None)

intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@bot.event
async def on_ready():
   print(f'Bot is ready with : \n username: {bot.user.name} \n id: {bot.user.id}')
   await bot.change_presence(activity=discord.Streaming(name="/help", url="https://www.twitch.tv/tuturp33"))
   reload = False

   for guild in bot.guilds:

      for role in roles_perm:
         existing_role = discord.utils.get(guild.roles, name=role)
         if existing_role is None:
            await guild.create_role(name=role)
      
      con, cur = choose_db(guild.id)
      cur.execute('''
         CREATE TABLE IF NOT EXISTS warns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            moderator_id INTEGER,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
         )''')
      cur.execute('''
         CREATE TABLE IF NOT EXISTS badwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            badword TEXT,
            utilisation INTEGER,
            create_by_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
         )''')
      cur.execute('''
         CREATE TABLE IF NOT EXISTS whitelist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            moderator_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
         )''')
      cur.execute('''
         CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            moderator_id INTEGER,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
         )''')
      cur.execute('''
         CREATE TABLE IF NOT EXISTS commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commande TEXT,
            perm TEXT,
            utilisation TEXT,
            active BOOLEAN
         )''')
      cur.execute('''
         CREATE TABLE IF NOT EXISTS config (
            env TEXT,
            id TEXT
         )''')
      cur.execute('''
         CREATE TABLE IF NOT EXISTS ownerbot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            moderator_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
         )''')
      cur.execute('''
         CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            messages INTEGER,
            voice INTEGER,
            coins INTEGER,
            bank INTEGER,
            xp INTEGER,
            level INTEGER,
            last_daily DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_work DATETIME DEFAULT CURRENT_TIMESTAMP,
            xp_multiplier INTEGER DEFAULT 1,
            coins_multiplier INTEGER DEFAULT 1
         )''')

      config_values = [
         ("LOG_MESSAGE", "None"),
         ("LOG_JOIN_LEAVE", "None"),
         ("LOG_MODERATION", "None"),
         ("LOG_MEMBER_UPDATE", "None"),
         ("LOG_CHANNEL", "None"),
         ("LOG_ROLE", "None"),
         ("LOG_BOOST", "None"),
         ("ROLE_MUTE_ID", "None"),
         ("CHANNEL_JOIN", "None"),
         ("CHANNEL_LEAVE", "None"),
         ("ROLE_ACTIVITY", "None"),
         ("ACTIVITY_FOR_ROLE", "None"),
         ("ROLE_BOOST", "None"),
         ("LOG_MP_BOT", "None"),
         ("anti link", "True"),
         ("anti spam", "True"),
      ]
      for env, id in config_values:
         cur.execute("SELECT 1 FROM config WHERE env = ?", (env,))
         if cur.fetchone() is None:
            cur.execute("INSERT INTO config (env, id) VALUES (?, ?)", (env, id))


      global commands_info
      commands_info = {
         "sync": ["ownerbot", "", 1, "Synchronise les commandes du bot"],
         "say": ["perm 5", "<votre_phrase>", 1, "Fait parler le bot"],
         "ban": ["perm 4", "<membre> <raison> <delete_message_days>", 1, "Banni un membre"],
         "kick": ["perm 3", "<membre> <raison>", 1, "Kick un membre"],
         "bantemp": ["perm 4", "<membre> <temps> <raison> <delete_message_days>", 1, "Banni temporairement un membre"],
         "clear": ["perm 2", "<nombre_de_messages>", 1, "Supprime des messages"],
         "mute": ["perm 1", "<membre> <raison>", 1, "Mute un membre"],
         "unmute": ["perm 1", "<membre> <raison>", 1, "Unmute un membre"],
         "addrole": ["perm 3", "<membre> <role> <raison>", 1, "Ajoute un rôle à un membre"],
         "removerole": ["perm 3", "<membre> <role> <raison>", 1, "Retire un rôle à un membre"],
         "poll": ["perm 1", "<question> <option1> <option2> <option3>...<option10>", 1, "Crée un sondage"],
         "userinfo": ["None", "<membre>", 1, "Donne des informations sur un membre"],
         "ping": ["None", "", 1, "Donne le ping du bot"],
         "serverinfo": ["None", "", 1, "Donne des informations sur le serveur"],
         "stats": ["None", "", 1, "Donne des statistiques sur le bot"],
         "memberlist": ["None", "", 1, "Donne la liste des membres du serveur"],
         "rolelist": ["None", "", 1, "Donne la liste des rôles du serveur"],
         "channellist": ["None", "", 1, "Donne la liste des channels du serveur"],
         "roleinfo": ["None", "<role>", 1, "Donne des informations sur un rôle"],
         "channelinfo": ["None", "<channel>", 1, "Donne des informations sur un channel"],
         "lock": ["perm 4", "<channel>", 1, "Verrouille un channel"],
         "unlock": ["perm 4", "<channel>", 1, "Déverrouille un channel"],
         "channelcreate": ["perm 5", "<nom_du_channel> <type> <category>", 1, "Crée un channel"],
         "channeldelete": ["perm 5", "<channel>", 1, "Supprime un channel"],
         "channelrename": ["perm 5", "<channel> <nouveau_nom>", 1, "Renomme un channel"],
         "wikisearch": ["None", "<recherche>", 1, "Recherche sur wikipedia"],
         "warn": ["perm 1", "<membre> <raison>", 1, "Warn un membre"],
         "warnlist": ["perm 1", "<membre>", 1, "Donne la liste des warns d'un membre"],
         "delwarn": ["perm 2", "<membre> <warn_id>", 1, "Supprime un warn d'un membre"],
         "resetwarn": ["perm 2", "<membre>", 1, "Supprime tous les warns d'un membre"],
         "addbadword": ["perm 2", "<badword>", 1, "Ajoute un mot interdit"],
         "delbadword": ["perm 2", "<badword>", 1, "Supprime un mot interdit"],
         "badwordlist": ["None", "", 1, "Donne la liste des mots interdits"],
         "resetbadword": ["perm 2", "", 1, "Supprime tous les mots interdits"],
         "badwordinfo": ["None", "<badword>", 1, "Donne des informations sur un mot interdit"],
         "tempmute": ["perm 1", "<membre> <temps> <raison>", 1, "Mute temporairement un membre"],
         "snipe": ["None", "", 1, "Donne le dernier message supprimé"],
         "snipeall": ["None", "", 1, "Donne les messages supprimés de tout les channels"],
         "botstatut": ["ownerbot", "<statut>", 1, "Change le statut du bot"],
         "avatar": ["None", "<membre>", 1, "Donne l'avatar d'un membre"],
         "addemoji": ["perm 3", "<nom> <url>", 1, "Ajoute un emoji"],
         "wladd": ["ownerbot", "<membre>", 1, "Ajoute un membre à la whitelist"],
         "wldel": ["ownerbot", "<membre>", 1, "Supprime un membre de la whitelist"],
         "wl": ["perm 5", "", 1, "Donne la liste des membres de la whitelist"],
         "wlreset": ["ownerbot", "", 1, "Supprime tous les membres de la whitelist"],
         "wlinfo": ["perm 5", "<membre>", 1, "Donne des informations sur un membre de la whitelist"],
         "bladd": ["ownerbot", "<membre> <raison>", 1, "Ajoute un membre à la blacklist"],
         "bldel": ["ownerbot", "<membre>", 1, "Supprime un membre de la blacklist"],
         "bl": ["perm 5", "", 1, "Donne la liste des membres de la blacklist"],
         "blreset": ["ownerbot", "", 1, "Supprime tous les membres de la blacklist"],
         "blinfo": ["perm 5", "<membre>", 1, "Donne des informations sur un membre de la blacklist"],
         "calc": ["None", "<calcul>", 1, "Calcule une opération"],
         "help": ["None", "<commande|optionnel> <page|optionnel>", 1, "Donne la liste des commandes"],
         "commandeperms": ["perm 5", "", 1, "Donne la liste des commandes avec leurs permissions"],
         "commandechangeperms": ["ownerbot", "<commande> <perm>", 1, "Change les permissions d'une commande"],
         "mp": ["perm 5", "<membre> <message>", 1, "Envoie un message privé à un membre"],
         "giveaway": ["perm 5", "<temps> <nombre_de_gagnants> <prix>", 1, "Crée un giveaway"],
         "reroll": ["perm 5", "<giveaway_id>", 1, "Relance un giveaway"],
         "changeactive": ["ownerbot", "<commande> <active(1 ou 2)>", 1, "Change l'activation d'une commande"],
         "config": ["ownerbot", "<config> <valeur>", 1, "Permet de changer la config ud bot"],
         "configall": ["perm 5", "", 1, "Donne la liste des configs du bot"],
         "setbotavatar": ["ownerbot", "<url>", 1, "Change l'avatar du bot"],
         "ownerbot": ["perm 5", "", 1, "Donne la liste des propriétaires du bot"],
         "ownerbotadd": ["ownerbot", "<membre>", 1, "Ajoute un membre à la liste des propriétaires du bot"],
         "ownerbotremove": ["ownerbot", "<membre>", 1, "Supprime un membre de la liste des propriétaires du bot"],
         "ownerbotreset": ["ownerbot", "", 1, "Supprime tous les membres de la liste des propriétaires du bot"],
         "reload": ["ownerbot", "", 1, "Redémarre le bot"],
         "embed": ["perm 5", "<titre> <description> <couleur> <image> <footer>", 1, "Crée un embed"],
         "rename": ["perm 5", "<nouveau_nom>", 1, "Renomme un membre"],
         "setbotname": ["ownerbot", "<nouveau_nom>", 1, "Change le nom du bot"],
         "join": ["perm 5", "<channel|optionnel>", 1, "Fait rejoindre un salon vocal au bot qui joue de la musique"],
         "leave": ["perm 5", "", 1, "Fait quitter le bot du salon vocal"],
         "banner": ["None", "<membre>", 1, "Donne la bannière d'un membre"],
         "serverlist": ["ownerbot", "", 1, "Donne la liste des serveurs où est le bot"],
         "boosters": ["None", "", 1, "Donne la liste des boosters du serveur"],
         "botlist": ["None", "", 1, "Donne la liste des bots"],
         "botadmin": ["perm 5", "", 1, "Donne la liste de tout les bots qui ont les permissions administrateur"],
         "support": ["None", "", 1, "Donne le lien du serveur support"],
         "emojiinfo": ["None", "<emoji>", 1, "Donne des informations sur un emoji"],
         "emojilist": ["None", "", 1, "Donne la liste des emojis du serveur"],
         "coin": ["None", "<membre|optionnel>", 1, "Donne le nombre de coins d'un membre"],
         "level": ["None", "<membre|optionnel>", 1, "Donne le niveau d'un membre"],
         "coinflip": ["None", "<mise>", 1, "Joue à pile ou face"],
         "leaderboard": ["None", "<coins|bank|level|messages|voice>", 1, "Donne le classement des membres"],
         "daily": ["None", "", 1, "Donne des coins tous les jours"],
         "work": ["None", "", 1, "Gagne des coins en travaillant"],
         "deposit": ["None", "<montant>", 1, "Dépose des coins dans la banque"],
         "withdraw": ["None", "<montant>", 1, "Retire des coins de la banque"],
         "give": ["ownerbot", "<coins|bank|xp|level|messages|voice> <montant> <membre|optionnel>", 1, "Donne des coins, de la bank, de l'xp, des levels, des messages ou de la voice à un membre"],
         "take": ["ownerbot", "<coins|bank|xp|level|messages|voice> <montant> <membre|optionnel>", 1, "Retire des coins, de la bank, de l'xp, des levels, des messages ou de la voice à un membre"],
         "reset": ["ownerbot", "<coins|bank|xp|level|messages|voice|all> <membre|optionnel>", 1, "Supprime les coins, la bank, l'xp, les levels, les messages ou la voice d'un membre"],
         "pay": ["None", "<montant> <membre>", 1, "Donne des coins à un membre"],
         "shop": ["None", "", 1, "Donne la liste des items du shop"],
         "buy": ["None", "<item>", 1, "Achète un item du shop"],
         "mpall": ["ownerbot", "<message>", 1, "Envoie un message privé à tout les membres du serveur"],
         "unban": ["perm 4", "<membre>", 1, "Unban un membre"],
      }
      for command, atribus in commands_info.items():
         cur.execute("SELECT * FROM commands WHERE commande = ?", (command,))
         if cur.fetchone() is None:
            reload = True
            cur.execute("INSERT INTO commands (commande, perm, utilisation, active) VALUES (?, ?, ?, ?)", (command, atribus[0], atribus[1], atribus[2]))
      con.commit()

      for user in guild.members:
         cur.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
         if cur.fetchone() is None:
            cur.execute("INSERT INTO users (user_id, messages, voice, coins, bank, xp, level) VALUES (?, ?, ?, ?, ?, ?, ?)", (user.id, 0, 0, 0, 0, 0, 0))
      con.commit()

      try:
         synced = await bot.tree.sync(guild=guild)
         print(f"Synced {len(synced)} commands for guild {guild.id}")
      except Exception as e:
         print(f"Error syncing commands for guild {guild.id}: {e}")

   if reload == True:
      redemarrer_script()

      

async def check_permissions(interaction, fonc_name):
   con, cur = choose_db(interaction.guild.id)
   try:
      if interaction.user.id == 671763971803447298:
         return True
      
      cur.execute("SELECT * FROM blacklist WHERE user_id = ?", (interaction.user.id,))
      if cur.fetchone() is not None:
         return False
      cur.execute("SELECT * FROM ownerbot WHERE user_id = ?", (interaction.user.id,))
      if cur.fetchone() is not None:
         return True

      cur.execute("SELECT * FROM commands WHERE commande = ?", (fonc_name,))
      command = cur.fetchone()
      if command is None:
         return False
      permissions = command[2]
      if permissions == "None":
         return True
      elif permissions == "ownerbot":
         return False
      else:
         for i in roles_perm:
            role = discord.utils.get(interaction.guild.roles, name=i)
            if role in interaction.user.roles:
               if roles_perm.index(role.name) <= roles_perm.index(permissions):
                  return True
               else:
                  return False
         return False
   except:
      if interaction.author.id == 671763971803447298:
         return True
      
      cur.execute("SELECT * FROM blacklist WHERE user_id = ?", (interaction.author.id,))
      if cur.fetchone() is not None:
         return False
      cur.execute("SELECT * FROM ownerbot WHERE user_id = ?", (interaction.author.id,))
      if cur.fetchone() is not None:
         return True
      
      cur.execute("SELECT * FROM commands WHERE commande = ?", (fonc_name,))
      command = cur.fetchone()
      if command is None:
         return False
      permissions = command[2]
      if permissions == "None":
         return True
      elif permissions == "ownerbot":
         return False
      else:
         for i in roles_perm:
            role = discord.utils.get(interaction.guild.roles, name=i)
            if role in interaction.author.roles:
               if roles_perm.index(role.name) <= roles_perm.index(permissions):
                  return True
               else:
                  return False
         return False

async def not_perm(interaction, command_name):
   con, cur = choose_db(interaction.guild.id)
   cur.execute("SELECT perm FROM commands WHERE commande = ?", (command_name,))
   perm = cur.fetchone()[0]
   embed = discord.Embed(title="Vous n'avez pas la permission d'utiliser cette commande", color=0xff0000)
   embed.add_field(name="Commande", value=f"{command_name}", inline=False)
   embed.add_field(name="Permissions requises", value=f"{perm}", inline=False)
   try:
      await interaction.response.send_message(embed=embed)
   except:
      await interaction.send(embed=embed)
      


def active_commande(command_name):
   active_guilds = []

   db_folder = "db"
   db_files = [f for f in os.listdir(db_folder) if os.path.isfile(os.path.join(db_folder, f)) and f.endswith(".db")]

   for db_file in db_files:
      guild_id = os.path.splitext(db_file)[0]  # Extract ID from the filename without extension

      con, cur = choose_db(guild_id)
      cur.execute("SELECT active FROM commands WHERE commande = ?", (command_name,))
      active_status = cur.fetchone()

      if active_status and active_status[0] == 1:
         active_guilds.append(discord.Object(id=int(guild_id)))
   return active_guilds


def active_basic_commande(ctx, command_name):
   con, cur = choose_db(ctx.guild.id)
   cur.execute("SELECT active FROM commands WHERE commande = ?", (command_name,))
   active_status = cur.fetchone()
   if active_status and active_status[0] == 1:
      return True
   else:
      return False



@bot.tree.command(guilds=active_commande("sync"), name="sync", description="Synchronise les commandes du bot")
async def sync(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   await interaction.response.send_message("Synchronisation des commandes en cours...")
   try:
      await bot.tree.sync(guild=interaction.guild)
      await interaction.channel.send(f"Synced commands for guild {interaction.guild.name}")
   except Exception as e:
      await interaction.channel.send(f"Error syncing commands for guild {interaction.guild.name}: {e}")



@bot.command()
async def sync(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   await ctx.send("Synchronisation des commandes en cours...")
   try:
      await bot.tree.sync(guild=ctx.guild)
      await ctx.send(f"Synced commands for guild {ctx.guild.name}")
   except Exception as e:
      await ctx.send(f"Error syncing commands for guild {ctx.guild.name}: {e}")



@bot.tree.command(guilds=active_commande("say"), name="say", description="Permets de faire parler le bot")
async def say(interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if channel is not None:
      send_channel = channel
      res = f"Message envoyé dans {send_channel.mention}"
   else:
      send_channel = interaction.channel
      res = "Message envoyé"
   await send_channel.send(message)
   await interaction.response.send_message(res, ephemeral=True)


@bot.command()
async def say(ctx, *, message=None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if message == None:
      await ctx.send('Vous devez spécifier un message')
   else:
      await ctx.send(message)



@bot.tree.command(guilds=active_commande("ban"), name="ban", description="Permets de bannir un membre")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = None, delete_message_days: int = 0):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   await member.ban(reason=reason, delete_message_days=delete_message_days)
   await interaction.response.send_message(f"{member.mention} a été banni")


@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   await member.ban(reason=reason)
   await ctx.send(f"{member.mention} a été banni")



@bot.tree.command(guilds=active_commande("kick"), name="kick", description="Permets de kick un membre")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   await member.kick(reason=reason)
   await interaction.response.send_message(f"{member.mention} a été kick", ephemeral=True)


@bot.command()
async def kick(ctx, member: discord.Member, *, reason=None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   await member.kick(reason=reason)
   await ctx.send(f"{member.mention} a été kick")



@bot.tree.command(guilds=active_commande("bantemp"), name="bantemp", description="Bannir temporairement un membre.")
@app_commands.describe(member="Quel membre ou utilisateur voulez-vous bannir temporairement ?",
                       temp="Combien de temps voulez-vous le bannir ?",
                       echelle="Quelle échelle de temps voulez-vous utiliser ?",
                       reason="Pour quelle raison voulez-vous le bannir ?",
                       delete_message_days="Combien de jours de messages voulez-vous supprimer ?")
@app_commands.rename(delete_message_days="messages_à_supprimer",
                     echelle="échelle_de_temps")
async def bantemp(interaction: discord.Interaction, member: discord.Member, temp: int, echelle: Literal["secondes", "minutes", "heures", "jours"] = "minutes", reason: str = None, delete_message_days: int = 0):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   reason = f"{interaction.user.name} : {reason} | durée : {temp} {echelle}"
   time = 0
   if echelle == "secondes":
      time = temp
   elif echelle == "minutes":
      time = temp * 60
   elif echelle == "heures":
      time = temp * 3600
   elif echelle == "jours":
      time = temp * 86400
   else:
      await interaction.response.send_message("Le temps n'est pas valide", ephemeral=True)
      return
   await member.ban(reason=reason, delete_message_days=delete_message_days)
   embed = discord.Embed(title="Membre banni temporairement", color=0xff0000)
   embed.add_field(name="Membre", value=member.mention, inline=False)
   embed.add_field(name="Temps", value=f"{temp} {echelle}", inline=False)
   embed.add_field(name="Raison", value=reason, inline=False)
   embed.add_field(name="Messages supprimés", value=delete_message_days, inline=False)
   embed.add_field(name="Modérateur", value=interaction.user.mention, inline=False)
   embed.add_field(name="Date", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=False)
   await interaction.response.send_message(embed=embed)
   await asyncio.sleep(time)
   try:
      await member.unban(reason="Fin du ban temporaire")
   except:
      pass



@bot.command()
async def bantemp(ctx, member: discord.Member, time: str, *, reason=None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   reason = f"{ctx.author.name} : {reason} | durée : {time} seconds"
   if time[-1] == "s":
      time = int(time[:-1])
   elif time[-1] == "m":
      time = int(time[:-1]) * 60
   elif time[-1] == "h":
      time = int(time[:-1]) * 3600
   elif time[-1] == "d":
      time = int(time[:-1]) * 86400
   else:
      await ctx.send("Le temps n'est pas valide")
      return
   await member.ban(reason=reason)
   embed = discord.Embed(title="Membre banni temporairement", color=0xff0000)
   embed.add_field(name="Membre", value=member.mention, inline=False)
   embed.add_field(name="Temps", value=f"{time} secondes", inline=False)
   embed.add_field(name="Raison", value=reason, inline=False)
   embed.add_field(name="Modérateur", value=ctx.author.mention, inline=False)
   embed.add_field(name="Date", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=False)
   await ctx.send(embed=embed)
   await asyncio.sleep(time)
   try:
      await member.unban(reason="Fin du ban temporaire")
   except:
      pass



@bot.tree.command(guilds=active_commande("clear"), name="clear", description="Permet de supprimer des messages")
@app_commands.describe(number="Combien de messages voulez-vous supprimer ?")
@app_commands.rename(number="nombre_de_messages")
async def clear(interaction: discord.Interaction, number: int):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   await interaction.response.send_message(f"{number} messages vont être supprimés", ephemeral=True)
   await interaction.channel.purge(limit=number)


@bot.command()
async def clear(ctx, number: int):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   await ctx.channel.purge(limit=number)



@bot.tree.command(guilds=active_commande("mute"), name="mute", description="Permet de mute un membre")
@app_commands.describe(member="Quel membre ou utilisateur voulez-vous mute ?",
                       reason="Pour quelle raison voulez-vous le mute ?")
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("ROLE_MUTE_ID",))
   role_mute_id = cur.fetchone()[1]
   try:
      role_mute = discord.utils.get(interaction.guild.roles, id=int(role_mute_id))
      if member.roles.__contains__(role_mute):
         await interaction.response.send_message(f"{member.mention} est déjà mute")
         return
      await member.add_roles(role_mute, reason=reason)
      await interaction.response.send_message(f"{member.mention} a été mute")
   except:
      await interaction.response.send_message(f"{member.mention} n'a pas été mute car le rôle mute n'existe pas. Vous devez le créer et le mettre dans la config du bot en faisant `/config ROLE_MUTE_ID <id du rôle>`")



@bot.command()
async def mute(ctx, member: discord.Member, *, reason=None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("ROLE_MUTE_ID",))
   role_mute_id = cur.fetchone()[1]
   try:
      role_mute = discord.utils.get(ctx.guild.roles, id=int(role_mute_id))
      if member.roles.__contains__(role_mute):
         await ctx.send(f"{member.mention} est déjà mute")
         return
      await member.add_roles(role_mute, reason=reason)
      await ctx.send(f"{member.mention} a été mute")
   except:
      await ctx.channel.send(f"{member.mention} n'a pas été mute car le rôle mute n'existe pas. Vous devez le créer et le mettre dans la config du bot en faisant `/config ROLE_MUTE_ID <id du rôle>`")



@bot.tree.command(guilds=active_commande("unmute"), name="unmute", description="Permet de unmute un membre")
@app_commands.describe(member="Quel membre ou utilisateur voulez-vous unmute ?",
                       reason="Pour quelle raison voulez-vous le unmute ?")
async def unmute(interaction: discord.Interaction, member: discord.Member, reason: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("ROLE_MUTE_ID",))
   role_mute_id = cur.fetchone()[1]
   try:
      role_mute = discord.utils.get(interaction.guild.roles, id=int(role_mute_id))
      if not member.roles.__contains__(role_mute):
         await interaction.response.send_message(f"{member.mention} n'était pas mute")
         return
      await member.remove_roles(role_mute, reason=reason)
      await interaction.response.send_message(f"{member.mention} a été unmute")
   except:
      await interaction.response.send_message(f"{member.mention} n'a pas été unmute car le rôle mute n'existe pas. Vous devez le créer et le mettre dans la config du bot en faisant `/config ROLE_MUTE_ID <id du rôle>`")



@bot.command()
async def unmute(ctx, member: discord.Member, *, reason=None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("ROLE_MUTE_ID",))
   role_mute_id = cur.fetchone()[1]
   try:
      role_mute = discord.utils.get(ctx.guild.roles, id=int(role_mute_id))
      if not member.roles.__contains__(role_mute):
         await ctx.send(f"{member.mention} n'était pas mute")
         return
      await member.remove_roles(role_mute, reason=reason)
      await ctx.send(f"{member.mention} a été unmute")
   except:
      await ctx.channel.send(f"{member.mention} n'a pas été unmute car le rôle mute n'existe pas. Vous devez le créer et le mettre dans la config du bot en faisant `/config ROLE_MUTE_ID <id du rôle>`")



@bot.tree.command(guilds=active_commande("addrole"), name="addrole", description="Permet d'ajouter un rôle à un membre")
@app_commands.describe(member="Quel membre ou utilisateur voulez-vous ajouter un rôle ?",
                       role="Quel rôle voulez-vous ajouter ?",
                       reason="Pour quelle raison voulez-vous ajouter ce rôle ?")
@app_commands.rename(role="rôle")
async def addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role, reason: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   if interaction.user.top_role < role and interaction.user.id != 671763971803447298:
      await interaction.response.send_message("Vous ne pouvez pas ajouter ce rôle car il est supérieur à votre rôle le plus haut", ephemeral=True)
      return
   if member.roles.__contains__(role):
      await interaction.response.send_message(f"{member.mention} a déjà le rôle {role.mention}")
      return
   await member.add_roles(role, reason=reason)
   await interaction.response.send_message(f"{member.mention} a reçu le rôle {role.mention}")


@bot.command()
async def addrole(ctx, member: discord.Member, role: discord.Role, *, reason=None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   if ctx.author.top_role < role and ctx.author.id != 671763971803447298:
      await ctx.send("Vous ne pouvez pas ajouter ce rôle car il est supérieur à votre rôle le plus haut")
      return
   if member.roles.__contains__(role):
      await ctx.send(f"{member.mention} a déjà le rôle {role.mention}")
      return
   await member.add_roles(role, reason=reason)
   await ctx.send(f"{member.mention} a reçu le rôle {role.mention}")



@bot.tree.command(guilds=active_commande("removerole"), name="removerole", description="Permet de retirer un rôle à un membre")
@app_commands.describe(member="Quel membre ou utilisateur voulez-vous retirer un rôle ?",
                       role="Quel rôle voulez-vous retirer ?",
                       reason="Pour quelle raison voulez-vous retirer ce rôle ?")
@app_commands.rename(role="rôle")
async def removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role, reason: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   if interaction.user.top_role < role and interaction.user.id != 671763971803447298:
      await interaction.response.send_message("Vous ne pouvez pas retirer ce rôle car il est supérieur à votre rôle le plus haut", ephemeral=True)
      return
   if not member.roles.__contains__(role):
      await interaction.response.send_message(f"{member.mention} n'a pas le rôle {role.mention}")
      return
   await member.remove_roles(role, reason=reason)
   await interaction.response.send_message(f"{member.mention} a perdu le rôle {role.mention}")


@bot.command()
async def removerole(ctx, member: discord.Member, role: discord.Role, *, reason=None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   if ctx.author.top_role < role and ctx.author.id != 671763971803447298:
      await ctx.send("Vous ne pouvez pas retirer ce rôle car il est supérieur à votre rôle le plus haut")
      return
   if not member.roles.__contains__(role):
      await ctx.send(f"{member.mention} n'a pas le rôle {role.mention}")
      return
   await member.remove_roles(role, reason=reason)
   await ctx.send(f"{member.mention} a perdu le rôle {role.mention}")



@bot.tree.command(guilds=active_commande("poll"), name="poll", description="Permet de créer un sondage")
async def poll(interaction: discord.Interaction, question: str, option1: str = None, option2: str = None, option3: str = None, option4: str = None, option5: str = None, option6: str = None, option7: str = None, option8: str = None, option9: str = None, option10: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   options = []
   if option1 is not None:
      options.append(option1)
   if option2 is not None:
      options.append(option2)
   if option3 is not None:
      options.append(option3)
   if option4 is not None:
      options.append(option4)
   if option5 is not None:
      options.append(option5)
   if option6 is not None:
      options.append(option6)
   if option7 is not None:
      options.append(option7)
   if option8 is not None:
      options.append(option8)
   if option9 is not None:
      options.append(option9)
   if option10 is not None:
      options.append(option10)
   if len(options) == 1:
      await interaction.response.send_message("Il faut au moins 2 options", ephemeral=True)
      return
   embed = discord.Embed(title=question, color=0x3498db)
   for i in range(len(options)):
      embed.add_field(name=f"Option {i+1}", value=options[i], inline=False)
   message = await interaction.channel.send(embed=embed)
   if len(options) == 0:
      await message.add_reaction("✅")
      await message.add_reaction("❌")
   else:
      for i in range(len(options)):
         await message.add_reaction(f"{i+1}\U000020e3")


@bot.command()
async def poll(ctx, question, *options):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if len(options) < 2 or len(options) > 10:
      await ctx.send("Veuillez fournir au moins 2 options et au maximum 10 options.")
      return
   formatted_options = [f"{chr(0x1F1E6 + i)} - {option}" for i, option in enumerate(options)]
   poll_message = f"**{question}**\n\n" + "\n".join(formatted_options)
   poll_embed = discord.Embed(title="Sondage", description=poll_message, color=0x3498db)
   poll_msg = await ctx.send(embed=poll_embed)
   for i in range(len(options)):
      await poll_msg.add_reaction(chr(0x1F1E6 + i))



@bot.tree.command(guilds=active_commande("userinfo"), name="userinfo", description="Permet d'avoir des informations sur un membre")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = interaction.user
   embed = discord.Embed(title="Informations sur le membre", color=0xff0000)
   embed.add_field(name="Membre", value=member.mention, inline=False)
   embed.add_field(name="ID", value=member.id, inline=False)
   tz_target = pytz.timezone('Europe/Paris')
   created_at_paris = member.created_at.astimezone(tz_target)
   joined_at_paris = member.joined_at.astimezone(tz_target)
   embed.add_field(name="Date de création du compte", value=created_at_paris.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
   embed.add_field(name="Date d'arrivée", value=joined_at_paris.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
   embed.add_field(name="En attente", value=member.pending, inline=False)
   embed.add_field(name="Bot", value=member.bot, inline=False)
   embed.add_field(name="Rôles", value=" ".join([role.mention for role in member.roles]), inline=False)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if member.avatar:
      embed.set_author(name=member.name, icon_url=member.avatar.url)
      embed.set_thumbnail(url=member.avatar.url)
   else:
      default_avatar_url = member.default_avatar.url
      embed.set_author(name=member.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def userinfo(ctx, member: discord.Member = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = ctx.author
   embed = discord.Embed(title="Informations sur le membre", color=0xff0000)
   embed.add_field(name="Membre", value=member.mention, inline=False)
   embed.add_field(name="ID", value=member.id, inline=False)
   tz_target = pytz.timezone('Europe/Paris')
   created_at_paris = member.created_at.astimezone(tz_target)
   joined_at_paris = member.joined_at.astimezone(tz_target)
   embed.add_field(name="Date de création du compte", value=created_at_paris.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
   embed.add_field(name="Date d'arrivée", value=joined_at_paris.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
   embed.add_field(name="En attente", value=member.pending, inline=False)
   embed.add_field(name="Bot", value=member.bot, inline=False)
   embed.add_field(name="Rôles", value=" ".join([role.mention for role in member.roles]), inline=False)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if member.avatar:
      embed.set_author(name=member.name, icon_url=member.avatar.url)
      embed.set_thumbnail(url=member.avatar.url)
   else:
      default_avatar_url = member.default_avatar.url
      embed.set_author(name=member.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("serverinfo"), name="ping", description="Permet de voir le ping du bot")
async def ping(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Ping", color=0xff0000)
   embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)}ms", inline=False)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if bot.user.avatar:
      embed.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)
      embed.set_thumbnail(url=bot.user.avatar.url)
   else:
      default_avatar_url = bot.user.default_avatar.url
      embed.set_author(name=bot.user.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def ping(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Ping", color=0xff0000)
   embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)}ms", inline=False)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if bot.user.avatar:
      embed.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)
      embed.set_thumbnail(url=bot.user.avatar.url)
   else:
      default_avatar_url = bot.user.default_avatar.url
      embed.set_author(name=bot.user.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("serverinfo"), name="serverinfo", description="Permet d'avoir des informations sur le serveur")
async def serverinfo(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Informations sur le serveur", color=0xff0000)
   embed.add_field(name="Nom", value=interaction.guild.name, inline=False)
   embed.add_field(name="ID", value=interaction.guild.id, inline=False)
   embed.add_field(name="Propriétaire", value=interaction.guild.owner.mention, inline=False)
   embed.add_field(name="Nombre de membres", value=interaction.guild.member_count, inline=False)
   embed.add_field(name="Nombre de rôles", value=len(interaction.guild.roles), inline=False)
   embed.add_field(name="Nombre de catégories", value=len(interaction.guild.categories), inline=False)
   embed.add_field(name="Nombre de salons textuels", value=len(interaction.guild.text_channels), inline=False)
   embed.add_field(name="Nombre de salons vocaux", value=len(interaction.guild.voice_channels), inline=False)
   embed.add_field(name="Nombre d'émojis", value=len(interaction.guild.emojis), inline=False)
   embed.add_field(name="Nombre de boosts", value=interaction.guild.premium_subscription_count, inline=False)
   embed.add_field(name="Niveau de boost", value=interaction.guild.premium_tier, inline=False)
   embed.add_field(name="Date de création", value=interaction.guild.created_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if interaction.guild.icon:
      embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
      embed.set_thumbnail(url=interaction.guild.icon.url)
   else:
      default_avatar_url = interaction.guild.default_avatar.url
      embed.set_author(name=interaction.guild.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def serverinfo(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Informations sur le serveur", color=0xff0000)
   embed.add_field(name="Nom", value=ctx.guild.name, inline=False)
   embed.add_field(name="ID", value=ctx.guild.id, inline=False)
   embed.add_field(name="Propriétaire", value=ctx.guild.owner.mention, inline=False)
   embed.add_field(name="Nombre de membres", value=ctx.guild.member_count, inline=False)
   embed.add_field(name="Nombre de rôles", value=len(ctx.guild.roles), inline=False)
   embed.add_field(name="Nombre de catégories", value=len(ctx.guild.categories), inline=False)
   embed.add_field(name="Nombre de salons textuels", value=len(ctx.guild.text_channels), inline=False)
   embed.add_field(name="Nombre de salons vocaux", value=len(ctx.guild.voice_channels), inline=False)
   embed.add_field(name="Nombre d'émojis", value=len(ctx.guild.emojis), inline=False)
   embed.add_field(name="Nombre de boosts", value=ctx.guild.premium_subscription_count, inline=False)
   embed.add_field(name="Niveau de boost", value=ctx.guild.premium_tier, inline=False)
   embed.add_field(name="Date de création", value=ctx.guild.created_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if ctx.guild.icon:
      embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
      embed.set_thumbnail(url=ctx.guild.icon.url)
   else:
      default_avatar_url = ctx.guild.default_avatar.url
      embed.set_author(name=ctx.guild.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("stats"), name="stats", description="Permet d'avoir des informations sur le bot")
async def stats(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Statistiques du serveur", color=0xff0000)
   embed.add_field(name="Nombre de membres", value=interaction.guild.member_count, inline=False)
   embed.add_field(name="Nombre de personnes en ligne", value=len([member for member in interaction.guild.members if member.status != discord.Status.offline]), inline=False)
   embed.add_field(name="Nombre de personnes en vocal", value=len([member for member in interaction.guild.members if member.voice != None]), inline=False)
   embed.add_field(name="Nombre de boosts", value=interaction.guild.premium_subscription_count, inline=False)
   embed.add_field(name="Niveau de boost", value=interaction.guild.premium_tier, inline=False)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if interaction.guild.icon:
      embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
      embed.set_thumbnail(url=interaction.guild.icon.url)
   else:
      default_avatar_url = interaction.guild.default_avatar.url
      embed.set_author(name=interaction.guild.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def stats(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Statistiques du serveur", color=0xff0000)
   embed.add_field(name="Nombre de membres", value=ctx.guild.member_count, inline=False)
   embed.add_field(name="Nombre de personnes en ligne", value=len([member for member in ctx.guild.members if member.status != discord.Status.offline]), inline=False)
   embed.add_field(name="Nombre de personnes en vocal", value=len([member for member in ctx.guild.members if member.voice != None]), inline=False)
   embed.add_field(name="Nombre de boosts", value=ctx.guild.premium_subscription_count, inline=False)
   embed.add_field(name="Niveau de boost", value=ctx.guild.premium_tier, inline=False)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if ctx.guild.icon:
      embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
      embed.set_thumbnail(url=ctx.guild.icon.url)
   else:
      default_avatar_url = ctx.guild.default_avatar.url
      embed.set_author(name=ctx.guild.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("memberlist"), name="memberlist", description="Permet d'avoir la liste des membres du serveur")
async def memberlist(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Liste des membres",
                        description='\n'.join([member.mention for member in interaction.guild.members]),
                        color=0xff0000)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if interaction.guild.icon:
      embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
      embed.set_thumbnail(url=interaction.guild.icon.url)
   else:
      default_avatar_url = interaction.guild.default_avatar.url
      embed.set_author(name=interaction.guild.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def memberlist(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Liste des membres",
                        description='\n'.join([member.mention for member in ctx.guild.members]),
                        color=0xff0000)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if ctx.guild.icon:
      embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
      embed.set_thumbnail(url=ctx.guild.icon.url)
   else:
      default_avatar_url = ctx.guild.default_avatar.url
      embed.set_author(name=ctx.guild.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("rolelist"), name="rolelist", description="Permet d'avoir la liste des rôles du serveur")
async def rolelist(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Liste des rôles",
                        description='\n'.join([role.mention for role in interaction.guild.roles]),
                        color=0xff0000)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if interaction.guild.icon:
      embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
      embed.set_thumbnail(url=interaction.guild.icon.url)
   else:
      default_avatar_url = interaction.guild.default_avatar.url
      embed.set_author(name=interaction.guild.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def rolelist(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Liste des rôles",
                        description='\n'.join([role.mention for role in ctx.guild.roles]),
                        color=0xff0000)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if ctx.guild.icon:
      embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
      embed.set_thumbnail(url=ctx.guild.icon.url)
   else:
      default_avatar_url = ctx.guild.default_avatar.url
      embed.set_author(name=ctx.guild.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("channellist"), name="channellist", description="Permet d'avoir la liste des channels du serveur")
async def channellist(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Liste des salons",
                        description='\n'.join([channel.mention for channel in interaction.guild.channels]),
                        color=0xff0000)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if interaction.guild.icon:
      embed.set_author(name=interaction.guild.name, icon_url=interaction.guild.icon.url)
      embed.set_thumbnail(url=interaction.guild.icon.url)
   else:
      default_avatar_url = interaction.guild.default_avatar.url
      embed.set_author(name=interaction.guild.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def channellist(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Liste des salons",
                        description='\n'.join([channel.mention for channel in ctx.guild.channels]),
                        color=0xff0000)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   if ctx.guild.icon:
      embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon.url)
      embed.set_thumbnail(url=ctx.guild.icon.url)
   else:
      default_avatar_url = ctx.guild.default_avatar.url
      embed.set_author(name=ctx.guild.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("roleinfo"), name="roleinfo", description="Permet d'avoir des informations sur un rôle")
async def roleinfo(interaction: discord.Interaction, role: discord.Role):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Informations sur le rôle", color=0xff0000)
   embed.add_field(name="Rôle", value=role.mention, inline=False)
   embed.add_field(name="ID", value=role.id, inline=False)
   embed.add_field(name="Couleur", value=role.color, inline=False)
   embed.add_field(name="Position", value=role.position, inline=False)
   embed.add_field(name="Mentionnable", value=role.mentionable, inline=False)
   embed.add_field(name="Affiché séparément", value=role.hoist, inline=False)
   embed.add_field(name="Permissions", value="\n".join([permission[0] for permission in role.permissions if permission[1]]), inline=False)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   await interaction.response.send_message(embed=embed)


@bot.command()
async def roleinfo(ctx, role: discord.Role):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Informations sur le rôle", color=0xff0000)
   embed.add_field(name="Rôle", value=role.mention, inline=False)
   embed.add_field(name="ID", value=role.id, inline=False)
   embed.add_field(name="Couleur", value=role.color, inline=False)
   embed.add_field(name="Position", value=role.position, inline=False)
   embed.add_field(name="Mentionnable", value=role.mentionable, inline=False)
   embed.add_field(name="Affiché séparément", value=role.hoist, inline=False)
   embed.add_field(name="Permissions", value="\n".join([permission[0] for permission in role.permissions if permission[1]]), inline=False)
   embed.set_footer(text=f"Le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("channelinfo"), name="channelinfo", description="Permet d'avoir des informations sur un channel")
async def channelinfo(interaction: discord.Interaction, channel: discord.TextChannel = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = interaction.channel
   embed = discord.Embed(title="Informations sur le channel", color=0xff0000)
   embed.add_field(name="Channel", value=channel.mention, inline=False)
   embed.add_field(name="ID", value=channel.id, inline=False)
   embed.add_field(name="Type", value=channel.type, inline=False)
   embed.add_field(name="Position", value=channel.position, inline=False)
   embed.add_field(name="Catégorie", value=channel.category, inline=False)
   embed.add_field(name="NSFW", value=channel.is_nsfw(), inline=False)
   embed.add_field(name="Slowmode", value=channel.slowmode_delay, inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def channelinfo(ctx, channel: discord.TextChannel = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = ctx.channel
   embed = discord.Embed(title="Informations sur le channel", color=0xff0000)
   embed.add_field(name="Channel", value=channel.mention, inline=False)
   embed.add_field(name="ID", value=channel.id, inline=False)
   embed.add_field(name="Type", value=channel.type, inline=False)
   embed.add_field(name="Position", value=channel.position, inline=False)
   embed.add_field(name="Catégorie", value=channel.category, inline=False)
   embed.add_field(name="NSFW", value=channel.is_nsfw(), inline=False)
   embed.add_field(name="Slowmode", value=channel.slowmode_delay, inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("lock"), name="lock", description="Permet de lock un channel")
async def lock(interaction: discord.Interaction, channel: discord.TextChannel = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = interaction.channel
   overwrite = channel.overwrites_for(interaction.guild.default_role)
   overwrite.send_messages = False
   await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
   await interaction.response.send_message(f"{channel.mention} a été verrouillé")


@bot.command()
async def lock(ctx, channel: discord.TextChannel = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = ctx.channel
   overwrite = channel.overwrites_for(ctx.guild.default_role)
   overwrite.send_messages = False
   await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
   await ctx.send(f"{channel.mention} a été verrouillé")



@bot.tree.command(guilds=active_commande("unlock"), name="unlock", description="Permet de unlock un channel")
async def unlock(interaction: discord.Interaction, channel: discord.TextChannel = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = interaction.channel
   overwrite = channel.overwrites_for(interaction.guild.default_role)
   overwrite.send_messages = None
   await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
   await interaction.response.send_message(f"{channel.mention} a été déverrouillé")


@bot.command()
async def unlock(ctx, channel: discord.TextChannel = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = ctx.channel
   overwrite = channel.overwrites_for(ctx.guild.default_role)
   overwrite.send_messages = None
   await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
   await ctx.send(f"{channel.mention} a été déverrouillé")



@bot.tree.command(guilds=active_commande("channelcreate"), name="channelcreate", description="Permet de créer un channel")
async def channelcreate(interaction: discord.Interaction, name: str, type: str = "text", category: discord.CategoryChannel = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if type == "text":
      await interaction.guild.create_text_channel(name, category=category)
   elif type == "voice":
      await interaction.guild.create_voice_channel(name, category=category)
   else:
      await interaction.response.send_message("Le type n'est pas valide vous devez choisir entre `text` et `voice`", ephemeral=True)
      return
   await interaction.response.send_message("Channel créé", ephemeral=True)


@bot.command()
async def channelcreate(ctx, name: str, type: str = "text", category: discord.CategoryChannel = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if type == "text":
      await ctx.guild.create_text_channel(name, category=category)
   elif type == "voice":
      await ctx.guild.create_voice_channel(name, category=category)
   else:
      await ctx.send("Le type n'est pas valide vous devez choisir entre `text` et `voice`")
      return
   await ctx.send("Channel créé")



@bot.tree.command(guilds=active_commande("channeldelete"), name="channeldelete", description="Permet de supprimer un channel")
async def channeldelete(interaction: discord.Interaction, channel: discord.TextChannel = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = interaction.channel
   await channel.delete()
   await interaction.response.send_message("Channel supprimé", ephemeral=True)


@bot.command()
async def channeldelete(ctx, channel: discord.TextChannel = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = ctx.channel
   await channel.delete()
   await ctx.send("Channel supprimé")



@bot.tree.command(guilds=active_commande("channelrename"), name="channelrename", description="Permet de renommer un channel")
async def channelrename(interaction: discord.Interaction, channel: discord.TextChannel = None, name: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = interaction.channel
   if name is None:
      await interaction.response.send_message("Vous devez donner un nom", ephemeral=True)
      return
   await channel.edit(name=name)
   await interaction.response.send_message("Channel renommé", ephemeral=True)


@bot.command()
async def channelrename(ctx, channel: discord.TextChannel = None, name: str = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = ctx.channel
   if name is None:
      await ctx.send("Vous devez donner un nom")
      return
   await channel.edit(name=name)
   await ctx.send("Channel renommé")



@bot.tree.command(guilds=active_commande("wikisearch"), name="wikisearch", description="Permet de rechercher sur wikipedia")
async def wikisearch(interaction: discord.Interaction, search: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   current_language = "fr"
   try:
      wikipedia.set_lang(current_language)
      page = wikipedia.page(search)
      content = page.content[:1000] 

      if len(page.content) > 1000:
         content += "..."

      if not content:
         content = f"Désolé, je n'ai pas trouvé de résultats pour '{search}'."

      embed = discord.Embed(title=f"Wikipedia search results for '{search}':", color=0, description=content)
      embed.set_thumbnail(url=f"https://www.wikipedia.org/static/images/project-logos/{current_language}wiki.png")
      embed.add_field(name="Read more", value=f"[{search} on Wikipedia]({page.url})", inline=False)
      await interaction.response.send_message(embed=embed)

   except Exception as error:
      error = str(error)
      await interaction.response.send_message("Une erreur est survenue", ephemeral=True)


@bot.command()
async def wikisearch(ctx, search: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   current_language = "fr"
   try:
      wikipedia.set_lang(current_language)
      page = wikipedia.page(search)
      content = page.content[:1000] 

      if len(page.content) > 1000:
         content += "..."

      if not content:
         content = f"Désolé, je n'ai pas trouvé de résultats pour '{search}'."

      embed = discord.Embed(title=f"Wikipedia search results for '{search}':", color=0, description=content)
      embed.set_thumbnail(url=f"https://www.wikipedia.org/static/images/project-logos/{current_language}wiki.png")
      embed.add_field(name="Read more", value=f"[{search} on Wikipedia]({page.url})", inline=False)
      await ctx.send(embed=embed)

   except Exception as error:
      error = str(error)
      await ctx.send("Une erreur est survenue")



@bot.tree.command(guilds=active_commande("warn"), name="warn", description="Permet de warn un membre")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   con, cur = choose_db(interaction.guild.id)
   cur.execute('''
      INSERT INTO warns (user_id, moderator_id, reason)
      VALUES (?, ?, ?)
   ''', (member.id, interaction.user.id, reason))
   con.commit()
   if not member.bot:
      await member.send(f"Vous avez été averti sur le serveur {interaction.guild.name} pour la raison suivante : {reason}")
   await interaction.response.send_message(f"{member.mention} a été averti pour la raison suivante : {reason}")
   cur.execute('SELECT * FROM warns WHERE user_id = ?', (member.id,))
   warns = cur.fetchall()
   if len(warns) >= 5:
      cur.execute('SELECT * FROM config WHERE env = ?', ("ROLE_MUTE_ID",))
      role_mute_id = cur.fetchone()[1]
      try:
         role_mute = discord.utils.get(interaction.guild.roles, id=int(role_mute_id))
         await member.add_roles(role_mute, reason="5 warns")
         await interaction.channel.send(f"{member.mention} a été mute car il a 5 warns ou plus")
      except:
         await interaction.channel.send(f"{member.mention} a été mute car il a 5 warns ou plus mais le rôle mute n'existe pas. Vous devez le créer et le mettre dans la config du bot en faisant `/config ROLE_MUTE_ID <id du rôle>`")



@bot.command()
async def warn(ctx, member: discord.Member, reason: str = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if reason is None:
      reason = "Aucune raison donnée"
   con, cur = choose_db(ctx.guild.id)
   cur.execute('''
      INSERT INTO warns (user_id, moderator_id, reason)
      VALUES (?, ?, ?)
   ''', (member.id, ctx.author.id, reason))
   con.commit()
   if not member.bot:
      await member.send(f"Vous avez été averti sur le serveur {ctx.guild.name} pour la raison suivante : {reason}")
   await ctx.send(f"{member.mention} a été averti pour la raison suivante : {reason}")
   cur.execute('SELECT * FROM warns WHERE user_id = ?', (member.id,))
   warns = cur.fetchall()
   if len(warns) >= 5:
      cur.execute('SELECT * FROM config WHERE env = ?', ("ROLE_MUTE_ID",))
      role_mute_id = cur.fetchone()[1]
      try:
         role_mute = discord.utils.get(ctx.guild.roles, id=int(role_mute_id))
         await member.add_roles(role_mute, reason="5 warns")
         await ctx.channel.send(f"{member.mention} a été mute car il a 5 warns ou plus")
      except:
         await ctx.channel.send(f"{member.mention} a été mute car il a 5 warns ou plus mais le rôle mute n'existe pas. Vous devez le créer et le mettre dans la config du bot en faisant `/config ROLE_MUTE_ID <id du rôle>`")



@bot.tree.command(guilds=active_commande("warnlist"), name="warnlist", description="Permet d'avoir la liste des warns d'un membre")
async def warnlist(interaction: discord.Interaction, member: discord.Member):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('''
      SELECT * FROM warns WHERE user_id = ?
   ''', (member.id,))
   warns = cur.fetchall()
   if warns == []:
      embed = discord.Embed(title="Aucun avertissement", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des avertissements", color=0xff0000)
      for warn in warns:
         embed.add_field(name="Avertissement", value=f"{warn[0]} : {warn[3]}", inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def warnlist(ctx, member: discord.Member):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('''
      SELECT * FROM warns WHERE user_id = ?
   ''', (member.id,))
   warns = cur.fetchall()
   if warns == []:
      embed = discord.Embed(title="Aucun avertissement", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des avertissements", color=0xff0000)
      for warn in warns:
         embed.add_field(name="Avertissement", value=f"{warn[0]} : {warn[3]}", inline=False)
   await ctx.send(embed=embed)


   
@bot.tree.command(guilds=active_commande("delwarn"), name="delwarn", description="Permet de supprimer un warn d'un membre")
async def delwarn(interaction: discord.Interaction, member: discord.Member, warn_id: int = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   if warn_id is None:
      cur.execute('''
            DELETE FROM warns WHERE user_id = ?
      ''', (member.id,))
      con.commit()
      await interaction.response.send_message(f"Tous les avertissements de {member.mention} ont été retirés")
      return
   cur.execute('''
      SELECT * FROM warns WHERE user_id = ? AND id = ?
   ''', (member.id, warn_id))
   warn = cur.fetchone()
   if warn is None:
      await interaction.response.send_message(f"L'avertissement {warn_id} n'existe pas", ephemeral=True)
      return
   cur.execute('''
         DELETE FROM warns WHERE user_id = ? AND id = ?
      ''', (member.id, warn_id))
   con.commit()
   await interaction.response.send_message(f"L'avertissement {warn_id} a été retiré à {member.mention}")


@bot.command()
async def delwarn(ctx, member: discord.Member, warn_id: int = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   if warn_id is None:
      cur.execute('''
            DELETE FROM warns WHERE user_id = ?
      ''', (member.id,))
      con.commit()
      await ctx.send(f"Tous les avertissements de {member.mention} ont été retirés")
      return
   cur.execute('''
      SELECT * FROM warns WHERE user_id = ? AND id = ?
   ''', (member.id, warn_id))
   warn = cur.fetchone()
   if warn is None:
      await ctx.send(f"L'avertissement {warn_id} n'existe pas")
      return
   cur.execute('''
         DELETE FROM warns WHERE user_id = ? AND id = ?
      ''', (member.id, warn_id))
   con.commit()
   await ctx.send(f"L'avertissement {warn_id} a été retiré à {member.mention}")




@bot.tree.command(guilds=active_commande("resetwarn"), name="resetwarn", description="Permet de supprimer tous les warns d'un membre")
async def resetwarn(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('''
      DELETE FROM warns
   ''')
   con.commit()
   await interaction.response.send_message("Tous les avertissements du serveur ont été retirés")


@bot.command()
async def resetwarn(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('''
      DELETE FROM warns
   ''')
   con.commit()
   await ctx.send("Tous les avertissements du serveur ont été retirés")



@bot.tree.command(guilds=active_commande("addbadword"), name="addbadword", description="Permet d'ajouter un badword")
async def addbadword(interaction: discord.Interaction, word: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM badwords WHERE badword = ?', (word,))
   badword = cur.fetchone()
   if badword is not None:
      await interaction.response.send_message(f"Le mot {word} est déjà dans la liste des mots interdits", ephemeral=True)
      return
   cur.execute('''
      INSERT INTO badwords (badword, utilisation, create_by_id)
      VALUES (?, ?, ?)
   ''', (word ,0 ,interaction.user.id))
   con.commit()
   await interaction.response.send_message(f"Le mot {word} a été ajouté")


@bot.command()
async def addbadword(ctx, word: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM badwords WHERE badword = ?', (word,))
   badword = cur.fetchone()
   if badword is not None:
      await ctx.send(f"Le mot {word} est déjà dans la liste des mots interdits")
      return
   cur.execute('''
      INSERT INTO badwords (badword, utilisation, create_by_id)
      VALUES (?, ?, ?)
   ''', (word ,0 ,ctx.author.id))
   con.commit()
   await ctx.send(f"Le mot {word} a été ajouté")



@bot.tree.command(guilds=active_commande("delbadword"), name="delbadword", description="Permet de supprimer un badword")
async def delbadword(interaction: discord.Interaction, word: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM badwords WHERE badword = ?', (word,))
   badword = cur.fetchone()
   if badword is None:
      await interaction.response.send_message(f"Le mot {word} n'est pas dans la liste des mots interdits", ephemeral=True)
      return
   cur.execute('''
      DELETE FROM badwords WHERE badword = ?
   ''', (word,))
   con.commit()
   await interaction.response.send_message(f"Le mot {word} a été retiré")


@bot.command()
async def delbadword(ctx, word: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM badwords WHERE badword = ?', (word,))
   badword = cur.fetchone()
   if badword is None:
      await ctx.send(f"Le mot {word} n'est pas dans la liste des mots interdits")
      return
   cur.execute('''
      DELETE FROM badwords WHERE badword = ?
   ''', (word,))
   con.commit()
   await ctx.send(f"Le mot {word} a été retiré")



@bot.tree.command(guilds=active_commande("badwordlist"), name="badwordlist", description="Permet d'avoir la liste des badwords")
async def badwordlist(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM badwords')
   badwords = cur.fetchall()
   if badwords == []:
      embed = discord.Embed(title="Aucun mot interdit", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des mots interdits", color=0xff0000)
      for badword in badwords:
         embed.add_field(name="Mot interdit", value=f"{badword[0]} : {badword[1]}", inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def badwordlist(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM badwords')
   badwords = cur.fetchall()
   if badwords == []:
      embed = discord.Embed(title="Aucun mot interdit", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des mots interdits", color=0xff0000)
      for badword in badwords:
         embed.add_field(name="Mot interdit", value=f"{badword[0]} : {badword[1]}", inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("resetbadword"), name="resetbadword", description="Permet de supprimer tous les badwords")
async def resetbadword(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('DELETE FROM badwords')
   con.commit()
   await interaction.response.send_message("Tous les mots interdits ont été retirés")


@bot.command()
async def resetbadword(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('DELETE FROM badwords')
   con.commit()
   await ctx.send("Tous les mots interdits ont été retirés")



@bot.tree.command(guilds=active_commande("badwordinfo"), name="badwordinfo", description="Permet d'avoir des informations sur un badword")
async def badwordinfo(interaction: discord.Interaction, word: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM badwords WHERE badword = ?', (word,))
   badword = cur.fetchone()
   if badword is None:
      await interaction.response.send_message(f"Le mot {word} n'est pas dans la liste des mots interdits", ephemeral=True)
      return
   embed = discord.Embed(title="Informations sur le mot interdit", color=0xff0000)
   embed.add_field(name="Mot interdit", value=badword[1], inline=False)
   embed.add_field(name="ID", value=badword[0], inline=False)
   embed.add_field(name="Utilisation", value=badword[2], inline=False)
   embed.add_field(name="Créé par", value=f"<@{badword[3]}>", inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def badwordinfo(ctx, word: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM badwords WHERE badword = ?', (word,))
   badword = cur.fetchone()
   if badword is None:
      await ctx.send(f"Le mot {word} n'est pas dans la liste des mots interdits")
      return
   embed = discord.Embed(title="Informations sur le mot interdit", color=0xff0000)
   embed.add_field(name="Mot interdit", value=badword[1], inline=False)
   embed.add_field(name="ID", value=badword[0], inline=False)
   embed.add_field(name="Utilisation", value=badword[2], inline=False)
   embed.add_field(name="Créé par", value=f"<@{badword[3]}>", inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("tempmute"), name="tempmute", description="Permet de mute temporairement un membre")
async def tempmute(interaction: discord.Interaction, member: discord.Member, time: str, reason: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if time[-1] == "s":
      duration = timedelta(seconds=int(time[:-1]))
   elif time[-1] == "m":
      duration = timedelta(minutes=int(time[:-1]))
   elif time[-1] == "h":
      duration = timedelta(hours=int(time[:-1]))
   elif time[-1] == "d":
      duration = timedelta(days=int(time[:-1]))
   else:
      await interaction.response.send_message("Le temps n'est pas valide vous devez choisir entre `s`, `m`, `h` et `d`", ephemeral=True)
      return
   await member.timeout(duration, reason=reason)
   await interaction.channel.send(f"{member.mention} a été tempmute")


@bot.command()
async def tempmute(ctx, member: discord.Member, time: str, reason: str = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if time[-1] == "s":
      duration = timedelta(seconds=int(time[:-1]))
   elif time[-1] == "m":
      duration = timedelta(minutes=int(time[:-1]))
   elif time[-1] == "h":
      duration = timedelta(hours=int(time[:-1]))
   elif time[-1] == "d":
      duration = timedelta(days=int(time[:-1]))
   else:
      await ctx.send("Le temps n'est pas valide vous devez choisir entre `s`, `m`, `h` et `d`")
      return
   await member.timeout(duration, reason=reason)
   await ctx.send(f"{member.mention} a été tempmute")



@bot.tree.command(guilds=active_commande("snipe"), name="snipe", description="Permet de voir le dernier message supprimé")
async def snipe(interaction: discord.Interaction, channel: discord.TextChannel = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel_id = interaction.channel.id
   else:
      channel_id = channel.id
   if channel_id not in sniped_messages:
      await interaction.response.send_message("Aucun message supprimé", ephemeral=True)
      return
   message = sniped_messages[channel_id]
   embed = discord.Embed(title="Dernier message supprimé", color=0xff0000)
   embed.add_field(name="Message", value=message.content, inline=False)
   embed.add_field(name="Auteur", value=message.author.mention, inline=False)
   embed.add_field(name="Channel", value=message.channel.mention, inline=False)
   embed.add_field(name="Date", value=message.created_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def snipe(ctx, channel: discord.TextChannel = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel_id = ctx.channel.id
   else:
      channel_id = channel.id
   if channel_id not in sniped_messages:
      await ctx.send("Aucun message supprimé")
      return
   message = sniped_messages[channel_id]
   embed = discord.Embed(title="Dernier message supprimé", color=0xff0000)
   embed.add_field(name="Message", value=message.content, inline=False)
   embed.add_field(name="Auteur", value=message.author.mention, inline=False)
   embed.add_field(name="Channel", value=message.channel.mention, inline=False)
   embed.add_field(name="Date", value=message.created_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("snipeall"), name="snipeall", description="Permet de voir les derniers messages supprimés")
async def snipeall(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if sniped_messages == {}:
      await interaction.response.send_message("Aucun message supprimé", ephemeral=True)
      return
   description = ""
   for channel_id in sniped_messages:
      message = sniped_messages[channel_id]
      description += f"**Message** : {message.content}\n**Auteur** : {message.author.mention}\n**Channel** : {message.channel.mention}\n**Date** : {message.created_at.strftime('%d/%m/%Y à %H:%M:%S')}\n\n"
   embed = discord.Embed(title="Derniers messages supprimés", description=description, color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def snipeall(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if sniped_messages == {}:
      await ctx.send("Aucun message supprimé")
      return
   embed = discord.Embed(title="Derniers messages supprimés", color=0xff0000)
   for channel_id in sniped_messages:
      message = sniped_messages[channel_id]
      embed.add_field(name="Message", value=message.content, inline=False)
      embed.add_field(name="Auteur", value=message.author.mention, inline=False)
      embed.add_field(name="Channel", value=message.channel.mention, inline=False)
      embed.add_field(name="Date", value=message.created_at.strftime("%d/%m/%Y à %H:%M:%S"), inline=False)
      embed.add_field(name="---", value=" ", inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("botstatut"), name="botstatut", description="Permet de changer le statut du bot")
async def botstatut(interaction: discord.Interaction, statut: str, type: str = "playing"):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if type == "playing":
      await bot.change_presence(activity=discord.Game(name=statut))
   elif type == "listening":
      await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=statut))
   elif type == "watching":
      await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=statut))
   elif type == "streaming":
      await bot.change_presence(activity=discord.Streaming(name=statut, url="https://www.twitch.tv/tuturp33"))
   else:
      await interaction.response.send_message("Le type n'est pas valide vous devez choisir entre `playing`, `listening`, `watching` et `streaming`", ephemeral=True)
      return
   await interaction.response.send_message("Statut changé", ephemeral=True)


@bot.command()
async def botstatut(ctx, statut: str, type: str = "playing"):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if type == "playing":
      await bot.change_presence(activity=discord.Game(name=statut))
   elif type == "listening":
      await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=statut))
   elif type == "watching":
      await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=statut))
   elif type == "streaming":
      await bot.change_presence(activity=discord.Streaming(name=statut, url="https://www.twitch.tv/tuturp33"))
   else:
      await ctx.send("Le type n'est pas valide vous devez choisir entre `playing`, `listening`, `watching` et `streaming`")
      return
   await ctx.send("Statut changé")



@bot.tree.command(guilds=active_commande("avatar"), name="avatar", description="Permet d'avoir l'avatar d'un membre")
async def avatar(interaction: discord.Interaction, member: discord.Member = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = interaction.user
   if member.avatar:
      avatar = member.avatar.url
   else:
      avatar = member.default_avatar.url
   embed = discord.Embed(title="Avatar", color=0xff0000)
   embed.set_image(url=avatar)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def avatar(ctx, member: discord.Member = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = ctx.author
   if member.avatar:
      avatar = member.avatar.url
   else:
      avatar = member.default_avatar.url
   embed = discord.Embed(title="Avatar", color=0xff0000)
   embed.set_image(url=avatar)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("addemoji"), name="addemoji", description="Permet d'ajouter un emoji")
async def addemoji(interaction: discord.Interaction, name: str, url: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
         if response.status != 200:
               await interaction.response.send_message("Impossible de récupérer l'image", ephemeral=True)
               return
         image_data = await response.read()
   try:
      await interaction.guild.create_custom_emoji(name=name, image=image_data)
      await interaction.response.send_message("Emoji ajouté")
   except discord.HTTPException:
      await interaction.response.send_message("Une erreur s'est produite lors de l'ajout de l'emoji", ephemeral=True)


@bot.command()
async def addemoji(ctx, name: str, url: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   async with aiohttp.ClientSession() as session:
      async with session.get(url) as response:
         if response.status != 200:
               await ctx.send("Impossible de récupérer l'image")
               return
         image_data = await response.read()
   try:
      await ctx.guild.create_custom_emoji(name=name, image=image_data)
      await ctx.send("Emoji ajouté")
   except discord.HTTPException:
      await ctx.send("Une erreur s'est produite lors de l'ajout de l'emoji")



@bot.tree.command(guilds=active_commande("wladd"), name="wladd", description="Permet d'ajouter un membre à la whitelist")
async def wladd(interaction: discord.Interaction, member: discord.Member):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM whitelist WHERE user_id = ?', (member.id,))
   whitelisted = cur.fetchone()
   if whitelisted is not None:
      await interaction.response.send_message(f"{member.mention} est déjà dans la whitelist", ephemeral=True)
      return
   cur.execute('''
      INSERT INTO whitelist (user_id, moderator_id)
      VALUES (?, ?)
   ''', (member.id, interaction.user.id))
   con.commit()
   await interaction.response.send_message(f"{member.mention} a été ajouté à la whitelist")


@bot.command()
async def wladd(ctx, member: discord.Member):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM whitelist WHERE user_id = ?', (member.id,))
   whitelisted = cur.fetchone()
   if whitelisted is not None:
      await ctx.send(f"{member.mention} est déjà dans la whitelist")
      return
   cur.execute('''
      INSERT INTO whitelist (user_id, moderator_id)
      VALUES (?, ?)
   ''', (member.id, ctx.author.id))
   con.commit()
   await ctx.send(f"{member.mention} a été ajouté à la whitelist")



@bot.tree.command(guilds=active_commande("wldel"), name="wldel", description="Permet de supprimer un membre de la whitelist")
async def wldel(interaction: discord.Interaction, member: discord.Member):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM whitelist WHERE user_id = ?', (member.id,))
   whitelisted = cur.fetchone()
   if whitelisted is None:
      await interaction.response.send_message(f"{member.mention} n'est pas dans la whitelist", ephemeral=True)
      return
   cur.execute('''
      DELETE FROM whitelist WHERE user_id = ?
   ''', (member.id,))
   con.commit()
   await interaction.response.send_message(f"{member.mention} a été retiré de la whitelist")


@bot.command()
async def wldel(ctx, member: discord.Member):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM whitelist WHERE user_id = ?', (member.id,))
   whitelisted = cur.fetchone()
   if whitelisted is None:
      await ctx.send(f"{member.mention} n'est pas dans la whitelist")
      return
   cur.execute('''
      DELETE FROM whitelist WHERE user_id = ?
   ''', (member.id,))
   con.commit()
   await ctx.send(f"{member.mention} a été retiré de la whitelist")



@bot.tree.command(guilds=active_commande("wl"), name="wl", description="Permet d'avoir la liste des membres de la whitelist")
async def wl(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM whitelist')
   whitelisted = cur.fetchall()
   if whitelisted == []:
      embed = discord.Embed(title="Aucun membre dans la whitelist", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des membres de la whitelist", description='\n'.join([f"<@{member[1]}>" for member in whitelisted]), color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def wl(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM whitelist')
   whitelisted = cur.fetchall()
   if whitelisted == []:
      embed = discord.Embed(title="Aucun membre dans la whitelist", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des membres de la whitelist", description='\n'.join([f"<@{member[1]}>" for member in whitelisted]), color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("wlreset"), name="wlreset", description="Permet de supprimer tous les membres de la whitelist")
async def wlreset(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('DELETE FROM whitelist')
   con.commit()
   await interaction.response.send_message("Tous les membres de la whitelist ont été retirés")


@bot.command()
async def wlreset(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('DELETE FROM whitelist')
   con.commit()
   await ctx.send("Tous les membres de la whitelist ont été retirés")



@bot.tree.command(guilds=active_commande("wlinfo"), name="wlinfo", description="Permet d'avoir des informations sur un membre de la whitelist")
async def wlinfo(interaction: discord.Interaction, member: discord.Member):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM whitelist WHERE user_id = ?', (member.id,))
   whitelisted = cur.fetchone()
   if whitelisted is None:
      await interaction.response.send_message(f"{member.mention} n'est pas dans la whitelist", ephemeral=True)
      return
   embed = discord.Embed(title="Informations sur le membre de la whitelist", color=0xff0000)
   embed.add_field(name="Membre", value=f"<@{whitelisted[1]}>", inline=False)
   embed.add_field(name="ID", value=whitelisted[0], inline=False)
   embed.add_field(name="Ajouté par", value=f"<@{whitelisted[2]}>", inline=False)
   embed.add_field(name="Date d'ajout", value=whitelisted[3], inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def wlinfo(ctx, member: discord.Member):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM whitelist WHERE user_id = ?', (member.id,))
   whitelisted = cur.fetchone()
   if whitelisted is None:
      await ctx.send(f"{member.mention} n'est pas dans la whitelist")
      return
   embed = discord.Embed(title="Informations sur le membre de la whitelist", color=0xff0000)
   embed.add_field(name="Membre", value=f"<@{whitelisted[1]}>", inline=False)
   embed.add_field(name="ID", value=whitelisted[0], inline=False)
   embed.add_field(name="Ajouté par", value=f"<@{whitelisted[2]}>", inline=False)
   embed.add_field(name="Date d'ajout", value=whitelisted[3], inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("bladd"), name="bladd", description="Permet d'ajouter un membre à la blacklist")
async def bladd(interaction: discord.Interaction, member: discord.Member = None, user_id: str = None, reason: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if member is None and user_id is None:
      await interaction.response.send_message("Vous devez mentionner un membre ou donner son ID")
      return
   if member is not None:
      member = member
   else:
      member = await bot.fetch_user(int(user_id))
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM blacklist WHERE user_id = ?', (member.id,))
   blacklisted = cur.fetchone()
   if blacklisted is not None:
      await interaction.response.send_message(f"{member.mention} est déjà dans la blacklist")
      return
   cur.execute('''
      INSERT INTO blacklist (user_id, moderator_id, reason)
      VALUES (?, ?, ?)
   ''', (member.id, interaction.user.id, reason))
   con.commit()
   await interaction.response.send_message(f"{member.mention} a été ajouté à la blacklist")
   await member.ban(reason=reason)


@bot.command()
async def bladd(ctx, member: discord.Member, reason: str = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM blacklist WHERE user_id = ?', (member.id,))
   blacklisted = cur.fetchone()
   if blacklisted is not None:
      await ctx.send(f"{member.mention} est déjà dans la blacklist")
      return
   cur.execute('''
      INSERT INTO blacklist (user_id, moderator_id, reason)
      VALUES (?, ?, ?)
   ''', (member.id, ctx.author.id, reason))
   con.commit()
   await ctx.send(f"{member.mention} a été ajouté à la blacklist")
   await member.ban(reason=reason)



@bot.tree.command(guilds=active_commande("bldel"), name="bldel", description="Permet de supprimer un membre de la blacklist")
async def bldel(interaction: discord.Interaction, member: discord.Member = None, user_id:str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if member is None and user_id is None:
      await interaction.response.send_message("Vous devez mentionner un membre ou donner son ID")
      return
   if member is not None:
      member = member
   else:
      member = await bot.fetch_user(int(user_id))
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM blacklist WHERE user_id = ?', (member.id,))
   blacklisted = cur.fetchone()
   if blacklisted is None:
      await interaction.response.send_message(f"{member.mention} n'est pas dans la blacklist")
      return
   cur.execute('''
      DELETE FROM blacklist WHERE user_id = ?
   ''', (member.id,))
   con.commit()
   await interaction.response.send_message(f"{member.mention} a été retiré de la blacklist")


@bot.command()
async def bldel(ctx, member: discord.Member):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM blacklist WHERE user_id = ?', (member.id,))
   blacklisted = cur.fetchone()
   if blacklisted is None:
      await ctx.send(f"{member.mention} n'est pas dans la blacklist")
      return
   cur.execute('''
      DELETE FROM blacklist WHERE user_id = ?
   ''', (member.id,))
   con.commit()
   await ctx.send(f"{member.mention} a été retiré de la blacklist")



@bot.tree.command(guilds=active_commande("bl"), name="bl", description="Permet d'avoir la liste des membres de la blacklist")
async def bl(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM blacklist')
   blacklisted = cur.fetchall()
   if blacklisted == []:
      embed = discord.Embed(title="Aucun membre dans la blacklist", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des membres de la blacklist", description='\n'.join([f"<@{member[1]}> : {member[3]}" for member in blacklisted]), color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def bl(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM blacklist')
   blacklisted = cur.fetchall()
   if blacklisted == []:
      embed = discord.Embed(title="Aucun membre dans la blacklist", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des membres de la blacklist", description='\n'.join([f"<@{member[1]}> : {member[3]}" for member in blacklisted]), color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("blreset"), name="blreset", description="Permet de supprimer tous les membres de la blacklist")
async def blreset(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('DELETE FROM blacklist')
   con.commit()
   await interaction.response.send_message("Tous les membres de la blacklist ont été retirés")


@bot.command()
async def blreset(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('DELETE FROM blacklist')
   con.commit()
   await ctx.send("Tous les membres de la blacklist ont été retirés")



@bot.tree.command(guilds=active_commande("blinfo"), name="blinfo", description="Permet d'avoir des informations sur un membre de la blacklist")
async def blinfo(interaction: discord.Interaction, member: discord.Member):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM blacklist WHERE user_id = ?', (member.id,))
   blacklisted = cur.fetchone()
   if blacklisted is None:
      await interaction.response.send_message(f"{member.mention} n'est pas dans la blacklist", ephemeral=True)
      return
   embed = discord.Embed(title="Informations sur le membre de la blacklist", color=0xff0000)
   embed.add_field(name="Membre", value=f"<@{blacklisted[1]}>", inline=False)
   embed.add_field(name="ID", value=blacklisted[0], inline=False)
   embed.add_field(name="Ajouté par", value=f"<@{blacklisted[2]}>", inline=False)
   embed.add_field(name="Date d'ajout", value=blacklisted[4], inline=False)
   embed.add_field(name="Raison", value=blacklisted[3], inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def blinfo(ctx, member: discord.Member):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM blacklist WHERE user_id = ?', (member.id,))
   blacklisted = cur.fetchone()
   if blacklisted is None:
      await ctx.send(f"{member.mention} n'est pas dans la blacklist")
      return
   embed = discord.Embed(title="Informations sur le membre de la blacklist", color=0xff0000)
   embed.add_field(name="Membre", value=f"<@{blacklisted[1]}>", inline=False)
   embed.add_field(name="ID", value=blacklisted[0], inline=False)
   embed.add_field(name="Ajouté par", value=f"<@{blacklisted[2]}>", inline=False)
   embed.add_field(name="Date d'ajout", value=blacklisted[4], inline=False)
   embed.add_field(name="Raison", value=blacklisted[3], inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("calc"), name="calc", description="Permet de faire un calcul")
async def calc(interaction: discord.Interaction, calcul: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Calculatrice", color=0xff0000)
   try:
      result = eval(calcul)
      embed.add_field(name="Calcul", value=calcul, inline=False)
      embed.add_field(name="Résultat", value=result, inline=False)
   except Exception as error:
      embed.add_field(name="Erreur", value=error, inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def calc(ctx, calcul: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   try:
      result = eval(calcul)
      await ctx.send(f"Le résultat est : {result}")
   except Exception as error:
      await ctx.send("Une erreur est survenue")



giveaways = {}
@bot.tree.command(guilds=active_commande("giveaway"), name="giveaway", description="Permet de créer un giveaway")
async def giveaway(interaction: discord.Interaction, time: str, winners: int, prize: str, channel: discord.TextChannel = None, description: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = interaction.channel
   if time[-1] == "s":
      duration = timedelta(seconds=int(time[:-1]))
   elif time[-1] == "m":
      duration = timedelta(minutes=int(time[:-1]))
   elif time[-1] == "h":
      duration = timedelta(hours=int(time[:-1]))
   elif time[-1] == "d":
      duration = timedelta(days=int(time[:-1]))
   else:
      await interaction.response.send_message("Le temps n'est pas valide vous devez choisir entre `s`, `m`, `h` et `d`", ephemeral=True)
      return
   embed = discord.Embed(title="Giveaway", description=description, color=0xff0000)
   embed.add_field(name="Prix", value=prize, inline=False)
   embed.add_field(name="Durée", value=f"<t:{round(datetime.now().timestamp() + duration.total_seconds() + 1)}:R>", inline=False)
   embed.add_field(name="Gagnants", value=winners, inline=False)
   embed.add_field(name="Créé par", value=interaction.user.mention, inline=False)
   embed.add_field(name="Channel", value=channel.mention, inline=False)
   embed.set_footer(text="Giveaway")
   message = await channel.send(embed=embed)
   await message.add_reaction("🎉")
   await interaction.response.send_message("Giveaway créé", ephemeral=True)
   await asyncio.sleep(duration.total_seconds())
   message = await channel.fetch_message(message.id)
   users = []
   async for user in message.reactions[0].users():
      users.append(user)
   users.remove(bot.user)
   if len(users) < winners:
      winners = len(users)
      if winners == 0:
         embed = discord.Embed(title="Giveaway terminé", description=description, color=0xff0000)
         embed.add_field(name="Bravo !", value=f"Aucun gagnant", inline=False)
         embed.add_field(name="Gagnants", value="Aucun", inline=False)
         embed.add_field(name="Créé par", value=interaction.user.mention, inline=False)
         embed.set_footer(text="Giveaway")
         await message.edit(embed=embed, content="Aucun gagnant")
         return
   winners = sample(users, winners)
   winners = [winner.mention for winner in winners]
   embed = discord.Embed(title="Giveaway terminé", description=description, color=0xff0000)
   embed.add_field(name="Bravo !", value=f"Félicitations à {', '.join(winners)} qui gagne **{prize}**", inline=False)
   embed.add_field(name="Gagnants", value='\n'.join(winners), inline=False)
   embed.add_field(name="Créé par", value=interaction.user.mention, inline=False)
   embed.set_footer(text="Giveaway")
   giveaways[message] = [winners, users,prize , interaction.user.mention]
   await message.edit(embed=embed, content='\n'.join(winners))


@bot.command()
async def giveaway(ctx, time: str, winners: int, prize: str, channel: discord.TextChannel = None, description: str = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = ctx.channel
   if time[-1] == "s":
      duration = timedelta(seconds=int(time[:-1]))
   elif time[-1] == "m":
      duration = timedelta(minutes=int(time[:-1]))
   elif time[-1] == "h":
      duration = timedelta(hours=int(time[:-1]))
   elif time[-1] == "d":
      duration = timedelta(days=int(time[:-1]))
   else:
      await ctx.send("Le temps n'est pas valide vous devez choisir entre `s`, `m`, `h` et `d`")
      return
   embed = discord.Embed(title="Giveaway", description=description, color=0xff0000)
   embed.add_field(name="Prix", value=prize, inline=False)
   embed.add_field(name="Durée", value=f"<t:{round(datetime.now().timestamp() + duration.total_seconds() + 1)}:R>", inline=False)
   embed.add_field(name="Gagnants", value=winners, inline=False)
   embed.add_field(name="Créé par", value=ctx.author.mention, inline=False)
   embed.add_field(name="Channel", value=channel.mention, inline=False)
   embed.set_footer(text="Giveaway")
   message = await channel.send(embed=embed)
   await message.add_reaction("🎉")
   await ctx.send("Giveaway créé")
   await asyncio.sleep(duration.total_seconds())
   message = await channel.fetch_message(message.id)
   users = []
   async for user in message.reactions[0].users():
      users.append(user)
   users.remove(bot.user)
   if len(users) < winners:
      winners = len(users)
      if winners == 0:
         embed = discord.Embed(title="Giveaway terminé", description=description, color=0xff0000)
         embed.add_field(name="Bravo !", value=f"Aucun gagnant", inline=False)
         embed.add_field(name="Gagnants", value="Aucun", inline=False)
         embed.add_field(name="Créé par", value=ctx.author.mention, inline=False)
         embed.set_footer(text="Giveaway")
         await message.edit(embed=embed, content="Aucun gagnant")
         return
   winners = sample(users, winners)
   winners = [winner.mention for winner in winners]
   embed = discord.Embed(title="Giveaway terminé", description=description, color=0xff0000)
   embed.add_field(name="Bravo !", value=f"Félicitations à {', '.join(winners)} qui gagne **{prize}**", inline=False)
   embed.add_field(name="Gagnants", value='\n'.join(winners), inline=False)
   embed.add_field(name="Créé par", value=ctx.author.mention, inline=False)
   embed.set_footer(text="Giveaway")
   giveaways[message] = [winners, users,prize , ctx.author.mention]
   await message.edit(embed=embed, content='\n'.join(winners))



@bot.tree.command(guilds=active_commande("reroll"), name="reroll", description="Permet de relancer un giveaway")
async def reroll(interaction: discord.Interaction, message_id: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   try:
      message_id = int(message_id)
   except ValueError:
      await interaction.response.send_message("L'ID n'est pas valide", ephemeral=True)
      return
   message = await interaction.channel.fetch_message(message_id)
   if message not in giveaways:
      await interaction.response.send_message("Le message n'est pas un giveaway", ephemeral=True)
      return
   winners, participants, prize, author = giveaways[message]
   winners = sample(participants, len(winners))
   winners = [winner.mention for winner in winners]
   embed = discord.Embed(title="Giveaway terminé", color=0xff0000)
   embed.add_field(name="Bravo !", value=f"Félicitations à {', '.join(winners)} qui gagne **{prize}**", inline=False)
   embed.add_field(name="Gagnants", value='\n'.join(winners), inline=False)
   embed.add_field(name="Créé par", value=author, inline=False)
   embed.set_footer(text="Giveaway")
   await message.edit(embed=embed, content='\n'.join(winners))
   await interaction.response.send_message("Giveaway rerollé", ephemeral=True)


@bot.command()
async def reroll(ctx, message_id: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
   try:
      message_id = int(message_id)
   except ValueError:
      await ctx.send("L'ID n'est pas valide")
      return
   message = await ctx.channel.fetch_message(message_id)
   if message not in giveaways:
      await ctx.send("Le message n'est pas un giveaway")
      return
   winners, participants, prize, author = giveaways[message]
   winners = sample(participants, len(winners))
   winners = [winner.mention for winner in winners]
   embed = discord.Embed(title="Giveaway terminé", color=0xff0000)
   embed.add_field(name="Bravo !", value=f"Félicitations à {', '.join(winners)} qui gagne **{prize}**", inline=False)
   embed.add_field(name="Gagnants", value='\n'.join(winners), inline=False)
   embed.add_field(name="Créé par", value=author, inline=False)
   embed.set_footer(text="Giveaway")
   await message.edit(embed=embed, content='\n'.join(winners))
   await ctx.send("Giveaway rerollé")



@bot.tree.command(guilds=active_commande("commandeperms"), name="commandeperms", description="Permet d'avoir les permissions d'une commande")
async def commandeperms(interaction: discord.Interaction, command: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   if command is None:
      cur.execute('SELECT * FROM commands')
      perms = cur.fetchall()
      embed = discord.Embed(title="Permissions des commandes", description='\n'.join([f"{perm[1]} : {perm[2]}" for perm in perms]), color=0xff0000)
   else:
      cur.execute('SELECT * FROM commands WHERE commande = ?', (command,))
      perm = cur.fetchone()
      if perm is None:
         await interaction.response.send_message("La commande n'existe pas", ephemeral=True)
         return
      embed = discord.Embed(title="Permissions de la commande", color=0xff0000)
      embed.add_field(name="ID", value=perm[0], inline=False)
      embed.add_field(name="Commande", value=perm[1], inline=False)
      embed.add_field(name="Permissions", value=perm[2], inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def commandeperms(ctx, command: str = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   if command is None:
      cur.execute('SELECT * FROM perms')
      perms = cur.fetchall()
      embed = discord.Embed(title="Permissions des commandes", description='\n'.join([f"{perm[1]} : {perm[2]}" for perm in perms]), color=0xff0000)
   else:
      cur.execute('SELECT * FROM perms WHERE commande = ?', (command,))
      perm = cur.fetchone()
      if perm is None:
         await ctx.send("La commande n'existe pas")
         return
      embed = discord.Embed(title="Permissions de la commande", color=0xff0000)
      embed.add_field(name="ID", value=perm[0], inline=False)
      embed.add_field(name="Commande", value=perm[1], inline=False)
      embed.add_field(name="Permissions", value=perm[2], inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("commandechangeperms"), name="commandechangeperms", description="Permet de changer les permissions d'une commande")
async def commandechangeperms(interaction: discord.Interaction, command: str, perms: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM commands WHERE commande = ?', (command,))
   perm = cur.fetchone()
   if perm is None:
      await interaction.response.send_message("La commande n'existe pas", ephemeral=True)
      return
   cur.execute('''
      UPDATE commands SET perm = ? WHERE commande = ?
   ''', (perms, command))
   con.commit()
   await interaction.response.send_message("Permissions changées", ephemeral=True)


@bot.command()
async def commandechangeperms(ctx, command: str, perms: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM perms WHERE commande = ?', (command,))
   perm = cur.fetchone()
   if perm is None:
      await ctx.send("La commande n'existe pas")
      return
   cur.execute('''
      UPDATE perms SET perm = ? WHERE commande = ?
   ''', (perms, command))
   con.commit()
   await ctx.send("Permissions changées")



@bot.tree.command(guilds=active_commande("mp"), name="mp", description="Permet d'envoyer un message privé à un membre")
async def mp(interaction: discord.Interaction, member: discord.Member, message: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   await interaction.response.defer()
   await member.send(message)
   await interaction.followup.send("Message envoyé")


@bot.command()
async def mp(ctx, member: discord.Member, message: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   await member.send(message)
   await ctx.send("Message envoyé")



@bot.tree.command(guilds=active_commande("changeactive"), name="changeactive", description="Permet de changer l'activation d'une commande")
async def changeactive(interaction: discord.Interaction, command: str, active: int = 1):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM commands WHERE commande = ?', (command,))
   perm = cur.fetchone()
   if perm is None:
      await interaction.response.send_message("La commande n'existe pas", ephemeral=True)
      return
   cur.execute('''
      UPDATE commands SET active = ? WHERE commande = ?
   ''', (active, command))
   con.commit()
   await interaction.response.send_message("Activation changée, redémarrage du bot...", ephemeral=True)
   redemarrer_script()



@bot.command()
async def changeactive(ctx, command: str, active: int = 1):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM perms WHERE commande = ?', (command,))
   perm = cur.fetchone()
   if perm is None:
      await ctx.send("La commande n'existe pas")
      return
   cur.execute('''
      UPDATE perms SET active = ? WHERE commande = ?
   ''', (active, command))
   con.commit()
   await ctx.send("Activation changée, redémarrage du bot...")
   redemarrer_script()



@bot.tree.command(guilds=active_commande("config"), name="config", description="Permet de changer la config du bot")
@app_commands.describe(config="La config à changer",
                       value="La valeur de la config à changer")
async def changeconfig(interaction: discord.Interaction, config: Literal["LOG_MESSAGE", "LOG_JOIN_LEAVE", "LOG_MODERATION", "LOG_MEMBER_UPDATE", "LOG_CHANNEL", "LOG_ROLE", "LOG_BOOST", "ROLE_MUTE_ID", "CHANNEL_JOIN", "CHANNEL_LEAVE", "ROLE_ACTIVITY", "ACTIVITY_FOR_ROLE", "ROLE_BOOST", "LOG_MP_BOT", "anti link", "anti spam"], value: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', (config,))
   conf = cur.fetchone()
   embed = discord.Embed(title="Configuration des variables d'environement du bot", color=0xff0000) 
   if conf is None:
      embed.add_field(name="Config", value="La config n'existe pas", inline=False)
      await interaction.response.send_message(embed=embed)
      return
   if value is None:
      embed.add_field(name="Config", value=f"{conf[0]} : {conf[1]}", inline=False)
      await interaction.response.send_message(embed=embed)
      return
   cur.execute('''
      UPDATE config SET id = ? WHERE env = ?
   ''', (value, config))
   con.commit()
   embed.add_field(name="Config", value=f"{config} : {conf[1]} -> {value}", inline=False)
   await interaction.response.send_message(embed=embed)



@bot.command()
async def config(ctx, config: Literal["LOG_MESSAGE", "LOG_JOIN_LEAVE", "LOG_MODERATION", "LOG_MEMBER_UPDATE", "LOG_CHANNEL", "LOG_ROLE", "LOG_BOOST", "ROLE_MUTE_ID", "CHANNEL_JOIN", "CHANNEL_LEAVE", "ROLE_ACTIVITY", "ACTIVITY_FOR_ROLE", "ROLE_BOOST", "LOG_MP_BOT", "anti link", "anti spam"], value: str = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', (config,))
   conf = cur.fetchone()
   embed = discord.Embed(title="Configuration des variables d'environement du bot", color=0xff0000) 
   if conf is None:
      embed.add_field(name="Config", value="La config n'existe pas", inline=False)
      await ctx.send(embed=embed)
      return
   if value is None:
      embed.add_field(name="Config", value=f"{conf[0]} : {conf[1]}", inline=False)
      await ctx.send(embed=embed)
      return
   cur.execute('''
      UPDATE config SET id = ? WHERE env = ?
   ''', (value, config))
   con.commit()
   embed.add_field(name="Config", value=f"{config} : {conf[1]} -> {value}", inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("configall"), name="configall", description="Permet de voir toutes les configs du bot")
async def configall(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM config')
   confs = cur.fetchall()
   embed = discord.Embed(title="Configuration des variables d'environement du bot", color=0xff0000)
   for conf in confs:
      embed.add_field(name="Config", value=f"{conf[0]} : {conf[1]}", inline=False)
   await interaction.response.send_message(embed=embed)



@bot.command()
async def configall(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM config')
   confs = cur.fetchall()
   embed = discord.Embed(title="Configuration des variables d'environement du bot", color=0xff0000)
   for conf in confs:
      embed.add_field(name="Config", value=f"{conf[0]} : {conf[1]}", inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("setbotavatar"), name="setbotavatar", description="Permet de changer l'avatar du bot")
async def setbotavatar(interaction: discord.Interaction, url: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
   await interaction.response.defer()
   async with aiohttp.ClientSession() as session:
      try:
         async with session.get(url) as resp:
            if resp.status == 200:
               await bot.user.edit(avatar=await resp.read())
               await interaction.followup.send("Avatar changé")
            else:
               await interaction.followup.send("L'url n'est pas valide")
      except:
         await interaction.followup.send("L'url n'est pas valide")


      
@bot.command()
async def setbotavatar(ctx, url: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
   async with aiohttp.ClientSession() as session:
      try:
         async with session.get(url) as resp:
            if resp.status == 200:
               await bot.user.edit(avatar=await resp.read())
               await ctx.send("Avatar changé")
            else:
               await ctx.send("L'url n'est pas valide")
      except:
         await ctx.send("L'url n'est pas valide")



@bot.tree.command(guilds=active_commande("help"), name="help", description="Permet d'avoir la liste des commandes")
@app_commands.describe(command="Entrez le nom de la commande pour avoir plus d'informations dessus")
@app_commands.rename(command="le_nom_de_la_commande")
async def help(interaction: discord.Interaction, command: str = None, page: int = 1):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM commands')
   commandes = cur.fetchall()
   actives = [cmd for cmd in commandes if cmd[4] == 1]
   commands_info_list = [f"{cmd[1]} - {commands_info[cmd[1]][3]}" for cmd in actives]
   commands_per_page = 20
   if command is not None:
      cur.execute('SELECT * FROM commands WHERE commande = ?', (command,))
      commande = cur.fetchone()
      if commande is None:
         await interaction.response.send_message("La commande n'existe pas")
         return
      if commande[4] == 0:
         await interaction.response.send_message("La commande n'est pas activée")
         return
      embed = discord.Embed(title=f"Informations sur la commande {commande[1]} :", color=0xff0000)
      embed.add_field(name="ID", value=commande[0], inline=False)
      embed.add_field(name="Commande", value=commande[1], inline=False)
      embed.add_field(name="Permissions", value=commande[2], inline=False)
      embed.add_field(name="Utilisation", value=f"/{commande[1]} {commande[3]}\n?{commande[1]} {commande[3]}", inline=False)
      embed.add_field(name="Description", value=commands_info[commande[1]][3], inline=False)
      await interaction.response.send_message(embed=embed)
      return
   total_pages = (len(commands_info_list) + commands_per_page - 1) // commands_per_page
   if page < 1 or page > total_pages:
      await interaction.response.send_message("Page invalide", ephemeral=True)
      return
   start_index = (page - 1) * commands_per_page
   end_index = start_index + commands_per_page
   embed = discord.Embed(title=f"Liste des commandes (Page {page}/{total_pages})", description='\n\n'.join(commands_info_list[start_index:end_index]), color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def help(ctx, command: str = None, page: int = 1):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM commands')
   commandes = cur.fetchall()
   actives = [cmd for cmd in commandes if cmd[4] == 1]
   commands_info_list = [f"{cmd[1]} - {commands_info[cmd[1]][3]}" for cmd in actives]
   commands_per_page = 20
   if command is not None:
      cur.execute('SELECT * FROM commands WHERE commande = ?', (command,))
      commande = cur.fetchone()
      if commande is None:
         await ctx.send("La commande n'existe pas")
         return
      if commande[4] == 0:
         await ctx.send("La commande n'est pas activée")
         return
      embed = discord.Embed(title=f"Informations sur la commande {commande[1]} :", color=0xff0000)
      embed.add_field(name="ID", value=commande[0], inline=False)
      embed.add_field(name="Commande", value=commande[1], inline=False)
      embed.add_field(name="Permissions", value=commande[2], inline=False)
      embed.add_field(name="Utilisation", value=f"/{commande[1]} {commande[3]}\n?{commande[1]} {commande[3]}", inline=False)
      embed.add_field(name="Description", value=commands_info[commande[1]][3], inline=False)
      await ctx.send(embed=embed)
      return
   total_pages = (len(commands_info_list) + commands_per_page - 1) // commands_per_page
   if page < 1 or page > total_pages:
      await ctx.send("Page invalide")
      return
   start_index = (page - 1) * commands_per_page
   end_index = start_index + commands_per_page
   embed = discord.Embed(title=f"Liste des commandes (Page {page}/{total_pages})", description='\n\n'.join(commands_info_list[start_index:end_index]), color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("ownerbot"), name="ownerbot", description="Permet d'ajouter un owner au bot")
async def ownerbot(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM ownerbot')
   owners = cur.fetchall()
   if len(owners) == 0:
      embed = discord.Embed(title="Liste des owners du bot", description="Aucun owner bot", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des owners du bot", color=0xff0000)
      for owner in owners:
         embed.add_field(name="Owner :", value=f"<@{owner[1]}>", inline=False)
   await interaction.response.send_message(embed=embed)



@bot.command()
async def ownerbot(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM ownerbot')
   owners = cur.fetchall()
   if len(owners) == 0:
      embed = discord.Embed(title="Liste des owners du bot", description="Aucun owner bot", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des owners du bot", color=0xff0000)
      for owner in owners:
         embed.add_field(name="Owner :", value=f"<@{owner[1]}>", inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("ownerbotadd"), name="ownerbotadd", description="Permet d'ajouter un owner au bot")
@app_commands.describe(member="Le membre à ajouter en owner")
async def ownerbotadd(interaction: discord.Interaction, member: discord.Member):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM ownerbot WHERE user_id = ?', (member.id,))
   owner = cur.fetchone()
   if owner is not None:
      await interaction.response.send_message("Le membre est déjà owner du bot")
      return
   cur.execute('''
      INSERT INTO ownerbot (user_id, moderator_id) VALUES (?, ?)
   ''', (member.id, interaction.user.id))
   con.commit()
   await interaction.response.send_message("Owner ajouté")



@bot.command()
async def ownerbotadd(ctx, member: discord.Member):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM ownerbot WHERE user_id = ?', (member.id,))
   owner = cur.fetchone()
   if owner is not None:
      await ctx.send("Le membre est déjà owner du bot")
      return
   cur.execute('''
      INSERT INTO ownerbot (user_id, moderator_id) VALUES (?, ?)
   ''', (member.id, ctx.author.id))
   con.commit()
   await ctx.send("Owner ajouté")



@bot.tree.command(guilds=active_commande("ownerbotremove"), name="ownerbotremove", description="Permet de retirer un owner au bot")
@app_commands.describe(member="Le membre à retirer en owner")
async def ownerbotremove(interaction: discord.Interaction, member: discord.Member):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT * FROM ownerbot WHERE user_id = ?', (member.id,))
   owner = cur.fetchone()
   if owner is None:
      await interaction.response.send_message("Le membre n'est pas owner du bot")
      return
   cur.execute('''
      DELETE FROM ownerbot WHERE user_id = ?
   ''', (member.id,))
   con.commit()
   await interaction.response.send_message("Owner retiré")



@bot.command()
async def ownerbotremove(ctx, member: discord.Member):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT * FROM ownerbot WHERE user_id = ?', (member.id,))
   owner = cur.fetchone()
   if owner is None:
      await ctx.send("Le membre n'est pas owner du bot")
      return
   cur.execute('''
      DELETE FROM ownerbot WHERE user_id = ?
   ''', (member.id,))
   con.commit()
   await ctx.send("Owner retiré")



@bot.tree.command(guilds=active_commande("ownerbotreset"), name="ownerbotreset", description="Permet de retirer tous les owners du bot")
async def ownerbotreset(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('''
      DELETE FROM ownerbot
   ''')
   con.commit()
   await interaction.response.send_message("Owners retirés")



@bot.command()
async def ownerbotreset(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('''
      DELETE FROM ownerbot
   ''')
   con.commit()
   await ctx.send("Owners retirés")



@bot.tree.command(guilds=active_commande("reload"), name="reload", description="Permet de redémarrer le bot")
async def reload(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   await interaction.response.defer()
   await interaction.followup.send("Redémarrage du bot...")
   redemarrer_script()



@bot.command()
async def reload(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   await ctx.message.delete()
   await ctx.send("Redémarrage du bot...")
   redemarrer_script()



@bot.tree.command(guilds=active_commande("embed"), name="embed", description="Permet d'envoyer un embed")
@app_commands.describe(channel="Le channel où envoyer l'embed",
                       title="Le titre de l'embed",
                       description="La description de l'embed",
                       color="La couleur de l'embed",
                       footer="Le footer de l'embed")
async def embed(interaction: discord.Interaction, title: str, description: str, color: Literal["Aléatoire", "Rouge", "Vert", "Bleu", "Jaune", "Rose", "Violet", "Orange", "Noir", "Blanc", "Gris", "Marron", "Turquoise", "Bleu clair", "Vert clair", "Jaune clair", "Rose clair", "Violet clair", "Orange clair", "Noir clair", "Blanc clair", "Gris clair", "Marron clair", "Turquoise clair"] = "Rouge", channel: discord.TextChannel = None, footer: str = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = interaction.channel
   if color == "Rouge":
      color = "ff0000"
   elif color == "Aléatoire":
      color = hex(randint(0, 0xffffff)).lstrip("0x")
   elif color == "Vert":
      color = "00ff00"
   elif color == "Bleu":
      color = "0000ff"
   elif color == "Jaune":
      color = "ffff00"
   elif color == "Rose":
      color = "ff00ff"
   elif color == "Violet":
      color = "800080"
   elif color == "Orange":
      color = "ffa500"
   elif color == "Noir":
      color = "000000"
   elif color == "Blanc":
      color = "ffffff"
   elif color == "Gris":
      color = "808080"
   elif color == "Marron":
      color = "800000"
   elif color == "Turquoise":
      color = "40e0d0"

   embed = discord.Embed(title=title, description=description, color=int(color, 16))
   if footer is not None:
      embed.set_footer(text=footer)
   await channel.send(embed=embed)
   await interaction.response.send_message("Embed envoyé", ephemeral=True)


@bot.command()
async def embed(ctx, title: str, description: str, color: Literal["Aléatoire", "Rouge", "Vert", "Bleu", "Jaune", "Rose", "Violet", "Orange", "Noir", "Blanc", "Gris", "Marron", "Turquoise", "Bleu clair", "Vert clair", "Jaune clair", "Rose clair", "Violet clair", "Orange clair", "Noir clair", "Blanc clair", "Gris clair", "Marron clair", "Turquoise clair"] = "Rouge", channel: discord.TextChannel = None, footer: str = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if channel is None:
      channel = ctx.channel
   if color == "Rouge":
      color = "ff0000"
   elif color == "Aléatoire":
      color = hex(randint(0, 0xffffff)).lstrip("0x")
   elif color == "Vert":
      color = "00ff00"
   elif color == "Bleu":
      color = "0000ff"
   elif color == "Jaune":
      color = "ffff00"
   elif color == "Rose":
      color = "ff00ff"
   elif color == "Violet":
      color = "800080"
   elif color == "Orange":
      color = "ffa500"
   elif color == "Noir":
      color = "000000"
   elif color == "Blanc":
      color = "ffffff"
   elif color == "Gris":
      color = "808080"
   elif color == "Marron":
      color = "800000"
   elif color == "Turquoise":
      color = "40e0d0"

   embed = discord.Embed(title=title, description=description, color=int(color, 16))
   if footer is not None:
      embed.set_footer(text=footer)
   await channel.send(embed=embed)
   await ctx.send("Embed envoyé")



@bot.tree.command(guilds=active_commande("rename"), name="rename", description="Permet de renommer un membre")
@app_commands.describe(member="Le membre à renommer",
                       nickname="Le nouveau pseudo du membre")
async def rename(interaction: discord.Interaction, member: discord.Member, nickname: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   await interaction.response.defer()
   await member.edit(nick=nickname)
   await interaction.followup.send("Membre renommé")



@bot.command()
async def rename(ctx, member: discord.Member, nickname: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   await member.edit(nick=nickname)
   await ctx.send("Membre renommé")



@bot.tree.command(guilds=active_commande("setbotname"), name="setbotname", description="Permet de changer le nom du bot")
async def setbotname(interaction: discord.Interaction, name: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   await interaction.response.defer()
   await bot.user.edit(username=name)
   await interaction.followup.send("Nom changé")



@bot.tree.command(guilds=active_commande("join"), name="join", description="Permet de faire rejoindre le bot dans un salon vocal")
@app_commands.describe(channel="Le salon vocal où rejoindre le bot")
async def join(interaction: discord.Interaction, channel: discord.VoiceChannel = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
   if channel is None:
      channel = interaction.user.voice.channel
   if interaction.guild.voice_client is not None:
      await interaction.guild.voice_client.disconnect()
   voice_channel = await channel.connect()
   await interaction.response.send_message("Le bot a rejoint le salon vocal")
   async def play_audio():
      while True:
         audio_source = discord.FFmpegPCMAudio("musique.mp3")
         voice_channel.play(audio_source, after=lambda e: print('Player error: %s' % e) if e else None)
         while voice_channel.is_playing():
            await asyncio.sleep(1)
   bot.loop.create_task(play_audio())
   


@bot.command()
async def join(ctx, channel: discord.VoiceChannel = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if channel is None:
      channel = ctx.author.voice.channel
   if ctx.guild.voice_client is not None:
      await ctx.guild.voice_client.disconnect()
   voice_channel = await channel.connect()
   await ctx.send("Le bot a rejoint le salon vocal")
   async def play_audio():
      while True:
         audio_source = discord.FFmpegPCMAudio("musique.mp3")
         voice_channel.play(audio_source, after=lambda e: print('Player error: %s' % e) if e else None)
         while voice_channel.is_playing():
            await asyncio.sleep(1)
   bot.loop.create_task(play_audio())



@bot.tree.command(guilds=active_commande("leave"), name="leave", description="Permet de faire quitter le bot d'un salon vocal")
async def leave(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   await interaction.response.defer()
   await interaction.guild.voice_client.disconnect()
   await interaction.followup.send("Le bot a quitté le salon vocal")


@bot.command()
async def leave(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   await ctx.guild.voice_client.disconnect()
   await ctx.send("Le bot a quitté le salon vocal")



@bot.tree.command(guilds=active_commande("banner"), name="banner", description="Permet de voir la bannière d'un membre")
@app_commands.describe(member="Le membre dont on veut voir la bannière")
async def banner(interaction: discord.Interaction, member: discord.Member = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = interaction.user
   req = await bot.http.request(discord.http.Route("GET", "/users/{uid}", uid=member.id))
   banner_id = req["banner"]
   if banner_id:
      banner_url = f"https://cdn.discordapp.com/banners/{member.id}/{banner_id}?size=1024"
      embed = discord.Embed(title=f"Bannière de {member.name}", color=0xff0000)
      embed.set_image(url=banner_url)
   else:
      embed = discord.Embed(title=f"{member.name} n'a pas de bannière", color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def banner(ctx, user:discord.Member = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if user == None:
      user = ctx.author
   req = await bot.http.request(discord.http.Route("GET", "/users/{uid}", uid=user.id))
   banner_id = req["banner"]
   if banner_id:
      banner_url = f"https://cdn.discordapp.com/banners/{user.id}/{banner_id}?size=1024"
      embed = discord.Embed(title=f"Bannière de {user.name}", color=0xff0000)
      embed.set_image(url=banner_url)
   else:
      embed = discord.Embed(title=f"{user.name} n'a pas de bannière", color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("serverlist"), name="serverlist", description="Permet de voir la liste des serveurs où est le bot")
async def serverlist(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Liste des serveurs où est le bot", description='\n'.join([f"{guild.name}" for guild in bot.guilds]), color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def serverlist(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Liste des serveurs où est le bot", description='\n'.join([f"{guild.name}" for guild in bot.guilds]), color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("boosters"), name="boosters", description="Permet de voir la liste des boosters du serveur")
async def boosters(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   boosters = interaction.guild.premium_subscribers
   if len(boosters) == 0:
      embed = discord.Embed(title="Liste des boosters du serveur", description="Aucun booster", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des boosters du serveur", description='\n'.join([f"{booster.name}" for booster in boosters]), color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def boosters(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   boosters = ctx.guild.premium_subscribers
   if len(boosters) == 0:
      embed = discord.Embed(title="Liste des boosters du serveur", description="Aucun booster", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des boosters du serveur", description='\n'.join([f"{booster.name}" for booster in boosters]), color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("botadmin"), name="botadmin", description="Permet de voir la liste des bot qui ont les permissions administrateur")
async def botadmin(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   bots = [member for member in interaction.guild.members if member.bot]
   bot_admin = []
   for bot in bots:
      if bot.guild_permissions.administrator:
         bot_admin.append(bot)
   embed = discord.Embed(title="Liste des bots administrateurs", description='\n'.join([f"{bot.name}" for bot in bot_admin]), color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def botadmin(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   bots = [member for member in ctx.guild.members if member.bot]
   bot_admin = []
   for bot in bots:
      if bot.guild_permissions.administrator:
         bot_admin.append(bot)
   embed = discord.Embed(title="Liste des bots administrateurs", description='\n'.join([f"{bot.name}" for bot in bot_admin]), color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("botlist"), name="botlist", description="Permet de voir la liste des bots sur le serveur")
async def botlist(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   bots = [member for member in interaction.guild.members if member.bot]
   if len(bots) == 0:
      embed = discord.Embed(title="Liste des bots sur le serveur", description="Aucun bot", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des bots sur le serveur", description='\n'.join([f"{bot.name}" for bot in bots]), color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def botlist(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   bots = [member for member in ctx.guild.members if member.bot]
   if len(bots) == 0:
      embed = discord.Embed(title="Liste des bots sur le serveur", description="Aucun bot", color=0xff0000)
   else:
      embed = discord.Embed(title="Liste des bots sur le serveur", description='\n'.join([f"{bot.name}" for bot in bots]), color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("support"), name="support", description="Permet de voir le serveur de support")
async def support(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Serveur de support", description="https://discord.gg/zP7sHFpTZX", color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def support(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Serveur de support", description="https://discord.gg/zP7sHFpTZX", color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("emojiinfo"), name="emojiinfo", description="Permet de voir les informations sur un emoji")
@app_commands.describe(emoji="L'ID de l'emoji dont on veut voir les informations")
async def emojiinfo(interaction: discord.Interaction, emoji: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   try:
      emoji_object = bot.get_emoji(int(emoji))
   except discord.NotFound:
      await interaction.response.send_message("L'emoji spécifié n'a pas été trouvé.")
      return
   embed = discord.Embed(title=f"Informations sur l'emoji {emoji_object.name}", color=0xff0000)
   embed.add_field(name="Nom", value=emoji_object.name, inline=False)
   embed.add_field(name="ID", value=emoji_object.id, inline=False)
   embed.add_field(name="Animé", value=emoji_object.animated, inline=False)
   embed.set_thumbnail(url=emoji_object.url)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def emojiinfo(ctx, emoji: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   try:
      emoji_object = bot.get_emoji(int(emoji))
   except discord.NotFound:
      await ctx.send("L'emoji spécifié n'a pas été trouvé.")
      return
   embed = discord.Embed(title=f"Informations sur l'emoji {emoji_object.name}", color=0xff0000)
   embed.add_field(name="Nom", value=emoji_object.name, inline=False)
   embed.add_field(name="ID", value=emoji_object.id, inline=False)
   embed.add_field(name="Animé", value=emoji_object.animated, inline=False)
   embed.set_thumbnail(url=emoji_object.url)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("emojilist"), name="emojilist", description="Permet de voir la liste des emojis du serveur")
async def emojilist(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   await interaction.response.defer()

   emojis = interaction.guild.emojis
   if len(emojis) == 0:
      embed = discord.Embed(title="Liste des emojis du serveur", description="Aucun emoji", color=0xff0000)
      await interaction.followup.send(embed=embed)
      return

   emojis_per_page = 10
   total_pages = (len(emojis) - 1) // emojis_per_page + 1

   page_number = 1
   start_index = (page_number - 1) * emojis_per_page
   end_index = page_number * emojis_per_page

   emojis_on_page = emojis[start_index:end_index]

   embed = create_emojilist_embed(emojis_on_page, page_number, total_pages)
   message = await interaction.followup.send(embed=embed)

   # Add reactions for pagination
   await message.add_reaction("⬅️")
   await message.add_reaction("➡️")

   # Define a check function for wait_for
   def check(reaction, user):
      return user == interaction.user and str(reaction.emoji) in ["⬅️", "➡️"]

   while True:
      try:
         reaction, _ = await bot.wait_for("reaction_add", timeout=60, check=check)

         # Handle pagination based on the reaction
         if str(reaction.emoji) == "⬅️":
            page_number = max(1, page_number - 1)
         elif str(reaction.emoji) == "➡️":
            page_number = min(total_pages, page_number + 1)

         start_index = (page_number - 1) * emojis_per_page
         end_index = page_number * emojis_per_page

         emojis_on_page = emojis[start_index:end_index]
         embed = create_emojilist_embed(emojis_on_page, page_number, total_pages)
         await message.edit(embed=embed)

         # Remove the user's reaction to keep it clean
         await message.remove_reaction(reaction, interaction.user)

      except asyncio.TimeoutError:
         # Remove reactions when the timeout occurs
         await message.clear_reactions()
         break

def create_emojilist_embed(emojis, current_page, total_pages):
   embed = discord.Embed(title="Liste des emojis du serveur", color=0xff0000)
   for emoji in emojis:
      embed.add_field(name=emoji.name, value=f"<:{emoji.name}:{emoji.id}>", inline=False)

   embed.set_footer(text=f"Page {current_page}/{total_pages}")
   return embed



@bot.command()
async def emojilist(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return

   emojis = ctx.guild.emojis
   if len(emojis) == 0:
      embed = discord.Embed(title="Liste des emojis du serveur", description="Aucun emoji", color=0xff0000)
      await ctx.send(embed=embed)
      return

   emojis_per_page = 10
   total_pages = (len(emojis) - 1) // emojis_per_page + 1

   page_number = 1
   start_index = (page_number - 1) * emojis_per_page
   end_index = page_number * emojis_per_page

   emojis_on_page = emojis[start_index:end_index]

   embed = create_emojilist_embed(emojis_on_page, page_number, total_pages)
   message = await ctx.send(embed=embed)

   # Add reactions for pagination
   await message.add_reaction("⬅️")
   await message.add_reaction("➡️")

   # Define a check function for wait_for
   def check(reaction, user):
      return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]

   while True:
      try:
         reaction, _ = await bot.wait_for("reaction_add", timeout=60, check=check)

         # Handle pagination based on the reaction
         if str(reaction.emoji) == "⬅️":
            page_number = max(1, page_number - 1)
         elif str(reaction.emoji) == "➡️":
            page_number = min(total_pages, page_number + 1)

         start_index = (page_number - 1) * emojis_per_page
         end_index = page_number * emojis_per_page

         emojis_on_page = emojis[start_index:end_index]
         embed = create_emojilist_embed(emojis_on_page, page_number, total_pages)
         await message.edit(embed=embed)

         # Remove the user's reaction to keep it clean
         await message.remove_reaction(reaction, ctx.author)

      except asyncio.TimeoutError:
         # Remove reactions when the timeout occurs
         await message.clear_reactions()
         break



@bot.tree.command(guilds=active_commande("coin"), name="coin", description="Permet de voir le nombre de coins d'un membre")
@app_commands.describe(member="Le membre dont on veut voir le nombre de coins")
async def coin(interaction: discord.Interaction, member: discord.Member = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = interaction.user
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT coins, bank FROM users WHERE user_id = ?', (member.id,))
   coins, bank = cur.fetchone()
   embed = discord.Embed(title=f"Coins de {member.name}", color=0xff0000)
   embed.add_field(name="Coins", value=coins, inline=False)
   embed.add_field(name="Bank", value=bank, inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def coin(ctx, member: discord.Member = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if member is None:
      member = ctx.author
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT coins, bank FROM users WHERE user_id = ?', (member.id,))
   coins, bank = cur.fetchone()
   embed = discord.Embed(title=f"Coins de {member.name}", color=0xff0000)
   embed.add_field(name="Coins", value=coins, inline=False)
   embed.add_field(name="Bank", value=bank, inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("level"), name="level", description="Permet de voir le niveau d'un membre")
@app_commands.describe(member="Le membre dont on veut voir le niveau")
async def level(interaction: discord.Interaction, member: discord.Member = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = interaction.user
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT level, xp FROM users WHERE user_id = ?', (member.id,))
   level, xp = cur.fetchone()
   max_xp = round(level**1.2 * 200 + 1000)
   embed = discord.Embed(title=f"Niveau de {member.name}", color=0xff0000)
   embed.add_field(name="Niveau", value=level, inline=False)
   embed.add_field(name="XP", value=f"{xp}/{max_xp}", inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def level(ctx, member: discord.Member = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if member is None:
      member = ctx.author
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT level, xp FROM users WHERE user_id = ?', (member.id,))
   level, xp = cur.fetchone()
   max_xp = round(level**1.2 * 200 + 1000)
   embed = discord.Embed(title=f"Niveau de {member.name}", color=0xff0000)
   embed.add_field(name="Niveau", value=level, inline=False)
   embed.add_field(name="XP", value=f"{xp}/{max_xp}", inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("coinflip"), name="coinflip", description="Permet de jouer à pile ou face")
@app_commands.describe(mise="La mise que vous voulez faire")
async def coinflip(interaction: discord.Interaction, mise: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (interaction.user.id,))
   coins = cur.fetchone()[0]
   mise = mise.lower()
   if mise == "all" or mise == "max" or mise == "tout":
      mise = coins
   else:
      try:
         mise = int(mise)
      except:
         await interaction.response.send_message("La mise doit être un nombre ou 'all'")
         return
      if mise > coins:
         await interaction.response.send_message("Vous n'avez pas assez de coins.")
         return
   result = choice(["pile", "face"])
   if result == "pile":
      embed = discord.Embed(title="Pile ou face", description="Pile", color=0xff0000)
   else:
      embed = discord.Embed(title="Pile ou face", description="Face", color=0xff0000)
   
   if result == "pile":
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins + mise, interaction.user.id))
      con.commit()
      res = f"Vous avez gagné {mise} coins"
   else:
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - mise, interaction.user.id))
      con.commit()
      res = f"Vous avez perdu {mise} coins"
   
   embed.add_field(name="Résultat", value=res, inline=False)
   await interaction.response.send_message(embed=embed)



@bot.tree.command(guilds=active_commande("leaderboard"), name="leaderboard", description="Permet de voir le leaderboard")
@app_commands.describe(type="Le type de leaderboard")
async def leaderboard(interaction: discord.Interaction, type: Literal["coins", "bank", "level", "messages", "voice"]):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute(f'SELECT user_id, {type} FROM users ORDER BY {type} DESC')
   rows = cur.fetchall()
   description = f"Leaderboard {type}\n\n"
   for i, row in enumerate(rows[:10]):
      user = bot.get_user(row[0])
      if i == 0:
         place = "🥇"
      elif i == 1:
         place = "🥈"
      elif i == 2:
         place = "🥉"
      else:
         place = i + 1
      description += f"{place} - {user.mention}: {row[1]}\n\n"
   embed = discord.Embed(title=f"Leaderboard {type}", description=description, color=0x40e0d0)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def leaderboard(ctx, type: Literal["coins", "bank", "level", "messages", "voice"]):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute(f'SELECT user_id, {type} FROM users ORDER BY {type} DESC')
   rows = cur.fetchall()
   description = f"Leaderboard {type}\n\n"
   for i, row in enumerate(rows[:10]):
      user = bot.get_user(row[0])
      if i == 0:
         place = "🥇"
      elif i == 1:
         place = "🥈"
      elif i == 2:
         place = "🥉"
      else:
         place = i + 1
      description += f"{place} - {user.mention}: {row[1]}\n\n"
   embed = discord.Embed(title=f"Leaderboard {type}", description=description, color=0x40e0d0)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("daily"), name="daily", description="Permet de récupérer sa récompense quotidienne")
async def daily(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT last_daily FROM users WHERE user_id = ?', (interaction.user.id,))
   last_daily = cur.fetchone()[0]
   if last_daily is not None and datetime.now() - datetime.strptime(last_daily, "%Y-%m-%d %H:%M:%S") < timedelta(days=1):
      formatted_last_daily = datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
      remaining_time = formatted_last_daily + timedelta(days=1) - datetime.now()
      zero_datetime = datetime(1, 1, 1)
      remaining_time_datetime = zero_datetime + remaining_time
      formatted_remaining_time = remaining_time_datetime.strftime("`%H heures`, `%M minutes` et `%S secondes`")
      embed = discord.Embed(title="Récompense quotidienne", description=f"Vous avez déjà récupéré votre récompense quotidienne, vous devez encore attendre {formatted_remaining_time}.", color=0xff0000)
      if interaction.user.avatar:
         embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
         embed.set_thumbnail(url=interaction.user.avatar.url)
      else:
         default_avatar_url = interaction.user.default_avatar.url
         embed.set_author(name=interaction.user.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      await interaction.response.send_message(embed=embed)
      return
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (interaction.user.id,))
   coins = cur.fetchone()[0]
   add_coins = randint(500, 1000)
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins + add_coins, interaction.user.id))
   cur.execute('UPDATE users SET last_daily = ? WHERE user_id = ?', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), interaction.user.id))
   con.commit()
   embed = discord.Embed(title="Récompense quotidienne", description=f"Vous avez reçu vos {add_coins} coins quotidiens.", color=0xff0000)
   if interaction.user.avatar:
      embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
      embed.set_thumbnail(url=interaction.user.avatar.url)
   else:
      default_avatar_url = interaction.user.default_avatar.url
      embed.set_author(name=interaction.user.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def daily(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT last_daily FROM users WHERE user_id = ?', (ctx.author.id,))
   last_daily = cur.fetchone()[0]
   if last_daily is not None and datetime.now() - datetime.strptime(last_daily, "%Y-%m-%d %H:%M:%S") < timedelta(days=1):
      formatted_last_daily = datetime.strptime(last_daily, '%Y-%m-%d %H:%M:%S')
      remaining_time = formatted_last_daily + timedelta(days=1) - datetime.now()
      zero_datetime = datetime(1, 1, 1)
      remaining_time_datetime = zero_datetime + remaining_time
      formatted_remaining_time = remaining_time_datetime.strftime("`%H heures`, `%M minutes` et `%S secondes`")
      embed = discord.Embed(title="Récompense quotidienne", description=f"Vous avez déjà récupéré votre récompense quotidienne, vous devez encore attendre {formatted_remaining_time}.", color=0xff0000)
      if ctx.author.avatar:
         embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
         embed.set_thumbnail(url=ctx.author.avatar.url)
      else:
         default_avatar_url = ctx.author.default_avatar.url
         embed.set_author(name=ctx.author.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      await ctx.send(embed=embed)
      return
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (ctx.author.id,))
   coins = cur.fetchone()[0]
   add_coins = randint(500, 1000)
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins + add_coins, ctx.author.id))
   cur.execute('UPDATE users SET last_daily = ? WHERE user_id = ?', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ctx.author.id))
   con.commit()
   embed = discord.Embed(title="Récompense quotidienne", description=f"Vous avez reçu vos {add_coins} coins quotidiens.", color=0xff0000)
   if ctx.author.avatar:
      embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
      embed.set_thumbnail(url=ctx.author.avatar.url)
   else:
      default_avatar_url = ctx.author.default_avatar.url
      embed.set_author(name=ctx.author.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("work"), name="work", description="Permet de travailler pour gagner des coins")
async def work(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT last_work FROM users WHERE user_id = ?', (interaction.user.id,))
   last_work = cur.fetchone()[0]
   if last_work is not None and datetime.now() - datetime.strptime(last_work, "%Y-%m-%d %H:%M:%S") < timedelta(hours=2):
      formatted_last_work = datetime.strptime(last_work, '%Y-%m-%d %H:%M:%S')
      remaining_time = formatted_last_work + timedelta(hours=2) - datetime.now()
      zero_datetime = datetime(1, 1, 1)
      remaining_time_datetime = zero_datetime + remaining_time
      formatted_remaining_time = remaining_time_datetime.strftime("`%H heures`, `%M minutes` et `%S secondes`")
      embed = discord.Embed(title="Travail", description=f"Vous avez déjà travaillé, vous devez encore attendre {formatted_remaining_time}.", color=0xff0000)
      if interaction.user.avatar:
         embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
         embed.set_thumbnail(url=interaction.user.avatar.url)
      else:
         default_avatar_url = interaction.user.default_avatar.url
         embed.set_author(name=interaction.user.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      await interaction.response.send_message(embed=embed)
      return
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (interaction.user.id,))
   coins = cur.fetchone()[0]
   add_coins = randint(500, 1000)
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins + add_coins, interaction.user.id))
   cur.execute('UPDATE users SET last_work = ? WHERE user_id = ?', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), interaction.user.id))
   con.commit()
   embed = discord.Embed(title="Travail", description=f"Vous avez gagné {add_coins} coins en travaillant.", color=0xff0000)
   if interaction.user.avatar:
      embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
      embed.set_thumbnail(url=interaction.user.avatar.url)
   else:
      default_avatar_url = interaction.user.default_avatar.url
      embed.set_author(name=interaction.user.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=interaction.user.default_avatar.url)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def work(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT last_work FROM users WHERE user_id = ?', (ctx.author.id,))
   last_work = cur.fetchone()[0]
   if last_work is not None and datetime.now() - datetime.strptime(last_work, "%Y-%m-%d %H:%M:%S") < timedelta(hours=2):
      formatted_last_work = datetime.strptime(last_work, '%Y-%m-%d %H:%M:%S')
      remaining_time = formatted_last_work + timedelta(hours=2) - datetime.now()
      zero_datetime = datetime(1, 1, 1)
      remaining_time_datetime = zero_datetime + remaining_time
      formatted_remaining_time = remaining_time_datetime.strftime("`%H heures`, `%M minutes` et `%S secondes`")
      embed = discord.Embed(title="Travail", description=f"Vous avez déjà travaillé, vous devez encore attendre {formatted_remaining_time}.", color=0xff0000)
      if ctx.author.avatar:
         embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
         embed.set_thumbnail(url=ctx.author.avatar.url)
      else:
         default_avatar_url = ctx.author.default_avatar.url
         embed.set_author(name=ctx.author.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=ctx.author.default_avatar.url)
      await ctx.send(embed=embed)
      return
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (ctx.author.id,))
   coins = cur.fetchone()[0]
   add_coins = randint(500, 1000)
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins + add_coins, ctx.author.id))
   cur.execute('UPDATE users SET last_work = ? WHERE user_id = ?', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ctx.author.id))
   con.commit()
   embed = discord.Embed(title="Travail", description=f"Vous avez gagné {add_coins} coins en travaillant.", color=0xff0000)
   if ctx.author.avatar:
      embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
      embed.set_thumbnail(url=ctx.author.avatar.url)
   else:
      default_avatar_url = ctx.author.default_avatar.url
      embed.set_author(name=ctx.author.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=ctx.author.default_avatar.url)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("deposit"), name="deposit", description="Permet de déposer des coins dans la banque")
@app_commands.describe(mise="La mise que vous voulez déposer")
async def deposit(interaction: discord.Interaction, mise: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT coins, bank FROM users WHERE user_id = ?', (interaction.user.id,))
   coins, bank = cur.fetchone()
   mise = mise.lower()
   if mise == "all" or mise == "max" or mise == "tout":
      mise = coins
   else:
      try:
         mise = int(mise)
      except:
         await interaction.response.send_message("La mise doit être un nombre ou 'all'")
         return
      if mise > coins:
         await interaction.response.send_message("Vous n'avez pas assez de coins.")
         return
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - mise, interaction.user.id))
   cur.execute('UPDATE users SET bank = ? WHERE user_id = ?', (bank + mise, interaction.user.id))
   con.commit()
   embed = discord.Embed(title="Dépôt", description=f"Vous avez déposé {mise} coins dans votre banque.", color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def deposit(ctx, mise: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT coins, bank FROM users WHERE user_id = ?', (ctx.author.id,))
   coins, bank = cur.fetchone()
   mise = mise.lower()
   if mise == "all" or mise == "max" or mise == "tout":
      mise = coins
   else:
      try:
         mise = int(mise)
      except:
         await ctx.send("La mise doit être un nombre ou 'all'")
         return
      if mise > coins:
         await ctx.send("Vous n'avez pas assez de coins.")
         return
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - mise, ctx.author.id))
   cur.execute('UPDATE users SET bank = ? WHERE user_id = ?', (bank + mise, ctx.author.id))
   con.commit()
   embed = discord.Embed(title="Dépôt", description=f"Vous avez déposé {mise} coins dans votre banque.", color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("withdraw"), name="withdraw", description="Permet de retirer des coins de la banque")
@app_commands.describe(mise="La mise que vous voulez retirer")
async def withdraw(interaction: discord.Interaction, mise: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT coins, bank FROM users WHERE user_id = ?', (interaction.user.id,))
   coins, bank = cur.fetchone()
   mise = mise.lower()
   if mise == "all" or mise == "max" or mise == "tout":
      mise = bank
   else:
      try:
         mise = int(mise)
      except:
         await interaction.response.send_message("La mise doit être un nombre ou 'all'")
         return
      if mise > bank:
         await interaction.response.send_message("Vous n'avez pas assez de coins dans votre banque.")
         return
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins + mise, interaction.user.id))
   cur.execute('UPDATE users SET bank = ? WHERE user_id = ?', (bank - mise, interaction.user.id))
   con.commit()
   embed = discord.Embed(title="Retrait", description=f"Vous avez retiré {mise} coins de votre banque.", color=0xff0000)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def withdraw(ctx, mise: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT coins, bank FROM users WHERE user_id = ?', (ctx.author.id,))
   coins, bank = cur.fetchone()
   mise = mise.lower()
   if mise == "all" or mise == "max" or mise == "tout":
      mise = bank
   else:
      try:
         mise = int(mise)
      except:
         await ctx.send("La mise doit être un nombre ou 'all'")
         return
      if mise > bank:
         await ctx.send("Vous n'avez pas assez de coins dans votre banque.")
         return
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins + mise, ctx.author.id))
   cur.execute('UPDATE users SET bank = ? WHERE user_id = ?', (bank - mise, ctx.author.id))
   con.commit()
   embed = discord.Embed(title="Retrait", description=f"Vous avez retiré {mise} coins de votre banque.", color=0xff0000)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("give"), name="give", description="Donne des coins, de la bank, de l'xp, des levels, des messages ou de la voice à un membre")
@app_commands.describe(member="Le membre à qui donner", 
                       type="Le type de donnée", 
                       amount="La quantité à donner")
async def give(interaction: discord.Interaction, type: Literal["coins", "bank", "xp", "level", "messages", "voice"], amount: int, member: discord.Member = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = interaction.user
   con, cur = choose_db(interaction.guild.id)
   cur.execute(f'SELECT {type} FROM users WHERE user_id = ?', (member.id,))
   data = cur.fetchone()[0]
   cur.execute(f'UPDATE users SET {type} = ? WHERE user_id = ?', (data + amount, member.id))
   con.commit()
   await interaction.response.send_message(f"Vous avez give {amount} {type} à {member.mention}.")


@bot.command()
async def give(ctx, type: Literal["coins", "bank", "xp", "level", "messages", "voice"], amount: int, member: discord.Member = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = ctx.author
   con, cur = choose_db(ctx.guild.id)
   cur.execute(f'SELECT {type} FROM users WHERE user_id = ?', (member.id,))
   data = cur.fetchone()[0]
   cur.execute(f'UPDATE users SET {type} = ? WHERE user_id = ?', (data + amount, member.id))
   con.commit()
   await ctx.send(f"Vous avez give {amount} {type} à {member.mention}.")



@bot.tree.command(guilds=active_commande("take"), name="take", description="Prend des coins, de la bank, de l'xp, des levels, des messages ou de la voice à un membre")
@app_commands.describe(member="Le membre à qui prendre",
                       type="Le type de donnée",
                       amount="La quantité à prendre")
async def take(interaction: discord.Interaction, type: Literal["coins", "bank", "xp", "level", "messages", "voice"], amount: int, member: discord.Member = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = interaction.user
   con, cur = choose_db(interaction.guild.id)
   cur.execute(f'SELECT {type} FROM users WHERE user_id = ?', (member.id,))
   data = cur.fetchone()[0]
   if data - amount < 0:
      await interaction.response.send_message(f"{member.mention} n'a pas assez de {type}.")
      return
   cur.execute(f'UPDATE users SET {type} = ? WHERE user_id = ?', (data - amount, member.id))
   con.commit()
   await interaction.response.send_message(f"Vous avez pris {amount} {type} à {member.mention}.")


@bot.command()
async def take(ctx, type: Literal["coins", "bank", "xp", "level", "messages", "voice"], amount: int, member: discord.Member = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      member = ctx.author
   con, cur = choose_db(ctx.guild.id)
   cur.execute(f'SELECT {type} FROM users WHERE user_id = ?', (member.id,))
   data = cur.fetchone()[0]
   if data - amount < 0:
      await ctx.send(f"{member.mention} n'a pas assez de {type}.")
      return
   cur.execute(f'UPDATE users SET {type} = ? WHERE user_id = ?', (data - amount, member.id))
   con.commit()
   await ctx.send(f"Vous avez pris {amount} {type} à {member.mention}.")



@bot.tree.command(guilds=active_commande("reset"), name="reset", description="Reset les coins, la bank, l'xp, les levels, les messages, la voice ou tout d'un membre")
@app_commands.describe(member="Le membre à reset",
                       type="Le type de donnée")
async def reset(interaction: discord.Interaction, type: Literal["coins", "bank", "xp", "level", "messages", "voice", "all"], member: discord.Member = None):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      for member in interaction.guild.members:
         con, cur = choose_db(interaction.guild.id)
         if type == "all":
            cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (0, member.id))
            cur.execute('UPDATE users SET bank = ? WHERE user_id = ?', (0, member.id))
            cur.execute('UPDATE users SET xp = ? WHERE user_id = ?', (0, member.id))
            cur.execute('UPDATE users SET level = ? WHERE user_id = ?', (0, member.id))
            cur.execute('UPDATE users SET messages = ? WHERE user_id = ?', (0, member.id))
            cur.execute('UPDATE users SET voice = ? WHERE user_id = ?', (0, member.id))
            con.commit()
         else:
            cur.execute(f'UPDATE users SET {type} = ? WHERE user_id = ?', (0, member.id))
            con.commit()
      await interaction.response.send_message(f"Vous avez reset toutes les données de {type}.")
      return
   con, cur = choose_db(interaction.guild.id)
   if type == "all":
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (0, member.id))
      cur.execute('UPDATE users SET bank = ? WHERE user_id = ?', (0, member.id))
      cur.execute('UPDATE users SET xp = ? WHERE user_id = ?', (0, member.id))
      cur.execute('UPDATE users SET level = ? WHERE user_id = ?', (0, member.id))
      cur.execute('UPDATE users SET messages = ? WHERE user_id = ?', (0, member.id))
      cur.execute('UPDATE users SET voice = ? WHERE user_id = ?', (0, member.id))
      con.commit()
      await interaction.response.send_message(f"Vous avez reset toutes les données de {member.mention}.")
   else:
      cur.execute(f'UPDATE users SET {type} = ? WHERE user_id = ?', (0, member.id))
      con.commit()
      await interaction.response.send_message(f"Vous avez reset {type} de {member.mention}.")


@bot.command()
async def reset(ctx, type: Literal["coins", "bank", "xp", "level", "messages", "voice", "all"], member: discord.Member = None):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   if member is None:
      for member in ctx.guild.members:
         con, cur = choose_db(ctx.guild.id)
         if type == "all":
            cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (0, member.id))
            cur.execute('UPDATE users SET bank = ? WHERE user_id = ?', (0, member.id))
            cur.execute('UPDATE users SET xp = ? WHERE user_id = ?', (0, member.id))
            cur.execute('UPDATE users SET level = ? WHERE user_id = ?', (0, member.id))
            cur.execute('UPDATE users SET messages = ? WHERE user_id = ?', (0, member.id))
            cur.execute('UPDATE users SET voice = ? WHERE user_id = ?', (0, member.id))
            con.commit()
         else:
            cur.execute(f'UPDATE users SET {type} = ? WHERE user_id = ?', (0, member.id))
            con.commit()
      await ctx.send(f"Vous avez reset toutes les données de {type}.")
   con, cur = choose_db(ctx.guild.id)
   if type == "all":
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (0, member.id))
      cur.execute('UPDATE users SET bank = ? WHERE user_id = ?', (0, member.id))
      cur.execute('UPDATE users SET xp = ? WHERE user_id = ?', (0, member.id))
      cur.execute('UPDATE users SET level = ? WHERE user_id = ?', (0, member.id))
      cur.execute('UPDATE users SET messages = ? WHERE user_id = ?', (0, member.id))
      cur.execute('UPDATE users SET voice = ? WHERE user_id = ?', (0, member.id))
      con.commit()
      await ctx.send(f"Vous avez reset toutes les données de {member.mention}.")
   else:
      cur.execute(f'UPDATE users SET {type} = ? WHERE user_id = ?', (0, member.id))
      con.commit()
      await ctx.send(f"Vous avez reset {type} de {member.mention}.")



@bot.tree.command(guilds=active_commande("pay"), name="pay", description="Paye un membre")
@app_commands.describe(member="Le membre à qui payer",
                       amount="La quantité à payer")
async def pay(interaction: discord.Interaction, amount: int, member: discord.Member):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (interaction.user.id,))
   coins = cur.fetchone()[0]
   if amount > coins:
      await interaction.response.send_message("Vous n'avez pas assez de coins.")
      return
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (member.id,))
   member_coins = cur.fetchone()[0]
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - amount, interaction.user.id))
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (member_coins + amount, member.id))
   con.commit()
   await interaction.response.send_message(f"Vous avez payé {amount} coins à {member.mention}.")
   embed = discord.Embed(title="Paiement", description=f"{interaction.user.mention} vous a payé {amount} coins.", color=0xff0000)
   await member.send(embed=embed)


@bot.command()
async def pay(ctx, amount: int, member: discord.Member):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (ctx.author.id,))
   coins = cur.fetchone()[0]
   if amount > coins:
      await ctx.send("Vous n'avez pas assez de coins.")
      return
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (member.id,))
   member_coins = cur.fetchone()[0]
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - amount, ctx.author.id))
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (member_coins + amount, member.id))
   con.commit()
   await ctx.send(f"Vous avez payé {amount} coins à {member.mention}.")
   embed = discord.Embed(title="Paiement", description=f"{ctx.author.mention} vous a payé {amount} coins.", color=0xff0000)
   await member.send(embed=embed)



@bot.tree.command(guilds=active_commande("shop"), name="shop", description="Affiche la boutique")
async def shop(interaction: discord.Interaction):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Boutique", description="Pour acheter un item, faites `/buy <item>`", color=0xff0000)
   embed.add_field(name="XP x 2", value="50 000 coins", inline=False)
   embed.add_field(name="Coins x 2", value="100 000 coins", inline=False)
   embed.add_field(name="XP x 3", value="100 000 coins", inline=False)
   embed.add_field(name="Coins x 3", value="200 000 coins", inline=False)
   await interaction.response.send_message(embed=embed)


@bot.command()
async def shop(ctx):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   embed = discord.Embed(title="Boutique", description="Pour acheter un item, faites `/buy <item>`", color=0xff0000)
   embed.add_field(name="XP x 2", value="50 000 coins", inline=False)
   embed.add_field(name="Coins x 2", value="100 000 coins", inline=False)
   embed.add_field(name="XP x 3", value="100 000 coins", inline=False)
   embed.add_field(name="Coins x 3", value="200 000 coins", inline=False)
   await ctx.send(embed=embed)



@bot.tree.command(guilds=active_commande("buy"), name="buy", description="Achète un item dans la boutique")
@app_commands.describe(item="L'item à acheter")
async def buy(interaction: discord.Interaction, item: Literal["XP x 2", "Coins x 2", "XP x 3", "Coins x 3"]):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(interaction.guild.id)
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (interaction.user.id,))
   coins = cur.fetchone()[0]
   cur.execute('SELECT xp_multiplier FROM users WHERE user_id = ?', (interaction.user.id,))
   xp_multiplier = cur.fetchone()[0]
   cur.execute('SELECT coins_multiplier FROM users WHERE user_id = ?', (interaction.user.id,))
   coins_multiplier = cur.fetchone()[0]
   if item == "XP x 2":
      if xp_multiplier == 2 or xp_multiplier == 6:
         await interaction.response.send_message("Vous avez déjà acheté XP x 2.")
         return
      if coins < 50000:
         await interaction.response.send_message("Vous n'avez pas assez de coins.")
         return
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - 50000, interaction.user.id))
      cur.execute('UPDATE users SET xp_multiplier = ? WHERE user_id = ?', (xp_multiplier * 2, interaction.user.id))
      con.commit()
      await interaction.response.send_message("Vous avez acheté XP x 2.")
   elif item == "Coins x 2":
      if coins_multiplier == 2 or coins_multiplier == 6:
         await interaction.response.send_message("Vous avez déjà acheté Coins x 2.")
         return
      if coins < 100000:
         await interaction.response.send_message("Vous n'avez pas assez de coins.")
         return
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - 100000, interaction.user.id))
      cur.execute('UPDATE users SET coins_multiplier = ? WHERE user_id = ?', (coins_multiplier * 2, interaction.user.id))
      con.commit()
      await interaction.response.send_message("Vous avez acheté Coins x 2.")
   elif item == "XP x 3":
      if xp_multiplier == 3 or xp_multiplier == 6:
         await interaction.response.send_message("Vous avez déjà acheté XP x 3.")
         return
      if coins < 100000:
         await interaction.response.send_message("Vous n'avez pas assez de coins.")
         return
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - 100000, interaction.user.id))
      cur.execute('UPDATE users SET xp_multiplier = ? WHERE user_id = ?', (xp_multiplier * 3, interaction.user.id))
      con.commit()
      await interaction.response.send_message("Vous avez acheté XP x 3.")
   elif item == "Coins x 3":
      if coins_multiplier == 3 or coins_multiplier == 6:
         await interaction.response.send_message("Vous avez déjà acheté Coins x 3.")
         return
      if coins < 200000:
         await interaction.response.send_message("Vous n'avez pas assez de coins.")
         return
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - 200000, interaction.user.id))
      cur.execute('UPDATE users SET coins_multiplier = ? WHERE user_id = ?', (coins_multiplier * 3, interaction.user.id))
      con.commit()
      await interaction.response.send_message("Vous avez acheté Coins x 3.")


@bot.command()
async def buy(ctx, item: Literal["XP x 2", "Coins x 2", "XP x 3", "Coins x 3"]):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   con, cur = choose_db(ctx.guild.id)
   cur.execute('SELECT coins FROM users WHERE user_id = ?', (ctx.author.id,))
   coins = cur.fetchone()[0]
   cur.execute('SELECT xp_multiplier FROM users WHERE user_id = ?', (ctx.author.id,))
   xp_multiplier = cur.fetchone()[0]
   cur.execute('SELECT coins_multiplier FROM users WHERE user_id = ?', (ctx.author.id,))
   coins_multiplier = cur.fetchone()[0]
   if item == "XP x 2":
      if xp_multiplier == 2 or xp_multiplier == 6:
         await ctx.send("Vous avez déjà acheté XP x 2.")
         return
      if coins < 50000:
         await ctx.send("Vous n'avez pas assez de coins.")
         return
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - 50000, ctx.author.id))
      cur.execute('UPDATE users SET xp_multiplier = ? WHERE user_id = ?', (xp_multiplier * 2, ctx.author.id))
      con.commit()
      await ctx.send("Vous avez acheté XP x 2.")
   elif item == "Coins x 2":
      if coins_multiplier == 2 or coins_multiplier == 6:
         await ctx.send("Vous avez déjà acheté Coins x 2.")
         return
      if coins < 100000:
         await ctx.send("Vous n'avez pas assez de coins.")
         return
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - 100000, ctx.author.id))
      cur.execute('UPDATE users SET coins_multiplier = ? WHERE user_id = ?', (coins_multiplier * 2, ctx.author.id))
      con.commit()
      await ctx.send("Vous avez acheté Coins x 2.")
   elif item == "XP x 3":
      if xp_multiplier == 3 or xp_multiplier == 6:
         await ctx.send("Vous avez déjà acheté XP x 3.")
         return
      if coins < 100000:
         await ctx.send("Vous n'avez pas assez de coins.")
         return
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - 100000, ctx.author.id))
      cur.execute('UPDATE users SET xp_multiplier = ? WHERE user_id = ?', (xp_multiplier * 3, ctx.author.id))
      con.commit()
      await ctx.send("Vous avez acheté XP x 3.")
   elif item == "Coins x 3":
      if coins_multiplier == 3 or coins_multiplier == 6:
         await ctx.send("Vous avez déjà acheté Coins x 3.")
         return
      if coins < 200000:
         await ctx.send("Vous n'avez pas assez de coins.")
         return
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (coins - 200000, ctx.author.id))
      cur.execute('UPDATE users SET coins_multiplier = ? WHERE user_id = ?', (coins_multiplier * 3, ctx.author.id))
      con.commit()
      await ctx.send("Vous avez acheté Coins x 3.")



@bot.tree.command(guilds=active_commande("mpall"), name="mpall", description="Envoie un message à tous les membres du serveur")
@app_commands.describe(message="Le message à envoyer")
async def mpall(interaction: discord.Interaction, message: str):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   for member in interaction.guild.members:
      try:
         await member.send(message)
      except:
         pass
   await interaction.response.send_message("Message envoyé à tous les membres du serveur.")


@bot.command()
async def mpall(ctx, *, message: str):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   for member in ctx.guild.members:
      try:
         await member.send(message)
      except:
         pass
   await ctx.send("Message envoyé à tous les membres du serveur.")



@bot.tree.command(guilds=active_commande("unban"), name="unban", description="Unban un membre")
@app_commands.describe(member="Le membre à unban")
async def unban(interaction: discord.Interaction, member: discord.User):
   if not await check_permissions(interaction, inspect.currentframe().f_code.co_name):
      await not_perm(interaction, inspect.currentframe().f_code.co_name)
      return
   member = await bot.fetch_user(member.id)
   await interaction.guild.unban(member)
   await interaction.response.send_message(f"{member.mention} a été unban.")


@bot.command()
async def unban(ctx, member: discord.User):
   if not active_basic_commande(ctx, inspect.currentframe().f_code.co_name):
      return
   await ctx.message.delete()
   if not await check_permissions(ctx, inspect.currentframe().f_code.co_name):
      await not_perm(ctx, inspect.currentframe().f_code.co_name)
      return
   member = await bot.fetch_user(member.id)
   await ctx.guild.unban(member)
   await ctx.send(f"{member.mention} a été unban.")















@bot.event
async def on_guild_join(guild):
   redemarrer_script()



message_count = defaultdict(int)
spamming_users = set()
spam_limit = 6
spam_interval = 5

@bot.event
async def on_message(message):
   if message.author.bot:
      return 

   if isinstance(message.channel, discord.DMChannel):
      db_folder = "db"
      db_files = [f for f in os.listdir(db_folder) if os.path.isfile(os.path.join(db_folder, f)) and f.endswith(".db")]
      for db_file in db_files:
         guild_id = os.path.splitext(db_file)[0]

         con, cur = choose_db(guild_id)
         embed = discord.Embed(title="Message reçu en MP", color=0xff0000)
         embed.add_field(name="Message auteur", value=message.author.mention, inline=False)
         embed.add_field(name="Date", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
         embed.add_field(name="Message", value=f"`{message.content}`", inline=False)
         embed.add_field(name="ID", value=f"```py\nAuthor_ID = {message.author.id}```", inline=False)
         if message.author.avatar:
            embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
            embed.set_thumbnail(url=message.author.avatar.url)
         else:
            default_avatar_url = message.author.default_avatar.url
            embed.set_author(name=message.author.name, icon_url=default_avatar_url)
            embed.set_thumbnail(url=default_avatar_url)
         embed.set_footer(text="Message reçu")
         cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_MP_BOT",))
         log_mp_bot = cur.fetchone()
         try:
            log_channel = bot.get_channel(int(log_mp_bot[1]))
            await log_channel.send(embed=embed)
            await message.channel.send("Votre message a bien était envoyer a l'équipe du bot.")
         except:
            pass
         return


   await bot.process_commands(message) #ecoute les commande prefix

   con, cur = choose_db(message.guild.id)

   cur.execute('SELECT xp_multiplier, coins_multiplier FROM users WHERE user_id = ?', (message.author.id,))
   xp_multiplier, coins_multiplier = cur.fetchone()
   cur.execute('SELECT * FROM users WHERE user_id = ?', (message.author.id,))
   user = cur.fetchone()
   if user is None:
      cur.execute("INSERT INTO users (user_id, messages, voice, coins, bank, xp, level) VALUES (?, ?, ?, ?, ?, ?, ?)", (message.author.id, 0, 0, 0, 0, 0, 0))
      con.commit()
   cur.execute('UPDATE users SET messages = ? WHERE user_id = ?', (user[1] + 1, message.author.id))
   cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', (user[3] + randint(1, 5) * coins_multiplier, message.author.id))
   cur.execute('UPDATE users SET xp = ? WHERE user_id = ?', (user[5] + randint(5, 10) * xp_multiplier, message.author.id))
   con.commit()

   cur.execute('SELECT xp, level FROM users WHERE user_id = ?', (message.author.id,))
   xp, level = cur.fetchone()
   max_xp = round(level**1.2 * 200 + 1000)
   if xp >= max_xp:
      cur.execute('UPDATE users SET xp = ? WHERE user_id = ?', (xp - max_xp, message.author.id))
      cur.execute('UPDATE users SET level = ? WHERE user_id = ?', (level + 1, message.author.id))
      cur.execute('UPDATE users SET coins = ? WHERE user_id = ?', ((level * 500 + 1000) * coins_multiplier, message.author.id))
      con.commit()
      embed = discord.Embed(title="Bravo nouveau niveau", description=f"{message.author.mention} vous êtes passé niveau {level + 1} ! Et vous gagner {(level * 500 + 1000) * coins_multiplier} coins !", color=0xff0000)
      await message.channel.send(embed=embed)



   cur.execute('SELECT * FROM blacklist')
   blacklists = cur.fetchall()
   for blacklist in blacklists:
      if blacklist[1] == message.author.id:
         await message.author.ban(reason="Membre blacklist")
         return


   cur.execute('SELECT * FROM whitelist')
   blacklists = cur.fetchall()
   for blacklist in blacklists:
      if blacklist[1] == message.author.id:
         return

   cur.execute('SELECT * FROM config WHERE env = ?', ("anti link",))
   anti_link = cur.fetchone()
   if anti_link[1] == "True":
      if link_regex.search(message.content):
         await message.delete()
         await message.channel.send(f"{message.author.mention}, les liens ne sont pas autorisés ici.")
      
   cur.execute('SELECT * FROM config WHERE env = ?', ("anti spam",))
   anti_spam = cur.fetchone()
   if anti_spam[1] == "True":
      message_count[message.author.id] += 1
      if message_count[message.author.id] > spam_limit:
         await message.delete()

         if message.author.id not in spamming_users:
            spamming_users.add(message.author.id)
            await message.channel.send(f"{message.author.mention} Vous envoyez des messages trop rapidement. Merci de patienter.")
            await message.author.send("Vous envoyez des messages trop rapidement. Merci de patienter.")
            await asyncio.sleep(spam_interval)
            spamming_users.remove(message.author.id)

      await asyncio.sleep(spam_interval)
      message_count[message.author.id] = 0


   cur.execute('SELECT * FROM badwords')
   badwords = cur.fetchall()
   for badword in badwords:
      if badword[1] in message.content:
         cur.execute('UPDATE badwords SET utilisation = ? WHERE badword = ?', (badword[2] + 1, badword[1]))
         con.commit()
         cur.execute('''
            INSERT INTO warns (user_id, moderator_id, reason)
            VALUES (?, ?, ?)
         ''', (message.author.id, bot.user.id, f"Utilisation du mot {badword[1]}"))
         con.commit()
         await message.delete()
         await message.author.send(f"Vous avez été averti sur le serveur {message.guild.name} pour avoir utilisé le mot {badword[1]}")
         await message.channel.send(f"{message.author.mention} a été averti pour avoir utilisé le mot {badword[1]}")
         return



@bot.event
async def on_presence_update(before, after):
   con, cur = choose_db(after.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("ROLE_ACTIVITY",))
   role_activity_id = cur.fetchone()[1]
   cur.execute('SELECT * FROM config WHERE env = ?', ("ACTIVITY_FOR_ROLE",))
   activity_for_role = cur.fetchone()[1]
   if role_activity_id == "None" or activity_for_role == "None":
      return

   role_activity = after.guild.get_role(int(role_activity_id))
   if after.activity and activity_for_role in after.activity.name:
      if role_activity:
         await after.add_roles(role_activity)
   else:
      if role_activity:
         await after.remove_roles(role_activity)



@bot.event
async def on_message_delete(message):
   sniped_messages[message.channel.id] = message


   con, cur = choose_db(message.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_MESSAGE",))
   log_message = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_message[1]))
   except:
      return

   embed = discord.Embed(title="Message supprimé", color=0xff0000)
   embed.add_field(name="Message auteur", value=message.author.mention, inline=False)
   embed.add_field(name="Channel", value=message.channel.mention, inline=False)
   embed.add_field(name="Date", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
   embed.add_field(name="Message", value=f"`{message.content}`", inline=False)
   embed.add_field(name="ID", value=f"```py\nMessage_ID = {message.id}\nAuthor_ID = {message.author.id}\nChannel_ID = {message.channel.id}```", inline=False)
   if message.author.avatar:
      embed.set_author(name=message.author.name, icon_url=message.author.avatar.url)
      embed.set_thumbnail(url=message.author.avatar.url)
   else:
      default_avatar_url = message.author.default_avatar.url
      embed.set_author(name=message.author.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   embed.set_footer(text="Log message supprimé")
   await log_channel.send(embed=embed)
   


class MessageLinkButton(discord.ui.Button):
    def __init__(self, url: str):
      super().__init__(style=discord.ButtonStyle.link, url=url, label="Aller au message")


@bot.event
async def on_message_edit(before, after):
   if before.content == after.content:
      return
   
   con, cur = choose_db(before.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_MESSAGE",))
   log_message = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_message[1]))
   except:
      return

   embed = discord.Embed(title="Message édité", color=0xff0000)
   embed.add_field(name="Message auteur", value=before.author.mention, inline=False)
   embed.add_field(name="Channel", value=before.channel.mention, inline=False)
   embed.add_field(name="Date", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
   embed.add_field(name="Message avant l'édition", value=f"`{before.content}`", inline=False)
   embed.add_field(name="Message après l'édition", value=f"`{after.content}`", inline=False)
   embed.add_field(name="Message ID", value=f"```py\nMessage_ID = {after.id}\nAuthor_ID = {after.author.id}\nChannel_ID = {after.channel.id}```", inline=False)
   if after.author.avatar:
      embed.set_author(name=after.author.name, icon_url=after.author.avatar.url)
      embed.set_thumbnail(url=after.author.avatar.url)
   else:
      default_avatar_url = after.author.default_avatar.url
      embed.set_author(name=after.author.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   embed.set_footer(text="Log message édité")
   
   message_link = f"https://discord.com/channels/{after.guild.id}/{after.channel.id}/{after.id}"
   button = MessageLinkButton(url=message_link)
   view = discord.ui.View()
   view.add_item(button)
   await log_channel.send(embed=embed, view=view)



@bot.event
async def on_member_join(member):
   con, cur = choose_db(member.guild.id)
   cur.execute('SELECT * FROM users WHERE user_id = ?', (member.id,))
   user = cur.fetchone()
   if user is None:
      cur.execute("INSERT INTO users (user_id, messages, voice, coins, bank, xp, level) VALUES (?, ?, ?, ?, ?, ?, ?)", (member.id, 0, 0, 0, 0, 0, 0))
      con.commit()

   cur.execute('SELECT * FROM blacklist')
   blacklists = cur.fetchall()
   for blacklist in blacklists:
      if blacklist[1] == member.id:
         await member.ban(reason="Membre blacklist")
         return
      

   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_JOIN_LEAVE",))
   log_join_leave = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_join_leave[1]))
   except:
      return

   embed = discord.Embed(title="Membre rejoint", color=0xff0000)
   embed.add_field(name="Membre", value=member.mention, inline=False)
   embed.add_field(name="Date de création du compte", value=f"<t:{round(member.created_at.timestamp())}:F>", inline=False)
   embed.add_field(name="Date d'arrivée sur le serveur", value=f"<t:{round(member.joined_at.timestamp())}:F>", inline=False)
   embed.add_field(name="ID", value=f"```py\nMember_ID = {member.id}```", inline=False)
   if member.avatar:
      embed.set_author(name=member.name, icon_url=member.avatar.url)
      embed.set_thumbnail(url=member.avatar.url)
   else:
      default_avatar_url = member.default_avatar.url
      embed.set_author(name=member.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   embed.set_footer(text="Log membre rejoint")
   await log_channel.send(embed=embed)


   con, cur = choose_db(member.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("CHANNEL_JOIN",))
   log_join_leave = cur.fetchone()
   try:
      channel_join = bot.get_channel(int(log_join_leave[1]))
   except:
      return

   embed = discord.Embed(title=f"Bienvenue {member.name} ! \nNous sommes {member.guild.member_count} sur le serveur", color=randint(0, 0xffffff))
   if member.avatar:
      embed.set_author(name=member.name, icon_url=member.avatar.url)
      embed.set_thumbnail(url=member.avatar.url)
   else:
      default_avatar_url = member.default_avatar.url
      embed.set_author(name=member.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await channel_join.send(embed=embed)

   

@bot.event
async def on_member_remove(member):
   con, cur = choose_db(member.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_JOIN_LEAVE",))
   log_join_leave = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_join_leave[1]))
   except:
      return

   embed = discord.Embed(title="Membre quitté", color=0xff0000)
   embed.add_field(name="Membre", value=member.mention, inline=False)
   embed.add_field(name="Date de création du compte", value=f"<t:{round(member.created_at.timestamp())}:F>", inline=False)
   embed.add_field(name="Date d'arrivée sur le serveur", value=f"<t:{round(member.joined_at.timestamp())}:F>", inline=False)
   embed.add_field(name="Date de départ du serveur", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
   embed.add_field(name="ID", value=f"```py\nMember_ID = {member.id}```", inline=False)
   if member.avatar:
      embed.set_author(name=member.name, icon_url=member.avatar.url)
      embed.set_thumbnail(url=member.avatar.url)
   else:
      default_avatar_url = member.default_avatar.url
      embed.set_author(name=member.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   embed.set_footer(text="Log membre quitté")
   await log_channel.send(embed=embed)


   con, cur = choose_db(member.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("CHANNEL_LEAVE",))
   log_join_leave = cur.fetchone()
   try:
      channel_leave = bot.get_channel(int(log_join_leave[1]))
   except:
      return

   embed = discord.Embed(title=f"Au revoir {member.name} ! \nNous sommes {member.guild.member_count} sur le serveur", color=randint(0, 0xffffff))
   if member.avatar:
      embed.set_author(name=member.name, icon_url=member.avatar.url)
      embed.set_thumbnail(url=member.avatar.url)
   else:
      default_avatar_url = member.default_avatar.url
      embed.set_author(name=member.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   await channel_leave.send(embed=embed)



@bot.event
async def on_member_ban(guild, user):
   con, cur = choose_db(guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_MODERATION",))
   log_moderation = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_moderation[1]))
   except:
      return

   embed = discord.Embed(title="Membre banni", color=0xff0000)
   embed.add_field(name="Membre", value=user.mention, inline=False)
   embed.add_field(name="Date du ban", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
   embed.add_field(name="Date de création du compte", value=f"<t:{round(user.created_at.timestamp())}:F>", inline=False)
   embed.add_field(name="Date d'arrivée sur le serveur", value=f"<t:{round(user.joined_at.timestamp())}:F>", inline=False)
   async for entry in guild.audit_logs(action=discord.AuditLogAction.ban):
      if entry.target == user:
         embed.add_field(name="Raison du bannissement", value=entry.reason, inline=False)
         break
      else:
         embed.add_field(name="Raison du bannissement", value="Aucune raison donnée", inline=False)
         break
   embed.add_field(name="ID", value=f"```py\nMember_ID = {user.id}```", inline=False)
   if user.avatar:
      embed.set_author(name=user.name, icon_url=user.avatar.url)
      embed.set_thumbnail(url=user.avatar.url)
   else:
      default_avatar_url = user.default_avatar.url
      embed.set_author(name=user.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   embed.set_footer(text="Log membre banni")
   await log_channel.send(embed=embed)



@bot.event
async def on_member_unban(guild, user):
   con, cur = choose_db(guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_MODERATION",))
   log_moderation = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_moderation[1]))
   except:
      return

   embed = discord.Embed(title="Membre débanni", color=0xff0000)
   embed.add_field(name="Membre", value=user.mention, inline=False)
   embed.add_field(name="Date du déban", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
   embed.add_field(name="Date de création du compte", value=f"<t:{round(user.created_at.timestamp())}:F>", inline=False)
   async for entry in guild.audit_logs(action=discord.AuditLogAction.unban):
      if entry.target == user:
         embed.add_field(name="Raison du débannissement", value=entry.reason, inline=False)
         break
      else:
         embed.add_field(name="Raison du débannissement", value="Aucune raison donnée", inline=False)
         break
   embed.add_field(name="ID", value=f"```py\nMember_ID = {user.id}```", inline=False)
   if user.avatar:
      embed.set_author(name=user.name, icon_url=user.avatar.url)
      embed.set_thumbnail(url=user.avatar.url)
   else:
      default_avatar_url = user.default_avatar.url
      embed.set_author(name=user.name, icon_url=default_avatar_url)
      embed.set_thumbnail(url=default_avatar_url)
   embed.set_footer(text="Log membre débanni")
   await log_channel.send(embed=embed)



@bot.event
async def on_member_update(before, after):
   con, cur = choose_db(after.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("ROLE_BOOST",))
   role_boost_id = cur.fetchone()
   try:
      role_boost = bot.get_role(int(role_boost_id[1]))
      if before.premium_since != after.premium_since and after.premium_since is not None:
         if role_boost:
            await after.add_roles(role_boost)
      elif before.premium_since != after.premium_since and after.premium_since is None:
         if role_boost:
            await after.remove_roles(role_boost)
   except:
      pass

   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_ROLE",))
   log_role = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_role[1]))
   except:
      return
   if before.roles != after.roles:
      embed = discord.Embed(title="Membre rôle modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      if len(before.roles) < len(after.roles):
         embed.add_field(name="Rôles ajouté", value='\n'.join([f"{role.mention}" for role in after.roles if role not in before.roles]), inline=False)
      elif len(before.roles) > len(after.roles):
         embed.add_field(name="Rôles retiré", value='\n'.join([f"{role.mention}" for role in before.roles if role not in after.roles]), inline=False)
      async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_role_update):
         if entry.target == after:
            embed.add_field(name="ajouter/retirer par", value=entry.user.mention, inline=False)
            break
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log membre rôle modifié")
      await log_channel.send(embed=embed)


   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_MEMBER_UPDATE",))
   log_member_update = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_member_update[1]))
   except:
      return

   if before.nick != after.nick:
      embed = discord.Embed(title="Membre pseudo modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Pseudo avant la modification", value=f"`{before.nick}`", inline=False)
      embed.add_field(name="Pseudo après la modification", value=f"`{after.nick}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log membre pseudo modifié")
      await log_channel.send(embed=embed)

   if before.avatar != after.avatar:
      embed = discord.Embed(title="Membre avatar modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Avatar avant la modification", value=f"[Lien]({before.avatar.url})", inline=False)
      embed.add_field(name="Avatar après la modification", value=f"[Lien]({after.avatar.url})", inline=False)
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log membre avatar modifié")
      await log_channel.send(embed=embed)

   if before.activity != after.activity:
      embed = discord.Embed(title="Membre activité modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Activité avant la modification", value=f"`{before.activity}`", inline=False)
      embed.add_field(name="Activité après la modification", value=f"`{after.activity}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log membre activité modifié")
      await log_channel.send(embed=embed)

   if before.status != after.status:
      embed = discord.Embed(title="Membre status modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Status avant la modification", value=f"`{before.status}`", inline=False)
      embed.add_field(name="Status après la modification", value=f"`{after.status}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log membre status modifié")
      await log_channel.send(embed=embed)

   if before.pending != after.pending:
      embed = discord.Embed(title="Membre pending modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Pending avant la modification", value=f"`{before.pending}`", inline=False)
      embed.add_field(name="Pending après la modification", value=f"`{after.pending}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log membre pending modifié")
      await log_channel.send(embed=embed)

   if before.premium_since != after.premium_since:
      embed = discord.Embed(title="Membre boost modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Boost avant la modification", value=f"`{before.premium_since}`", inline=False)
      embed.add_field(name="Boost après la modification", value=f"`{after.premium_since}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log membre boost modifié")
      await log_channel.send(embed=embed)

   if before.is_on_mobile() != after.is_on_mobile():
      embed = discord.Embed(title="Membre mobile modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Mobile avant la modification", value=f"`{before.is_on_mobile()}`", inline=False)
      embed.add_field(name="Mobile après la modification", value=f"`{after.is_on_mobile()}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log membre mobile modifié")
      await log_channel.send(embed=embed)

   if before.desktop_status != after.desktop_status:
      embed = discord.Embed(title="Membre desktop status modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Desktop status avant la modification", value=f"`{before.desktop_status}`", inline=False)
      embed.add_field(name="Desktop status après la modification", value=f"`{after.desktop_status}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log membre desktop status modifié")
      await log_channel.send(embed=embed)

   if before.mobile_status != after.mobile_status:
      embed = discord.Embed(title="Membre mobile status modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Mobile status avant la modification", value=f"`{before.mobile_status}`", inline=False)
      embed.add_field(name="Mobile status après la modification", value=f"`{after.mobile_status}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log membre mobile status modifié")
      await log_channel.send(embed=embed)

   if before.web_status != after.web_status:
      embed = discord.Embed(title="Membre web status modifié", color=0xff0000)
      embed.add_field(name="Membre", value=after.mention, inline=False)
      embed.add_field(name="Web status avant la modification", value=f"`{before.web_status}`", inline=False)
      embed.add_field(name="Web status après la modification", value=f"`{after.web_status}`", inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="ID", value=f"```py\nMember_ID = {after.id}```", inline=False)
      if after.avatar:
         embed.set_author(name=after.name, icon_url=after.avatar.url)
         embed.set_thumbnail(url=after.avatar.url)
      else:
         default_avatar_url = after.default_avatar.url
         embed.set_author(name=after.name, icon_url=default_avatar_url)
         embed.set_thumbnail(url=default_avatar_url)
      embed.set_footer(text="Log web status modifié")
      await log_channel.send(embed=embed)

   

@bot.event
async def on_guild_channel_create(channel):
   con, cur = choose_db(channel.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_CHANNEL",))
   log_channel = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_channel[1]))
   except:
      return

   embed = discord.Embed(title="Channel créé", color=0xff0000)
   embed.add_field(name="Channel", value=channel.mention, inline=False)
   embed.add_field(name="Date de création", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
   embed.add_field(name="Type de channel", value=f"`{channel.type}`", inline=False)
   embed.add_field(name="Position", value=channel.position, inline=False)
   embed.add_field(name="Catégorie", value=channel.category, inline=False)
   async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create):
      if entry.target == channel:
         embed.add_field(name="Créateur", value=entry.user.mention, inline=False)
         break
      else:
         embed.add_field(name="Créateur", value="Aucun créateur trouvé", inline=False)
         break
   embed.add_field(name="ID", value=f"```py\nChannel_ID = {channel.id}```", inline=False)
   embed.set_author(name=channel.name, icon_url=channel.guild.icon.url)
   embed.set_thumbnail(url=channel.guild.icon.url)
   embed.set_footer(text="Log channel créé")
   await log_channel.send(embed=embed)



@bot.event
async def on_guild_channel_delete(channel):
   con, cur = choose_db(channel.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_CHANNEL",))
   log_channel = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_channel[1]))
   except:
      return

   embed = discord.Embed(title="Channel supprimé", color=0xff0000)
   embed.add_field(name="Channel", value=channel.mention, inline=False)
   embed.add_field(name="Date de suppression", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
   embed.add_field(name="Type de channel", value=f"`{channel.type}`", inline=False)
   embed.add_field(name="Position", value=channel.position, inline=False)
   embed.add_field(name="Catégorie", value=channel.category, inline=False)
   async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete):
      if entry.target == channel:
         embed.add_field(name="Supprimeur", value=entry.user.mention, inline=False)
         break
      else:
         embed.add_field(name="Supprimeur", value="Aucun supprimeur trouvé", inline=False)
         break
   embed.add_field(name="ID", value=f"```py\nChannel_ID = {channel.id}```", inline=False)
   embed.set_author(name=channel.name, icon_url=channel.guild.icon.url)
   embed.set_thumbnail(url=channel.guild.icon.url)
   embed.set_footer(text="Log channel supprimé")
   await log_channel.send(embed=embed)



@bot.event
async def on_guild_channel_update(before, after):
   con, cur = choose_db(after.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_CHANNEL",))
   log_channel = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_channel[1]))
   except:
      return

   if before.name != after.name:
      embed = discord.Embed(title="Channel nom modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Nom avant la modification", value=f"`{before.name}`", inline=False)
      embed.add_field(name="Nom après la modification", value=f"`{after.name}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel nom modifié")
      await log_channel.send(embed=embed)

   if before.type != after.type:
      embed = discord.Embed(title="Channel type modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Type avant la modification", value=f"`{before.type}`", inline=False)
      embed.add_field(name="Type après la modification", value=f"`{after.type}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel type modifié")
      await log_channel.send(embed=embed)

   if before.position != after.position:
      embed = discord.Embed(title="Channel position modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Position avant la modification", value=f"`{before.position}`", inline=False)
      embed.add_field(name="Position après la modification", value=f"`{after.position}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel position modifié")
      await log_channel.send(embed=embed)
   
   if before.category != after.category:
      embed = discord.Embed(title="Channel catégorie modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Catégorie avant la modification", value=f"`{before.category}`", inline=False)
      embed.add_field(name="Catégorie après la modification", value=f"`{after.category}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel catégorie modifié")
      await log_channel.send(embed=embed)

   if before.is_nsfw() != after.is_nsfw():
      embed = discord.Embed(title="Channel nsfw modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="Nsfw avant la modification", value=f"`{before.is_nsfw()}`", inline=False)
      embed.add_field(name="Nsfw après la modification", value=f"`{after.is_nsfw()}`", inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel nsfw modifié")
      await log_channel.send(embed=embed)

   if before.slowmode_delay != after.slowmode_delay:
      embed = discord.Embed(title="Channel slowmode delay modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="Slowmode delay avant la modification", value=f"`{before.slowmode_delay}`", inline=False)
      embed.add_field(name="Slowmode delay après la modification", value=f"`{after.slowmode_delay}`", inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel slowmode delay modifié")
      await log_channel.send(embed=embed)

   if isinstance(after, discord.VoiceChannel) and before.bitrate != after.bitrate:
      embed = discord.Embed(title="Channel bitrate modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="Bitrate avant la modification", value=f"`{before.bitrate}`", inline=False)
      embed.add_field(name="Bitrate après la modification", value=f"`{after.bitrate}`", inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)      
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel bitrate modifié")
      await log_channel.send(embed=embed)

   if isinstance(after, discord.VoiceChannel) and before.user_limit != after.user_limit:
      embed = discord.Embed(title="Channel user limit modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="User limit avant la modification", value=f"`{before.user_limit}`", inline=False)
      embed.add_field(name="User limit après la modification", value=f"`{after.user_limit}`", inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)      
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)      
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel user limit modifié")
      await log_channel.send(embed=embed)

   if isinstance(after, discord.VoiceChannel) and before.rtc_region != after.rtc_region:
      embed = discord.Embed(title="Channel rtc region modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="Rtc region avant la modification", value=f"`{before.rtc_region}`", inline=False)
      embed.add_field(name="Rtc region après la modification", value=f"`{after.rtc_region}`", inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)      
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)      
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel rtc region modifié")
      await log_channel.send(embed=embed)

   if isinstance(after, discord.VoiceChannel) and before.video_quality_mode != after.video_quality_mode:
      embed = discord.Embed(title="Channel video quality mode modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="Video quality mode avant la modification", value=f"`{before.video_quality_mode}`", inline=False)
      embed.add_field(name="Video quality mode après la modification", value=f"`{after.video_quality_mode}`", inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)      
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)      
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel video quality mode modifié")
      await log_channel.send(embed=embed)

   if before.permissions_synced != after.permissions_synced:
      embed = discord.Embed(title="Channel permissions synced modifié", color=0xff0000)
      embed.add_field(name="Channel", value=after.mention, inline=False)
      embed.add_field(name="Permissions synced avant la modification", value=f"`{before.permissions_synced}`", inline=False)
      embed.add_field(name="Permissions synced après la modification", value=f"`{after.permissions_synced}`", inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)      
      embed.add_field(name="ID", value=f"```py\nChannel_ID = {after.id}```", inline=False)      
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log channel permissions synced modifié")
      await log_channel.send(embed=embed)



@bot.event
async def on_guild_role_create(role):
   con, cur = choose_db(role.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_ROLE",))
   log_role = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_role[1]))
   except:
      return

   embed = discord.Embed(title="Rôle créé", color=0xff0000)
   embed.add_field(name="Rôle", value=role.mention, inline=False)
   embed.add_field(name="Date de création", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
   embed.add_field(name="Position", value=role.position, inline=False)
   embed.add_field(name="Couleur", value=role.color, inline=False)
   embed.add_field(name="Permissions", value=role.permissions, inline=False)
   embed.add_field(name="ID", value=f"```py\nRole_ID = {role.id}```", inline=False)
   embed.set_author(name=role.name, icon_url=role.guild.icon.url)
   embed.set_thumbnail(url=role.guild.icon.url)
   embed.set_footer(text="Log rôle créé")
   await log_channel.send(embed=embed)



@bot.event
async def on_guild_role_delete(role):
   con, cur = choose_db(role.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_ROLE",))
   log_role = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_role[1]))
   except:
      return

   embed = discord.Embed(title="Rôle supprimé", color=0xff0000)
   embed.add_field(name="Rôle", value=role.mention, inline=False)
   embed.add_field(name="Date de suppression", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
   embed.add_field(name="Position", value=role.position, inline=False)
   embed.add_field(name="Couleur", value=role.color, inline=False)
   embed.add_field(name="Permissions", value=role.permissions, inline=False)
   embed.add_field(name="ID", value=f"```py\nRole_ID = {role.id}```", inline=False)
   embed.set_author(name=role.name, icon_url=role.guild.icon.url)
   embed.set_thumbnail(url=role.guild.icon.url)
   embed.set_footer(text="Log rôle supprimé")
   await log_channel.send(embed=embed)



@bot.event
async def on_guild_role_update(before, after):
   con, cur = choose_db(after.guild.id)
   cur.execute('SELECT * FROM config WHERE env = ?', ("LOG_ROLE",))
   log_role = cur.fetchone()
   try:
      log_channel = bot.get_channel(int(log_role[1]))
   except:
      return

   if before.name != after.name:
      embed = discord.Embed(title="Rôle nom modifié", color=0xff0000)
      embed.add_field(name="Rôle", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Nom avant la modification", value=f"`{before.name}`", inline=False)
      embed.add_field(name="Nom après la modification", value=f"`{after.name}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nRole_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log rôle nom modifié")
      await log_channel.send(embed=embed)

   if before.position != after.position:
      embed = discord.Embed(title="Rôle position modifié", color=0xff0000)
      embed.add_field(name="Rôle", value=after.mention, inline=False)
      embed.add_field(name="Date de modification", value=f"<t:{round(datetime.now().timestamp())}:F>", inline=False)
      embed.add_field(name="Position avant la modification", value=f"`{before.position}`", inline=False)
      embed.add_field(name="Position après la modification", value=f"`{after.position}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nRole_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log rôle position modifié")
      await log_channel.send(embed=embed)

   if before.color != after.color:
      embed = discord.Embed(title="Rôle couleur modifié", color=0xff0000)
      embed.add_field(name="Rôle", value=after.mention, inline=False)
      embed.add_field(name="Couleur avant la modification", value=f"`{before.color}`", inline=False)
      embed.add_field(name="Couleur après la modification", value=f"`{after.color}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nRole_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log rôle couleur modifié")
      await log_channel.send(embed=embed)

   if before.hoist != after.hoist:
      embed = discord.Embed(title="Rôle hoist modifié", color=0xff0000)
      embed.add_field(name="Rôle", value=after.mention, inline=False)
      embed.add_field(name="Hoist avant la modification", value=f"`{before.hoist}`", inline=False)
      embed.add_field(name="Hoist après la modification", value=f"`{after.hoist}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nRole_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log rôle hoist modifié")
      await log_channel.send(embed=embed)

   if before.mentionable != after.mentionable:
      embed = discord.Embed(title="Rôle mentionable modifié", color=0xff0000)
      embed.add_field(name="Rôle", value=after.mention, inline=False)
      embed.add_field(name="Mentionable avant la modification", value=f"`{before.mentionable}`", inline=False)
      embed.add_field(name="Mentionable après la modification", value=f"`{after.mentionable}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nRole_ID = {after.id}```", inline=False)
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log rôle mentionable modifié")
      await log_channel.send(embed=embed)

   if before.managed != after.managed:
      embed = discord.Embed(title="Rôle managed modifié", color=0xff0000)
      embed.add_field(name="Rôle", value=after.mention, inline=False)
      embed.add_field(name="Managed avant la modification", value=f"`{before.managed}`", inline=False)
      embed.add_field(name="Managed après la modification", value=f"`{after.managed}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nRole_ID = {after.id}```", inline=False)      
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log rôle managed modifié")
      await log_channel.send(embed=embed)

   if before.mentionable != after.mentionable:
      embed = discord.Embed(title="Rôle mentionable modifié", color=0xff0000)
      embed.add_field(name="Rôle", value=after.mention, inline=False)
      embed.add_field(name="Mentionable avant la modification", value=f"`{before.mentionable}`", inline=False)
      embed.add_field(name="Mentionable après la modification", value=f"`{after.mentionable}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nRole_ID = {after.id}```", inline=False)      
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log rôle mentionable modifié")
      await log_channel.send(embed=embed)

   if before.permissions != after.permissions:
      embed = discord.Embed(title="Rôle permissions modifié", color=0xff0000)
      embed.add_field(name="Rôle", value=after.mention, inline=False)
      embed.add_field(name="Permissions avant la modification", value=f"`{before.permissions}`", inline=False)
      embed.add_field(name="Permissions après la modification", value=f"`{after.permissions}`", inline=False)
      embed.add_field(name="ID", value=f"```py\nRole_ID = {after.id}```", inline=False)      
      embed.set_author(name=after.name, icon_url=after.guild.icon.url)
      embed.set_thumbnail(url=after.guild.icon.url)
      embed.set_footer(text="Log rôle permissions modifié")
      await log_channel.send(embed=embed)

   

bot.run(os.getenv('TOKEN'))