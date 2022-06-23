import time
import string
import discord
import json
import os
import asyncio
import time
import random
import string
import copy
import collections
import codecs
from PIL import Image, ImageDraw, ImageFont
from discord.ext import commands
from datetime import date
from random import choice, shuffle
from discord import Client, Member, Guild
from discord.utils import get
from os import listdir
from os.path import isfile, join

bot = commands.Bot(command_prefix=['m','M'], help_command=None, case_insensitive=True) #The original karuta bot uses letters, so i'm keeping them for now.

CURRENT_DIR = os.getcwd()

IMAGE_DIR = f"{CURRENT_DIR}/card_gen/"
JSON_DIR=f"{CURRENT_DIR}/bot_data/"
MII_DIR=f"{CURRENT_DIR}/miis/"

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
    "Conditions": ["\u2606\u2606\u2606\u2606","\u2605\u2606\u2606\u2606","\u2605\u2605\u2606\u2606","\u2605\u2605\u2605\u2606","\u2605\u2605\u2605\u2605",]
  }

with codecs.open(f'{JSON_DIR}prints.json', encoding='utf-8') as f:
    prints = json.load(f)

with codecs.open(f'{JSON_DIR}accounts.json', encoding='utf-8') as f:
    accounts = json.load(f)

for object in [prints, accounts]:
  json.dumps(object, ensure_ascii=False)

class ImageFunctions:
    def write_image(background,frame,clan_tag,card_id,card_name,print_number,overlay):

        mii = ImageFunctions.render_mii(card_name)
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

    def new_card_id(): #CHECK - MUST CHECK IF ID DOESNT EXIST
        id = ""
        for i in range(6):
            id += random.choice(string.ascii_lowercase)
        if id in [user[3][0] for user in accounts]:
            id = ImageFunctions.new_card_id()
        return id

    def new_drop(num_cards):
        drops = os.listdir("miis")
        random.shuffle(drops)
        cards, card_images = [], []
        for i in drops[:num_cards]:
            new_card = ImageFunctions.generate_card(i[:-4])
            cards.append(new_card)
            card_images.append(ImageFunctions.render_card(new_card))
        img = ImageFunctions.merge_images(card_images)
        return [cards, img]

    def merge_images(images):
        w = images[0].size[0] + images[1].size[0] + images[2].size[0]
        h = max(images[0].size[1], images[1].size[1], images[2].size[1])
        im = Image.new("RGBA", (w, h))
        x = 0
        for i in images:
            im.paste(i, (x, 0))
            x += i.size[0]
        return im

    def generate_card(person):
        ##["id", "name", "clan", print, "bg", "frame", quality, tag, albums]
        id = ImageFunctions.new_card_id()
        clan_tag = prints[person]["Clan Tag"]
        print_number = prints[person]["Print"] + 1
        background_name = "bg_gray"
        frame_name = "ed1"
        quality = 4

        card = [id, person, clan_tag, print_number, background_name, frame_name, quality, None, []]
        return card

    def render_mii(card_name):
        try:
            mii_image = Image.open(f'{MII_DIR}{card_name}.png')
        except: #make sure you catch only the needed error.
            mii_image = Image.open('missingfile.png').convert("RGBA")
        return mii_image

    def save_mii(card_name):
        im = ImageFunctions.render_mii(card_name)
        image_name = 'viewmii.png'
        im.save(image_name)
        return image_name

    def render_card(card):
        ##["id", "name", "clan", print, "bg", "frame", quality]
        background = Image.open(f'{IMAGE_DIR}{card[4]}.png')
        frame = Image.open(f'{IMAGE_DIR}{card[5]}.png')
        card_id,card_name,clan_tag,card_number = card[0:4]

        overlay = Image.open(f'{IMAGE_DIR}quality_{str(card[6])}.png')
        card=ImageFunctions.write_image(background,frame,clan_tag,card_id,card_name,str(card_number),overlay)
        return card

    def save_card(card):
        im = ImageFunctions.render_card(card)
        image_name = 'viewcard.png'
        im.save(image_name)
        return image_name

class StringFunctions:
    #If arg user_id is a mention, it will extract only the id str
    #if arg user_id is not in accounts.json, return None
    def check_user(user_id):
        if len(str(user_id)) > 4 and str(user_id)[0:2] == '<@':
            user_id = "".join([letter for letter in user_id if letter.isdigit()]) #sometimes mentions can be in the form <@!numbers>
        if not user_id in accounts.keys():
            return None
        return user_id

    #Will be used later
    def listargs(arg0,arg1,arg2,arg3,arg4,arg5):
        args = [arg0,arg1,arg2,arg3,arg4,arg5]
        l = []
        for i in args:
            if not i==None:
                l.append(i.lower())
        return l

    #Will be used later
    def list_to_string(l):
        str1 = " "
        return (str1.join(l))
