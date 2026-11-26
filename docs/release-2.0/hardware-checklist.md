# Link Edition 2.0: physical hardware and multiplayer checklist

These are the checks emulation can't settle. The emulator suites (see the
[release checklist](checklist.md)) cover the logic: saves, migration,
scripts, every Cable Club format over a virtual cable that follows the
hardware's clocking, and cuts at every Championship commit boundary. What's
left is real cartridges, real cables, real screens and real people.

Record each result in the table at the end: the date, the console and
cartridge, who tested, and pass or fail with a note. A failure blocks the
release only if it's in a **blocker** row.

## What you need

- Two Game Boy Color consoles (a Game Boy Advance or SP running the game in
  its Game Boy Color mode also counts, and is worth one test of its own).
- Two cartridges with the release ROM: MBC5, battery-backed save RAM of at
  least 32 KiB, 2 MiB or larger. The ROM header says MBC5+RAM+BATTERY, 2 MiB
  ROM, 32 KiB RAM. No real-time clock is needed (the world clock is software).
- A Game Boy Color link cable (the GBC-to-GBC kind). A GBA link cable won't
  work for Game Boy Color games.
- The family's three saves, and a copy of each kept on a computer first.
- The release ROMs, checked against `CHECKSUMS.txt` before flashing.

## 1. Cartridge and boot (blockers)

| # | Check | How | Expect |
|---|---|---|---|
| 1.1 | The flashed ROM is the release | Read the cartridge back with the flasher and compare its SHA-1 with `CHECKSUMS.txt` | Identical |
| 1.2 | Boots on a Game Boy Color | Power on | The title screen, then the menu, no garbage |
| 1.3 | Boots on a Game Boy Advance or SP | Power on | The same, in the GBA's Game Boy Color mode |
| 1.4 | A classic Game Boy refuses politely | Power on a DMG or Pocket, if you have one | Not a crash (the game is for Game Boy Color) |
| 1.5 | A new game | New Game, name, the first save | Saves, and Continue after a power cycle resumes it |

## 2. Saves and the world clock (blockers)

| # | Check | How | Expect |
|---|---|---|---|
| 2.1 | Saves survive power | Save, power off for a minute, power on, Continue | Exactly where you saved |
| 2.2 | Saves survive a night | Save, leave the console off overnight | Still there (the cartridge battery holds) |
| 2.3 | The world clock persists | Note the in-game time, play 10 minutes, save, power off, power on | The clock carries on from the saved time plus about the 10 minutes (it only runs while you play) |
| 2.4 | A day passes | Play 90 minutes in one or several sittings, saving at the end of each | Morning, day, evening and night all come round; daily events (the Kimono Cup's type, daily sightings) move on |
| 2.5 | Power lost while saving | Choose Save, answer Yes, and switch off before "saved the game" appears (try a few timings across several runs). Power on and Continue | The game loads the last good save (the backup) or the new one; never a corrupted save. Note which |
| 2.6 | The family's saves | Copy each family save onto a cartridge, Continue | Each loads with its party, boxes, badges, Trainer Card records and Friend teams intact |
| 2.7 | Save with a Friend team stored | Battle a friend over the cable (which stores their team), save, power cycle | The team is at the third desk |

## 3. Cable Club, each format (blockers)

For each, both players choose the same format at the battle desk. Play the
battle to the end unless the row says otherwise. Afterwards each player's
party must be exactly as before (levels, items, HP restored), and the
Trainer Card must count the battle.

| # | Format | Expect |
|---|---|---|
| 3.1 | Standard | Level 50, up to six; one legendary at most |
| 3.2 | Random teams | Six generated Pokémon each; no Friend team stored afterwards |
| 3.3 | Rising Star | Exactly three at level 30 |
| 3.4 | Unrestricted | Their own levels |
| 3.5 | Championship | Registers both in one bracket (see section 5) |
| 3.6 | Different formats | One chooses Standard, the other Rising Star: both desks refuse, saying the formats differ |
| 3.7 | Trade | Trade one Pokémon each way; both games save; each has the other's Pokémon after a power cycle |
| 3.8 | Friend Battle | At the third desk, battle a stored team offline; party restored afterwards |

## 4. Cable trouble (blockers for 4.1–4.4)

| # | Check | How | Expect |
|---|---|---|---|
| 4.1 | Unplug mid-battle | Pull the cable during a turn's move choice, wait 10 seconds | Both games say the link was lost and return control; parties restored; neither save damaged |
| 4.2 | Bump the cable | Wiggle the plug for a second mid-battle | The battle carries on, or both stop with the same message; never two different battles |
| 4.3 | Unplug at the desk | Pull the cable while the desk is checking the link | "The link didn't go through", with an offer to try again; plugging back in and retrying works |
| 4.4 | Unplug mid-trade | Pull the cable while the trade animation plays | Neither game loses or duplicates the Pokémon after a power cycle |
| 4.5 | Different builds | Link a release cartridge with an older build | The desk refuses: not the same build |
| 4.6 | Different clocks | One game in the morning, the other at night | They link and battle normally |

## 5. The linked World Championship (blockers for 5.1–5.4)

| # | Check | How | Expect |
|---|---|---|---|
| 5.1 | Register | Choose Championship at the desk together | Both see one bracket, each in a different half, at the Indigo Plateau |
| 5.2 | Play rounds offline | Each plays their quarterfinal at the Indigo Plateau, saves | Results kept after a power cycle |
| 5.3 | Sync | Link again at the desk | Each hears the other's result; the bracket screens agree |
| 5.4 | Cut during sync | Pull the cable during the second link-up's exchange, then link again | Both end at the desk; the next link-up leaves both in one bracket with every result kept |
| 5.5 | The final | Both reach the final; link and battle | Recorded on both as the same result; the champion's prize given once |
| 5.6 | One finalist | Only one reaches the final | That player plays the other half's finalist at the Indigo Plateau |

## 6. Screen, sound and pacing (not blockers; note anything that looks wrong)

| # | Check | Where |
|---|---|---|
| 6.1 | Palettes readable on the GBC's screen (and on the GBA's, which is brighter) | Towns by day and night, caves, the Orange Islands |
| 6.2 | The corrupted Ilex Forest (violet trees) is readable, and the healing scene's pulse isn't harsh | Ilex Forest after Red and the time travel |
| 6.3 | Scene effects: flashes, shakes, title cards, the camera panning | Shamouti Shrine, the Alph statue, Cerulean Cave, Pallet's ending. With the Flash & Shake option off, no flashes or shakes |
| 6.4 | Visible wild Pokémon move smoothly; walking in grass doesn't hitch badly | Route 29, Route 32 |
| 6.5 | Music transitions in the movie scenes, no glitched notes | The four movie campaigns |
| 6.6 | Followers: the lead Pokémon follows without flicker | Anywhere |
| 6.7 | Text: nothing runs off a text box, no garbled characters | The Orange Islands, the Field Book, the Album |

## 7. Natural play (owner)

| # | Check |
|---|---|
| 7.1 | A full playthrough from New Bark Town to Red, then the post-game (issue ledger L9) |
| 7.2 | Each movie campaign from its start, including a loss and a save mid-quest |
| 7.3 | The Orange League in a different badge order from the last test |
| 7.4 | All six cups; one Kimono win on a few different days |
| 7.5 | The Pallet Invitational and its ending |

## Results

| Row | Date | Console and cartridge | Tester | Result | Notes |
|---|---|---|---|---|---|
| | | | | | |
