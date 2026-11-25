# Event flags: audit

`wEventFlags` is saved: 2,304 flags in 288 bytes (`NUM_EVENTS`). An assert in
`constants/event_flags.asm` keeps the save size fixed. Every slot is taken
except 16 left by retired flags, marked `const_skip` with the old name beside
them:

| Retired flag | Slots |
|---|---:|
| `EVENT_SWITCH_1` to `_3`, `EVENT_EMERGENCY_SWITCH` | 4 |
| `EVENT_COPYCAT_1` to `_4` | 4 |
| `EVENT_REMATCH_GYM_LEADER_4` to `_6` | 3 |
| `EVENT_ROUTE_10_CUT_TREE_3`, `_4`, `EVENT_VERMILION_CITY_CUT_TREE` | 3 |
| `EVENT_YELLOW_FAIRY_BOOK` | 1 |
| `EVENT_ROUTE_5_6_POKEFAN_M_BLOCKS_UNDERGROUND_PATH` | 1 |

Before reusing one, remember that a save from before it was retired may
still have it set. A new event in that slot would start out "done" on such a
save. To reuse one safely:

- Give it a meaning where "already set" does no harm, such as "a hint was
  seen", not "a reward was given"; or
- Clear it once on such saves: in `utils/save_upgrade/upgrade_save.py`, or
  in-game the first time the new feature's map loads, guarded by a flag of
  its own.

Checked: Ben's, Sam's and Dereck's saves have none of the 16 set. Beyond these
16 there is no room: a new flag needs a retired one, a reused one or a
larger save layout.
