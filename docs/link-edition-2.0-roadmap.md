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
| **2. Clock and living world** | The software clock, save migration, palettes and gameplay timers are in the build. Add the daily Kimono Cup type rotation with phase 5. | Emulator checks cover 90-minute days, 10.5-hour weeks, older primary and backup saves, daily sightings, and contest and phone timers. A morning save and a night save stayed in sync for 11 link action exchanges. Verify clock and save persistence on physical cartridges without RTC hardware. |
| **3. Ecology** | The eight movement profiles and environmental interactions are in the build. | Emulator checks cover movement speeds, aggression at walls and habitat boundaries, territory, schooling, and the Sweet Honey Bag flow. Verify encounter pacing and feel on hardware during the release playthrough. |
| **4. Narrative campaigns** | Built: the Cinnabar flight log and witness before the clone battle (with a psychic echo for saves that already caught Mewtwo); the three elemental beacons, Melody, weather and Lawrence leading to Lugia; Molly, the visible illusion and Hale's rescue, with two Unown illusions (Teddiursa, Phanpy) to beat first; the forest loop, the Marauder's three corrupted forest Pokémon, Celebi healed at the shrine and Sammy, the traveler from another time, whom Prof. Oak turns out to have been. Illusory and corrupted Pokémon use BATTLETYPE_SHADOW: no ball can catch them and you can't run. Optional later: short leads for the other legendaries (Mew, Ho-Oh, the beasts). | Each story explains its conflict and resolution, including on saves that already caught the associated legendary. Test alternate completion order, full item pockets, losses and returning after a save. |
| **5. Regional tournaments** | Built: the solo cup runner (engine/events/cups.asm): a cup's rules (level, team size, how it is chosen, type rule), your party kept aside and restored, battles at the cup's level for everyone with no experience or items, healing between rounds, first-win records in the saved party area. Rising Star (National Park gate) and the Whirl Cup (Olivine Port, converted) run on it. Next: Kimono, Dragon Masters and Rental, then the solo World Championship. Publish availability in the Field Book, map, TV and radio. | Rising Star is 3 at level 30. Whirl is 3–6 Water types at level 50. Kimono is 3 at level 50 with a deterministic 18-day rotation and a win per type. Dragon Masters includes a Dragon type at level 50. Rental generates level-50 teams. World Championship is 6 at level 50 across an eight-contestant bracket. Test loss, retry, full reward pocket, and party restoration. |
| **6. Orange League** | Keep the four islands open to exploration. Give Cissy a short Surf course, Danny an ascent and ice puzzle, Rudy three matchup rounds and Luana a two-Pokémon singles battle. Reuse current trainers and appropriate assets. Keep Drake's six-on-six match and the Pallet ending. | Enter from the ferry in either direction and complete all four challenges in any order. Preserve earlier badges and wins. Check reachability, post-battle placement and the next story handoff. |
| **7. Cable Club** | Retain Standard and Random. Add Rising Star and Unrestricted through a shared rules handshake. Prototype offline Friend Battles using a separately budgeted team cache linked to the existing opponent identities. Add preview, updates after compatible exchanges and independent team removal. | Each format validates legal party size and level on both ends. Unrestricted admits legendaries. Generated teams never replace personal teams. The saved team and its lifetime opponent record can be managed independently. |
| **8. Linked World Championship** | Reuse phase 5 brackets and phase 7 rules. Connect for registration, assign opposite halves, and save a shared identity, seed and rules. Play NPC rounds offline. Reconcile results on reconnect and run the human final over the cable when both qualify. | Exercise both finalists, one finalist, both eliminated, duplicate result exchange and interrupted sessions. Test disconnects and different console clocks. Provide an NPC final for the surviving player. |
| **9. Bedroom achievements** | Reuse bedroom decorations for Indigo and Orange trophies, one upgraded tournament trophy and an Adventure Album. Use existing story flags and the new cup and championship result flags. | Older wins populate the album. Test trophy upgrades and preserve bedroom customization and the Pokédex diploma. |
| **10. Presentation** | Reuse appropriate in-project artwork, then budget for original or authorized art where reuse makes characters hard to recognize. Favor movement, cries, lighting and palette changes before adding dedicated backgrounds. The title screen is optional. | Confirm source and permission for each new asset. Review palette readability, animation and staging on the original screen size. |
| **11. Release testing** | Run a natural playthrough, the emulator and full encounter suites, save migration, ROM-oracle tests and hardware link tests. Record the build size, save compatibility and known limitations in the release notes. | A clean build fits 2 MiB. Manual saves and cable recovery work on supported hardware. The story, all 18 Kimono types, trophies and every supported format pass. |

## Budget and order

Measure free ROM after each phase. The cleanup recovered 19,960 bytes over the
quest-map build. The clock changes recovered another 601 bytes. Ecology uses
779 bytes of ROM, leaving 28,333 bytes free in the 2 MiB build. The largest
available ROM areas are one empty 16 KiB bank and another with 11,700 bytes
available.
The proposed 45 KB budget remains a planning estimate. Use 7 KiB as a working
maintenance reserve when estimating new features.

Battery-backed save space is separate. The current link map reports 444 free
bytes across four save banks, with 422 bytes split across three gaps in bank 0.
Profile one stored friend team and one bracket checkpoint before deciding how
many teams can fit. Record the cost of every new persistent field. The 65
opponent history rows are already allocated and should survive migration.

The fixed work RAM bank has 41 unallocated bytes. Switchable work RAM reports
13 free bytes in bank 1, 2,779 in bank 2 and 2,062 in bank 5. Both video RAM
banks are mapped to existing graphics and screens. Budget new effects in the
screen or map that uses them and verify the reused tiles in the emulator.

Play one solo cup from entry to payout. Expand the story and Orange challenges
alongside that work. Finish the offline cup and new cable handshake before
starting linked championships. Schedule original hardware tests before calling
the release ready. Seasons, doubles and the simulator overhaul remain deferred.
