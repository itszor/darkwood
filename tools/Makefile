# tools/unpack: libroger's ARM2 interpreter as an unpacker (see unpack.c).
# "make unpacked": ../unpacked/QTMTracker, the module disc 1's
# Modules.QTMModule installs.
ROGER   ?= $(HOME)/stuff/libroger
CC      ?= gcc

unpacked: ../unpacked/QTMTracker

../unpacked/QTMTracker: unpack
	mkdir -p ../unpacked
	./unpack "$$(ls ../game/!DarkWood/Disc1/Modules/QTMModule,*)" --headless --limit=50000000 --write=$@

unpack: unpack.c $(ROGER)/libroger.a $(ROGER)/include/roger.h
	$(CC) -O2 -g -Wall -I$(ROGER)/include -o $@ unpack.c $(ROGER)/libroger.a $(shell pkg-config --libs sdl3) -lm -lpthread

$(ROGER)/libroger.a: FORCE
	$(MAKE) -C $(ROGER) libroger.a

clean:
	rm -f unpack

.PHONY: FORCE clean unpacked
