| mutant (class) | smoke-pyboy | conn | execguard | fuzz | oam-maps | battle-pic | battle-menus | ppu-timing | audio-scan | music-loops | sfx-music | x-frames | x-audio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| control (none) | ok | ok | ok | ok | FALSE ALARM | FALSE ALARM | ok | ok | ok | ok | ok | ok | ok |

False alarms on the control build: 2
- oam-maps: oam_vram_integrity_maps: sprite / tilemap integrity: object-not-drawn: object N (sprite N) at (N,N) has no OAM entry (26 maps, e.g. BURNED_TOWER_B1F)
- battle-pic: 25/40 scenarios, 2 failure signatures, 67s; {"scenarios": 40, "outcomes": {"no-encounter": 11, "skip": 26, "fail": 3}, "battles": 0, "seconds": 97} 3 failure signatures; UserWarning: Using SDL2 binaries from pysdl2-dll 2.32.10
Missed although the detector family was expected to see the class: 0
