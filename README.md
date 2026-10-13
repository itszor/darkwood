Darkwood 0.63 (Tom Cooper / Eclipse, 1995) - static recompilation
=================================================================

A 3D arcade adventure on six discs: the wizard's tower and its rooms, the
landscapes outside, a map, speech, QTM tracker music. Disc 1 holds the
program (!DarkWood: the front end, the code, graphics) and !DarkInstl, the
hard disc installer; discs 2-5 the landscapes, rooms, music and speech;
disc 6 !DarkSave, the game in progress.

A recipe: this repository holds no game data. It rebuilds the game from
your own copy, recognised by content (recipe.json):

    ./build.sh "Darkwood 0.63 (1995)(Tom Cooper)(Disk 1 of 6).hfe" ...    (all six)
    cd recomp && ./darkwood

build.sh runs recipe.json's steps with SuperSpider's tools/weave.py
(~/stuff/superspider, or $SUPERSPIDER; $SS below): it decodes the six HxC
.hfe images ($SS/tools/hfe.py: MFM to ADFS E sectors), extracts them, lays
their applications out in game/ as the hard disc installation has them
(!DarkWood with Disc1, then Disc2-Disc6), keeps disc 1's image itself
(extracted/disc1.hfe, for the copy protection, below), unpacks QTMTracker,
then analyses, translates and links. Needs python3, OCaml/dune, gcc and
SDL3.

    tools/images.py     the translated images and how they're analysed
    tools/unpack.c      runs Modules.QTMModule (a packed installer) under
                        libroger's interpreter and saves the module it inserts
    analysis/           SuperSpider's results; *.roots are gap entries
                        (make roots), *.xroots the cross-image calls
    recomp/             make regen (analysis + gen), make, ./darkwood

The inputs must be flux-level images of the discs (.hfe), disc 1's at
least: its copy protection is a track a sector image (.adf) can't hold.
weave.py takes .hfe files (or a .zip of them); an .adf of disc 1 is
recognised by its files, but the game then asks for disc 1 for ever.

Running
-------

    cd recomp && ./darkwood [--screen=normal|multisync] [--detail=high|medium|low]
                            [--music=full|action|off] [--speech=fast|medium|slow]
                            [--no-sound] [--scale=N] [--fullscreen]
    ./darkwood --trace-gaps     log untranslated code reached (untranslated.log)
    ./darkwood --save=DIR       where what the game saves goes (default savedata/)
    ./darkwood --limit=N        headless, deterministic: Start, then out of the
                                tower ('), left, forward, fire, jump

The options are the front end's options window: given, they're saved to
MiscData.Config (in the save directory) and kept. The disc's Config has
Multisync (GameModes' mode 49, 320x480: the view above, the text below),
graphics detail high, speech medium and music full; --screen=normal is
mode 13, 320x256 (text over the view).

Keys (from the freeware re-release's !Help): Z X turn, ' / walk forwards
and backwards, Space fire, Return jump, P pause and in-game options,
Ctrl-Escape quit to the title. The mouse works the menus and the action
buttons at the bottom right; its pointer is the host's (the game draws
none: it relied on the desktop's pointer staying on when it changed mode -
libroger's desktop_pointer). A controller: left/right turn, up/down walk,
A fire, B jump, X pause, back Escape.

What runs
---------

!Run: sets Dark1$Dir..Dark6$Dir and DarkSave$Dir (as !RunHD, the installed
copy's, does: game.c's variables), RMLoads Modules.GameModes, runs
Modules.QTMModule and runs FrontEnd.Front, a BASIC Wimp task: an icon-bar
icon, the options window and saving the game in progress to a directory
of the user's. Clicking the icon runs !RunGame: WimpSlot 1024K and *Run
Code.MCMain1. Here:

- GameModes: translated (gen/gamemodes). Modes 48 and 49 (320x480, VGA
  timing) through Service_ModeExtension, only for multisync and VGA
  monitors: libroger's monitor is configured as multisync.
- QTMModule: a packed absolute that inserts QTMTracker (1.2x), the music
  and sample player. tools/unpack runs it and saves the module
  (unpacked/QTMTracker), translated (gen/qtm) and loaded at start-up.
- Front: not run (its options are command-line options; its "save game
  to a directory" isn't there - the game's own saving to !DarkSave is).
- The game: MCMain1 (gen/mcmain1, loaded at &F49CC, entered at &F51DC -
  its execution address, which the extracted name lost) *Loads MCMain2
  (&49C04, most of the game), DitGouraud or PlnGouraud at &675F8 (by
  graphics detail, over part of MCMain2), MCTitle or MCMap at &A807C,
  MCRoom (&B209C), MCLand (&E6680) and MCFinish (&EE07C, over MCLand) as
  it goes, and calls into them at fixed addresses. Each is translated on
  its own (tools/images.py), with the others' ranges as --extern; the calls
  each makes into another are that one's entry points, until there are no
  new ones. They're loaded as overlays (roger_config.programs): the one
  loaded last at an address is the one that runs there.

The copy protection
-------------------

"Dan Simms, disc protection routines" (MCTitle's credits). Every code file
carries the same check, and the game won't go on (it asks for disc 1)
until it passes: it looks up FileCore (OS_Module 18) and ADFS's FileCore
instance (OS_FSControl 20), turns ADFS's retries off and calls FileCore's
SWI handler directly - past the SWI vector - as FileCore_DiscOp, reading
track 79, side 1 of disc 1 as ten 256-byte sectors (an alternative disc
record; the track holds a 1K sector and nine of 256, 512 and 1K, some with
bad CRCs):

- sector 1, a random length of it: must start "G" and run on as the
  sector does;
- sector 3: must read;
- sector 2: must fail (a data CRC error) - and its data, which the
  controller reads into the buffer all the same, is half the key;
- sector 6, 8 bytes: zero, then the other half.

The key, &45BC9, is what the caller checks for. libroger now does this as
the machine did (src/disc.c): the floppy in drive 0 is disc 1's .hfe,
decoded track by track with each sector's ID and CRC kept, FileCore and
ADFS have module headers whose SWI handlers come back into libroger, and
a sector with a bad CRC is a disc error after its data is transferred.

Known differences and open questions
------------------------------------

- Played so far: the title page, the wizard's tower and out into
  Ecklesfit village (a few minutes of it). Other parts of the game may
  reach code the analysis missed: it's interpreted (interpret_gaps), so
  it runs, more slowly; --trace-gaps logs it, then make roots, make regen,
  make translate it. analysis/mcmain2.roots lists by hand the entries of
  a span fill that jumps back into a run of stmias (sub pc, lr, r11, asr
  #3 at &67384), a form SuperSpider doesn't follow.
- The title page has no music (QTM is configured and stopped again); not
  checked against the original.
- In headless runs, use --full-os for screenshots: without it libroger
  answers VDU variable 149 (the display bank's address) with the write
  bank, so both of the game's screen pointers are the same.
- The freeware re-release (Acorn Arcade, 2004: one !DarkWood holding all
  six discs, protection removed - its code files differ) isn't a recipe
  input; it could be one, with its own translations.

What this game added elsewhere
------------------------------

SuperSpider ($SS):

- tools/hfe.py, and .hfe inputs in weave.py (decoded, recognised by their
  sectors; "raw" keeps the .hfe)
- --extern FROM-TO: calls into another image's range return (r0-r12
  unknown) and are listed (extern_calls) as that image's entry points
- MRC/MCR p15 (an ARM3 test, an undefined instruction on an ARM2) is code
- add pc,pc,rX,lsl #k (k >= 5): all the 2^k-byte blocks of an unrolled
  loop after it are entry points (the Gouraud routines)

libroger:

- the floppy (roger_config.floppy, --floppy=): FileCore_DiscOp and
  ADFS_DiscOp sector reads from an .hfe or .adf, ADFS_Retries, OS_FSControl
  14 and 20, OS_Module 18, FileCore and ADFS as ROM modules
- roger_config.monitor_type, for Service_ModeExtension
- roger_config.desktop_pointer: the desktop's pointer left on
- the undefined instruction trap (OS_ChangeEnvironment 1's handler)
- OS_ReadSysInfo 2 (the hardware: IOC, MEMC1, VIDC1)
- overlays: the image loaded last at an address runs there (over another
  overlay or the program), and a gap in one is the program's, not a
  module's

To do
-----

- Play further with --trace-gaps (the map, the rooms past the first, the
  other landscapes, the end sequence: MCMap, MCFinish), and make roots,
  make regen, make.
- Accept the freeware re-release (the 2004 zip) as an alternative input:
  a "plain disc" holding all six discs' files, with its own (de-protected)
  code files to translate and no floppy needed.
- Shared changes held back for fear of breaking other games are listed in
  $SS/PORTING.md, "Deferred": backward computed jumps (`sub pc, ...`;
  here, the hand roots in analysis/mcmain2.roots), adf_extract.py's lost
  execution addresses (here, MCMain1's entry in game.c), and the rest.
