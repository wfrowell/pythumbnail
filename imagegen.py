import os, sys, json, shutil, requests, re
import rosu_pp_py as rosu
from ossapi import Score, Beatmap, Beatmapset
from ossapi.models import NonLegacyMod
# from osrparse import Mod
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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

    modIconList = []

    i = 0
    for mod in score.mods:
        if isinstance(mod, str):
            try:
                modIconList.append( Image.open(
                    f'./assets/Mods/selection-mod-{mod}@2x.png').resize( (90, 88) )
                )
            except:
                continue
        elif isinstance(mod, NonLegacyMod):
            try:
                modIconList.append( Image.open(
                    f'./assets/Mods/selection-mod-{mod.acronym}@2x.png').resize( (90, 88) )
                )
            except:
                continue

    modCount = len(modIconList) - 1
    modWidth = 91

    # if there's more than 4 mod icons, stack them
    if modCount >= 4:
        # the higher this last number is, the tighter the mods will be stacked together
        modWidth -= modCount * 7

    if modCount >= 1:
        # adjust width to fit the last mod
        modWidth = (modWidth * (modCount - 1) ) + 91 - 1

    im = Image.new('RGBA', (modWidth, 88))

    for modIcon in modIconList:
        if i == modCount:
            # adjust width to fit the last mod
            im.paste(modIcon, ( ((i - 1) * modWidth) + 91, 0), modIcon)
        else:
            im.paste(modIcon, (i * modWidth, 0), modIcon)
        i += 1  # python should have increment/decrement :(

    return im


def __dropShadow(output, coords: tuple, text, textLength, font):
    im = Image.new('RGBA', (int(textLength) + 20, 1000))
    draw = ImageDraw.Draw(im)

    draw.text((10, 0), text, fill='black', font=font)

    im = im.filter(ImageFilter.GaussianBlur(7))

    output.paste(im, (coords[0] - 10, coords[1]), im)

# maybe possibly thing
# def __shapeDropShadow(output, coords: tuple, shape: Image.Image):
#     im = Image.new('RGBA', shape.size)
#     draw = ImageDraw.Draw(im)

#     draw.bitmap(coords, im.tobitmap())


def __textLen(draw, text, font):
    return int(draw.textlength(text, font))


# https://stackoverflow.com/a/51061279/20501327
def __tempPath(relative_path):
    base_path = os.path.abspath(".")

    return os.path.join( base_path, os.path.normpath(relative_path) )


def __convertMods(mods: list[NonLegacyMod]) -> list[str]:
    """converts an ossapi Mod list to a rosu mod dict.

    Args:
        mods (Mod): the ossapi Mod list

    Returns:
        list(str): list of mod acronym strings
    """

    output = []
    for m in mods:
        output.append(m.acronym)
    return output


def __cleanFilename(filename: str) -> str:
    # 1. Define invalid characters for Windows/Linux/macOS
    # < > : " / \ | ? * and control characters (0-31)
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    
    # 2. Replace invalid characters with an underscore
    cleaned = re.sub(invalid_chars, '_', filename)
    
    # 3. Optional: Prevent filenames from ending in spaces or periods (Windows constraint)
    cleaned = cleaned.strip('. ')
    
    # 4. Fallback if the filename becomes completely empty
    return cleaned if cleaned else "untitled"


def calculateSR(score: Score):
    if score.beatmap == None:
        print('No beatmap found for score.')
        return

    if score.mods == []:
        return f'{score.beatmap.difficulty_rating:.2f}'
    
    config = json.load(open('config.json'))
    beatmap = None

    for dirname in os.listdir(config['beatmaps_path']):
        # find the folder containing the beatmap
        if str(dirname).split('/')[-1].startswith( str(score.beatmap.beatmapset_id) ):
            for f in os.listdir(os.path.join(config['beatmaps_path'], dirname)):
                if str(f).find(score.beatmap.version) != -1:
                    beatmap = rosu.Beatmap( path=os.path.join(config['beatmaps_path'], dirname, f) )
                    break
        
        if beatmap != None:
            break

    if beatmap == None:
        print('Beatmap not found locally.')
        return

    calc = rosu.Difficulty( mods=__convertMods(score.mods) )
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

    star = Image.open( __tempPath('assets/SRstar.png') ).resize((60, 60)).convert('RGBA')
    # __shapeDropShadow(output, (1120, 500), star)
    output.paste(star, (1124 + round(length), 500), star)

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


    filename = __cleanFilename( f'{score.user().username} - {score.beatmapset.title}' )

    if not os.path.exists('./output'):
        os.makedirs('./output')
        
    if os.path.exists(f'{os.path.abspath(os.getcwd())}output/{filename}'):
        print('Replacing existing thumbnail with same filename.')
        os.remove(f'{os.path.abspath(os.getcwd())}output/{filename}')

    output.save(f'output/{filename}.png')
    output.show()


    return f'output/{filename}'
