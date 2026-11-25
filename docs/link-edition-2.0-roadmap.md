# Link Edition 2.0 development roadmap

The release keeps the 2 MiB Game Boy Color ROM and prioritizes the original
hardware target. Start with the storage and clock changes. Build the solo
tournament system and prove it works before extending the cable protocol.
Keep the Field Book and quest map as the common source of player directions.

## Release baseline

- The Field Book catches up returning players and skips completed story beats.
  Quest pins cover early progression, post-Red leads and open errands. The
  Pokégear and wall maps both provide access to the directions.
- Red starts the post-League route. Molly and Hale, Celebi and the Marauder,
  and the Mewtwo clone sequence are playable. Tracey, the Orange Crew and
  Misty hand off the next open chapter. The Orange League, Whirl Cup and
  Pallet Invitational already have victories, rematches or retry paths.
- Cable Club has standard and generated-team battles. The Trainer Card
  records lifetime and current-year results against 65 distinct opponents.
  The current year rolls over manually. Lifetime totals survive the in-game
  adventure erase.
- The engine cleanup removes overworld autosave, Start-menu box access and
  Pokédex footprints. Four Magikarp patterns share the existing palette and
  animation system. Legacy party forms convert on Continue. Boxed forms
  convert when read. The old form IDs remain safe to receive over the cable.
- The world clock runs in software on a cartridge without RTC hardware. A day
  takes 90 minutes of play, split evenly between daylight and night. Manual
  saves carry the world clock forward, including upgrades from the old clock.
  Daily and weekday events follow that clock. The Bug-Catching Contest and
  phone delays use gameplay time.
- Visible wild Pokémon use eight movement profiles. Walking, running, cycling,
  standing still, Repel, Sweet Honey and nighttime affect how they react. The
  encounter tables and shiny odds still determine which Pokémon appear.

## Phase checklist

| Phase | Remaining work | Acceptance |
| --- | --- | --- |
| **1. Engine cleanup** | Core removals and old-form conversion are in the build. Emulator checks cover manual saves, party and box decoding, shiny state and retained Pokédex icons. Keep measuring opportunities to deduplicate data before adding costly artwork. | Verify older save copies and the revised game on original hardware. Record size deltas for any further optimization. |
| **2. Clock and living world** | The software clock, save migration, palettes and gameplay timers are in the build. The Kimono Cup's daily type rotation is in (phase 5). | Emulator checks cover 90-minute days, 10.5-hour weeks, older primary and backup saves, daily sightings, and contest and phone timers. A morning save and a night save stayed in sync for 11 link action exchanges. Verify clock and save persistence on physical cartridges without RTC hardware. |
| **3. Ecology** | The eight movement profiles and environmental interactions are in the build. | Emulator checks cover movement speeds, aggression at walls and habitat boundaries, territory, schooling, and the Sweet Honey Bag flow. Verify encounter pacing and feel on hardware during the release playthrough. |
| **4. Narrative campaigns** | Cinnabar's flight log leads to the clone battle, with an echo for existing Mewtwo catches. Shamouti's three beacons and Lawrence lead to Lugia. Alph has a staged rescue and two optional illusion battles. Ilex has a time-travel entry, corrupted forest Pokémon, the Marauder and Sammy's reveal. Short leads for Mew, Ho-Oh and the beasts remain optional. | Verify each campaign on hardware and past saves, including alternate beacon order, full reward pockets, losses and resuming a saved quest. |
| **5. Regional tournaments** | Six solo tournaments run on the shared engine. Indigo Plateau hosts the World Championship after Red. The Field Book lists the rules and today's Kimono type. The quest map tracks open cups and held first prizes. TV and Oak's Pokémon Talk rotate through available tournaments. Hardware testing remains part of the release playthrough. | Rising Star is 3 at level 30. Whirl is 3–6 Water types at level 50. Kimono is 3 at level 50, rotates continuously through 18 types and records a win per type before paying its reward. Dragon Masters includes a Dragon type at level 50. Rental supplies three level-50 Pokémon to each side. The World Championship is 6 at level 50 across an eight-contestant bracket. Emulator checks cover advancement, losses, retries, held prizes across a save and party restoration. |
| **6. Orange League** | Cissy runs a Surf course on Warm Beach. Danny sends players up Rocky Peak, with an ice puzzle and a ladder back down. Rudy has three single-Pokémon type rounds. Luana has two-Pokémon singles. The Field Book gives directions for all four. Drake's six-on-six and the Pallet ending follow the Crew badges. | Check the ferries in both directions and earn badges out of order. Earlier badges still count and allow rematches. Verify the ridge, the Surf checkpoints, the restricted-party loss and retry paths, and the handoffs to Drake and Pallet. |
| **7. Cable Club** | Standard, Random, Rising Star and Unrestricted use the same format handshake and team checks. Next is the offline Friend Battle cache, with team previews, updates after compatible exchanges and independent removal. | Verify both Game Boys agree on level and party size and refuse mismatched formats. Unrestricted admits legendaries. Keep generated teams out of the Friend Battle cache and let players remove saved teams separately from lifetime records. |
| **8. Linked World Championship** | Reuse phase 5 brackets and phase 7 rules. Connect for registration, assign opposite halves, and save a shared identity, seed and rules. Play NPC rounds offline. Reconcile results on reconnect and run the human final over the cable when both qualify. | Exercise both finalists, one finalist, both eliminated, duplicate result exchange and interrupted sessions. Test disconnects and different console clocks. Provide an NPC final for the surviving player. |
| **9. Bedroom achievements** | Built: the Hall of Fame's Silver and Gold Trophies stay as they are; the Orange Trophy (owned once Drake is beaten) and the Cup Trophy (owned after any cup win; bronze, silver at three cups, gold at all six) are new ornaments using the trophy sprites with new palettes, and the bedroom PC's Album pages through Leagues, Stories and Cups. Ownership and the album read existing story flags and cup records, so no save space is added. | Older wins populate the album. Test trophy upgrades and preserve bedroom customization and the Pokédex diploma. |
| **10. Presentation** | Reuse appropriate in-project artwork, then budget for original or authorized art where reuse makes characters hard to recognize. Favor movement, cries, lighting and palette changes before adding dedicated backgrounds. The title screen is optional. | Confirm source and permission for each new asset. Review palette readability, animation and staging on the original screen size. |
| **11. Release testing** | Run a natural playthrough, the emulator and full encounter suites, save migration, ROM-oracle tests and hardware link tests. Record the build size, save compatibility and known limitations in the release notes. | A clean build fits 2 MiB. Manual saves and cable recovery work on supported hardware. The story, all 18 Kimono types, trophies and every supported format pass. |

## Budget and order

Measure free ROM after each phase. The cleanup recovered 19,960 bytes over the
quest-map build. The clock changes recovered another 601 bytes. The first
ecology pass used 779 bytes and left 28,333 bytes free. The solo World
Championship and broadcasts used 1,282 bytes. The Orange League challenges
used another 1,229 bytes. The Cable Club formats used 396 bytes, leaving
17,489 bytes free in the 2 MiB build. The largest areas are one empty 16 KiB
bank and 863 bytes in another bank. Keeping a 7 KiB reserve leaves 10,321
bytes for remaining work.

Battery-backed save space is separate. The current link map reports 444 free
bytes across four save banks, with 422 bytes split across three gaps in bank 0.
A packing prototype fits the battle data for six Pokémon and trainer metadata
in 146 bytes. A record of that size fits each of the 179- and 220-byte gaps.
Reserve room for the linked bracket checkpoint before committing to a cache
capacity. The 65 opponent history rows are already allocated and should
survive migration.

The fixed work RAM bank has 18 unallocated bytes. Switchable work RAM reports
13 free bytes in bank 1, 1,643 in bank 2 and 2,062 in bank 5. Both video RAM
banks are mapped to existing graphics and screens. Budget new effects in the
screen or map that uses them and verify the reused tiles in the emulator.

Build the Friend Battle cache next, then use the shared rules for linked
championships. Schedule original hardware tests before calling
the release ready. Seasons, doubles and the simulator overhaul remain deferred.
