import discord, json, os, asyncio, time, random, string, copy, collections, codecs
from discord.ext import commands
from datetime import date
from random import choice, shuffle
from discord import Client, Member, Guild
from discord.utils import get
from PIL import Image, ImageDraw, ImageFont
from os import listdir
from os.path import isfile, join

current_dir = os.getcwd()

with codecs.open('prints.json', encoding='utf-8') as f:
    prints = json.load(f)

with codecs.open('accounts.json', encoding='utf-8') as f:
    accounts = json.load(f)

with codecs.open('shop.json', encoding='utf-8') as f:
    itemshop = json.load(f)

with codecs.open('friendcodes.json', encoding='utf-8') as f:
    fcs = json.load(f)

json.dumps(prints, ensure_ascii=False)
json.dumps(accounts, ensure_ascii=False)
json.dumps(itemshop, ensure_ascii=False)
json.dumps(fcs, ensure_ascii=False)

client = commands.Bot(command_prefix=['m','M'],help_command=None, case_insensitive=True)

@client.event
async def on_ready():

    ##the following is just to make text files telling me what miis and print entries are missing
    json = list(prints.keys())
    os.chdir(os.path.join(current_dir, "miis"))
    allprints = os.listdir()
    lines = []
    for name in json:
        if prints[name]["Tag"] != "F/A":
            imgname = name + ".png"
            if not os.path.exists(imgname):
                lines.append(prints[name]["Tag"] + " " + name + "\n")
    lines.sort()
    t = time.asctime(time.gmtime())
    msg = "Missing Entries at " + t + "\n"
    for line in lines:
        msg += line
    os.chdir(current_dir)
    with codecs.open('missingpictures.txt', 'w', encoding='utf-8') as f:
        f.write(msg)

    json = list(prints.keys())
    os.chdir(os.path.join(current_dir, "miis"))
    allprints = os.listdir()
    msg = ""
    comma = ", "
    for Print in allprints:
        if not Print[0:-4] in json:
            msg += Print[0:-4] + comma
    os.chdir(current_dir)
    with codecs.open('missingentries.txt', 'w', encoding='utf-8') as f:
        f.write(msg)
    ##end of debug stuff

    print('The bot is ready.')
    await client.change_presence(activity=discord.Game(name="Beep Boop, I'm ready for some Tier 5!"))

##Helper Functions

def createaccount(id):
    ##Grab time, Drop time, Daily time, Card collection, Inventory, Money
    accounts[str(id)] = [time.time()-700, time.time()-2000, time.time()-90000,[], [], 0]
    with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
        json.dump(accounts, json_file, ensure_ascii=False)

def checkuser(user):
    if len(str(user)) > 4 and str(user)[0:2] == '<@':
        user = str(user)[2:-1]
    if not user in accounts.keys():
        print(str(user) + " couldn't have their collection found.")
        return None
    return user

##Card Making

def write_image(background,frame,clan_tag,card_id,card_name,print_number,overlay):
    mii = rendermii(card_name)
    img = Image.new("RGBA", background.size,0)
    img.paste(background)
    img.paste(mii, (0,86), mii)
    img.paste(frame.convert("RGBA"), (0,0), frame.convert("RGBA"))
    draw = ImageDraw.Draw(img)
    font1 = ImageFont.truetype('arial.ttf',size=40)
    font2 = ImageFont.truetype('arial.ttf',size=20)
    w,h = img.size # get width and height of image
    t1_width, t1_height = draw.textsize(clan_tag, font1) # clan tag
    t2_width, t2_height = draw.textsize(card_id, font2) # id
    t3_width, t3_height = draw.textsize(card_name, font1) # name
    t4_width, t4_height = draw.textsize(print_number, font2) # print
    p1 = ((w-t1_width)/2,605) # clan tag
    p2 = ((w-t2_width)/2,74) # id
    p3 = ((w-t3_width)/2,112) # name
    p4 = ((w-t4_width)/2,670) # print
    draw.text(p1, clan_tag, fill=(0,0,0), font=font1) # clan tag
    draw.text(p2, card_id, fill=(255,255,255), font=font2) # id
    draw.text(p3, card_name, fill=(0,0,0), font=font1) # name
    draw.text(p4, print_number, fill=(255,255,255), font=font2) # print
    img.paste(overlay.convert("RGBA"), (0,0), overlay.convert("RGBA"))
    return img

def newid():
    id = ""
    letters = string.ascii_lowercase
    for i in range(6):
        id += random.choice(letters)
    for user in accounts:
        if len(user[3]) > 0:
            for card in user[3]:
                if user[0] == id:
                    id = newid()
    return id

def merge(im1, im2, im3):
    w = im1.size[0] + im2.size[0] + im2.size[0]
    h = max(im1.size[1], im2.size[1])
    im = Image.new("RGBA", (w, h))
    im.paste(im1)
    im.paste(im2, (im1.size[0], 0))
    im.paste(im3, (im1.size[0]+im2.size[0], 0))
    im.save('drop.png')
    return

def generatecard(person):
    ##["id", "name", "clan", print, "bg", "frame", quality]
    id = newid()
    prints[person]["Print"] += 1
    with codecs.open('prints.json', 'w', encoding='utf-8') as json_file:
        json.dump(prints, json_file, ensure_ascii=False)
    tag = prints[person]["Tag"]
    print_number = prints[person]["Print"]
    background_name = "bg_gray"
    frame_name = "ed1"
    quality = 4
    card = [id, person, tag, print_number, background_name, frame_name, quality]
    return card

def rendermii(card_name):
    try:
        os.chdir(os.path.join(current_dir, "miis"))
        mii_image = Image.open(card_name + '.png')
        os.chdir(current_dir)
    except:
        os.chdir(current_dir)
        mii_image = Image.open('missingfile.png').convert("RGBA")
    return mii_image

def savemii(card_name):
    im = rendermii(card_name)
    image_name = 'viewmii.png'
    im.save(image_name)
    return image_name

def rendercard(card):
    ##["id", "name", "clan", print, "bg", "frame", quality]
    background = Image.open(card[4] + '.png')
    frame = Image.open(card[5] + '.png')
    clan_tag = card[2]
    card_id = card[0]
    card_name = card[1]
    print_number = str(card[3])

    overlay = Image.open('quality_' + str(card[6]) + '.png')
    return write_image(background,frame,clan_tag,card_id,card_name,print_number,overlay)

def savecard(card):
    im = rendercard(card)
    image_name = 'viewcard.png'
    im.save(image_name)
    return image_name


@client.command()
async def d(ctx):
    if not str(ctx.author.id) in accounts.keys():
        createaccount(str(ctx.author.id))
    elif time.time() - accounts[str(ctx.author.id)][0] < 300:
        formattedtime = time.gmtime(300 - (time.time() - accounts[str(ctx.author.id)][0]))
        await ctx.send(ctx.author.mention + ", you must wait ``" + time.strftime("%M minutes %S seconds", formattedtime) + "`` to drop again.")
        return
    accounts[str(ctx.author.id)][0] = time.time()
    os.chdir(os.path.join(current_dir, "miis"))
    drops = os.listdir()
    os.chdir(current_dir)
    random.shuffle(drops)
    cards = []
    for i in drops[0:3]:
        cards.append(generatecard(i[:-4]))
    merge(rendercard(cards[0]), rendercard(cards[1]), rendercard(cards[2]))
    timeout = time.time() + 15
    dropannouncement = await ctx.send(ctx.author.mention + " is dropping 3 cards!")
    dropmessage = await ctx.send(file=discord.File('drop.png'))
    await dropmessage.add_reaction('1\ufe0f\N{COMBINING ENCLOSING KEYCAP}')
    await dropmessage.add_reaction('2\ufe0f\N{COMBINING ENCLOSING KEYCAP}')
    await dropmessage.add_reaction('3\ufe0f\N{COMBINING ENCLOSING KEYCAP}')

    availablegrabs = ['1\ufe0f\N{COMBINING ENCLOSING KEYCAP}', '2\ufe0f\N{COMBINING ENCLOSING KEYCAP}', '3\ufe0f\N{COMBINING ENCLOSING KEYCAP}']
    nograbs = []

    def check(reaction, user):
        return user != dropmessage.author and str(reaction.emoji) in availablegrabs and not user in nograbs and reaction.message == dropmessage

    while len(availablegrabs) > 0:
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=30, check=check)
        except asyncio.TimeoutError:
            break
        nograbs.append(user)
        if not str(user.id) in accounts.keys():
            createaccount(str(user.id))
        if time.time() - accounts[str(user.id)][1] < 60:
            formattedtime = time.gmtime(60 - (time.time() - accounts[str(user.id)][1]))
            await ctx.send(user.mention + ", you must wait ``" + time.strftime("%M minutes %S seconds", formattedtime) + "`` to grab again.")
            continue
        if reaction.emoji == '1\ufe0f\N{COMBINING ENCLOSING KEYCAP}':
            cardgrabbed = cards[0]
            availablegrabs.remove('1\ufe0f\N{COMBINING ENCLOSING KEYCAP}')
        elif reaction.emoji == '2\ufe0f\N{COMBINING ENCLOSING KEYCAP}':
            cardgrabbed = cards[1]
            availablegrabs.remove('2\ufe0f\N{COMBINING ENCLOSING KEYCAP}')
        elif reaction.emoji == '3\ufe0f\N{COMBINING ENCLOSING KEYCAP}':
            cardgrabbed = cards[2]
            availablegrabs.remove('3\ufe0f\N{COMBINING ENCLOSING KEYCAP}')
        else:
            await ctx.send(user.mention + " your grab was somehow unrecognized. Show maxi, cuz this shouldnt happen.")
            print("A grab was somehow unrecognized. Show maxi, cuz this shouldnt happen!")
            return
        accounts[str(user.id)][1] = time.time()
        quality = random.choice([0,1,1,2,2,2,2,3,3,4])
        cardgrabbed[6] = quality
        accounts[str(user.id)][3].append(cardgrabbed)
        quality_message = ["Unfortunately, its condition is badly **damaged**.", "Unfortuntely, its condition is quite **poor**.", "It's in **good** condition.", "Great, it's in **excellent** condition!", "Wow, it appears to be in **mint** condition!"]
        await ctx.send(user.mention + " grabbed **" + cardgrabbed[1] + "** card ``" + cardgrabbed[0] + "``! " + quality_message[quality])
        with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
            json.dump(accounts, json_file, ensure_ascii=False)
        if time.time() > timeout:
            break
    await dropannouncement.edit(content = "*This drop has expired.*")
    return

@client.command()
async def c(ctx, person=None, tag=None): ##collection
    t=None
    p=None
    if person == None:
        person = str(ctx.author.id)
    elif tag != None:
        if len(tag) > 2:
            if tag[0:2] == 't:':
                t = tag[2:]
            elif tag[0:2] == 'p:':
                p = tag[2:]
    if person[0:2] == 't:':
        t = person[2:]
        person = str(ctx.author.id)
    if person[0:2] == 'p:':
        p = person[2:]
        person = str(ctx.author.id)
    person = checkuser(person)
    if person == None:
        await ctx.send(ctx.author.mention + " Error: This user was not found.")
        return
    try:
        print("t=" + t + " p=" + p)
    except:
        print("OK")
    cardsfound = copy.copy(accounts[person][3])
    if t != None and len(cardsfound) > 0:
        for card in accounts[person][3]:
            if len(t) > len(card[2]):
                cardsfound.remove(card)
                continue
            if not t.lower() in card[2].lower():
                cardsfound.remove(card)
    if p != None and len(cardsfound) > 0:
        for card in accounts[person][3]:
            if not card in cardsfound:
                continue
            if len(p) > len(card[1]):
                cardsfound.remove(card)
                continue
            if not p.lower() in card[1].lower():
                cardsfound.remove(card)

    msg1 = str(len(cardsfound)) + " cards found for <@" + person + ">\n"
    msg2 = ""
    if len(cardsfound) < 1:
        msg1 += '\n*empty*'
        embed=discord.Embed(title="Card Collection", description=msg1, color=0xFFFFFF)
        await ctx.send(embed=embed)
        return
    elif len(cardsfound) < 10:
        msg1 += 'Showing cards 1 - ' + str(len(cardsfound)) + "\n\n"
    else:
        msg2 = 'Showing cards 1 - 10\n\n'
    cardsfound.reverse()
    conditions = ["\u2606\u2606\u2606\u2606","\u2605\u2606\u2606\u2606","\u2605\u2605\u2606\u2606","\u2605\u2605\u2605\u2606","\u2605\u2605\u2605\u2605",]
    for card in cardsfound[0:min(10,len(cardsfound))]:
        msg2 += '``' + card[0] + '`` · ``' + conditions[card[6]] + '`` · ``#' + str(card[3]) + '`` · ' + card[2] + ' · **' + card[1] + '**\n'
    embed=discord.Embed(title="Card Collection", description=msg1+msg2, color=0xFFFFFF)
    embedmessage = await ctx.send(embed=embed)
    if len(cardsfound) < 11:
        return
    await embedmessage.add_reaction('\N{LEFTWARDS BLACK ARROW}')
    await embedmessage.add_reaction('\N{BLACK RIGHTWARDS ARROW}')
    author = str(ctx.author.id)
    start = 0
    done = False
    reactions = ['\N{LEFTWARDS BLACK ARROW}','\N{BLACK RIGHTWARDS ARROW}']
    def check(reaction, user):
        return str(user.id) == author and str(reaction.emoji) in reactions and reaction.message == embedmessage
    while done == False:
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=20, check=check)
        except asyncio.TimeoutError:
            return
        msg2 = "Showing cards "
        if reaction.emoji == '\N{LEFTWARDS BLACK ARROW}':
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
        msg2 += str(start+1) + " - " + str(start + 10) + "\n\n"
        for card in cardsfound[start:start + 10]:
            msg2 += '``' + card[0] + '`` · ``' + conditions[card[6]] + '`` · ``#' + str(card[3]) + '`` · ' + card[2] + ' · **' + card[1] + '**\n'
        embed=discord.Embed(title="Card Collection", description=msg1+msg2, color=0xFFFFFF)
        await embedmessage.edit(embed=embed)

@client.command()
async def lu(ctx, tag=None): ##lookup
    if tag==None:
        await ctx.send(ctx.author.mention + " Error: missing field.")
        return
    tag=tag.lower()
    cardsfound = []
    names = list(prints.keys())

    for x in names:
        if tag in x.lower() or tag in prints[x]["Clan"].lower() or tag in prints[x]["Tag"].lower() or tag in prints[x]["Alt Name"].lower():
            cardsfound.append([prints[x]["Tag"],x])

    if len(cardsfound) < 1:
        await ctx.send(ctx.author.mention + ", no results were found for *" + tag + "*.")
        return

    cardsfound.sort()
    limit = min(10,len(cardsfound))
    msg1 = ctx.author.mention + ", please select an option using the menu below.\n\n"
    msg2 = '**Showing cards 1 - ' + str(limit) + " of " + str(len(cardsfound)) + "**\n"

    for x in range(limit):
        msg2 += str(x+1) + ". " + cardsfound[x][0] + ' · **' + cardsfound[x][1] + '**\n'
    embed=discord.Embed(title="Card Lookup", description=msg1+msg2, color=0xFFFFFF)
    embedmessage = await ctx.send(embed=embed)
    many_pages = True
    if len(cardsfound) > 10:
        await embedmessage.add_reaction('\N{LEFTWARDS BLACK ARROW}')
        await embedmessage.add_reaction('\N{BLACK RIGHTWARDS ARROW}')
        many_pages = True
    reactions = ['\N{LEFTWARDS BLACK ARROW}','\N{BLACK RIGHTWARDS ARROW}']
    author = str(ctx.author.id)
    start = 0
    while True:
        tasks = [
        client.loop.create_task(client.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel), name="rrem"),
        client.loop.create_task(client.wait_for('reaction_add', check=lambda reaction, user: str(user.id) == author and str(reaction.emoji) in reactions and reaction.message == embedmessage and many_pages == True), name="radd")
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
            if reaction.emoji == '\N{LEFTWARDS BLACK ARROW}':
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
            msg2 = '**Showing cards ' + str(start+1) + ' - ' + str(start+10) + " of " + str(len(cardsfound)) + "**\n"
            for x in range(10):
                msg2 += str(x+1) + ". " + cardsfound[x+start][0] + ' · **' + cardsfound[x+start][1] + '**\n'
            embed=discord.Embed(title="Card Lookup", description=msg1+msg2, color=0xFFFFFF)
            await embedmessage.edit(embed=embed)
        else:
            user_message = result.content
            if not str(user_message).isdigit():
                continue
            if not int(user_message)+start-1 in range(start+limit):
                continue
            image_file = savemii(cardsfound[int(user_message)+start-1][1])
            file = discord.File(image_file)
            msg = "This is a placeholder." #TODO
            embed=discord.Embed(title="Card Info", description=msg, color=0x000000)
            embed.set_thumbnail(url="attachment://" + image_file)
            await ctx.send(file=file, embed=embed)
            return


@client.command()
async def b(ctx, id=None): ##burn
    if checkuser(str(ctx.author.id)) == None:
        await ctx.send(ctx.author.mention + " Error: Your MKWKaruta collection was not found.")
        return
    author = str(ctx.author.id)
    if len(accounts[author][3]) < 1:
        await ctx.send(ctx.author.mention + " Error: No cards found in your MKWKaruta")
        return
    quality_burnvalues = [2, 5, 10, 20, 40]
    if id==None:
        card = accounts[author][3][-1]
        id = card[0]
        image_file = savecard(card)
        file = discord.File(image_file)
        burnvalue = quality_burnvalues[card[6]]
        if card[3] < 100:
            burnvalue += 10
            if card[3] < 10:
                burnvalue += 10
    else:
        if not len(id)==6:
            await ctx.send(ctx.author.mention + "Error: this is an invalid 6 letter card ID")
            return
        cardfound = False
        for card in accounts[author][3]:
            if card[0] == id:
                cardfound = True
                image_file = savecard(card)
                file = discord.File(image_file)
                burnvalue = quality_burnvalues[card[6]]
                if card[3] < 100:
                    burnvalue += 10
                    if card[3] < 10:
                        burnvalue += 10
                break
        if cardfound == False:
            await ctx.send(ctx.author.mention + " Error: you do not own " + '``' + id + '``')
            return
    msg = "<@" + author + ">, by burning ``" + id + "`` you will receive:\n\n" + '\N{MONEY WITH WINGS}: **' + str(burnvalue) + '** Dollas\n'
    embed=discord.Embed(title="Burn Card", description=msg, color=0xFFFFFF)
    embed.set_thumbnail(url="attachment://" + image_file)
    options = ['\N{CROSS MARK}','\N{FIRE}']
    embedmessage = await ctx.send(file=file, embed=embed)
    await embedmessage.add_reaction('\N{CROSS MARK}')
    await embedmessage.add_reaction('\N{FIRE}')
    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in options and reaction.message == embedmessage
    try:
        reaction, user = await client.wait_for('reaction_add', timeout=20, check=check)
    except asyncio.TimeoutError:
        return
    if reaction.emoji == '\N{CROSS MARK}':
        msg = "<@" + author + ">, card burning for ``" + id + "`` has been canceled."
        embed=discord.Embed(title="Burn Card", description=msg, color=0xFF0000)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
    else:
        for card in accounts[author][3]:
            if card[0] == id:
                accounts[author][5] += burnvalue
                accounts[author][3].remove(card)
                break
        with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
            json.dump(accounts, json_file, ensure_ascii=False)
        msg = "<@" + author + ">, ``" + id + "`` has been successfully burned. \n You have recieved:\n\n" + '\N{MONEY WITH WINGS}: **' + str(burnvalue) + '** Dollas\n'
        embed=discord.Embed(title="Burn Card", description=msg, color=0x00FF2F)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
    return

@client.command()
async def give(ctx, giftee=None, id=None): ##give
    try:
        giftee = giftee[2:-1]
        if not giftee in accounts.keys():
            await ctx.send(ctx.author.mention + " Error: This user was not found.")
            return
        if giftee == str(ctx.author.id):
            await ctx.send(ctx.author.mention + " Error: You cannot gift a card to yourself")
            return
    except:
        await ctx.send(ctx.author.mention + " Error: This user is invalid.")
        return
    if checkuser(str(ctx.author.id)) == None:
        await ctx.send(ctx.author.mention + " Error: Your MKWKaruta collection was not found.")
        return
    author = str(ctx.author.id)
    if len(accounts[author][3]) < 1:
        await ctx.send(ctx.author.mention + " Error: No cards found in your MKWKaruta")
        return
    card = None
    if id==None:
        card = accounts[author][3][-1]
        id = card[0]
    else:
        if not len(id)==6:
            await ctx.send(ctx.author.mention + "Error: this is an invalid 6 letter card ID")
            return
        for c in accounts[author][3]:
            if c[0] == id:
                card = c
                break
        if c == None:
            await ctx.send(ctx.author.mention + " Error: you do not own " + '``' + id + '``')
            return
    msg = "<@" + giftee + ">, do you accept the gift of **" + id + "** from <@" + author + "> ?"
    embed=discord.Embed(title="Give Card", description=msg, color=0xFFFFFF)
    image_file = savecard(card)
    file = discord.File(image_file)
    embed.set_thumbnail(url="attachment://" + image_file)
    options = ['\N{CROSS MARK}','\N{WHITE HEAVY CHECK MARK}']
    embedmessage = await ctx.send(file=file, embed=embed)
    await embedmessage.add_reaction('\N{CROSS MARK}')
    await embedmessage.add_reaction('\N{WHITE HEAVY CHECK MARK}')
    def check(reaction, user):
        check1 = str(user.id) == giftee and str(reaction.emoji) in options and reaction.message == embedmessage
        check2 = str(user.id) == author and str(reaction.emoji) == '\N{CROSS MARK}' and reaction.message == embedmessage
        return check1 or check2
    try:
        reaction, user = await client.wait_for('reaction_add', timeout=20, check=check)
    except asyncio.TimeoutError:
        msg = "<@" + author + ">, card gifting for **" + id + "** to <@" + giftee + "> has timed out."
        embed=discord.Embed(title="Give Card", description=msg, color=0xFF0000)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
        return
    if reaction.emoji == '\N{CROSS MARK}':
        msg = "<@" + author + ">, card gifting for **" + id + "** to <@" + giftee + "> has been canceled."
        embed=discord.Embed(title="Give Card", description=msg, color=0xFF0000)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
    else:
        for i in range(len(accounts[author][3])):
            if accounts[author][3][i][0] == id:
                giftedcard = accounts[author][3].pop(i)
                accounts[giftee][3].append(giftedcard)
                break
        with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
            json.dump(accounts, json_file, ensure_ascii=False)
        msg = "<@" + author + ">, **" + id + "** has been successfully gifted to to <@" + giftee + ">."
        embed=discord.Embed(title="Give Card", description=msg, color=0x00FF2F)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
    return

@client.command()
async def mt(ctx, giftee=None): ##give
    try:
        giftee = giftee[2:-1]
        if not giftee in accounts.keys():
            await ctx.send(ctx.author.mention + " Error: This user was not found.")
            return
        if giftee == str(ctx.author.id):
            await ctx.send(ctx.author.mention + " Error: You cannot trade with yourself")
            return
    except:
        await ctx.send(ctx.author.mention + " Error: This user is invalid.")
        return
    if checkuser(str(ctx.author.id)) == None:
        await ctx.send(ctx.author.mention + " Error: Your MKWKaruta collection was not found.")
        return
    author = str(ctx.author.id)
    card = None
    msg = "<@" + giftee + ">, would you like to trade with <@" + author + "> ?"
    desc = "<@" + giftee + ">, please accept or decline the trade request with <@" + author + "> to continue."
    embed=discord.Embed(title="Trade Request", description=msg, color=0xFFFFFF)
    image_file = savecard(card)
    file = discord.File(image_file)
    embed.set_thumbnail(url="attachment://" + image_file)
    options = ['\N{CROSS MARK}','\N{WHITE HEAVY CHECK MARK}']
    embedmessage = await ctx.send(file=file, embed=embed)
    await embedmessage.add_reaction('\N{CROSS MARK}')
    await embedmessage.add_reaction('\N{WHITE HEAVY CHECK MARK}')
    def check(reaction, user):
        check1 = str(user.id) == giftee and str(reaction.emoji) in options and reaction.message == embedmessage
        check2 = str(user.id) == author and str(reaction.emoji) == '\N{CROSS MARK}' and reaction.message == embedmessage
        return check1 or check2
    try:
        reaction, user = await client.wait_for('reaction_add', timeout=20, check=check)
    except asyncio.TimeoutError:
        msg = "<@" + author + ">, card gifting for **" + id + "** to <@" + giftee + "> has timed out."
        embed=discord.Embed(title="Give Card", description=msg, color=0xFF0000)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
        return
    if reaction.emoji == '\N{CROSS MARK}':
        msg = "<@" + author + ">, card gifting for **" + id + "** to <@" + giftee + "> has been canceled."
        embed=discord.Embed(title="Give Card", description=msg, color=0xFF0000)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
    else:
        for i in range(len(accounts[author][3])):
            if accounts[author][3][i][0] == id:
                giftedcard = accounts[author][3].pop(i)
                accounts[giftee][3].append(giftedcard)
                break
        with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
            json.dump(accounts, json_file, ensure_ascii=False)
        msg = "<@" + author + ">, **" + id + "** has been successfully gifted to to <@" + giftee + ">."
        embed=discord.Embed(title="Give Card", description=msg, color=0x00FF2F)
        embed.set_thumbnail(url="attachment://" + image_file)
        await embedmessage.edit(embed=embed)
    return


@client.command()
async def i(ctx, user=None): ##inventory
    if user == None:
        user = str(ctx.author.id)
    user = checkuser(user)
    if user == None:
        await ctx.send(ctx.author.mention + " Error: This user was not found.")
        return
    embed=discord.Embed(title="Inventory", description="Items carried by <@" + user + ">", color=0x91FFFB)
    msg = '\N{MONEY WITH WINGS}: **' + str(accounts[user][5]) + '** Dollas\n'
    if len(accounts[user][4]) > 0:
        for item in accounts[user][4]:
            msg += "**" + itemshop[item][0] + "** · ``" + item + '``\n'
    embed.add_field(name="\u200b", value=msg, inline=False)
    await ctx.send(embed=embed)
    return

@client.command()
async def v(ctx, id=None):
    if checkuser(str(ctx.author.id)) == None:
        await ctx.send(ctx.author.mention + " Error: Your MKWKaruta collection was not found.")
        return
    author = str(ctx.author.id)
    conditions = ["\u2606\u2606\u2606\u2606","\u2605\u2606\u2606\u2606","\u2605\u2605\u2606\u2606","\u2605\u2605\u2605\u2606","\u2605\u2605\u2605\u2605",]
    card = None
    if id==None:
        if len(accounts[author][3]) < 1:
            await ctx.send(ctx.author.mention + " Error: No cards found in your MKWKaruta")
            return
        card = accounts[author][3][-1]
        account = author
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
        await ctx.send(ctx.author.mention + " Error: Card with id ``" + id + "`` does not exist.")
        return
    msg = '``' + card[0] + '`` · ``' + conditions[card[6]] + '`` · ``#' + str(card[3]) + '`` · ' + card[2] + ' · **' + card[1] + '**'
    desc = "Card owned by <@" + str(account) + ">\n\n" + msg
    embed = discord.Embed(title="View Card", description=desc, color=0xFFFFFF)
    image_file = savecard(card)
    file = discord.File(image_file)
    embed.set_image(url="attachment://" + image_file)
    await ctx.send(file=file, embed=embed)
    return



@client.command()
async def cd(ctx, user=None): ##inventory
    if user == None:
        user = str(ctx.author.id)
    user = checkuser(user)
    if user == None:
        await ctx.send(ctx.author.mention + " Error: This user was not found.")
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

@client.command()
async def daily(ctx): ##inventory
    user = str(ctx.author.id)
    if not str(user) in accounts.keys():
        createaccount(str(user))
    else:
        seconds = time.time() - accounts[str(user)][2]
        if seconds < 86400:
            dailytime = time.gmtime(86400 - seconds)
            await ctx.send(ctx.author.mention + ' **Daily** is available in ``' + time.strftime("%H hours, %M minutes, %S seconds", dailytime) + '``\n')
            return
    dailyreward = random.randrange(50,100)
    accounts[user][5] += dailyreward
    accounts[user][2] = time.time()
    with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
        json.dump(accounts, json_file, ensure_ascii=False)
    await ctx.send(ctx.author.mention + ' You have gained ``' + str(dailyreward) + '`` Dollas!\n')
    return

@client.command()
async def addbackground(ctx, id=None, background=None): ##give
    if background == None:
        await ctx.send(ctx.author.mention + " Error: maddbackground <card id> <item>.")
        return
    author = str(ctx.author.id)
    if checkuser(author) == None:
        await ctx.send(ctx.author.mention + " Error: Your MKWKaruta collection was not found.")
        return
    id = id.lower()
    background = background.lower()
    if len(accounts[author][3]) < 1:
        await ctx.send(ctx.author.mention + " Error: No cards found in your MKWKaruta")
        return
    if not len(id)==6:
        await ctx.send(ctx.author.mention + " Error: this is an invalid 6 letter card ID")
        return
    if not background in accounts[author][4]:
        await ctx.send(ctx.author.mention + " Error: You do not own ``" + background + "``")
        return
    for card in accounts[author][3]:
        if card[0] == id:
            newcard = copy.copy(card)
            newcard[4] = background
            desc = " <@" + str(author) + ">, would you like to use this background? You will lose: \n"
            desc += "```diff\n-1 " + background + "```"
            embed = discord.Embed(title="New Background", description=desc, color=0xFFFFFF)
            image_file = savecard(newcard)
            file = discord.File(image_file)
            embed.set_image(url="attachment://" + image_file)
            options = ['\N{CROSS MARK}','\N{WHITE HEAVY CHECK MARK}']
            embedmessage = await ctx.send(file=file, embed=embed)
            await embedmessage.add_reaction('\N{CROSS MARK}')
            await embedmessage.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            def check(reaction, user):
                return str(user.id) == author and str(reaction.emoji) in options and reaction.message == embedmessage
            try:
                reaction, user = await client.wait_for('reaction_add', timeout=20, check=check)
            except asyncio.TimeoutError:
                msg = "<@" + author + ">, This action has timed out."
                embed.add_field(name="\u200b", value=msg, inline=False)
                embed.color = 0xFF1100
                await embedmessage.edit(embed=embed)
                return
            if reaction.emoji == '\N{CROSS MARK}':
                msg = "<@" + author + ">, This action has been canceled."
                embed.add_field(name="\u200b", value=msg, inline=False)
                embed.color = 0xFF1100
                await embedmessage.edit(embed=embed)
                return
            else:
                if not background in accounts[author][4]:
                    msg = "<@" + author + ">, You do not own this background."
                    embed.add_field(name="\u200b", value=msg, inline=False)
                    embed.color = 0xFF1100
                    await embedmessage.edit(embed=embed)
                    return
                msg = "<@" + author + ">, This background has been applied!"
                embed.add_field(name="\u200b", value=msg, inline=False)
                embed.color = 0x00FF00
                card[4] = background
                accounts[author][4].remove(background)
                await embedmessage.edit(embed=embed)
                with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
                    json.dump(accounts, json_file, ensure_ascii=False)
                return
    await ctx.send(ctx.author.mention + " Error: you do not own " + '``' + id + '``')
    return

@client.command()
async def shop(ctx): ##itemshop
    user = str(ctx.author.id)
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

@client.command()
async def buy(ctx, item=None): ##itemshop
    author = str(ctx.author.id)
    if not author in accounts.keys():
        await ctx.send(ctx.author.mention + " Error: Your MKWKaruta account was not found. Drop or grab a card to start!")
        return
    if item==None:
        await ctx.send(ctx.author.mention + " Please use mbuy <itemid> to make a purchase. Use *mshop* to view a list of available items.")
        return
    item = item.lower()
    if not item in itemshop.keys():
        await ctx.send(ctx.author.mention + " The item with id ``" + item + "`` was not found. Use *mshop* to view a list of available items.")
        return
    embed=discord.Embed(title="Item Purchase", description="**" + itemshop[item][0] + "**\n*" + itemshop[item][2] + "*", color=0xFFFFFF)
    msg = "<@" + author + "> will **gain**\n"
    msg += "```diff\n+1 " + item + "```\n"
    msg2 = "<@" + author + "> will **lose**\n"
    msg2 += "```diff\n-" + str(itemshop[item][1]) + " Dollas" + "```\n"
    embed.add_field(name="\u200b", value=msg, inline=False)
    embed.add_field(name="\u200b", value=msg2, inline=False)
    options = ['\N{CROSS MARK}','\N{WHITE HEAVY CHECK MARK}']
    embedmessage = await ctx.send(embed=embed)
    await embedmessage.add_reaction('\N{CROSS MARK}')
    await embedmessage.add_reaction('\N{WHITE HEAVY CHECK MARK}')
    def check(reaction, user):
        return str(user.id) == author and str(reaction.emoji) in options and reaction.message == embedmessage
    try:
        reaction, user = await client.wait_for('reaction_add', timeout=20, check=check)
    except asyncio.TimeoutError:
        msg = "<@" + author + ">, The purchase has timed out."
        embed.add_field(name="\u200b", value=msg, inline=False)
        embed.color = 0xFF1100
        await embedmessage.edit(embed=embed)
        return
    if reaction.emoji == '\N{CROSS MARK}':
        msg = "<@" + author + ">, This purchase has been canceled."
        embed.add_field(name="\u200b", value=msg, inline=False)
        embed.color = 0xFF1100
        await embedmessage.edit(embed=embed)
    else:
        if accounts[author][5] < itemshop[item][1]:
            msg = "<@" + author + ">, You do not have the funds to make this purchase."
            embed.add_field(name="\u200b", value=msg, inline=False)
            embed.color = 0xFF1100
            await embedmessage.edit(embed=embed)
        else:
            accounts[author][5] = accounts[author][5] - itemshop[item][1]
            accounts[author][4].append(item)
            with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
                json.dump(accounts, json_file, ensure_ascii=False)
            msg = "<@" + author + ">, This purchase has been completed!"
            embed.add_field(name="\u200b", value=msg, inline=False)
            embed.color = 0x00FF00
            await embedmessage.edit(embed=embed)
    return

@client.command()
async def upgrade(ctx, id=None):
    author = str(ctx.author.id)
    if checkuser(author) == None:
        await ctx.send("<@" + author + "> Error: Your MKWKaruta collection was not found.")
        return
    success = ""
    done = False
    while done == False:
        if len(accounts[author][3]) < 1:
            await ctx.send("<@" + author + "> Error: No cards found in your MKWKaruta")
            return
        cardfound = None
        if id==None:
            cardfound = accounts[author][3][-1]
            id = cardfound[0]
            image_file = savecard(cardfound)
            file = discord.File(image_file)
        else:
            if not len(id)==6:
                await ctx.send("<@" + author + "> Error: This is an invalid 6 letter card ID")
                return
            for card in accounts[author][3]:
                if card[0] == id:
                    cardfound = card
                    image_file = savecard(card)
                    file = discord.File(image_file)
                    break
        if cardfound == None:
            await ctx.send("<@" + author + "> Error: You do not own " + '``' + id + '``')
            return
        old_condition = cardfound[6]
        if old_condition >= 4:
            await ctx.send("<@" + author + "> Error: This card is already in mint condition.")
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
        msg += "<@" + author + ">, upgrading the condition of ``" + id + "`` from **" + conditions[old_condition][0] + "** to **" + conditions[old_condition + 1][0]
        msg += "** has a **" + str(conditions[old_condition][2]) + "%** chance of succeeding. If this upgrade fails, the card's condition will not change.\n\n"
        msg += "Attempting the upgrade will cost the following resources:\n"
        msg += "```diff\n-" + str(conditions[old_condition][1]) + " Dollas```"
        embed=discord.Embed(title="Card Upgrade", description=msg, color=embedcolor)
        embed.set_thumbnail(url="attachment://" + image_file)
        embedmessage = await ctx.send(file=file, embed=embed)
        await embedmessage.add_reaction('\N{WRENCH}')
        def check(reaction, user):
            return str(user.id) == author and str(reaction.emoji) == '\N{WRENCH}' and reaction.message == embedmessage
        try:
            reaction, user = await client.wait_for('reaction_add', timeout=20, check=check)
        except asyncio.TimeoutError:
            print("TimeoutError")
            return
        if accounts[author][5] < conditions[cardfound[6]][1]:
            msg = "<@" + author + ">, you do not have enough Dollas to attempt this upgrade."
            embed=discord.Embed(title="Card Upgrade", description=msg, color=0xFF0000)
            embed.set_thumbnail(url="attachment://" + image_file)
            await embedmessage.edit(embed=embed)
            return
        accounts[author][5] = accounts[author][5] - conditions[cardfound[6]][1]
        rng = random.randrange(1,100)
        cardfound = None
        for card in accounts[author][3]:
            if card[0] == id:
                cardfound = card
                break
        if cardfound == None:
            await ctx.send("<@" + author + "> Error: You do not own " + '``' + id + '``')
            return
        if rng > conditions[old_condition][2]:
            success = "no"
        else:
            success = "yes"
            card[6] += 1
            if old_condition == 3:
                msg = "<@" + author + ">, ``" + id + "`` has been successfully upgraded to **mint** condition!"
                embed=discord.Embed(title="Card Upgrade", description=msg, color=0x00FF2F)
                image_file = savecard(card)
                file = discord.File(image_file)
                embed.set_image(url="attachment://" + image_file)
                await ctx.send(file=file, embed=embed)
                Done = True
                with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
                    json.dump(accounts, json_file, ensure_ascii=False)
                return
        with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
            json.dump(accounts, json_file, ensure_ascii=False)
    print("no!!!!!")
    return



@client.command()
async def help(ctx):
    msg = "**How to Play**\n\n"
    msg += "**Burn** `mb <id>` to destroy a card from your inventory.\n"
    msg += "**Drop** `md` to drop cards. Use one of the reactions to grab the corresponding card.\n"
    msg += "**Collection** `mc <@user> <t=tag>` to view a card collection.\n"
    msg += "**Cooldowns** `mcd` to view the cooldown times for Drop, Grab, and Daily Reward.\n"
    msg += "**Daily Reward** `mdaily` to get a daily reward.\n"
    msg += "**Give** `mg <@user> <id>` to gift a card to someone else.\n"
    msg += "**Inventory** `mi <@user>` to view an inventory\n"
    msg += "**Shop** `mshop` to view the item shop.\n"
    msg += "**Upgrade** `mupgrade <id>` to attempt a card upgrade.\n"
    msg += "**View** `mv <id>` to view a card."
    await ctx.send(msg)

##Administrator commands

@commands.has_permissions(administrator=True)
@client.command()
async def deleteallcollections(ctx):
    for person in accounts:
        accounts[person][3] = []
    with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
        json.dump(accounts, json_file, ensure_ascii=False)
    await ctx.send("Holy shit. Everyone's invintories have been deleted!")

@commands.has_permissions(administrator=True)
@client.command()
async def resetallprints(ctx):
    for card in prints:
        prints[card]["Print"] = 0
    await ctx.send("Wow. All card prints have been reset!")
    with codecs.open('prints.json', 'w', encoding='utf-8') as json_file:
        json.dump(prints, json_file, ensure_ascii=False)

@commands.has_permissions(administrator=True)
@client.command()
async def r(ctx):
    accounts[str(ctx.author.id)][0] = time.time()-2000
    accounts[str(ctx.author.id)][1] = time.time()-700
    accounts[str(ctx.author.id)][2] = time.time()-87000
    with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
        json.dump(accounts, json_file, ensure_ascii=False)
    await ctx.send('Your cooldowns have been reset.')

@client.command()
async def m(ctx, money):
    accounts[str(ctx.author.id)][5] = money
    with codecs.open('accounts.json', 'w', encoding='utf-8') as json_file:
        json.dump(accounts, json_file, ensure_ascii=False)
    await ctx.send('Your balance has been set to ' + str(money))

@client.command()
async def testcard(ctx, name="", bg="bg_gray", frame="ed1", quality=4):
    try:
        tag = prints[name]["Tag"]
    except:
        await ctx.send('Error: this card was not found (try using different capitalization). ')
        return
    card = ["000000", name, tag, 0, bg, frame, 4]
    desc = "Test Card"
    conditions = ["\u2606\u2606\u2606\u2606","\u2605\u2606\u2606\u2606","\u2605\u2605\u2606\u2606","\u2605\u2605\u2605\u2606","\u2605\u2605\u2605\u2605",]
    msg = '``' + card[0] + '`` · ``' + conditions[card[6]] + '`` · ``#' + str(card[3]) + '`` · ' + card[2] + ' · **' + card[1] + '**\n'
    embed = discord.Embed(title="View Card", description=desc, color=0xFFFFFF)
    embed.add_field(name="\u200b", value=msg, inline=False)
    image_file = savecard(card)
    file = discord.File(image_file)
    embed.set_image(url="attachment://" + image_file)
    await ctx.send(file=file, embed=embed)
    return



@commands.has_permissions(administrator=True)
@client.command()
async def getfcs(ctx):
    json = list(prints.keys())
    os.chdir(os.path.join(current_dir, "miis"))
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
    os.chdir(current_dir)
    with codecs.open('missingimageswithfcs.txt', 'w', encoding='utf-8') as f:
        f.write(msg)
    await ctx.send("Saved to missingimageswithfcs.txt")
    msg = "Missing FCs from " + "\n".join(missingfcs)
    with codecs.open('missingfcs.txt', 'w', encoding='utf-8') as f:
        f.write(msg)
    return

@commands.has_permissions(administrator=True)
@client.command()
async def checkduplicates(ctx):
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

@commands.has_permissions(administrator=True)
@client.command()
async def images(ctx):
    json = list(prints.keys())
    os.chdir(os.path.join(current_dir, "miis"))
    allprints = os.listdir()
    lines = []
    for name in json:
        if prints[name]["Tag"] != "F/A":
            imgname = name + ".png"
            if not os.path.exists(imgname):
                lines.append(prints[name]["Tag"] + " " + name + "\n")
    os.chdir(current_dir)
    lines.sort()
    t = time.asctime(time.gmtime())
    msg = str(len(lines)) + " missing mii pictures\n"
    for line in lines:
        msg += line
    await ctx.send(msg[0:1999])
    await ctx.send(msg[1999:])



client.run('')
