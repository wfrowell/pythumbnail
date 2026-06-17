import rosu_pp_py as rosu
from ossapi import User, BeatmapCompact, Score, mod, enums
from ossapi import Mod as OssapiMod
from osuapi import getScore, getUser, getBeatmap
from imagegen import imageGen
from tkinter import filedialog
from osrparse import *


def replayAcc(replay: Replay):
    n300 = replay.count_300
    n100 = replay.count_100
    n50 = replay.count_50
    n0 = replay.count_miss

    scorev = (300 * n300) + (100 * n100) + (50 * n50)
    maxval = 300 * (n300 + n100 + n50 + n0)

    # return f'{((scorev / maxval) * 100):.2f}'
    return scorev / maxval


def replayGrade(replay: Replay):  # could use some testing further
    n300 = replay.count_300
    n100 = replay.count_100
    n50 = replay.count_50
    n0 = replay.count_miss

    total = n300 + n100 + n50 + n0

    # fuck if this works lmao
    silver = (Mod.Flashlight | Mod.Hidden | Mod.FadeIn) in replay.mods

    # woo if statement tree
    if n300 == total:  # SS
        if silver:
            return enums.Grade('SSH')
        else:
            return enums.Grade('SS')
    else:  # maybe do some bitwise stuff? prob not worth it for readability though
        if n0 == 0:
            if n300 > 0.9 * total and n50 <= 0.01 * total:
                return enums.Grade('SH') if silver else enums.Grade('S')
            if n300 > 0.8 * total:
                return enums.Grade('A')
            if n300 > 0.7 * total:
                return enums.Grade('B')
        else:
            if n300 > 0.9 * total:
                return enums.Grade('A')
            if n300 > 0.8 * total:
                return enums.Grade('B')
            if n300 > 0.7 * total:
                return enums.Grade('C')
            else:
                return enums.Grade('D')


def replay():
    score = Score()
    replay: Replay

    while True:
        # TODO: get actual file explorer version working
        # returns an empty tuple when you it cancel for some reason lmao
        path = filedialog.askopenfilename()

        if type(path) is tuple:
            print('exiting...')
            return
        elif not path.endswith('.osr'):
            print('Invalid replay file.')
            continue
        else:
            replay = Replay.from_path(path)
            break

    

    beatmap = getBeatmap(beatmapHash=replay.beatmap_hash)
    score.__setattr__('beatmap', beatmap)
    score.__setattr__(
        'beatmapset',
        beatmap.beatmapset())  # necessary for background downlaod

    user = getUser(username=replay.username)
    score.__setattr__('user_id', user.id)
    score.__setattr__('_user', user)

    score.__setattr__('accuracy', float(replayAcc(replay)))
    score.__setattr__('max_combo', int(replay.max_combo))
    score.__setattr__('rank', replayGrade(replay))
    
    # modlist = OssapiMod(replay.mods)
    # score.__setattr__('mods')
    
    # calc = rosu.Performance(mod=)

    print('Generating image...')
    
    outputpath = imageGen(score)
    print(f'image saved as {outputpath}')


# replay()