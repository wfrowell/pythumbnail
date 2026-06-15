import os, sys, json, re, tkinter
from ossapi import Ossapi, User, Beatmap, Domain
from tkinter import filedialog

tkinter.Tk().withdraw()


def getBeatmapsPath():
    print('Select your beatmaps directory.')
    return filedialog.askdirectory()


try:
    config = json.load(open('config.json'))
    path = config['beatmaps_path']
except KeyError:
    print('Select the your osu! beatmaps folder')
    beatmaps_path = filedialog.askdirectory()

    config = dict()
    config['beatmaps_path'] = beatmaps_path

    with open('config.json', 'w') as f:
        f.write(json.dumps(config))

    config = json.load(open('config.json'))
except FileNotFoundError:
    with open('config.json', 'x') as f:
        contents = {
            'version': '1.4',
            'beatmaps_path': getBeatmapsPath(),
            # 'ID': 16965,  # I think this is necessary but also ok to push with
            'ID': 0,
            'SECRET': ''
        }

        f.write(json.dumps(contents, indent=4))

    config = json.load(open('config.json'))
    input(
        'If you have an API v2 ID and secret, enter them in the config file.')
    sys.exit() # prevents it from continuing and erroring out.


if config['SECRET'] == '' or config['ID'] == 0:
    input(
        'If you have an API v2 ID and secret, enter them in the config file.')
    sys.exit() # prevents it from continuing and erroring out.

    #api = Ossapi(config['ID'],
    #             config['SECRET'],
    #             redirect_uri='http://localhost:4444/',
    #             grant='authorization',
    #             domain=Domain.OSU)
else:
    api = Ossapi(config['ID'], config['SECRET'])


# returns ID and mode if available from a beatmap, user, or score URL
def convertURL(url: str):
    suffix = url[19:]
    params = suffix.split('/')

    if params[0] == 'b' or params[0] == 'beatmaps':  # beatmap [diff ID]
        return [params[1]]
    elif params[0] == 'beatmapsets':  # beatmapset [diff ID, mode]
        return [params[2], params[1].split('#')[1]]
    elif params[0] == 'u' or params[0] == 'users':  # user [user ID]
        return [params[1]]
    elif params[0] == 'scores':  # score [score ID, mode]
        return [params[2], params[1]]
    else:
        return list()


def getScore(url):
    # provide this yourself, functionality for lazer login may come tho
    api = Ossapi(config['ID'], config['SECRET'])
    scoreID = convertURL(url)
    return api.score_mode(scoreID[1], int(scoreID[0]))


def getUser(url: str = str(None), username: str = str(None)) -> User:
    api = Ossapi(config['ID'], config['SECRET'])

    if username:
        return api.user(username)
    else:
        uid = convertURL(url)[0]
        return api.user(uid)


def getBeatmap(url: str = str(None), beatmapHash: str = str(None)) -> Beatmap:
    api = Ossapi(config['ID'], config['SECRET'])

    if beatmapHash:
        return api.beatmap(checksum=beatmapHash)
    else:
        bid = convertURL(url)[0]
        return api.beatmap(int(bid))
