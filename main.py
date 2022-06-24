import discord
import json
import os
import asyncio
import time
import random
import copy
import codecs
import discord.ext
from discord.ext import commands
import shared



"""

GLOBAL RESOURCES

"""

CURRENT_DIR = os.getcwd()

IMAGE_DIR = f"{CURRENT_DIR}/card_gen/"
JSON_DIR=f"{CURRENT_DIR}/bot_data/"
MII_DIR=f"{CURRENT_DIR}/miis/"

ADMINS={
    "Maxi": 313434926219264000,
    "Fear": 683193773055934474
}

emojis = {
    "1": "1\ufe0f\N{COMBINING ENCLOSING KEYCAP}",
    "2": "2\ufe0f\N{COMBINING ENCLOSING KEYCAP}",
    "3": "3\ufe0f\N{COMBINING ENCLOSING KEYCAP}",
    "No Stars": "\u2606\u2606\u2606\u2606",
    "One Star": "\u2606\u2606\u2606\u2606",
    "Two Stars": "\u2606\u2606\u2606\u2606",
    "Three Stars": "\u2606\u2606\u2606\u2606",
    "Four Stars": "\u2606\u2606\u2606\u2606",
    "Left Arrow": "\N{LEFTWARDS BLACK ARROW}",
    "Right Arrow": "\N{BLACK RIGHTWARDS ARROW}",
    "Cash": "\N{MONEY WITH WINGS}",
    "Red X": "\N{CROSS MARK}",
    "Fire": "\N{FIRE}",
    "Check": "\N{WHITE HEAVY CHECK MARK}",
    "Conditions": ["\u2606\u2606\u2606\u2606","\u2605\u2606\u2606\u2606","\u2605\u2605\u2606\u2606","\u2605\u2605\u2605\u2606","\u2605\u2605\u2605\u2605",],
    "Black Square": "\N{BLACK MEDIUM SMALL SQUARE}"
  }


"""

JSON LOADING

"""

with codecs.open(f'{JSON_DIR}prints.json', encoding='utf-8') as f:
    prints = json.load(f)

with codecs.open(f'{JSON_DIR}accounts.json', encoding='utf-8') as f:
    accounts = json.load(f)

with codecs.open(f'{JSON_DIR}shop.json', encoding='utf-8') as f:
    itemshop = json.load(f)

with codecs.open(f'{JSON_DIR}friendcodes.json', encoding='utf-8') as f:
    fcs = json.load(f)

for object in [prints, accounts, itemshop, fcs]:
  json.dumps(object, ensure_ascii=False, indent=2, separators=(',', ': '))

bot = commands.Bot(command_prefix=['m','M'], help_command=None, case_insensitive=True) #The original karuta bot uses letters, so i'm keeping them for now.

"""

HELPER FUNCTIONS

"""
class HelperFunctions:

    #Creates a new entry in accounts.json
    def create_account(user_id):
        """
        0 Grab time
        1 Drop time
        2 Daily time
        3 Card Collection
        4 inventory
        5 Money (Dollas)
        6 Collection Tags
        """
        accounts[str(user_id)] = [time.time()-700, time.time()-2000, time.time()-90000,[], [], 0]
        HelperFunctions.dump_accounts()

    def dump_accounts():
        with codecs.open(f'{JSON_DIR}accounts.json', 'w', encoding='utf-8') as json_file:
            json.dump(accounts, json_file, ensure_ascii=False, indent=2, separators=(',', ': '))

    def dump_prints():
        with codecs.open(f'{JSON_DIR}prints.json', 'w', encoding='utf-8') as json_file:
            json.dump(prints, json_file, ensure_ascii=False, indent=2, separators=(',', ': '))

class DropFunctions:
    #Drop command helper that adds 3 number emojis to the given message.
    async def add_reactions(message):
        await message.add_reaction(emojis["1"])
        await message.add_reaction(emojis["2"])
        await message.add_reaction(emojis["3"])
        return

    #Drop command helper that waits for users to react to the drop message
    async def wait_for_grabs(dropmessage, author, cards):
        availablegrabs = [emojis["1"], emojis["2"], emojis["3"]]
        nograbs = [] #adds user if the user is on cooldown

        def check(reaction, user):
            return user != dropmessage.author and reaction.message == dropmessage and reaction.emoji in availablegrabs

        while len(availablegrabs) > 0:

            reaction, user = await bot.wait_for('reaction_add', check=check)
            user_id = str(user.id)

            if not user_id in accounts.keys():
                HelperFunctions.create_account(user_id)

            if time.time() - accounts[user_id][0] < 60:
                if not user in nograbs:
                    nograbs.append(user) ##user only gets cooldown message once
                    wait_time = time.strftime("%M minutes %S seconds", time.gmtime(60 - (time.time() - accounts[user_id][0])))
                    await dropmessage.channel.send(f"{user.mention}, you must wait ``{wait_time}`` to grab again.")
                continue

            if reaction.emoji == emojis["1"]:
                task = asyncio.create_task(DropFunctions.grab_card(reaction, author, cards[0], user))
                availablegrabs.remove(emojis["1"])

            elif reaction.emoji == emojis["2"]:
                task = asyncio.create_task(DropFunctions.grab_card(reaction, author, cards[1], user))
                availablegrabs.remove(emojis["2"])

            else:
                task = asyncio.create_task(DropFunctions.grab_card(reaction, author, cards[2], user))
                availablegrabs.remove(emojis["3"])

    #Drop command helper that waits for users to submit reactions, and chooses a user to win it.
    async def grab_card(reaction, author, card, initiator):
        users = await DropFunctions.collect_reactions(reaction)
        users.append(initiator)

        quality_message = ["Unfortunately, its condition is badly **damaged**.", "Unfortuntely, its condition is quite **poor**.",
                           "It's in **good** condition.", "Great, it's in **excellent** condition!", "Wow, it appears to be in **mint** condition!"]
        quality = random.choice([0,1,1,2,2,2,2,3,3,4])
        card[6] = quality

        competitors = []
        msg = []

        for user in users:
            if user.bot == True:
                continue
            user_id = str(user.id)
            if not user_id in accounts.keys():
                HelperFunctions.create_account(user_id)
            if time.time() - accounts[user_id][0] >= 60:
                accounts[user_id][0] = time.time()
                competitors.append(user)
            else:
                wait_time = time.strftime("%M minutes %S seconds", time.gmtime(60 - (time.time() - accounts[user_id][0])))
                msg.append(f"{user.mention}, you must wait ``{wait_time}`` to grab again.")

        if len(competitors) == 0:
            await reaction.message.channel.send("This is an error: 0 reactions found somehow wtf")
            return
        elif len(competitors) == 1:
            winner = users[0]
            award_message = f"{winner.mention} grabbed **{card[1]}** card ``{card[0]}``! {quality_message[quality]}"
        elif len(competitors) == 2:
            if author in competitors:
                competitors.remove(author)
                winner = author
                loser = competitors[0]
            else:
                random.shuffle(competitors)
                winner = competitors[0]
                loser = competitors[1]
            award_message = f"{winner.mention} fought off {loser.mention} and took the **{card[1]}** card ``{card[0]}``! {quality_message[quality]}"
        else:
            if author in competitors:
                winner = author
            else:
                random.shuffle(competitors)
                winner = competitors[0]
            award_message = f"{winner.mention} fought off {len(competitors) - 1} others and took the **{card[1]}** card ``{card[0]}``! {quality_message[quality]}"

        accounts[str(winner.id)][3].append(card)

        if msg:
            msg.append(award_message)
            msg.reverse()
            msg = "\n".join()
        else:
            msg = award_message

        await reaction.message.channel.send(msg)
        HelperFunctions.dump_accounts()
        return

    async def collect_reactions(og_reaction):
        def check(reaction, user):
            return reaction.message == og_reaction.message and reaction.emoji == og_reaction.emoji

        users = []
        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', check=check, timeout = 2)
            except asyncio.TimeoutError:
                return users
            users.append(user)


"""

USER COMMANDS

"""

# This command generates 3 new cards and merges them into one image (drop.png)
# Then, it adds 3 numbered reactions for which anyone can react to and "grab" the corresponding card.
# Both drop and grab have their own cooldowns, wherein users must wait to perform these actions
@commands.cooldown(1, 5, commands.BucketType.user)
@bot.command(aliases=["d"])
async def drop(ctx):
    str_author_id = str(ctx.author.id)
    mention_author = ctx.author.mention
    drop_cooldown = 300
    if not str_author_id in accounts.keys():
        HelperFunctions.create_account(str_author_id)

    user_drop_cooldown = drop_cooldown - (time.time() - accounts[str_author_id][1])
    if user_drop_cooldown > 0: #check drop cooldown
        wait_time = time.strftime("%M minutes %S seconds", time.gmtime(user_drop_cooldown))
        await ctx.send(f"{mention_author}, you must wait ``{wait_time}`` to drop again.")
        return

    cards, img = shared.ImageFunctions.new_drop(3) #generate 3 new cards and merge the images into a png

    for card in cards:
        prints[card[1]]["Print"] += 1  #increment print number for the dropped cards
    HelperFunctions.dump_prints()

    accounts[str_author_id][1] = time.time() #reset the user's drop cooldown
    dropannouncement = await ctx.send(mention_author + " is dropping 3 cards!")
    image_name = f"{str_author_id}.png"
    img.save(image_name)
    dropmessage = await ctx.send(file=discord.File(image_name))
    os.remove(image_name)

    tasks = [asyncio.create_task(DropFunctions.add_reactions(dropmessage)),
             asyncio.create_task(asyncio.wait_for(DropFunctions.wait_for_grabs(dropmessage, ctx.author, cards), timeout=30))]
    try:
        await asyncio.gather(*tasks)
    except asyncio.TimeoutError:
        for task in tasks:
            task.cancel()
    await dropannouncement.edit(content = "*This drop has expired.*")
    return



#Display a user's card collection in an embed
#that can display multiple pages using arrow reactions.
#Collections can be filtered by clan tag.
@bot.command(aliases=["c"])
async def collection(ctx, *words):
    str_author_id = str(ctx.author.id)
    mention_author = ctx.author.mention

    #messy section maxi will clean up
    c=None
    p=None
    t=None
    person=None
    gen = (word for word in words if len(word) > 2)
    for word in gen:
        user_check = shared.StringFunctions.check_user(word)
        if user_check:
            person = user_check
        elif word[:2] == 'c:':
            c = word[2:].lower()
        elif word[:2] == 'p:':
            p = word[2:].lower()
        elif word[:2] == 't:':
            t = word[2:].lower()

    if person == None:
        person = shared.StringFunctions.check_user(str_author_id)
    if not person:
        await ctx.send(mention_author + " Error: This user was not found.")
        return
    cardsfound = copy.copy(accounts[person][3])
    tags = accounts[person][6].copy()
    tags[None] = emojis["Black Square"]
    if c and len(cardsfound) > 0: #remove cards that dont have given clan tag
        for card in accounts[person][3]:
            if len(c) > len(card[2]):
                cardsfound.remove(card)
                continue
            if not c in card[2].lower():
                cardsfound.remove(card)
    if p and len(cardsfound) > 0: #remove cards that dont have given card name
        for card in accounts[person][3]:
            if not card in cardsfound: #if the card is already removed, continue
                continue
            if len(p) > len(card[1]):
                cardsfound.remove(card)
                continue
            if not p in card[1].lower():
                cardsfound.remove(card)
    if t and len(cardsfound) > 0: #remove cards that dont have given tag
        for card in accounts[person][3]:
            if not card in cardsfound: #if the card is already removed, continue
                continue
            if not t == card[7]:
                cardsfound.remove(card)

    msg1 = str(len(cardsfound)) + " cards found for <@" + person + ">\n"

    if len(cardsfound) < 1:
        msg2 = '\n*empty*'
        embed=discord.Embed(title="Card Collection", description=msg1+msg2, color=0xFFFFFF)
        await ctx.send(embed=embed)
        return

    elif len(cardsfound) < 10:
        msg2 = f"Showing cards 1 - {str(len(cardsfound))}\n\n"

    else:
        msg2 = 'Showing cards 1 - 10\n\n'

    cardsfound.reverse()
    conditions = emojis["Conditions"]

    for card in cardsfound[0:min(10,len(cardsfound))]:
        msg2 += f"{tags[card[7]]} ``{card[0]}`` · ``{conditions[card[6]]}`` · ``#{card[3]}`` · {card[2]} · **{card[1]}**\n"

    embed=discord.Embed(title="Card Collection", description=msg1+msg2, color=0xFFFFFF)
    embedmessage = await ctx.send(embed=embed)
    if len(cardsfound) < 11:
        return
    await embedmessage.add_reaction(emojis["Left Arrow"])
    await embedmessage.add_reaction(emojis["Right Arrow"])
    start = 0
    done = False
    reactions = [emojis["Left Arrow"],emojis["Right Arrow"]]
    def check(reaction, user):
        return str(user.id) == str_author_id and str(reaction.emoji) in reactions and reaction.message == embedmessage
    while done == False:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=20, check=check)
        except asyncio.TimeoutError:
            return
        if reaction.emoji == emojis["Left Arrow"]:
            if start < 11:
                start = 0
            else:
                start = start - 10
        else:
            if start + 10 > len(cardsfound):
                continue
            elif start + 20 > len(cardsfound):
                start = len(cardsfound) - 10
            else:
                start = start + 10
        msg2 = f"Showing cards {start+1} - {start + 10}\n\n"
        for card in cardsfound[start:start + 10]:
            msg2 += f"{tags[card[7]]} ``{card[0]}`` · ``{conditions[card[6]]}`` · ``#{card[3]}`` · {card[2]} · **{card[1]}**\n"
        embed=discord.Embed(title="Card Collection", description=msg1+msg2, color=0xFFFFFF)
        await embedmessage.edit(embed=embed)

#Lookup cards in prints.json based on player or clan
@bot.command(aliases=["lu"])
async def lookup(ctx, tag=None):
    str_author_id = str(ctx.author.id)
    mention_author = ctx.author.mention
    if tag==None:
        await ctx.send(mention_author + " Error: missing field.")
        return
    tag=tag.lower()
    cardsfound = []
    names = list(prints.keys())

    for x in names:
        if tag in x.lower() or tag in prints[x]["Clan"].lower() or tag in prints[x]["Clan Tag"].lower() or tag in prints[x]["Alt Name"].lower():
            cardsfound.append([prints[x]["Clan Tag"],x])

    if len(cardsfound) < 1:
        await ctx.send(mention_author + " no results were found for *" + tag + "*.")
        return

    cardsfound.sort()
    limit = min(10,len(cardsfound))
    msg1 = mention_author + " please select an option using the menu below.\n\n"
    msg2 = f"**Showing cards 1 - {limit} of {len(cardsfound)}**\n"

    for x in range(limit):
        msg2 += f"{x+1}. {cardsfound[x][0]} · **{cardsfound[x][1]}**\n"
    embed=discord.Embed(title="Card Lookup", description=msg1+msg2, color=0xFFFFFF)
    embedmessage = await ctx.send(embed=embed)
    many_pages = True
    if len(cardsfound) > 10:
        await embedmessage.add_reaction(emojis["Left Arrow"])
        await embedmessage.add_reaction(emojis["Right Arrow"])
        many_pages = True
    reactions = [emojis["Left Arrow"],emojis["Right Arrow"]]
    start = 0
    while True:
        tasks = [
        bot.loop.create_task(bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel), name="rrem"),
        bot.loop.create_task(bot.wait_for('reaction_add', check=lambda reaction, user: str(user.id) == str_author_id and str(reaction.emoji) in reactions and reaction.message == embedmessage and many_pages == True), name="radd")
        ]
        try:
            done, pending = await asyncio.wait(tasks, timeout=30, return_when=asyncio.FIRST_COMPLETED)
        except asyncio.TimeoutError:
            return

        finished = list(done)[0]

        action = finished.get_name()
        result = finished.result()

        done, pending = None, None

        if action == "radd":
            reaction, user = result
            if reaction.emoji == emojis["Left Arrow"]:
                if start == 0:
                    continue
                if start < 11:
                    start = 0
                else:
                    start = start - 10
            else:
                if start + 10 > len(cardsfound):
                    continue
                elif start + 20 > len(cardsfound):
                    start = len(cardsfound) - 10
                else:
                    start = start + 10
            msg2 = f"**Showing cards {start+1} - {start+10} of {len(cardsfound)}**\n"
            for x in range(10):
                msg2 += f"{x+1}. {cardsfound[x][0]} · **{cardsfound[x][1]}**\n"
            embed=discord.Embed(title="Card Lookup", description=msg1+msg2, color=0xFFFFFF)
            await embedmessage.edit(embed=embed)
        else:
            user_message = result.content
            if not str(user_message).isdigit():
                continue
            if not int(user_message)+start-1 in range(start+limit):
                continue
            image_file = shared.ImageFunctions.save_mii(cardsfound[int(user_message)+start-1][1])
            file = discord.File(image_file)
            msg = "This is a placeholder." #TODO
            embed=discord.Embed(title="Card Info", description=msg, color=0x000000)
            embed.set_thumbnail(url="attachment://" + image_file)
            await ctx.send(file=file, embed=embed)
            return

#Allows the user to delete a card for in-game currency
@bot.command(aliases=["b"])
async def burn(ctx, id=None):
    str_author_id = str(ctx.author.id)
    mention_author = ctx.author.mention
    if shared.StringFunctions.check_user(str_author_id) == None:
        await ctx.send(mention_author + " Error: Your MKWKaruta collection was not found.")
        return
    if len(accounts[str_author_id][3]) < 1:
        await ctx.send(mention_author + " Error: No cards found in your MKWKaruta")
        return
    quality_burnvalues = [2, 5, 10, 20, 40]
    if id==None:
        card = accounts[str_author_id][3][-1]
        id = card[0]
        image_file = shared.ImageFunctions.save_card(card)
        file = discord.File(image_file)
        burnvalue = quality_burnvalues[card[6]]
        if card[3] < 100:
            burnvalue += 10
            if card[3] < 10:
                burnvalue += 10
    else:
        if not len(id)==6:
            await ctx.send(mention_author + "Error: this is an invalid 6 letter card ID")
            return
        cardfound = False
        for card in accounts[str_author_id][3]:
            if card[0] == id:
                cardfound = True
                image_file = shared.ImageFunctions.save_card(card)
                file = discord.File(image_file)
                burnvalue = quality_burnvalues[card[6]]
                if card[3] < 100:
                    burnvalue += 10
                    if card[3] < 10:
                        burnvalue += 10
                break
        if cardfound == False:
            await ctx.send(mention_author + " Error: you do not own " + '``' + id + '``')
            return
    msg = mention_author + ", by burning ``" + id + "`` you will receive:\n\n" + '\N{MONEY WITH WINGS}: **' + str(burnvalue) + '** Dollas\n'
    embed=discord.Embed(title="Burn Card", description=msg, color=0xFFFFFF)
    embed.set_thumbnail(url="attachment://" + image_file)
    options = [emojis["Red X"],emojis["Fire"]]
    embedmessage = await ctx.send(file=file, embed=embed)
    await embedmessage.add_reaction(emojis["Red X"])
    await embedmessage.add_reaction(emojis["Fire"])
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in options and reaction.message == embedmessage
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=20, check=check)
    except asyncio.TimeoutError:
        return
    if reaction.emoji == emojis["Red X"]:
        msg = mention_author + ", card burning for ``" + id + "`` has been canceled."
        embed=discord.Embed(title="Burn Card", description=msg, color=0xFF0000)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
    else:
        for card in accounts[str_author_id][3]:
            if card[0] == id:
                accounts[str_author_id][5] += burnvalue
                accounts[str_author_id][3].remove(card)
                break
        HelperFunctions.dump_accounts()
        msg = mention_author + ", ``" + id + "`` has been successfully burned. \n You have recieved:\n\n" + '\N{MONEY WITH WINGS}: **' + str(burnvalue) + '** Dollas\n'
        embed=discord.Embed(title="Burn Card", description=msg, color=0x00FF2F)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
    return

#Allows users to gift one of their cards to another user
@bot.command(aliases=["g"])
async def give(ctx, giftee=None, id=None):
    str_author_id = str(ctx.author.id)
    mention_author = ctx.author.mention
    try:
        giftee = giftee[2:-1]
        if not giftee in accounts.keys():
            await ctx.send(mention_author + " Error: This user was not found.")
            return
        if giftee == str_author_id:
            await ctx.send(mention_author + " Error: You cannot gift a card to yourself")
            return
    except:
        await ctx.send(mention_author + " Error: This user is invalid.")
        return
    if shared.StringFunctions.check_user(str_author_id) == None:
        await ctx.send(mention_author + " Error: Your MKWKaruta collection was not found.")
        return
    if len(accounts[str_author_id][3]) < 1:
        await ctx.send(mention_author + " Error: No cards found in your MKWKaruta")
        return
    card = None
    if id==None:
        card = accounts[str_author_id][3][-1]
        id = card[0]
    else:
        if not len(id)==6:
            await ctx.send(mention_author + "Error: this is an invalid 6 letter card ID")
            return
        for c in accounts[str_author_id][3]:
            if c[0] == id:
                card = c
                break
        if c == None:
            await ctx.send(mention_author + " Error: you do not own " + '``' + id + '``')
            return
    msg = "<@" + giftee + ">, do you accept the gift of **" + id + "** from <@" + str_author_id + "> ?"
    embed=discord.Embed(title="Give Card", description=msg, color=0xFFFFFF)
    image_file = shared.ImageFunctions.save_card(card)
    file = discord.File(image_file)
    embed.set_thumbnail(url="attachment://" + image_file)
    options = [emojis["Red X"],emojis["Check"]]
    embedmessage = await ctx.send(file=file, embed=embed)
    await embedmessage.add_reaction(emojis["Red X"])
    await embedmessage.add_reaction(emojis["Check"])
    def check(reaction, user):
        check1 = str(user.id) == giftee and str(reaction.emoji) in options and reaction.message == embedmessage
        check2 = str(user.id) == str_author_id and str(reaction.emoji) == emojis["Red X"] and reaction.message == embedmessage
        return check1 or check2
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=20, check=check)
    except asyncio.TimeoutError:
        msg = mention_author + ", card gifting for **" + id + "** to <@" + giftee + "> has timed out."
        embed=discord.Embed(title="Give Card", description=msg, color=0xFF0000)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
        return
    if reaction.emoji == emojis["Red X"]:
        msg = mention_author + ", card gifting for **" + id + "** to <@" + giftee + "> has been canceled."
        embed=discord.Embed(title="Give Card", description=msg, color=0xFF0000)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
    else:
        for i in range(len(accounts[str_author_id][3])):
            if accounts[str_author_id][3][i][0] == id:
                giftedcard = accounts[str_author_id][3].pop(i)
                accounts[giftee][3].append(giftedcard)
                break
        HelperFunctions.dump_accounts()
        msg = mention_author + ", **" + id + "** has been successfully gifted to to <@" + giftee + ">."
        embed=discord.Embed(title="Give Card", description=msg, color=0x00FF2F)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
    return

#Displays a user's inventory in an embed
@bot.command(aliases=["i"])
async def inventory(ctx, user=None):
    mention_author = ctx.author.mention
    if user == None:
        user = str(ctx.author.id)
    user = shared.StringFunctions.check_user(user)
    if user == None:
        await ctx.send(f"{mention_author} Error: This user was not found.")
        return
    embed=discord.Embed(title="Inventory", description="Items carried by <@" + user + ">", color=0x91FFFB)
    msg = f"\N{MONEY WITH WINGS}: **{accounts[user][5]}** Dollas\n"
    if len(accounts[user][4]) > 0:
        for item in accounts[user][4]:
            msg += f"**{itemshop[item][0]}** · ``{item}``\n"
    embed.add_field(name="\u200b", value=msg, inline=False)
    await ctx.send(embed=embed)
    return

#Shows an embed containing a picture of any given card
#Arg: card_id
@bot.command(aliases=["v"])
async def view(ctx, id=None):
    str_author_id = str(ctx.author.id)
    mention_author = ctx.author.mention
    if shared.StringFunctions.check_user(str_author_id) == None:
        await ctx.send(mention_author + " Error: Your MKWKaruta collection was not found.")
        return

    conditions = emojis["Conditions"]
    card = None
    if id==None:
        if len(accounts[str_author_id][3]) < 1:
            await ctx.send(mention_author + " Error: No cards found in your MKWKaruta")
            return
        card = accounts[str_author_id][3][-1]
        account = str_author_id
    else:
        for a in accounts:
            for c in accounts[a][3]:
                if c[0] == id:
                    card = c
                    account = a
                    break
            if card != None:
                break
    if card == None:
        await ctx.send(mention_author + " Error: Card with id ``" + id + "`` does not exist.")
        return
    msg = '``' + card[0] + '`` · ``' + conditions[card[6]] + '`` · ``#' + str(card[3]) + '`` · ' + card[2] + ' · **' + card[1] + '**'
    desc = "Card owned by " + mention_author + "\n\n" + msg
    embed = discord.Embed(title="View Card", description=desc, color=0xFFFFFF)
    image_file = shared.ImageFunctions.save_card(card)
    file = discord.File(image_file)
    embed.set_image(url="attachment://" + image_file)
    await ctx.send(file=file, embed=embed)
    return


#Shows an embed with a user's grab, drop, and daily reward cooldowns.
@bot.command(aliases=["cd"])
async def cooldown(ctx, user=None): ##inventory
    mention_author = ctx.author.mention
    if user == None:
        user = str(ctx.author.id)
    user = shared.StringFunctions.check_user(user)
    if user == None:
        await ctx.send(mention_author + " Error: This user was not found.")
        return
    embed=discord.Embed(title="Cooldowns", description="Cooldowns for <@" + user + ">", color=0xFFFFFF)
    seconds = time.time() - accounts[str(user)][0]
    if seconds < 60:
        grabtime = time.gmtime(60 - seconds)
        msg = '**Grab** is available in ``' + time.strftime("%M minutes, %S seconds", grabtime) + '``\n'
    else:
        msg = '**Grab** is currently available.\n'
    seconds = time.time() - accounts[str(user)][1]
    if seconds < 300:
        droptime = time.gmtime(300 - seconds)
        msg += '**Drop** is available in ``' + time.strftime("%M minutes, %S seconds", droptime) + '``\n'
    else:
        msg += '**Drop** is currently available.\n'
    seconds = time.time() - accounts[str(user)][2]
    if seconds < 86400:
        dailytime = time.gmtime(86400 - seconds)
        msg += '**Daily** is available in ``' + time.strftime("%H hours, %M minutes, %S seconds", dailytime) + '``\n'
    else:
        msg += '**Daily** is currently available.\n'
    embed.add_field(name="\u200b", value=msg, inline=False)
    await ctx.send(embed=embed)
    return

#Gives between 50-100 currency to the user. Can only be done once every 24 hours
@bot.command()
async def daily(ctx): ##inventory
    str_author_id = str(ctx.author.id)
    mention_author = ctx.author.mention
    if not str_author_id in accounts.keys():
        HelperFunctions.create_account(str_author_id)
    else:
        seconds = time.time() - accounts[str_author_id][2]
        if seconds < 86400:
            dailytime = time.gmtime(86400 - seconds)
            await ctx.send(mention_author + ' **Daily** is available in ``' + time.strftime("%H hours, %M minutes, %S seconds", dailytime) + '``\n')
            return
    dailyreward = random.randrange(50,100)
    accounts[str_author_id][5] += dailyreward
    accounts[str_author_id][2] = time.time()
    HelperFunctions.dump_accounts()
    await ctx.send(mention_author + ' You have gained ``' + str(dailyreward) + '`` Dollas!\n')
    return

#Allows a user to consume a background they own and apply it to a card in their collection.
@bot.command(aliases=["use"])
async def addbackground(ctx, id=None, background=None): ##give
    str_author_id = str(ctx.author.id)
    mention_author = ctx.author.mention
    if background == None:
        await ctx.send(mention_author + " Error: maddbackground <card id> <item>.")
        return
    if shared.StringFunctions.check_user(str_author_id) == None:
        await ctx.send(mention_author + " Error: Your MKWKaruta collection was not found.")
        return
    id = id.lower()
    background = background.lower()
    if len(accounts[str_author_id][3]) < 1:
        await ctx.send(mention_author + " Error: No cards found in your MKWKaruta")
        return
    if not len(id)==6:
        await ctx.send(mention_author + " Error: this is an invalid 6 letter card ID")
        return
    if not background in accounts[str_author_id][4]:
        await ctx.send(mention_author + " Error: You do not own ``" + background + "``")
        return
    for card in accounts[str_author_id][3]:
        if card[0] == id:
            newcard = copy.copy(card)
            newcard[4] = background
            desc = " <@" + str_author_id + ">, would you like to use this background? You will lose: \n"
            desc += "```diff\n-1 " + background + "```"
            embed = discord.Embed(title="New Background", description=desc, color=0xFFFFFF)
            image_file = shared.ImageFunctions.save_card(newcard)
            file = discord.File(image_file)
            embed.set_image(url="attachment://" + image_file)
            options = [emojis["Red X"],emojis["Check"]]
            embedmessage = await ctx.send(file=file, embed=embed)
            await embedmessage.add_reaction(emojis["Red X"])
            await embedmessage.add_reaction(emojis["Check"])
            def check(reaction, user):
                return str(user.id) == str_author_id and str(reaction.emoji) in options and reaction.message == embedmessage
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=20, check=check)
            except asyncio.TimeoutError:
                msg = mention_author + ", This action has timed out."
                embed.add_field(name="\u200b", value=msg, inline=False)
                embed.color = 0xFF1100
                await embedmessage.edit(embed=embed)
                return
            if reaction.emoji == emojis["Red X"]:
                msg = mention_author + ", This action has been canceled."
                embed.add_field(name="\u200b", value=msg, inline=False)
                embed.color = 0xFF1100
                await embedmessage.edit(embed=embed)
                return
            else:
                if not background in accounts[str_author_id][4]:
                    msg = mention_author + ", You do not own this background."
                    embed.add_field(name="\u200b", value=msg, inline=False)
                    embed.color = 0xFF1100
                    await embedmessage.edit(embed=embed)
                    return
                msg = mention_author + ", This background has been applied!"
                embed.add_field(name="\u200b", value=msg, inline=False)
                embed.color = 0x00FF00
                card[4] = background
                accounts[str_author_id][4].remove(background)
                await embedmessage.edit(embed=embed)
                HelperFunctions.dump_accounts()
                return
    await ctx.send(mention_author + " Error: you do not own " + '``' + id + '``')
    return

#Displays an embed of the item store. Currently, it only sells backgrounds.
@bot.command(aliases=["s", "itemshop", "store"])
async def shop(ctx):
    if user in accounts.keys():
        balance = str(accounts[user][5])
        embed=discord.Embed(title="Item Shop", description="<@" + user + ">'s balance: " + balance + " dollas", color=0x91FFFB)
    else:
        embed=discord.Embed(title="Item Shop", description="<@" + user + ">", color=0x91FFFB)
    msg = ""
    for item in itemshop.keys():
        name = itemshop[item][0]
        price = itemshop[item][1]
        msg += '**' + name + "**  · ``" + item + "`` · " + str(price) + " Dollas\n"
    embed.add_field(name="\u200b", value=msg, inline=False)
    await ctx.send(embed=embed)
    return

#Allows users to buy an item from the shop using currency.
@bot.command()
async def buy(ctx, item=None): ##itemshop
    mention_author = ctx.author.mention
    str_author_id = str(ctx.author.id)
    if not str_author_id in accounts.keys():
        await ctx.send(mention_author + " Error: Your MKWKaruta account was not found. Drop or grab a card to start!")
        return
    if item==None:
        await ctx.send(mention_author + " Please use mbuy <itemid> to make a purchase. Use *mshop* to view a list of available items.")
        return
    item = item.lower()
    if not item in itemshop.keys():
        await ctx.send(mention_author + " The item with id ``" + item + "`` was not found. Use *mshop* to view a list of available items.")
        return
    embed=discord.Embed(title="Item Purchase", description="**" + itemshop[item][0] + "**\n*" + itemshop[item][2] + "*", color=0xFFFFFF)
    msg = mention_author + " will **gain**\n"
    msg += "```diff\n+1 " + item + "```\n"
    msg2 = mention_author + " will **lose**\n"
    msg2 += "```diff\n-" + str(itemshop[item][1]) + " Dollas" + "```\n"
    embed.add_field(name="\u200b", value=msg, inline=False)
    embed.add_field(name="\u200b", value=msg2, inline=False)
    options = [emojis["Red X"],emojis["Check"]]
    embedmessage = await ctx.send(embed=embed)
    await embedmessage.add_reaction(emojis["Red X"])
    await embedmessage.add_reaction(emojis["Check"])
    def check(reaction, user):
        return str(user.id) == str_author_id and str(reaction.emoji) in options and reaction.message == embedmessage
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=20, check=check)
    except asyncio.TimeoutError:
        msg = mention_author + ", The purchase has timed out."
        embed.add_field(name="\u200b", value=msg, inline=False)
        embed.color = 0xFF1100
        await embedmessage.edit(embed=embed)
        return
    if reaction.emoji == emojis["Red X"]:
        msg = mention_author + ", This purchase has been canceled."
        embed.add_field(name="\u200b", value=msg, inline=False)
        embed.color = 0xFF1100
        await embedmessage.edit(embed=embed)
    else:
        if accounts[str_author_id][5] < itemshop[item][1]:
            msg = mention_author + ", You do not have the funds to make this purchase."
            embed.add_field(name="\u200b", value=msg, inline=False)
            embed.color = 0xFF1100
            await embedmessage.edit(embed=embed)
        else:
            accounts[str_author_id][5] = accounts[str_author_id][5] - itemshop[item][1]
            accounts[str_author_id][4].append(item)
            HelperFunctions.dump_accounts()
            msg = mention_author + ", This purchase has been completed!"
            embed.add_field(name="\u200b", value=msg, inline=False)
            embed.color = 0x00FF00
            await embedmessage.edit(embed=embed)
    return

#Allows users to upgrade a card in their collection.
@bot.command(aliases=["t"])
async def tag(ctx, tag, *cards):
    card_ids = list(cards)
    mention_author = ctx.author.mention
    str_author_id = str(ctx.author.id)
    if not str_author_id in accounts.keys():
        await ctx.send(mention_author + " Error: Your MKWKaruta account was not found. Drop or grab a card to start!")
        return
    if tag == None or card_ids == []:
        await ctx.send(mention_author + ", you must specify both a tag and card(s) you wish to tag.")
        return
    if len(accounts[str_author_id][3]) < 1:
        await ctx.send(mention_author + " Error: No cards found in your MKWKaruta")
        return
    tag = tag.lower()
    if not tag in accounts[str_author_id][6].keys():
        await ctx.send(f"{mention_author}, tag with name ``{tag}`` does not exist.")
        return
    for card in accounts[str_author_id][3]:
        if card[0] in card_ids:
            card[7] = tag
            card_ids.remove(card[0])
    if len(card_ids) > 0:
        await ctx.send(f"{mention_author}, at least one of the specified card ids was not found in your collection.")
        return
    HelperFunctions.dump_accounts()
    await ctx.send(f"{mention_author}, **{len(cards)}** cards have been successfully tagged!")
    return

#Allows users to upgrade a card in their collection.
@bot.command(aliases=["ut"])
async def untag(ctx, *cards):
    card_ids = list(cards)
    mention_author = ctx.author.mention
    str_author_id = str(ctx.author.id)
    if not str_author_id in accounts.keys():
        await ctx.send(mention_author + " Error: Your MKWKaruta account was not found. Drop or grab a card to start!")
        return
    if card_ids == []:
        await ctx.send(mention_author + ", you must specify the card(s) you wish to untag.")
        return
    if len(accounts[str_author_id][3]) < 1:
        await ctx.send(mention_author + " Error: No cards found in your MKWKaruta")
        return
    for card in accounts[str_author_id][3]:
        if card[0] in card_ids:
            card[7] = None
            card_ids.remove(card[0])
    if len(card_ids) > 0:
        await ctx.send(f"{mention_author}, at least one of the specified card ids was not found in your collection.")
        return
    HelperFunctions.dump_accounts()
    await ctx.send(f"{mention_author}, **{len(cards)}** cards have been successfully untagged.")
    return

#Allows users to create a tag.
@bot.command(aliases=["tc"])
async def tagcreate(ctx, tag=None, emoji=None):
    mention_author = ctx.author.mention
    str_author_id = str(ctx.author.id)
    if not str_author_id in accounts.keys():
        await ctx.send(mention_author + " Error: Your MKWKaruta account was not found. Drop or grab a card to start!")
        return
    if tag == None or emoji == None:
        await ctx.send(mention_author + ", you must specify both a name (without spaces) and emoji when attempting to add a new tag.")
        return
    tag = tag.lower()
    if not len(accounts[str_author_id][6]) == 0:
        max_tags = 10
        if len(accounts[str_author_id][6]) >= 10:
            await ctx.send(f"{mention_author}, you already have the max number of tags ({max_tags})")
            return
        if tag in accounts[str_author_id][6].keys():
            await ctx.send(f"{mention_author}, tag with name ``{tag}`` already exists")
            return
        if str(emoji) in str(accounts[str_author_id][6]):
            await ctx.send(f"{mention_author}, tag with emoji {emoji} already exists")
            return
    accounts[str_author_id][6][tag] = emoji
    HelperFunctions.dump_accounts()
    await ctx.send(f"{mention_author}, tag ``{tag}`` has been created!")
    return



#Allows users to delete a tag.
@bot.command(aliases=["td"])
async def tagdelete(ctx, tag=None):
    mention_author = ctx.author.mention
    str_author_id = str(ctx.author.id)
    if not str_author_id in accounts.keys():
        await ctx.send(mention_author + " Error: Your MKWKaruta account was not found. Drop or grab a card to start!")
        return
    if tag == None:
        await ctx.send(mention_author + ", you must specify the tag name when attempting to delete a tag.")
        return
    if len(accounts[str_author_id][6]) == 0:
        await ctx.send(mention_author + ", you have not yet created any tags.")
        return
    tag = tag.lower()
    result = accounts[str_author_id][6].pop(tag, None)
    if not result:
        await ctx.send(f"{mention_author}, tag with name ``{tag}`` does not exist.")
    else:
        if len(accounts[str_author_id][3]) > 0:
            for card in accounts[str_author_id][3]:
                if card[7] == tag:
                    card[7] = None
        HelperFunctions.dump_accounts()
        await ctx.send(f"{mention_author}, tag ``{tag}`` has been deleted.")
    return


#Allows users to view their tags.
@bot.command()
async def tags(ctx, user=None):
    mention_author = ctx.author.mention
    if user == None:
        user = str(ctx.author.id)
    user = shared.StringFunctions.check_user(user)
    if user == None:
        await ctx.send(f"{mention_author} Error: This user was not found.")
        return
    tagsfound = accounts[user][6]
    msg = f"User: <@{user}> \n\n"

    if len(tagsfound) < 1:
        msg += '*none*'
        embed=discord.Embed(title="Tags", description=msg, color=0xFFFFFF)
        await ctx.send(embed=embed)
        return

    for tag in tagsfound.keys():
        msg += f"{tagsfound[tag]} ``{tag}``\n"

    embed=discord.Embed(title="Tags", description=msg, color=0xFFFFFF)
    await ctx.send(embed=embed)
    return

#Allows users to upgrade a card in their collection.
@bot.command()
async def upgrade(ctx, id=None):
    mention_author = ctx.author.mention
    str_author_id = str(ctx.author.id)
    if shared.StringFunctions.check_user(str_author_id) == None:
        await ctx.send(mention_author + " Error: Your MKWKaruta collection was not found.")
        return
    success = ""
    done = False
    while done == False:
        if len(accounts[str_author_id][3]) < 1:
            await ctx.send(mention_author + " Error: No cards found in your MKWKaruta")
            return
        cardfound = None
        if id==None:
            cardfound = accounts[str_author_id][3][-1]
            id = cardfound[0]
            image_file = shared.ImageFunctions.save_card(cardfound)
            file = discord.File(image_file)
        else:
            if not len(id)==6:
                await ctx.send(mention_author + " Error: This is an invalid 6 letter card ID")
                return
            for card in accounts[str_author_id][3]:
                if card[0] == id:
                    cardfound = card
                    image_file = shared.ImageFunctions.save_card(card)
                    file = discord.File(image_file)
                    break
        if cardfound == None:
            await ctx.send(mention_author + " Error: You do not own " + '``' + id + '``')
            return
        old_condition = cardfound[6]
        if old_condition >= 4:
            await ctx.send(mention_author + " Error: This card is already in mint condition.")
            return
        msg = ""
        conditions = [["damaged",10,80], ["poor",25,70], ["good",50,60], ["excellent",100,50], ["mint",0,0]]
        if success == "no":
            msg += "**The upgrade failed.** The card condition has not changed.\n\n"
            embedcolor = 0xFF0000
        elif success == "yes":
            msg += "**The upgrade succeeded!** The card has been upgraded to **" + conditions[old_condition][0] + "** condition.\n\n"
            embedcolor = 0x00FF2F
        else:
            embedcolor = 0xFFFFFF
        msg += mention_author + ", upgrading the condition of ``" + id + "`` from **" + conditions[old_condition][0] + "** to **" + conditions[old_condition + 1][0]
        msg += "** has a **" + str(conditions[old_condition][2]) + "%** chance of succeeding. If this upgrade fails, the card's condition will not change.\n\n"
        msg += "Attempting the upgrade will cost the following resources:\n"
        msg += "```diff\n-" + str(conditions[old_condition][1]) + " Dollas```"
        embed=discord.Embed(title="Card Upgrade", description=msg, color=embedcolor)
        embed.set_thumbnail(url="attachment://" + image_file)
        embedmessage = await ctx.send(file=file, embed=embed)
        await embedmessage.add_reaction('\N{WRENCH}')
        def check(reaction, user):
            return str(user.id) == str_author_id and str(reaction.emoji) == '\N{WRENCH}' and reaction.message == embedmessage
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=20, check=check)
        except asyncio.TimeoutError:
            return
        if accounts[str_author_id][5] < conditions[cardfound[6]][1]:
            msg = mention_author + ", you do not have enough Dollas to attempt this upgrade."
            embed=discord.Embed(title="Card Upgrade", description=msg, color=0xFF0000)
            embed.set_thumbnail(url="attachment://" + image_file)
            await embedmessage.edit(embed=embed)
            return
        accounts[str_author_id][5] = accounts[str_author_id][5] - conditions[cardfound[6]][1]
        rng = random.randrange(1,100)
        cardfound = None
        for card in accounts[str_author_id][3]:
            if card[0] == id:
                cardfound = card
                break
        if cardfound == None:
            await ctx.send(mention_author + " Error: You do not own " + '``' + id + '``')
            return
        if rng > conditions[old_condition][2]:
            success = "no"
        else:
            success = "yes"
            card[6] += 1
            if old_condition == 3:
                msg = mention_author + ", ``" + id + "`` has been successfully upgraded to **mint** condition!"
                embed=discord.Embed(title="Card Upgrade", description=msg, color=0x00FF2F)
                image_file = shared.ImageFunctions.save_card(card)
                file = discord.File(image_file)
                embed.set_image(url="attachment://" + image_file)
                await ctx.send(file=file, embed=embed)
                Done = True
                HelperFunctions.dump_accounts()
                return
        HelperFunctions.dump_accounts()
    return



@bot.command(pass_context=True)
async def help(ctx):
    msg = """**How to Play**\n\n"
    "**Burn** `mb <id>` to destroy a card from your inventory.\n
    "**Drop** `md` to drop cards. Use one of the reactions to grab the corresponding card.
    "**Collection** `mc <@user> <t=tag>` to view a card collection.
    "**Cooldowns** `mcd` to view the cooldown times for Drop, Grab, and Daily Reward.
    "**Daily Reward** `mdaily` to get a daily reward.
    "**Give** `mg <@user> <id>` to gift a card to someone else.
    "**Inventory** `mi <@user>` to view an inventory
    "**Shop** `mshop` to view the item shop.
    **Upgrade** `mupgrade <id>` to attempt a card upgrade.
    **View** `mv <id>` to view a card"""
    await ctx.send(msg)

##Administrator commands

@bot.command()
async def deleteallcollections(ctx):
    if ctx.author.id not in list(ADMINS.values()):
        return
    for person in accounts:
        accounts[person][3] = []
    HelperFunctions.dump_accounts()
    await ctx.send("Holy shit. Everyone's inventories have been deleted!")

@bot.command()
async def changecards(ctx):
    if ctx.author.id not in list(ADMINS.values()):
        return
    for person in accounts:
        for i in range(len(accounts[person][3])):
            accounts[person][3][i] = accounts[person][3][i] + [None, []]
    HelperFunctions.dump_accounts()
    await ctx.send(str(accounts[str(ctx.author.id)][3][0]))

@bot.command()
async def newuserformat(ctx):
    if ctx.author.id not in list(ADMINS.values()):
        return
    emptydict = {}
    for person in accounts:
        accounts[person].append(emptydict)
    HelperFunctions.dump_accounts()
    await ctx.send("Done.")


@bot.command()
async def resetallprints(ctx):
    if ctx.author.id not in list(ADMINS.values()):
        return
    for card in prints:
        prints[card]["Print"] = 0
    await ctx.send("Wow. All card prints have been reset!")
    HelperFunctions.dump_prints()


@bot.command(aliases=["r"])
async def reset(ctx, user=None):
    if user == None:
        user = str(ctx.author.id)
    user = shared.StringFunctions.check_user(user)
#    if ctx.author.id not in list(ADMINS.values()):
#        return
    accounts[user][0] = time.time()-2000
    accounts[user][1] = time.time()-700
    accounts[user][2] = time.time()-87000
    HelperFunctions.dump_accounts()
    await ctx.send(f"<@{user}>'s cooldowns have been reset.")

@bot.command()
async def m(ctx, money):
    str_author_id = str(ctx.author.id)
    accounts[str_author_id][5] = money
    HelperFunctions.dump_accounts()
    await ctx.send('Your balance has been set to ' + str(money))

@bot.command()
async def testcard(ctx, name="", bg="bg_gray", frame="ed1", quality=4):
    try:
        clan_tag = prints[name]["Clan Tag"]
    except:
        await ctx.send('Error: this card was not found (try using different capitalization). ')
        return
    card = ["000000", name, clan_tag, 0, bg, frame, 4]
    desc = "Test Card"
    conditions = emojis["Conditions"]
    msg = '``' + card[0] + '`` · ``' + conditions[card[6]] + '`` · ``#' + str(card[3]) + '`` · ' + card[2] + ' · **' + card[1] + '**\n'
    embed = discord.Embed(title="View Card", description=desc, color=0xFFFFFF)
    embed.add_field(name="\u200b", value=msg, inline=False)
    image_file = shared.ImageFunctions.save_card(card)
    file = discord.File(image_file)
    embed.set_image(url="attachment://" + image_file)
    await ctx.send(file=file, embed=embed)
    return




@bot.command()
async def getfcs(ctx):
    if ctx.author.id not in list(ADMINS.values()):
        return
    json = list(prints.keys())
    os.chdir(os.path.join(CURRENT_DIR, "miis"))
    allprints = os.listdir()
    lines = []
    missingfcs = []
    for name in json:
        imgname = name + ".png"
        if not os.path.exists(imgname):
            try:
                code = fcs[name.lower()]["fc"]
                lines.append(name + " " + code + "\n")
            except:
                lines.append(name + "\n")
                missingfcs.append(name)
    lines.sort()
    t = time.asctime(time.gmtime())
    msg = "Missing Entries at " + t + "\n"
    for line in lines:
        msg += line
    os.chdir(CURRENT_DIR)
    with codecs.open(f'{JSON_DIR}missingimageswithfcs.txt', 'w', encoding='utf-8') as f:
        f.write(msg)
    await ctx.send("Saved to missingimageswithfcs.txt")
    msg = "Missing FCs from " + "\n".join(missingfcs)
    with codecs.open(f'{JSON_DIR}missingfcs.txt', 'w', encoding='utf-8') as f:
        f.write(msg)
    return


@bot.command()
async def checkduplicates(ctx):
    if ctx.author.id not in list(ADMINS.values()):
        return
    namelist = []
    duplicates = []
    for item in prints.keys():
        if item.lower() in namelist:
            duplicates.append(item.lower())
        else:
            namelist.append(item.lower())
    t = time.asctime(time.gmtime())
    msg = "Duplicate Entries at " + t + "\n"
    for item in duplicates:
        msg += item + ", "
    await ctx.send(msg[0:-2])

@bot.command()
async def images(ctx):
    if ctx.author.id not in list(ADMINS.values()):
        return
    json = list(prints.keys())
    os.chdir(os.path.join(CURRENT_DIR, "miis"))
    allprints = os.listdir()
    lines = []
    for name in json:
        if prints[name]["Clan Tag"] != "F/A":
            imgname = name + ".png"
            if not os.path.exists(imgname):
                lines.append(prints[name]["Clan Tag"] + " " + name + "\n")
    os.chdir(CURRENT_DIR)
    lines.sort()
    t = time.asctime(time.gmtime())
    msg = str(len(lines)) + " missing mii pictures\n"
    for line in lines:
        msg += line
    await ctx.send(msg[0:1999])
    await ctx.send(msg[1999:])

@bot.command()
async def cardstring(ctx, id=None):
    if ctx.author.id not in list(ADMINS.values()):
        return
    str_author_id = str(ctx.author.id)
    mention_author = ctx.author.mention
    if shared.StringFunctions.check_user(str_author_id) == None:
        await ctx.send(mention_author + " Error: Your MKWKaruta collection was not found.")
        return

    conditions = emojis["Conditions"]
    card = None
    if id==None:
        if len(accounts[str_author_id][3]) < 1:
            await ctx.send(mention_author + " Error: No cards found in your MKWKaruta")
            return
        card = accounts[str_author_id][3][-1]
        account = str_author_id
    else:
        for a in accounts:
            for c in accounts[a][3]:
                if c[0] == id:
                    card = c
                    account = a
                    break
            if card != None:
                break
    if card == None:
        await ctx.send(mention_author + " Error: Card with id ``" + id + "`` does not exist.")
        return
    await ctx.send(str(card))
    return

"""
#Error-catching (credit Fear)
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        return
    elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
        await ctx.send(str(error))
    elif isinstance(error, discord.ext.commands.errors.MissingAnyRole):
        await ctx.send(error)
        return
    else:
        await ctx.send(str(error))
        print(error)
        return
"""

@bot.event
async def on_ready():
    ##the following is just to make text files telling me what miis and print entries are missing
    os.chdir(os.path.join(CURRENT_DIR, "miis"))
    allprints = [file[:-4] for file in os.listdir()]
    lines = []
    for name in prints:
        if prints[name]["Clan Tag"] != "F/A":
            imgname = name + ".png"
            if not os.path.exists(imgname):
                lines.append(prints[name]["Clan Tag"] + " " + name + "\n")
    lines.sort()
    t = time.asctime(time.gmtime())
    msg = "Missing Entries at " + t + "\n"
    for line in lines:
        msg += line
    with codecs.open(f'{JSON_DIR}missingpictures.txt', 'w', encoding='utf-8') as f:
        f.write(msg)
    msg = ""
    comma = ", "
    for mii in allprints:
        if not mii in prints:
            msg += mii + comma
    os.chdir(CURRENT_DIR)
    with codecs.open(f'{JSON_DIR}missingentries.txt', 'w', encoding='utf-8') as f:
        f.write(msg)
    ##end of debug stuff


    print('The bot is ready.')

bot.run('OTcyMjI4NjI3OTU5NzkxNjM2.GR-QZ1.B-Uw-kuK_oDNO17E2gmbNmes2c_MHOXaa2n9cQ')
