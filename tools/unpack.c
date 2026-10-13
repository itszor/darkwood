/* Run a self-unpacking module installer with libroger's ARM2 interpreter
 * until it inserts the module it carries, then save that module.
 *
 *   unpack FILE --write=OUT [--limit=N]
 *
 * FILE (an absolute, filetype &FF8) is loaded at &8000 and entered there;
 * every instruction is interpreted. Disc 1's Modules.QTMModule is one:
 * QTMTracker, packed. When it calls OS_Module 10 or 11 (insert a module
 * from memory: R1 the module, its length in the word before it for 10, in
 * R2 for 11), the module is written to OUT. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <roger.h>

static uint8_t nocode[0x80000 / 32];
static struct roger_image image = {0x8000, 0x8000 + 0x80000, NULL, 0, nocode, 'P'};
static const char *out;

static int arg(const char *a)
{
    if (!strncmp(a, "--write=", 8)) { out = a + 8; return 1; }
    return 0;
}

static int insert_hook(uint32_t n, int x)
{
    (void)x;
    if ((n & ~0x20000u) != 0x1E || (R[0] != 10 && R[0] != 11)) return 0;   /* OS_Module 10/11 */
    uint32_t len = R[0] == 11 ? R[2] : RD32(R[1] - 4);
    FILE *f = fopen(out, "wb");
    if (!f) { perror(out); exit(1); }
    fwrite(MEM + R[1], 1, len, f);
    fclose(f);
    printf("OS_Module %u after %llu instructions: wrote the module at %08x, %u bytes, to %s\n",
           R[0], (unsigned long long)icount, R[1], len, out);
    exit(0);
}

static struct roger_config config = {
    .title = "unpack",
    .image = &image,
    .appdir = ".",
    .initial_mode = 12,
    .wimpslot = 640 * 1024,
    .interpret_gaps = 1,
    .arg = arg,
    .swi = insert_hook,
    .usage = "  --write=FILE   where the module goes\n",
};

int main(int argc, char **argv)
{
    for (int k = 1; k < argc; k++)
        if (!strncmp(argv[k], "--write=", 8)) out = argv[k] + 8;
        else if (argv[k][0] != '-') {                       /* the file: the (empty) image's extent */
            struct stat st;
            if (!stat(argv[k], &st) && st.st_size <= (long)sizeof nocode * 32) image.end = 0x8000 + st.st_size;
        }
    if (!out) { fprintf(stderr, "unpack: --write=FILE needed\n"); return 2; }
    roger_main(argc, argv, &config);
}
