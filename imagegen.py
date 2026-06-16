import os, sys, subprocess, json, shutil, requests, tkinter
import rosu_pp_py as rosu
from zipfile import *
from ossapi import Ossapi, Score, Beatmap, Beatmapset, mod
from osrparse import Mod
from tkinter import filedialog
from datetime import datetime
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, ImageColor, ImageFilter

# get font with size because yeah
# possible problem might be that it has to go through the file system more than I'd like, could be an area of slowdown
# solution would either be to find a way to open the font into a vartiable and change the size during use or somehow cache the file upon first use, maybe it even already does that
getFont = lambda x: ImageFont.truetype(__tempPath('assets/Font/NotoSans-Bold.ttf'), size=x)


# only gets main background from beatmapset
def __dlImageFromBeatmapID(beatmapset_id):
    req = requests.get(
        f'https://assets.ppy.sh/beatmaps/{beatmapset_id}/covers/fullsize.jpg',
        stream=True)
    req.raw.decode_content = True

    with open('tempbkg.jpg', 'wb') as file:
        shutil.copyfileobj(req.raw, file)


def __dlAvatarFromUID(user_id):
    req = requests.get(f'https://a.ppy.sh/{user_id}', stream=True)
    req.raw.decode_content = True

    with open('tempavatar.jpg', 'wb') as file:
        shutil.copyfileobj(req.raw, file)


# https://stackoverflow.com/a/11291419/20501327
def __roundCorners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im


def __modIcons(score: Score):
    if len(score.mods) == 0: return False

    modlist = []
    
    if isinstance(score.mods[0], str):
        modlist = score.mods
        # https://stackoverflow.com/a/9475354
    else:
        for mod in score.mods:
            modlist.append(mod.acronym)
        

    totalWidth = (91 * len(modlist)) - 1

    im = Image.new('RGBA', (totalWidth, 88))

    i = 0
    for modname in modlist:
        modIcon = Image.open(
            f'./assets/Mods/selection-mod-{modname}@2x.png').resize( (90, 88) )
        im.paste(modIcon, (i * 91, 0))
        i += 1  # python should have increment/decrement :(

    return im


def __dropShadow(output, coords: tuple, text, textLength, font):
    im = Image.new('RGBA', (int(textLength) + 20, 1000))
    draw = ImageDraw.Draw(im)

    draw.text((10, 0), text, fill='black', font=font)

    im = im.filter(ImageFilter.GaussianBlur(7))

    output.paste(im, (coords[0] - 10, coords[1]), im)


def __textLen(draw, text, font):
    return int(draw.textlength(text, font))


# https://stackoverflow.com/a/51061279/20501327
def __tempPath(relative_path):
    """ returns a path that works for the compiled code using sys._MEIPASS """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def calculateSR(score: Score):
    if not score.beatmap or not score.beatmapset:
        print('no beatmap found')
        return
    
    if score.mods == [] and score.beatmap: 
        return score.beatmap.difficulty_rating

    config = json.load(open('config.json'))
    calc = rosu.Difficulty(mods=score.mods)

    for (dirpath, dirnames, filenames) in os.walk(config['beatmaps_path']):
        for f in filenames:
            if f == f'{score.beatmapset.artist} - {score.beatmapset.title} ({score.beatmapset.creator}) [{score.beatmap.version}].osu':
                beatmap = rosu.Beatmap(content=f.read())

    print(
        'Required beatmap not found in beatmaps folder. Select the .osz or .osu file.'
    )
    while True:
        path = filedialog.askopenfilename()

        if type(path) is tuple:
            print('exiting without calculating star rating...')
            if score.beatmap:
                return score.beatmap.difficulty_rating
        elif path.endswith('.osz'):
            with ZipFile(path) as z:
                f = z.open(
                    f'{score.beatmapset.artist} - {score.beatmapset.title} ({score.beatmapset.creator}) [{score.beatmap.version}].osu'
                )
            break
        elif path.endswith('.osu'):
            f = open(path)
            break
        else:
            print('invalid file.')
            continue

    beatmap = rosu.Beatmap(content=f.read())
    return f'{calc.calculate(beatmap).stars:.2f}'


def imageGen(score: Score):
    if not score.beatmapset:
        score.beatmapset = Beatmapset()

    if not score.beatmap:
        score.beatmap = Beatmap()

    # open background into bkgImage
    beatmapset_id = score.beatmapset.id
    __dlImageFromBeatmapID(beatmapset_id)
    bkgImage = Image.open('tempbkg.jpg').convert('RGBA')

    # open avatar into avatarImage
    user_id = score.user_id
    __dlAvatarFromUID(user_id)
    avatarImage = Image.open('tempavatar.jpg').convert('RGBA')

    # blur background slightly, resize to 1080p, and locally save image, and remove jpg
    bkgImage = bkgImage.resize((1920, 1080))
    bkgImage = bkgImage.filter(ImageFilter.GaussianBlur(4))

    # bkgImage.save('tempbkg.png')
    os.remove(os.path.abspath(os.getcwd()) + '/tempbkg.jpg')

    # round corners of avatar and locally save image, and remove jpg
    # avatarImage = avatarImage.resize((192, 192)) # only if 720p
    avatarImage = __roundCorners(avatarImage, 35)

    os.remove(os.path.abspath(os.getcwd()) + '/tempavatar.jpg')

    # open ranking icon
    rankIcon = Image.open(
        __tempPath(f'assets/Rankings/ranking-{score.rank.value}.png') ).resize( (480, 626) )

    # generate mod icons
    modIcons = __modIcons(score)
    if modIcons:
        x = (1920 / 2) - (modIcons.width / 2)
        y = 624  # 1080/2 - 132/2, then moved down by 150px

    # finally putting together the actual image
    output = Image.new('RGBA', (1920, 1080))

    output.paste(bkgImage, (0, 0))
    output.paste(rankIcon, (18, 248), rankIcon)
    output.paste(
        avatarImage, (832, 362), avatarImage
    )  # 1920/2 - 256/2, 1080/2 - 256/2 to get upper left corner of centered image, then moved up by 50px
    if modIcons: output.paste(modIcons, (int(x), y), modIcons)

    # Text
    draw = ImageDraw.Draw(output)

    # Might be worth saving the strings to another variable also to cut down on processing
    tempFont = getFont(72)

    # Artist - Title; centered towards the top
    s = 96
    length = __textLen(draw,
                       f'{score.beatmapset.artist} - {score.beatmapset.title}',
                       font=getFont(s))

    # Prevents text from extending past screen boundaries by scaling it down until it fits
    while length > 1820:
        s = int(s - (s / length))  # im such a genius fr
        length = __textLen(
            draw,
            f'{score.beatmapset.artist} - {score.beatmapset.title}',
            font=getFont(s))

    # drop shadow
    coords = (int((1920 - length) / 2), 60)

    __dropShadow(output, coords,
                 f'{score.beatmapset.artist} - {score.beatmapset.title}',
                 length, getFont(s))
    draw.text(coords,
              f'{score.beatmapset.artist} - {score.beatmapset.title}',
              fill='white',
              font=getFont(s),
              stroke_width=2,
              stroke_fill='black')

    # [Difficulty]; smaller text, right under artist/title
    length = __textLen(draw, f'[{score.beatmap.version}]', font=getFont(64))
    coords = (int((1920 - length) / 2), 70 + s)

    __dropShadow(output, coords, f'[{score.beatmap.version}]', length,
                 getFont(64))
    draw.text(coords,
              f'[{score.beatmap.version}]',
              fill='white',
              font=getFont(64),
              stroke_width=2,
              stroke_fill='black')

    # ###pp; might be worth trying to make the pp number a diff color later
    if score.pp != None:
        text = f'{round(score.pp)}pp' if score.beatmapset.status == 1 else f'{round(score.pp)}pp (if ranked)'

        length = __textLen(draw, f'{round(score.pp)}pp', font=tempFont)

        __dropShadow(output, (800 - length, 360), f'{round(score.pp)}pp',
                     length, tempFont)
        draw.text((800 - length, 360),
                  f'{round(score.pp)}pp',
                  fill='white',
                  font=tempFont,
                  stroke_width=2,
                  stroke_fill='black')

    # ### BPM; subtracting length aligns text to right
    length = __textLen(draw, f'{score.beatmap.bpm} BPM', font=tempFont)

    __dropShadow(output, (800 - length, 480), f'{score.beatmap.bpm} BPM',
                 length, tempFont)
    draw.text((800 - length, 480),
              f'{score.beatmap.bpm} BPM',
              fill='white',
              font=tempFont,
              stroke_width=2,
              stroke_fill='black')

    # ##.##%; acc
    length = __textLen(draw, f'{(score.accuracy * 100):.2f}%', font=tempFont)

    __dropShadow(output, (800 - length, 600), f'{(score.accuracy * 100):.2f}%',
                 length, tempFont)
    draw.text((800 - length, 600),
              f'{(score.accuracy * 100):.2f}%',
              fill='white',
              font=tempFont,
              stroke_width=2,
              stroke_fill='black')

    # Username;
    __dropShadow(output, (1120, 360), f'{score.user().username}', 1000,
                 tempFont)
    draw.text((1120, 360),
              f'{score.user().username}',
              fill='white',
              font=tempFont,
              stroke_width=2,
              stroke_fill='black')

    # #.##☆; sr
    starRating = calculateSR(score)  # __scaledDifficulty(score)

    length = __textLen(draw, f'{starRating}',
                       font=tempFont)  # accounts for star placement as well

    __dropShadow(output, (1120, 480), f'{starRating}', length, tempFont)
    draw.text((1120, 480),
              f'{starRating}',
              fill='white',
              font=tempFont,
              stroke_width=2,
              stroke_fill='black')

    star = Image.open( __tempPath('assets/SRstar.png') ).resize((80, 80)).convert('RGBA')
    output.paste(star, (1124 + round(length), 480), star)

    # ####x; combo
    __dropShadow(output, (1120, 600), f'{score.max_combo}x', 1000, tempFont)
    draw.text((1120, 600),
              f'{score.max_combo}x',
              fill='white',
              font=tempFont,
              stroke_width=2,
              stroke_fill='black')

    # comment;
    comment = input("Enter the comment to be added. If none, leave blank.\n> ")
    if comment:
        length = __textLen(draw, comment, font=getFont(80))
        coords = (int((1920 - length) / 2), 840)

        __dropShadow(output, coords, comment, length, getFont(80))
        draw.text(coords,
                  comment,
                  fill='white',
                  font=getFont(80),
                  stroke_width=2,
                  stroke_fill='black')


    filename = f'{score.user().username}_{score.beatmapset.title}'

    if not os.path.exists('./output'):
        os.makedirs('./output')
        
    if os.path.exists(f'{os.path.abspath(os.getcwd())}output/{filename}'):
        os.remove(f'{os.path.abspath(os.getcwd())}output/{filename}')

    output.save(f'output/{filename}.png')
    output.show()


    return f'output/{filename}'
