#!/usr/bin/env python3
"""The translated images of Darkwood and the steps that build them.

    images.py analyse   SuperSpider (superspider analyse --full) on every image:
                        analysis/<name>.json. The images call each other at
                        fixed addresses, so each is analysed with the others'
                        ranges as --extern, and the calls one makes into
                        another become the other's entry points
                        (analysis/<name>.xroots), until there are no new ones;
                        analysis/<name>.roots, if there, adds more (gap roots)
    images.py roots LOG...
                        merges the gap entries of --trace-gaps runs (libroger's
                        untranslated.log) into analysis/<name>.roots
    images.py gen       superspider gen for every image -> recomp/gen/<name>/,
                        plus recomp/gen/images.inc (game.c's image tables)

The game is one program in several files, which !RunGame's
Code.MCMain1 loads with *Load and calls into (MCMain1 is the main loop):
  mcmain1     Code.MCMain1: the loader and main loop, loaded at &F49CC and
              entered at &F51DC (its execution address, which the extracted
              name lacks). The program image.
  mcmain2     Code.MCMain2 at &49C04: most of the game. Its first bytes are
              variables (DefaultVar and the saved game load over them) and
              &675F8 on is overwritten by a Gouraud overlay.
  ditgouraud, plngouraud
              Code.DitGouraud / PlnGouraud: the dithered and plain shading
              routines, *Loaded at &675F8 by graphics detail.
  mctitle, mcmap
              Code.MCTitle (the title pages) and Code.MCMap (the map), both
              at &A807C, one at a time.
  mcroom      Code.MCRoom at &B209C: inside the buildings.
  mcland      Code.MCLand at &E6680: the landscape.
  mcfinish    Code.MCFinish at &EE07C (over MCLand): the end sequence.

Modules (RMA addresses fixed here), in !Run's order:
  gamemodes   Modules.GameModes: screen modes (Service_ModeExtension)
  qtm         QTMTracker, the music player: Modules.QTMModule is a packed
              absolute that inserts it; tools/unpack saves it, in
              unpacked/QTMTracker
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
GAME = os.path.join(TOP, 'game')                 # !DarkWood, Disc2-6 (recipe.json)
CODE = '!DarkWood/Disc1/Code'
SS = os.environ.get('SUPERSPIDER', os.path.expanduser('~/stuff/superspider'))

# (name, leaf in Code, base, exec or None)
IMAGES = [
    ('mcmain1', 'MCMain1', 0xF49CC, 0xF51DC),
    ('mcmain2', 'MCMain2', 0x49C04, None),
    ('ditgouraud', 'DitGouraud', 0x675F8, None),
    ('plngouraud', 'PlnGouraud', 0x675F8, None),
    ('mctitle', 'MCTitle', 0xA807C, None),
    ('mcmap', 'MCMap', 0xA807C, None),
    ('mcroom', 'MCRoom', 0xB209C, None),
    ('mcland', 'MCLand', 0xE6680, None),
    ('mcfinish', 'MCFinish', 0xEE07C, None),
]
# images loaded over a part of another that holds nothing of its own (what
# MCMain2's file has at &675F8 is stale): code there is theirs. Other
# overlapping images are alternatives (MCFinish replaces the end of MCLand,
# whose code is there until it does).
MODULES = [
    ('gamemodes', '!DarkWood/Disc1/Modules/GameModes'),
    ('qtm', '../unpacked/QTMTracker'),
]
RMA = 0x1800000

STALE = {'ditgouraud': 'mcmain2', 'plngouraud': 'mcmain2'}


def find(d, leaf):
    for f in os.listdir(os.path.join(GAME, d)):
        if f.split(',')[0].lower() == leaf.lower():
            return d + '/' + f
    raise SystemExit('not found: %s/%s' % (d, leaf))


def images():
    """(name, path relative to game/, base, end, exec or None)"""
    out = []
    for name, leaf, base, exe in IMAGES:
        p = find(CODE, leaf)
        out.append((name, p, base, base + os.path.getsize(os.path.join(GAME, p)), exe))
    return out


def modules():
    """(name, path relative to game/, base)"""
    out, base = [], RMA
    for name, p in MODULES:
        if not p.startswith('..'):
            d, leaf = os.path.split(p)
            p = find(d, leaf)
        out.append((name, p, base))
        base = (base + os.path.getsize(os.path.join(GAME, p)) + 0xFFF) & ~0xFFF
    return out


def run(cmd, quiet=False):
    print('+', ' '.join(cmd), flush=True)
    r = subprocess.run(cmd, check=True, capture_output=quiet, text=True)
    if quiet:
        print(r.stdout.strip().splitlines()[-2] if r.stdout.strip() else '')


def read_roots(f):
    out = set()
    if os.path.exists(f):
        for line in open(f):
            line = line.split('#')[0].strip()
            if line:
                out.add(int(line.lstrip('&'), 16))
    return out


def externs(name, base, end, ims):
    """the other images' ranges, as this one sees them: not those of images
    it overlaps (alternatives to it), but the parts of one round it (MCLand
    round MCFinish), and those of images loaded over a stale part of it"""
    out = []
    for n, _, b, e, _ in ims:
        if n == name:
            continue
        if b >= end or e <= base:
            out.append((b, e))
        elif b < base and end <= e or b <= base and end < e:     # round this one
            out += [r for r in ((b, base), (end, e)) if r[0] < r[1]]
        elif STALE.get(n) == name:
            out.append((b, e))
    return out


def analyse():
    subprocess.run(['dune', 'build'], cwd=SS, check=True)
    exe = os.path.join(SS, '_build/default/bin/main.exe')
    an = os.path.join(TOP, 'analysis')
    os.makedirs(an, exist_ok=True)
    ims = images()
    xroots = {n: set() for n, *_ in ims}
    todo = [n for n, *_ in ims]
    while todo:
        found = {}
        for name, path, base, end, exe_addr in ims:
            if name not in todo:
                continue
            roots = sorted(xroots[name] | read_roots(os.path.join(an, name + '.roots')))
            if exe_addr is None and not roots:
                continue                            # nothing calls it yet
            with open(os.path.join(an, name + '.xroots'), 'w') as f:
                f.write('# entry points: calls into it from the other images (images.py)\n')
                f.writelines('%x\n' % r for r in sorted(xroots[name]))
            cmd = [exe, 'analyse', os.path.join(GAME, path), '%x' % base, '--full',
                   '--exec', '%x' % (exe_addr if exe_addr is not None else roots[0]),
                   '-o', os.path.join(an, name + '.json')]
            for r in roots:
                cmd += ['--entry', '%x' % r]
            for b, e in externs(name, base, end, ims):
                cmd += ['--extern', '%x-%x' % (b, e)]
            run(cmd, quiet=True)
            for t in json.load(open(os.path.join(an, name + '.json'))).get('extern_calls', []):
                found.setdefault(t, set()).add(name)
        todo = []
        for t in found:
            for name, _, base, end, _ in ims:
                if base <= t < end and t not in xroots[name] and not any(
                        n == name for n in found[t]):
                    xroots[name].add(t)
                    if name not in todo:
                        todo.append(name)
        if todo:
            print('new entry points for', ', '.join(todo), flush=True)
    for name, path, base in modules():
        cmd = [exe, 'analyse', os.path.join(GAME, path), '%x' % base, '--full', '--module',
               '-o', os.path.join(an, name + '.json')]
        rf = os.path.join(an, name + '.roots')
        if os.path.exists(rf):
            cmd += ['--roots', rf]
        run(cmd, quiet=True)


def roots(logs):
    """Merges the gap entries the --trace-gaps runs logged in LOGS (libroger's
    untranslated.log) into analysis/<name>.roots, for the next analyse."""
    an = os.path.join(TOP, 'analysis')
    for name, path, base in [i[:3] for i in images()] + modules():
        run([sys.executable, os.path.join(SS, 'tools/gap_roots.py'), os.path.join(GAME, path),
             '%x' % base, os.path.join(an, name + '.roots')] + logs)


def gen():
    exe = os.path.join(SS, '_build/default/bin/main.exe')
    rc = os.path.join(TOP, 'recomp')
    an = os.path.join(TOP, 'analysis')
    lines = ['/* generated by ../tools/images.py - the images, for game.c */']
    progs = []
    for k, (name, path, base, end, exe_addr) in enumerate(images()):
        tab = 'recomp' if name == 'mcmain1' else 'recomp_' + name
        prefix = 'F' if name == 'mcmain1' else 'M%d' % k
        run([exe, 'gen', os.path.join(GAME, path), '%x' % base, os.path.join(an, name + '.json'),
             '--c', os.path.join(rc, 'gen', name), '--prefix=' + prefix, '--tabprefix=' + tab,
             '--files=%d' % (16 if name == 'mcmain2' else 1), '--covtag=%s' % chr(ord('A') + k)])
        lines.append('extern const struct roger_image %s_image;' % tab)
        if name != 'mcmain1':
            progs.append('    {"%s", &%s_image, 1},' % (os.path.basename(path).split(',')[0], tab))
    lines.append('static const struct roger_program programs[] = {')
    lines += progs
    lines.append('    {NULL, NULL, 0}};')
    mods = []
    for k, (name, path, base) in enumerate(modules()):
        tab = 'recomp_' + name
        run([exe, 'gen', os.path.join(GAME, path), '%x' % base, os.path.join(an, name + '.json'),
             '--c', os.path.join(rc, 'gen', name), '--prefix=N%d' % k, '--tabprefix=' + tab,
             '--files=1', '--covtag=%s' % chr(ord('a') + k)])
        lines.append('extern const struct roger_image %s_image;' % tab)
        mods.append('    {"../game/%s", &%s_image, 0},' % (path, tab))
    lines.append('static const struct roger_module modules[] = {')
    lines += mods
    lines.append('    {NULL, NULL, 0}};')
    with open(os.path.join(rc, 'gen', 'images.inc'), 'w') as f:
        f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    if sys.argv[1] == 'roots':
        roots(sys.argv[2:] or ['untranslated.log'])
    else:
        {'analyse': analyse, 'gen': gen}[sys.argv[1]]()
