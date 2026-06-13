import os

if os.getenv("DISABLE_BOT") == "true":
    print("Bot disattivato")
    exit()

import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

TOKEN ="MTUxNTM5MDAxNDM1ODQyNTczMw.GWzdG7.HVsow8wu7UfGYjnldy6-NjxGPcfdBR2QqR1R1I" 
# INTENTS
intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

# DATABASE
conn = sqlite3.connect("adamcoin.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    coins INTEGER DEFAULT 0
)
""")

conn.commit()


# DATABASE FUNCTIONS

def get_balance(user_id):
    cursor.execute(
        "SELECT coins FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()

    if result is None:
        cursor.execute(
            "INSERT INTO users (user_id, coins) VALUES (?, ?)",
            (user_id, 0)
        )
        conn.commit()
        return 0

    return result[0]


def add_coins(user_id, amount):
    balance = get_balance(user_id)

    cursor.execute(
        "UPDATE users SET coins = ? WHERE user_id = ?",
        (balance + amount, user_id)
    )

    conn.commit()


def remove_coins(user_id, amount):
    balance = get_balance(user_id)

    cursor.execute(
        "UPDATE users SET coins = ? WHERE user_id = ?",
        (balance - amount, user_id)
    )

    conn.commit()


# READY EVENT

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Comandi sincronizzati: {len(synced)}")
    except Exception as e:
        print(e)

    print(f"{bot.user} online!")


# ERROR HANDLER

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error
):
    print(error)

    if not interaction.response.is_done():
        await interaction.response.send_message(
            f"❌ Errore: {error}",
            ephemeral=True
        )


# BALANCE

@bot.tree.command(
    name="balance",
    description="Mostra il tuo saldo Adam Coin"
)
async def balance(interaction: discord.Interaction):

    saldo = get_balance(interaction.user.id)

    await interaction.response.send_message(
        f"💰 Hai **{saldo} Adam Coin**"
    )


# GIVE (SOLO ADMIN)

@bot.tree.command(
    name="give",
    description="Dai Adam Coin a un utente"
)
@app_commands.describe(
    utente="Utente che riceve",
    quantita="Quantità"
)
async def give(
    interaction: discord.Interaction,
    utente: discord.Member,
    quantita: int
):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Devi essere amministratore per usare questo comando.",
            ephemeral=True
        )
        return

    if quantita <= 0:
        await interaction.response.send_message(
            "❌ Quantità non valida.",
            ephemeral=True
        )
        return

    add_coins(utente.id, quantita)

    await interaction.response.send_message(
        f"✅ Hai dato **{quantita} Adam Coin** a {utente.mention}"
    )


# TRADE

@bot.tree.command(
    name="trade",
    description="Trasferisci Adam Coin ad un utente"
)
@app_commands.describe(
    utente="Utente che riceve",
    quantita="Quantità di Adam Coin"
)
async def trade(
    interaction: discord.Interaction,
    utente: discord.Member,
    quantita: int
):

    ruolo = discord.utils.get(
        interaction.user.roles,
        name="MEMBRO COMMUNITY"
    )

    if ruolo is None:
        await interaction.response.send_message(
            "❌ Devi avere il ruolo MEMBRO COMMUNITY.",
            ephemeral=True
        )
        return

    if quantita <= 0:
        await interaction.response.send_message(
            "❌ Quantità non valida.",
            ephemeral=True
        )
        return

    saldo = get_balance(interaction.user.id)

    if saldo < quantita:
        await interaction.response.send_message(
            "❌ Non hai abbastanza Adam Coin.",
            ephemeral=True
        )
        return

    remove_coins(
        interaction.user.id,
        quantita
    )

    add_coins(
        utente.id,
        quantita
    )

    await interaction.response.send_message(
        f"💸 Hai inviato **{quantita} Adam Coin** a {utente.mention}"
    )


# 🧨 NUOVO COMANDO: REMOVE

@bot.tree.command(
    name="remove",
    description="Rimuovi Adam Coin a un utente (solo admin)"
)
@app_commands.describe(
    utente="Utente a cui rimuovere i coin",
    quantita="Quantità da rimuovere"
)
async def remove(
    interaction: discord.Interaction,
    utente: discord.Member,
    quantita: int
):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Devi essere amministratore per usare questo comando.",
            ephemeral=True
        )
        return

    if quantita <= 0:
        await interaction.response.send_message(
            "❌ Quantità non valida.",
            ephemeral=True
        )
        return

    saldo = get_balance(utente.id)

    if saldo < quantita:
        await interaction.response.send_message(
            "❌ L'utente non ha abbastanza Dig Coin.",
            ephemeral=True
        )
        return

    remove_coins(utente.id, quantita)

    await interaction.response.send_message(
        f"🧨 Hai rimosso **{quantita} Adam Coin** a {utente.mention}"
    )
# LEADERBOARD

@bot.tree.command(
    name="leaderboard",
    description="Classifica Adam Coin"
)
async def leaderboard(interaction: discord.Interaction):

    cursor.execute("""
        SELECT user_id, coins
        FROM users
        ORDER BY coins DESC
        LIMIT 10
    """)

    rows = cursor.fetchall()

    if not rows:
        await interaction.response.send_message(
            "Nessun dato disponibile."
        )
        return

    testo = "🏆 **CLASSIFICA ADAM COIN**\n\n"

    for posizione, (uid, coins) in enumerate(rows, start=1):
        testo += f"{posizione}. <@{uid}> - {coins} DC\n"

    await interaction.response.send_message(testo)


# AVVIO BOT
bot.run(TOKEN)
