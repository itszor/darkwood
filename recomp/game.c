/* Darkwood (Tom Cooper / Eclipse, 1995): what libroger needs to know about
 * the game.
 *
 * !Run sets the Dark1$Dir..Dark6$Dir variables to the six discs (!RunHD, the
 * installed copy's, to directories in !DarkWood: game/ is laid out like
 * that), RMLoads GameModes and runs QTMModule (QTMTracker, the music
 * player), then runs FrontEnd.Front, a BASIC Wimp task: an icon on the icon
 * bar, an options window (MiscData.Config) and saving the game in progress.
 * Clicking the icon runs !RunGame: WimpSlot 1024K and *Run Code.MCMain1.
 * MCMain1 *Loads the rest of the game (MCMain2, overlays) and calls into it
 * (../tools/images.py).
 *
 * The front end isn't run: its options are command-line options here
 * (--detail= &c.), saved to MiscData.Config as its options window does. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <roger.h>

extern const struct roger_image recomp_image;      /* gen/mcmain1 */
#include "gen/images.inc"                          /* MCMain2, the overlays and the modules */

#define FLOPPY "../extracted/disc1.hfe"

/* ---------------------------------------------------------------- options
 * MiscData.Config, 16 bytes (Front's PROCrestoreopts/PROCsaveopts): the
 * graphics detail (10 high, 5 medium, 1 low), the speech speed (-3 fast,
 * 0 medium, 4 slow), the screen mode (0 normal: mode 13, 320x256; 1
 * multisync: GameModes' mode 49, 320x480) and the music (0 full, 2 action
 * only, 99 off). An option given here changes that word and saves the file
 * (to the save directory, where the game reads it from from then on). */
static const struct opt { const char *name; int word; const char *const values[3]; const int nums[3]; } opts[] = {
    {"--detail=", 0, {"high", "medium", "low"}, {10, 5, 1}},
    {"--speech=", 1, {"fast", "medium", "slow"}, {-3, 0, 4}},
    {"--screen=", 2, {"normal", "multisync", NULL}, {0, 1, 0}},
    {"--music=", 3, {"full", "action", "off"}, {0, 2, 99}},
};
static int set[4], value[4];

static int arg(const char *a)
{
    for (int k = 0; k < 4; k++) {
        size_t l = strlen(opts[k].name);
        if (strncmp(a, opts[k].name, l)) continue;
        for (int v = 0; v < 3 && opts[k].values[v]; v++)
            if (!strcmp(a + l, opts[k].values[v])) { set[opts[k].word] = 1; value[opts[k].word] = opts[k].nums[v]; return 1; }
        fprintf(stderr, "%s: one of", opts[k].name);
        for (int v = 0; v < 3 && opts[k].values[v]; v++) fprintf(stderr, " %s", opts[k].values[v]);
        fprintf(stderr, "\n");
        exit(1);
    }
    return 0;
}

#define CONFIG_BUF 0x8000u                         /* free until MCMain1 loads things */

static void init(void)
{
    FILE *f = fopen(FLOPPY, "rb");
    if (f) fclose(f);
    else fprintf(stderr, "darkwood: no %s - the copy protection reads disc 1's track 79 as it is on\n"
                 "the disc, which only a flux-level image (.hfe) of it has; the game will ask for disc 1\n", FLOPPY);
    if (!(set[0] | set[1] | set[2] | set[3])) return;
    roger_cli("Load <Dark1$Dir>.MiscData.Config 8000");
    for (int k = 0; k < 4; k++)
        if (set[k]) WR32(CONFIG_BUF + 4 * k, (uint32_t)value[k]);
    roger_cli("Save <Dark1$Dir>.MiscData.Config 8000+10");
}

/* ---------------------------------------------------------------- the machine */
static const char *const variables[] = {             /* !RunHD */
    "DarkWood$Dir", "!DarkWood",
    "DarkFront$Dir", "!DarkWood.Disc1.FrontEnd",
    "Dark1$Dir", "!DarkWood.Disc1",
    "Dark2$Dir", "Disc2",
    "Dark3$Dir", "Disc3",
    "Dark4$Dir", "Disc4",
    "Dark5$Dir", "Disc5",
    "Dark6$Dir", "Disc6",
    "DarkSave$Dir", "Disc6.!DarkSave",
    "DarkWood$Install", "1",
    NULL};

/* The headless scenario (--limit runs; instruction counts, 2000 a
 * millisecond): Start on the title page (the multisync layout, as the
 * disc's Config has it), then out of the wizard's tower - forward ('),
 * left (Z), forward, fire (Space), jump (Return) */
static const struct roger_click clicks[] = {
    {14000000, 640, 538, 4}, {14600000, 640, 538, 0},
};
static const struct roger_key keys[] = {
    {80, 21000000, 27000000},                      /* ' */
    {98, 29000000, 30600000},                      /* Z */
    {80, 31000000, 39000000},                      /* ' */
    {99, 41000000, 41600000},                      /* Space */
    {74, 43000000, 43600000},                      /* Return */
};

static const struct roger_config config = {
    .title = "Darkwood (recompiled)",
    /* a controller: turning Z X, walking ' /, A fire (Space), B jump
     * (Return), X pause and options (P), back Escape */
    .pad_map = "left=Z,right=X,up=',down=/,a=Space,b=Return,x=P,back=Escape",
    /* MCMain1: load address &F49CC, execution address &F51DC (from the
     * disc's catalogue; the extracted name doesn't keep the latter) */
    .image_path = "../game/!DarkWood/Disc1/Code/MCMain1,000f49cc-00000000",
    .entry = 0xF51DC,
    .image = &recomp_image,
    .programs = programs,
    .modules = modules,                            /* GameModes, QTMTracker */
    .appdir = "../game",
    .variables = variables,
    .initial_mode = 12,
    /* a multisync monitor: the screen mode option is "Normal" - mode 13 -
     * or "Multisync" - GameModes' mode 49, 320x480 at 256 colours, which it
     * only defines for multisync and VGA monitors */
    .monitor_type = 1,
    .screen_size = 320 * 1024,                     /* two banks of mode 49 */
    .wimpslot = 1024 * 1024,                       /* !RunGame: WimpSlot 1024k */
    /* disc 1 as it is (the recipe's "raw"), for the copy protection: each
     * code file checks track 79 side 1 of disc 1, reading it as 256-byte
     * sectors with FileCore_DiscOp (a sector that must read, one with a
     * CRC error that must not - its data is the key - and 8 bytes that give
     * the value the caller expects), calling FileCore's SWI handler
     * directly */
    .floppy = FLOPPY,
    /* code the analysis missed (only some of the game has been played
     * with --trace-gaps) is interpreted rather than ending the run */
    .interpret_gaps = 1,
    .clicks = clicks,
    .nclicks = sizeof clicks / sizeof clicks[0],
    .keys = keys,
    .nkeys = sizeof keys / sizeof keys[0],
    .init = init,
    .arg = arg,
    .usage = "  --detail=high|medium|low     graphics detail     --music=full|action|off\n"
             "  --speech=fast|medium|slow    speech speed        --screen=normal|multisync\n"
             "                               (the front end's options: saved, kept for next time)\n",
};

int main(int argc, char **argv) { roger_main(argc, argv, &config); }
