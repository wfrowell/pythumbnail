# PLEASE READ

## Fair warning to anyone trying to use this right now

As far as I know, the exe doesn't work right now. I had a friend test it and there were some issues with libraries not compiling to the windows exe properly, which I unfortunately have no time to fix right now. It's absolutely on my radar though, as soon as my schedule allows.
Also, it currently can't do any specfic changes to the style or formatting outside of what is hard-coded, among some other user unfriendly aspects of it.
However, if at your disposal, the linux executable should work. Please submit a pull request or DM me on discord if you experience any other issues not mentioned, or you DON'T experience any of the issues I HAVE mentioned. The latter is more intriguing.

Generating by replay is depracated for now. osrparse doesn't seem to play well with lazer replays, so I don't see a point atm.

---

## pythumbnail

Generates thumbnail images for maryland osu (and hopefully later on, other osu scoreposting channels)

## TODO (yeah lotsa stuff)


- [x] fix mod icon alignment
- [x] add string safety to output filename
- [x] fix star rating float
- [x] find better star rating star (ideally svg - <https://stackoverflow.com/a/45262575>)
- [x] make 4+ mod icons stack on top of each other
- [ ] add a stroke to the star (fml im so stupid i forgot to do that)
- [ ] OAuth login
- [ ] make rate change scores work (add new element?)
- [ ] fix default profile picture sizing
- [ ] Add drop shadow to SR star?
- [ ] Compile to windows

## NOT HAPPENING FOR A WHILE

- create working ui
- parse .psd files to use as template :scp:

The .spec files are not necessary for runtime dw about them
