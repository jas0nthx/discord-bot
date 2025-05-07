from dotenv import load_dotenv
import discord
from discord.ext import commands
import os
import json
import random

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.start()


load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# === File Load/Save ===
def load_json(filename):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        if filename == "market.json":
            return []  # Return empty list for market
        return {}  # Return empty dict for other files

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

users = load_json("users.json")
market = load_json("market.json")  # Will be [] if not exists
boost = load_json("boost.json") or {"multiplier": 1, "spins_left": 0}

# === Events ===
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# === Commands ===
@bot.command()
async def spin(ctx):
    allowed_channel_id = 1368871928961568779  # 🔁 Replace this with your real channel ID

    if ctx.channel.id != allowed_channel_id:
        await ctx.send(f"❌ You can only use `!spin` in <#{allowed_channel_id}>.")
        return
        
    user_id = str(ctx.author.id)
    
    # Initialize user data if not exists
    if user_id not in users:
        users[user_id] = {"credits": 0, "inventory": []}
        
    multiplier = boost.get("multiplier", 1)
    if boost.get("spins_left", 0) > 0:
        boost["spins_left"] -= 1
        if boost["spins_left"] == 0:
            boost["multiplier"] = 1
    save_json("boost.json", boost)

    # Weighted spin: rare big numbers
    roll = int(min(999_999_999_999_999_999_999_999_999, random.gammavariate(1.2 * multiplier, 50)))
    users[user_id]["credits"] += roll
    save_json("users.json", users)

    await ctx.send(f"🎰 {ctx.author.name} spun and got **{roll:,}** credits! 💰")

@bot.command()
async def sacrifice(ctx, amount: int):
    user_id = str(ctx.author.id)
    
    # Initialize user data if not exists
    if user_id not in users:
        users[user_id] = {"credits": 0, "inventory": []}
    
    if user_id not in users or users[user_id]["credits"] < amount or amount <= 0:
        await ctx.send("❌ Not enough credits to sacrifice.")
        return

    users[user_id]["credits"] -= amount
    boost["multiplier"] = 1 + amount // 1000
    boost["spins_left"] = 10
    save_json("users.json", users)
    save_json("boost.json", boost)

    await ctx.send(f"🔥 {ctx.author.name} sacrificed {amount:,} credits!\n"
                   f"➡️ Boost active! Multiplier: x{boost['multiplier']} for {boost['spins_left']} spins.")

@bot.command()
async def credits(ctx):
    user_id = str(ctx.author.id)
    
    # Initialize user data if not exists
    if user_id not in users:
        users[user_id] = {"credits": 0, "inventory": []}
        save_json("users.json", users)
        
    balance = users[user_id]["credits"]
    await ctx.send(f"💳 {ctx.author.name}, you have **{balance:,}** credits.")

@bot.command()
async def additem(ctx, name: str, price: int):
    banned_role_name = "Market Banned"
    if discord.utils.get(ctx.author.roles, name=banned_role_name):
        await ctx.send("🚫 You are not allowed to add items to the market.")
        return

    if price <= 0:
        await ctx.send("❌ Price must be greater than 0 credits.")
        return

    user_id = str(ctx.author.id)
    market.append({"name": name, "price": price, "seller": user_id})
    save_json("market.json", market)
    await ctx.send(f"🛒 Added '{name}' to the market for {price:,} credits.")

@bot.command()
async def marketlist(ctx):
    if not market:
        await ctx.send("🛍️ The market is empty!")
        return

    msg = "**🛍️ Market Listings:**\n"
    for i, item in enumerate(market, start=1):
        try:
            seller_name = await bot.fetch_user(int(item["seller"]))
            msg += f"{i}. {item['name']} - {item['price']:,} credits (by {seller_name.name})\n"
        except:
            msg += f"{i}. {item['name']} - {item['price']:,} credits (by unknown user)\n"
    await ctx.send(msg)

@bot.command()
async def buy(ctx, item_number: int):
    user_id = str(ctx.author.id)
    
    # Initialize user data if not exists
    if user_id not in users:
        users[user_id] = {"credits": 0, "inventory": []}
        
    if item_number < 1 or item_number > len(market):
        await ctx.send("❌ Invalid item number.")
        return

    item = market[item_number - 1]
    if users[user_id]["credits"] < item["price"]:
        await ctx.send("❌ You don't have enough credits.")
        return

    users[user_id]["credits"] -= item["price"]
    
    # Make sure inventory exists
    if "inventory" not in users[user_id]:
        users[user_id]["inventory"] = []
        
    users[user_id]["inventory"].append(item["name"])
    save_json("users.json", users)

    market.pop(item_number - 1)
    save_json("market.json", market)

    await ctx.send(f"✅ You bought **{item['name']}**!")

@bot.command()
async def removeitem(ctx, item_number: int):
    user_id = str(ctx.author.id)
    is_owner = str(ctx.author.id) == "859193969061920788"

    if item_number < 1 or item_number > len(market):
        await ctx.send("❌ Invalid item number.")
        return

    item = market[item_number - 1]
    if item["seller"] != user_id and not is_owner:
        await ctx.send("⛔ You can only remove your own items (unless you're the server owner).")
        return

    removed = market.pop(item_number - 1)
    save_json("market.json", market)

    await ctx.send(f"🗑️ Removed **{removed['name']}** from the market.")

@bot.command()
async def bonus(ctx, multiplier: int):
    author_id = str(ctx.author.id)
    if author_id != "859193969061920788":  # 👈 Replace this with your actual ID
        await ctx.send("⛔ Only the server owner can use this bonus.")
        return

    if multiplier <= 1:
        await ctx.send("❌ Multiplier must be greater than 1.")
        return

    boost["multiplier"] = multiplier
    boost["spins_left"] = 1
    save_json("boost.json", boost)

    await ctx.send(f"🎁 Bonus activated! Multiplier x{multiplier} for the **next spin only**!")

@bot.command()
async def gamble(ctx):
    allowed_channel_id = 1369554651627782214  # replace this with your spin-for-credits channel ID

    if ctx.channel.id != allowed_channel_id:
        await ctx.send(f"🚫 You can only use `!gamble` in <#{allowed_channel_id}>.")
        return

    user_id = str(ctx.author.id)
    users.setdefault(user_id, {"credits": 0, "inventory": []})

    await ctx.send(f"{ctx.author.mention}, how much would you like to gamble? Type the amount below:")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
        amount = int(msg.content)
    except:
        await ctx.send("⏰ You didn't reply in time with a valid number!")
        return

    balance = users[user_id]["credits"]
    if amount > balance or amount <= 0:
        await ctx.send(f"❌ Invalid amount. You have {balance} credits.")
        return

    import random
    if random.random() < 0.5:
        users[user_id]["credits"] += amount
        await ctx.send(f"🎉 {ctx.author.mention} gambled and **doubled** {amount} credits! You now have {users[user_id]['credits']}.")
    else:
        users[user_id]["credits"] -= amount
        await ctx.send(f"💀 {ctx.author.mention} lost it all... {amount} credits gone. You now have {users[user_id]['credits']}.")

    save_json("users.json", users)

@bot.command()
async def forcegamble(ctx, member: discord.Member, amount: int):
    owner_id = "859193969061920788"  # replace with your Discord ID
    if str(ctx.author.id) != owner_id:
        await ctx.send("⛔ Only the server owner can force others to gamble.")
        return

    user_id = str(member.id)
    users.setdefault(user_id, {"credits": 0, "inventory": []})

    if amount <= 0:
        await ctx.send("❌ Amount must be greater than 0.")
        return

    if users[user_id]["credits"] < amount:
        await ctx.send(f"❌ {member.display_name} doesn't have enough credits to gamble {amount}.")
        return

    import random
    if random.random() < 0.5:
        users[user_id]["credits"] += amount
        await ctx.send(f"🎲 {ctx.author.mention} forced {member.mention} to gamble and they **WON**! They now have {users[user_id]['credits']} credits.")
    else:
        users[user_id]["credits"] -= amount
        await ctx.send(f"💀 {ctx.author.mention} forced {member.mention} to gamble and they **LOST** {amount} credits. Balance: {users[user_id]['credits']}.")

    save_json("users.json", users)






@bot.command()
async def resetcredits(ctx, member: discord.Member):
    # ✅ Only allow YOU to run it
    author_id = str(ctx.author.id)
    if author_id != "859193969061920788":  # ← Replace with your ID
        await ctx.send("⛔ Only the server owner can use this command.")
        return

    user_id = str(member.id)
    if user_id not in users:
        users[user_id] = {"credits": 0, "inventory": []}
    else:
        users[user_id]["credits"] = 0

    save_json("users.json", users)
    await ctx.send(f"🧼 Reset {member.mention}'s credits to **0**.")

@bot.command()
async def resetboost(ctx):
    author_id = str(ctx.author.id)
    if author_id != "859193969061920788":  # 👈 Replace with your real ID
        await ctx.send("⛔ Only the server owner can reset the boost.")
        return

    boost["multiplier"] = 1
    boost["spins_left"] = 0
    save_json("boost.json", boost)

    await ctx.send("🧯 Boost has been manually reset.")

@bot.command()
async def addcredits(ctx, member: discord.Member, amount: int):
    author_id = str(ctx.author.id)
    if author_id != "859193969061920788":  # 👈 Replace with your Discord ID
        await ctx.send("⛔ Only the server owner can give credits.")
        return

    if amount <= 0:
        await ctx.send("❌ Amount must be greater than 0.")
        return

    user_id = str(member.id)
    if user_id not in users:
        users[user_id] = {"credits": 0, "inventory": []}

    users[user_id]["credits"] += amount
    save_json("users.json", users)

    await ctx.send(f"💸 Gave {member.mention} **{amount}** credits.")

@bot.command()
async def remcredits(ctx, member: discord.Member, amount: int):
    author_id = str(ctx.author.id)
    if author_id != "859193969061920788":  # 👈 Replace with your user ID
        await ctx.send("⛔ Only the server owner can remove credits.")
        return

    if amount <= 0:
        await ctx.send("❌ Amount must be greater than 0.")
        return

    user_id = str(member.id)
    if user_id not in users:
        users[user_id] = {"credits": 0, "inventory": []}

    users[user_id]["credits"] = max(users[user_id]["credits"] - amount, 0)
    save_json("users.json", users)

    await ctx.send(f"➖ Removed **{amount}** credits from {member.mention}. New balance: {users[user_id]['credits']:,}")

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)

    if sender_id == receiver_id:
        await ctx.send("❌ You can't pay yourself.")
        return

    if amount <= 0:
        await ctx.send("❌ Amount must be greater than 0.")
        return

    # Make sure both users exist
    if sender_id not in users:
        users[sender_id] = {"credits": 0, "inventory": []}
    if receiver_id not in users:
        users[receiver_id] = {"credits": 0, "inventory": []}

    if users[sender_id]["credits"] < amount:
        await ctx.send("❌ You don't have enough credits to send.")
        return

    users[sender_id]["credits"] -= amount
    users[receiver_id]["credits"] += amount
    save_json("users.json", users)

    await ctx.send(f"💸 {ctx.author.name} sent **{amount}** credits to {member.mention}!")





# Add a work command for making credits (popular economy command)
@bot.command()
async def work(ctx):
    allowed_channel_id = 1368871928961568779  # 🔁 replace with your spin-for-credits channel ID
    if ctx.channel.id != allowed_channel_id:
        await ctx.send(f"🚫 You can only use `!work` in <#{allowed_channel_id}>.")
        return

    user_id = str(ctx.author.id)
    
    # Initialize user data if not exists
    if user_id not in users:
        users[user_id] = {"credits": 0, "inventory": []}
    
    # Give a random amount between 50 and 200 credits
    earnings = random.randint(50, 200)
    users[user_id]["credits"] += earnings
    save_json("users.json", users)
    
    # List of possible work scenarios
    work_scenarios = [
        f"You worked at the coffee shop and earned **{earnings}** credits!",
        f"You helped someone fix their computer and earned **{earnings}** credits!",
        f"You walked dogs in the neighborhood and earned **{earnings}** credits!",
        f"You wrote some code for a client and earned **{earnings}** credits!",
        f"You sold some of your old stuff online and earned **{earnings}** credits!"
    ]
    
    await ctx.send(f"💼 {ctx.author.name}, {random.choice(work_scenarios)}")

# Command to see inventory
@bot.command()
async def inventory(ctx):
    user_id = str(ctx.author.id)
    
    # Initialize user data if not exists
    if user_id not in users:
        users[user_id] = {"credits": 0, "inventory": []}
        save_json("users.json", users)
    
    if not users[user_id]["inventory"]:
        await ctx.send(f"🎒 {ctx.author.name}, your inventory is empty!")
        return
        
    items = users[user_id]["inventory"]
    
    # Count occurrences of each item
    item_counts = {}
    for item in items:
        if item in item_counts:
            item_counts[item] += 1
        else:
            item_counts[item] = 1
    
    # Format the inventory message
    msg = f"🎒 **{ctx.author.name}'s Inventory:**\n"
    for item, count in item_counts.items():
        if count > 1:
            msg += f"• {item} (x{count})\n"
        else:
            msg += f"• {item}\n"
    
    await ctx.send(msg)

# Command to check leaderboard
@bot.command(aliases=["lb"])
async def leaderboard(ctx):
    if not users:
        await ctx.send("📊 No users on the leaderboard yet!")
        return
    
    # Sort users by credits
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("credits", 0), reverse=True)
    
    # Take top 10
    top_users = sorted_users[:10]
    
    msg = "📊 **Credits Leaderboard:**\n"
    for i, (user_id, data) in enumerate(top_users, start=1):
        try:
            user = await bot.fetch_user(int(user_id))
            msg += f"{i}. {user.name}: **{data.get('credits', 0):,}** credits\n"
        except:
            msg += f"{i}. Unknown User: **{data.get('credits', 0):,}** credits\n"
    
    await ctx.send(msg)

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))