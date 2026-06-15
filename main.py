# console only ver for now
import os, sys, json, re
sys.path.append('./packages')
from osuapi import getScore
from imagegen import imageGen
from manual import manual
from byreplay import replay


def main():
    while True:
        pattern = re.compile(
            'https:\/\/osu\.ppy\.sh\/scores\/[a-zA-Z]+\/[0-9]+')
        url = input('Enter the URL of the score: ')
        if pattern.match(url):
            break
        else:
            print('Invalid score URL.')

    score = getScore(url)
    
    if score.mods != []:
        sr = input('Enter the mod weighted star rating of the beatmap.\n> ')
        if sr:
            score.beatmap.__setattr__('difficulty_rating', sr)

    print('Generating image...')

    outputpath = imageGen(score)
    print(f'image saved as {outputpath}')


if len(sys.argv) > 1:
    if sys.argv[1].lower() == '-m' or sys.argv[1].lower() == '--manual':
        manual()
    elif sys.argv[1].lower() == '-r' or sys.argv[1].lower() == '--replay':
        replay()
else:
    main()