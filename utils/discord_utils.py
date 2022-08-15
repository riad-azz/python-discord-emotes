import os
from os import path
from time import sleep
from tkinter import PhotoImage

import requests
from PIL import Image, ImageOps, ImageDraw


# ----------- LOCAL UTILS -----------
def load_avatar(url):
    avatar_path = "./data/avatar/avatar.png"
    default_path = "./data/avatar/avatar.png"
    if not path.exists("./data/avatar/avatar_default.png"):
        return PhotoImage(file=default_path)

    return PhotoImage(file=avatar_path)


def emote_fromJson(emotes_json, server_id):
    emotes = []
    for emote in emotes_json:
        if emote['available']:
            emote_id = emote['id']
            emote_file = server_id + "_" + emote_id + ".png"
            emote_name = emote['name']
            is_gif = emote["animated"]
            emote_thumbnail = f"https://cdn.discordapp.com/emojis/{emote_id}.png?size=56&quality=lossless"
            emote_url = None
            if is_gif:
                emote_url = f"https://cdn.discordapp.com/emojis/{emote_id}.gif?size=56&quality=lossless"
            else:
                emote_url = emote_thumbnail

            emote_obj = {"id": emote_id,
                         "server_id": server_id,
                         "name": emote_name,
                         "file_name": emote_file,
                         "is_gif": is_gif,
                         "thumbnail": emote_thumbnail,
                         "url": emote_url}
            emotes.append(emote_obj)

    return emotes


def clip_image(old_path, new_path=None):
    size = (64, 64)
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.pieslice((0, 0) + size, start=90, end=-90, fill=255)

    box = (0, 0, size[0] // 2, size[1])
    cropped_image = mask.crop(box)
    first_half = cropped_image.copy()
    second_half = ImageOps.mirror(first_half)
    image_size = first_half.size

    perfect_circle = Image.new('L', (2 * first_half.size[0], first_half.size[1]), 255)
    perfect_circle.paste(first_half, (0, 0))
    perfect_circle.paste(second_half, (image_size[0], 0))

    with Image.open(old_path) as im:
        output = ImageOps.fit(im, perfect_circle.size, centering=(0.5, 0.5), bleed=0.04)
        output.putalpha(perfect_circle)

        save_path = old_path
        if new_path is not None:
            save_path = new_path
        output.save(save_path)


# ----------- DISCORD API UTILS -----------


def fetch_user(token):
    HEADERS = {"authorization": token}

    URL = "https://discordapp.com/api/users/@me"
    response = requests.get(url=URL, headers=HEADERS)

    if response.status_code != 200:
        raise Exception("Failed to fetch user, please make sure your auth token is correct.")

    user = response.json()
    return user


def fetch_servers(token):
    HEADERS = {"authorization": token}

    URL = "https://discordapp.com/api/users/@me/guilds"
    response = requests.get(url=URL, headers=HEADERS)

    if response.status_code != 200:
        raise Exception("Failed to fetch servers")

    guilds = response.json()
    return guilds


def fetch_channels(token, guild_id):
    HEADERS = {"authorization": token}

    URL = f"https://discordapp.com/api/guilds/{guild_id}/channels"
    response = requests.get(url=URL, headers=HEADERS)

    if response.status_code != 200:
        raise Exception("Failed to fetch channels")

    channels = response.json()
    return channels


def fetch_server_emotes(token, guild_id):
    HEADERS = {"authorization": token}

    URL = f"https://discordapp.com/api/guilds/{guild_id}/emojis"
    response = requests.get(url=URL, headers=HEADERS)

    if response.status_code != 200:
        raise Exception("Failed to fetch server emotes")

    emotes = response.json()
    return emotes


def fetch_all_servers_emotes(token, guilds):
    guilds_emotes = dict()
    for guild in guilds:
        name = guild["name"]
        guild_id = guild['id']
        try:
            guilds_emotes[name] = fetch_server_emotes(token, guild_id)
        except:
            raise Exception("Failed to fetch servers emotes")
        sleep(1)

    return guilds_emotes


def download_avatar(url, save_path='./data/avatar/avatar.png'):
    if not path.exists("./data/"):
        os.mkdir("./data/")
    if not path.exists("./data/avatar/"):
        os.mkdir("./data/avatar/")

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    try:
        img_data = requests.get(url, headers=HEADERS).content
        with open(save_path, 'wb') as handler:
            handler.write(img_data)
    except:
        raise Exception("Failed to download user avatar")

    clip_image(save_path)


def download_image(url, save_dir='./', img_name="image.png"):
    if not path.exists(save_dir):
        os.mkdir(save_dir)

    save_path = save_dir + img_name
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    try:
        img_data = requests.get(url, headers=HEADERS).content
        with open(save_path, 'wb') as handler:
            handler.write(img_data)
    except:
        raise Exception("Failed to download image")


def download_emote(download_obj):
    save_dir = "./data/emotes/"

    if not path.exists("./data/"):
        os.mkdir("./data/")

    if not path.exists(save_dir):
        os.mkdir(save_dir)

    img_name = download_obj["file_name"]
    url = download_obj["url"]

    save_path = save_dir + img_name
    if path.exists(save_path):
        return

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

    try:
        img_data = requests.get(url, headers=HEADERS).content
        with open(save_path, 'wb') as handler:
            handler.write(img_data)
    except:
        raise Exception("Failed to download emotes")
