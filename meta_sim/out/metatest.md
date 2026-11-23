# Meta test

30,000 battles (390,000 including swap-test replays), 607 builds over 159 mons, seed 0, 309s.

**Impact** = points of team win rate a build adds over a random other build of the same family (offense / speed / defense / utility), from replaying the same battle with it swapped out. Typical standard error here: ±2.4 points, so treat differences under ~5 points as noise. **Job** = average percentile, within the playstyle, on the metrics for that job. Builds with fewer than 150 swap samples are left out of the rankings (still in the CSV).

## Strongest builds overall

| Mon | Playstyle | Impact | ± | Win % | Job |
|---|---|---|---|---|---|
| crobat | pivot | 16.38 | 2.9 | 64.7 | 100.0 |
| glaceon | revenge killer | 16.33 | 3.14 | 67.7 | 95.8 |
| magnezone | pivot | 15.7 | 3.7 | 58.7 | 71.1 |
| vaporeon | weather setter | 14.06 | 1.67 | 64.3 | 92.6 |
| golem_alolan | revenge killer | 12.59 | 3.0 | 57.3 | 68.8 |
| sneasler | pivot | 12.46 | 2.83 | 63.5 | 81.6 |
| mismagius | revenge killer | 12.34 | 2.56 | 59.0 | 89.6 |
| gengar | support | 11.39 | 2.9 | 58.5 | 74.3 |
| lanturn | revenge killer | 11.18 | 3.05 | 57.9 | 45.8 |
| overqwil | revenge killer | 10.63 | 3.02 | 57.2 | 92.4 |
| jolteon | pivot | 10.58 | 2.61 | 59.0 | 78.9 |
| aerodactyl | weather setter | 10.51 | 2.76 | 55.8 | 50.0 |
| glaceon | weather setter | 10.32 | 2.79 | 59.6 | 92.6 |
| gyarados | physical attacker | 10.3 | 2.07 | 58.7 | 97.8 |
| aerodactyl | revenge killer | 10.27 | 3.34 | 64.4 | 100.0 |

## Weakest builds overall

| Mon | Playstyle | Impact | ± | Win % | Job |
|---|---|---|---|---|---|
| unown | physical attacker | -21.24 | 1.94 | 30.6 | 2.9 |
| jumpluff | baton passer | -14.93 | 3.19 | 40.3 | 76.6 |
| cloyster | physical wall | -11.49 | 2.15 | 40.2 | 25.0 |
| delibird | baton passer | -11.29 | 3.1 | 37.0 | 40.6 |
| corsola_plain | weather setter | -10.74 | 3.44 | 39.3 | 39.4 |
| leafeon | baton passer | -10.66 | 3.14 | 41.4 | 57.8 |
| clodsire | hazard setter | -10.45 | 3.71 | 44.5 | 40.0 |
| fearow | baton passer | -9.73 | 2.6 | 40.1 | 42.2 |
| shuckle | support | -9.71 | 2.12 | 37.3 | 67.9 |
| tangrowth | special attacker | -9.52 | 2.02 | 45.0 | 13.6 |
| hypno | setup sweeper | -9.39 | 2.43 | 44.1 | 7.4 |
| farfetch_d_plain | pivot | -9.38 | 2.62 | 42.6 | 18.4 |
| arcanine_hisuian | weather setter | -9.07 | 2.6 | 37.9 | 31.9 |
| dewgong | weather setter | -8.91 | 2.69 | 41.7 | 31.9 |
| rapidash_galarian | baton passer | -8.88 | 2.47 | 43.8 | 53.1 |

## Overtuned candidates

Mons whose best playstyle is in the top 10% and clearly above an average teammate.

| Mon | Playstyle | Impact | ± | Win % | Job |
|---|---|---|---|---|---|
| crobat | pivot | 16.38 | 2.9 | 64.7 | 100.0 |
| glaceon | revenge killer | 16.33 | 3.14 | 67.7 | 95.8 |
| magnezone | pivot | 15.7 | 3.7 | 58.7 | 71.1 |
| vaporeon | weather setter | 14.06 | 1.67 | 64.3 | 92.6 |
| golem_alolan | revenge killer | 12.59 | 3.0 | 57.3 | 68.8 |
| sneasler | pivot | 12.46 | 2.83 | 63.5 | 81.6 |
| mismagius | revenge killer | 12.34 | 2.56 | 59.0 | 89.6 |
| gengar | support | 11.39 | 2.9 | 58.5 | 74.3 |
| lanturn | revenge killer | 11.18 | 3.05 | 57.9 | 45.8 |
| overqwil | revenge killer | 10.63 | 3.02 | 57.2 | 92.4 |
| jolteon | pivot | 10.58 | 2.61 | 59.0 | 78.9 |
| aerodactyl | weather setter | 10.51 | 2.76 | 55.8 | 50.0 |
| gyarados | physical attacker | 10.3 | 2.07 | 58.7 | 97.8 |
| perrserker | pivot | 10.25 | 3.58 | 61.1 | 64.5 |
| annihilape | pivot | 10.03 | 2.26 | 60.2 | 42.1 |

## Undertuned candidates

Mons that are clearly worse than an average teammate even in their best playstyle.

| Mon | Playstyle | Impact | ± | Win % | Job |
|---|---|---|---|---|---|
| unown | physical attacker | -21.24 | 1.94 | 30.6 | 2.9 |
| farfetch_d_plain | pivot | -9.38 | 2.62 | 42.6 | 18.4 |
| cloyster | hazard setter | -7.86 | 2.99 | 44.3 | 45.0 |
| weezing_plain | physical wall | -5.56 | 2.04 | 43.8 | 93.8 |
| raticate_plain | physical attacker | -5.44 | 1.93 | 45.5 | 8.7 |
| hypno | trick room setter | -3.65 | 1.79 | 45.6 | 45.0 |

## Not modelled

These mons rely on moves the engine does not simulate (Sketch, Transform outside Imposter), so they are left out of the rankings: smeargle.

## Physical attacker (68 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_dealt | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|
| gyarados | 10.3 | 2.07 | 97.8 | 1.251 | 1.082 | 6.2 | CHOICE_BAND |
| tauros_paldean | 9.32 | 1.99 | 91.3 | 1.154 | 0.975 | 11.6 | CHOICE_BAND |
| overqwil | 7.41 | 2.18 | 97.8 | 1.298 | 1.062 | 6.6 | CHOICE_BAND |
| heracross | 6.82 | 2.06 | 81.9 | 1.078 | 0.945 | 7.8 | FLAME_ORB |
| sneasler | 6.77 | 2.16 | 93.5 | 1.233 | 0.971 | 12.6 | CHOICE_BAND |
| weavile | 6.31 | 2.12 | 81.9 | 1.13 | 0.885 | 15.5 | CHOICE_BAND |
| octillery | -4.42 | 2.14 | 5.1 | 0.69 | 0.557 | 6.4 | CHOICE_BAND |
| arbok | -4.7 | 2.1 | 23.9 | 0.863 | 0.654 | 8.5 | CHOICE_BAND |
| raticate_plain | -5.44 | 1.93 | 8.7 | 0.733 | 0.473 | 8.0 | FLAME_ORB |
| tangrowth | -5.51 | 2.14 | 12.3 | 0.723 | 0.628 | 9.1 | CHOICE_BAND |
| slowbro_galarian | -6.82 | 2.08 | 11.6 | 0.694 | 0.644 | 7.2 | CHOICE_BAND |
| unown | -21.24 | 1.94 | 2.9 | 0.156 | 0.091 | 15.8 | CHOICE_BAND |

## Special attacker (59 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_dealt | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|
| alakazam | 9.67 | 1.91 | 94.1 | 1.24 | 0.976 | 9.3 | CHOICE_SPECS |
| vaporeon | 8.56 | 2.0 | 93.2 | 1.163 | 1.082 | 11.2 | CHOICE_SPECS |
| glaceon | 8.48 | 2.09 | 97.5 | 1.24 | 1.059 | 18.7 | CHOICE_SPECS |
| raichu_plain | 7.84 | 1.97 | 72.9 | 1.091 | 0.87 | 9.7 | CHOICE_SPECS |
| mismagius | 6.91 | 1.9 | 98.3 | 1.324 | 1.017 | 6.7 | CHOICE_SPECS |
| jolteon | 6.85 | 2.02 | 93.2 | 1.258 | 0.963 | 10.6 | CHOICE_SPECS |
| magcargo | -4.92 | 2.18 | 6.8 | 0.688 | 0.651 | 12.4 | CHOICE_SPECS |
| slowking_plain | -5.83 | 2.01 | 12.7 | 0.723 | 0.665 | 7.0 | CHOICE_SPECS |
| slowbro_galarian | -5.85 | 2.14 | 22.0 | 0.805 | 0.682 | 5.4 | CHOICE_SPECS |
| honchkrow | -6.86 | 2.06 | 3.4 | 0.721 | 0.583 | 11.5 | CHOICE_SPECS |
| exeggutor_alolan | -7.64 | 2.17 | 3.4 | 0.647 | 0.598 | 6.6 | CHOICE_SPECS |
| tangrowth | -9.52 | 2.02 | 13.6 | 0.729 | 0.664 | 6.9 | CHOICE_SPECS |

## Mixed attacker (14 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_dealt | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|
| electivire | 6.68 | 2.14 | 96.4 | 1.186 | 0.929 | 10.3 | FOCUS_SASH |
| flareon | 3.72 | 2.14 | 96.4 | 1.113 | 0.952 | 15.1 | CHOICE_SCARF |
| tyranitar | 1.88 | 2.09 | 60.7 | 0.866 | 0.823 | 22.5 | ASSAULT_VEST |
| dragonite | 1.74 | 2.08 | 85.7 | 1.034 | 0.854 | 7.5 | LIFE_ORB |
| raichu_plain | 0.13 | 2.15 | 64.3 | 0.995 | 0.7 | 7.2 | LIFE_ORB |
| victreebel | 0.12 | 1.93 | 39.3 | 0.82 | 0.688 | 7.9 | LIFE_ORB |
| slowbro_galarian | -1.36 | 2.1 | 57.1 | 0.922 | 0.772 | 7.6 | LIFE_ORB |
| honchkrow | -3.74 | 2.19 | 53.6 | 0.966 | 0.674 | 5.9 | LIFE_ORB |
| octillery | -3.76 | 2.09 | 21.4 | 0.72 | 0.582 | 5.4 | LIFE_ORB |
| exeggutor_alolan | -3.77 | 2.13 | 7.1 | 0.562 | 0.53 | 10.5 | LIFE_ORB |
| wyrdeer | -6.62 | 1.94 | 28.6 | 0.763 | 0.648 | 8.7 | LIFE_ORB |
| tangrowth | -6.75 | 2.09 | 14.3 | 0.696 | 0.539 | 7.1 | LIFE_ORB |

## Setup sweeper (88 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_dealt | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|
| overqwil | 10.05 | 2.8 | 98.3 | 1.296 | 1.22 | 16.7 | CHOICE_BAND |
| sneasler | 9.42 | 3.19 | 100.0 | 1.395 | 1.261 | 27.4 | FOCUS_SASH |
| weavile | 8.24 | 3.54 | 92.0 | 1.223 | 1.051 | 23.5 | FOCUS_SASH |
| electivire | 8.07 | 3.46 | 80.1 | 1.132 | 0.919 | 15.4 | FOCUS_SASH |
| aerodactyl | 8.02 | 3.12 | 92.0 | 1.218 | 1.065 | 18.2 | FOCUS_SASH |
| heracross | 7.85 | 2.92 | 80.7 | 1.038 | 1.047 | 18.0 | FLAME_ORB |
| farigiraf | -6.26 | 2.51 | 6.8 | 0.736 | 0.592 | 10.2 | FOCUS_SASH |
| magcargo | -6.27 | 3.38 | 20.5 | 0.795 | 0.72 | 14.4 | FOCUS_SASH |
| slowbro_plain | -6.55 | 2.72 | 9.7 | 0.729 | 0.665 | 11.7 | FOCUS_SASH |
| pidgeot | -6.69 | 2.73 | 5.1 | 0.732 | 0.546 | 9.5 | FOCUS_SASH |
| raticate_plain | -7.61 | 2.42 | 8.5 | 0.736 | 0.615 | 16.6 | FLAME_ORB |
| hypno | -9.39 | 2.43 | 7.4 | 0.715 | 0.661 | 14.3 | FOCUS_SASH |

## Revenge killer (72 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | kos | dmg_dealt | Survives % | Item |
|---|---|---|---|---|---|---|---|
| glaceon | 16.33 | 3.14 | 95.8 | 1.253 | 1.316 | 36.7 | CHOICE_SCARF |
| golem_alolan | 12.59 | 3.0 | 68.8 | 1.014 | 1.074 | 26.6 | CHOICE_SCARF |
| mismagius | 12.34 | 2.56 | 89.6 | 1.109 | 1.274 | 15.7 | CHOICE_SPECS |
| lanturn | 11.18 | 3.05 | 45.8 | 0.818 | 1.061 | 12.9 | CHOICE_SCARF |
| overqwil | 10.63 | 3.02 | 92.4 | 1.147 | 1.298 | 10.1 | CHOICE_SCARF |
| aerodactyl | 10.27 | 3.34 | 100.0 | 1.257 | 1.427 | 17.1 | EXPERT_BELT |
| rapidash_plain | -6.38 | 3.32 | 27.1 | 0.772 | 0.925 | 8.4 | CHOICE_SCARF |
| raticate_plain | -6.45 | 2.35 | 17.4 | 0.768 | 0.844 | 17.5 | CHOICE_BAND |
| ariados | -6.47 | 3.12 | 16.0 | 0.735 | 0.879 | 14.9 | CHOICE_SCARF |
| persian_plain | -7.64 | 2.43 | 2.8 | 0.593 | 0.772 | 12.5 | CHOICE_SCARF |
| pidgeot | -7.95 | 2.95 | 4.2 | 0.619 | 0.794 | 8.5 | CHOICE_SCARF |
| honchkrow | -8.1 | 2.99 | 8.3 | 0.707 | 0.835 | 9.3 | CHOICE_SCARF |

## Weather sweeper (23 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_dealt | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|
| overqwil | 4.02 | 1.35 | 100.0 | 1.162 | 0.971 | 11.2 | LIFE_ORB |
| kabutops | 3.62 | 2.04 | 43.5 | 0.75 | 0.704 | 16.8 | CHOICE_BAND |
| charizard | 3.6 | 1.92 | 91.3 | 1.086 | 0.896 | 9.4 | LIFE_ORB |
| dugtrio_alolan | 3.13 | 1.55 | 82.6 | 0.977 | 0.778 | 16.8 | LIFE_ORB |
| kingdra | 2.14 | 1.02 | 91.3 | 0.986 | 0.935 | 19.7 | LIFE_ORB |
| venusaur | 0.49 | 1.81 | 91.3 | 1.115 | 0.814 | 7.8 | CHOICE_SCARF |
| victreebel | -4.42 | 1.75 | 43.5 | 0.788 | 0.638 | 8.5 | LIFE_ORB |
| qwilfish_plain | -4.94 | 1.91 | 19.6 | 0.754 | 0.546 | 9.1 | LIFE_ORB |
| seaking | -4.98 | 1.63 | 39.1 | 0.773 | 0.646 | 13.8 | LIFE_ORB |
| omastar | -5.31 | 1.91 | 19.6 | 0.72 | 0.577 | 11.6 | LIFE_ORB |
| tangrowth | -7.25 | 1.78 | 17.4 | 0.707 | 0.599 | 10.6 | LIFE_ORB |
| houndoom | -8.6 | 1.92 | 28.3 | 0.751 | 0.605 | 7.7 | LIFE_ORB |

## Baton passer (32 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | passes | subs_made | Survives % | Item |
|---|---|---|---|---|---|---|---|
| glaceon | 8.95 | 3.24 | 53.1 | 0.114 | 0.272 | 38.0 | ASSAULT_VEST |
| alakazam | 4.25 | 2.59 | 23.4 | 0.072 | 0.168 | 23.1 | LIFE_ORB |
| gliscor | 2.44 | 2.93 | 78.1 | 0.093 | 0.523 | 21.5 | TOXIC_ORB |
| ninetales_alolan | 2.15 | 2.94 | 84.4 | 0.118 | 0.452 | 29.8 | LEFTOVERS |
| ninetales_plain | 0.75 | 3.62 | 43.8 | 0.078 | 0.321 | 26.9 | LEFTOVERS |
| rapidash_plain | -1.02 | 2.83 | 3.1 | 0.02 | 0.13 | 22.9 | LEFTOVERS |
| togekiss | -8.6 | 3.0 | 81.2 | 0.096 | 0.707 | 17.5 | LEFTOVERS |
| rapidash_galarian | -8.88 | 2.47 | 53.1 | 0.059 | 0.416 | 22.6 | LEFTOVERS |
| fearow | -9.73 | 2.6 | 42.2 | 0.08 | 0.274 | 22.7 | LEFTOVERS |
| leafeon | -10.66 | 3.14 | 57.8 | 0.091 | 0.373 | 22.9 | LEFTOVERS |
| delibird | -11.29 | 3.1 | 40.6 | 0.056 | 0.382 | 19.4 | LEFTOVERS |
| jumpluff | -14.93 | 3.19 | 76.6 | 0.125 | 0.396 | 24.7 | LEFTOVERS |

## Physical wall (32 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_taken | turns_active | heal_done | Survives % | Item |
|---|---|---|---|---|---|---|---|---|
| skarmory | 4.6 | 1.72 | 86.5 | 1.048 | 5.239 | 0.229 | 22.4 | LEFTOVERS |
| steelix | 3.93 | 2.55 | 82.3 | 1.107 | 4.913 | 0.162 | 28.0 | LEFTOVERS |
| overqwil | 3.25 | 1.79 | 72.9 | 0.976 | 4.584 | 0.18 | 26.8 | ASSAULT_VEST |
| forretress | 2.82 | 1.55 | 96.9 | 1.301 | 6.307 | 0.281 | 26.7 | LEFTOVERS |
| magnezone | 2.46 | 2.87 | 100.0 | 1.331 | 9.038 | 0.3 | 26.4 | LEFTOVERS |
| tauros_paldean | 2.35 | 1.59 | 37.5 | 0.956 | 3.136 | 0.092 | 25.1 | LEFTOVERS |
| slowbro_galarian | -3.55 | 1.92 | 81.2 | 1.135 | 4.487 | 0.173 | 24.0 | LEFTOVERS |
| golem_alolan | -3.81 | 2.17 | 51.0 | 0.901 | 3.215 | 0.171 | 27.8 | LEFTOVERS |
| sandslash_plain | -4.33 | 1.86 | 16.7 | 0.944 | 2.553 | 0.067 | 21.3 | LEFTOVERS |
| weezing_plain | -5.56 | 2.04 | 93.8 | 1.237 | 5.586 | 0.247 | 19.9 | LEFTOVERS |
| weezing_galarian | -5.82 | 2.13 | 75.0 | 1.063 | 3.765 | 0.162 | 26.2 | LEFTOVERS |
| cloyster | -11.49 | 2.15 | 25.0 | 0.947 | 2.728 | 0.072 | 20.1 | LEFTOVERS |

## Special wall (38 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_taken | turns_active | heal_done | Survives % | Item |
|---|---|---|---|---|---|---|---|---|
| gyarados | 6.73 | 1.77 | 86.0 | 1.168 | 6.408 | 0.254 | 27.1 | LEFTOVERS |
| wobbuffet | 5.08 | 1.65 | 93.9 | 1.342 | 7.136 | 0.55 | 24.3 | LEFTOVERS |
| blastoise | 4.55 | 2.39 | 95.6 | 1.39 | 7.68 | 0.335 | 29.7 | LEFTOVERS |
| venusaur | 4.44 | 1.99 | 25.4 | 0.991 | 3.688 | 0.048 | 21.9 | LEFTOVERS |
| togekiss | 3.13 | 2.04 | 40.4 | 0.985 | 4.318 | 0.117 | 28.3 | LEFTOVERS |
| muk_plain | 3.02 | 1.91 | 62.3 | 1.102 | 3.968 | 0.185 | 27.4 | LEFTOVERS |
| slowking_plain | -3.37 | 1.76 | 72.8 | 1.136 | 4.619 | 0.185 | 26.0 | LEFTOVERS |
| dewgong | -3.66 | 2.18 | 43.0 | 1.058 | 3.631 | 0.128 | 19.8 | LEFTOVERS |
| corsola_plain | -4.32 | 2.36 | 32.5 | 1.018 | 3.027 | 0.119 | 20.2 | LEFTOVERS |
| ledian | -4.43 | 1.74 | 22.8 | 0.995 | 2.987 | 0.097 | 21.7 | LEFTOVERS |
| hypno | -7.94 | 1.56 | 13.2 | 0.895 | 3.359 | 0.0 | 21.3 | LEFTOVERS |
| mr__rime | -8.28 | 2.04 | 21.9 | 0.993 | 3.235 | 0.083 | 20.4 | LEFTOVERS |

## Bulky tank (24 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_taken | dmg_dealt | turns_active | Survives % | Item |
|---|---|---|---|---|---|---|---|---|
| dragonite | 8.14 | 2.06 | 79.2 | 1.024 | 1.122 | 3.482 | 20.9 | LEFTOVERS |
| poliwrath | 7.15 | 2.08 | 31.9 | 0.813 | 0.954 | 2.209 | 21.6 | CHOICE_BAND |
| magcargo | 6.51 | 2.67 | 45.8 | 0.99 | 0.821 | 3.105 | 22.8 | LEFTOVERS |
| kingdra | 6.07 | 1.58 | 45.8 | 0.825 | 1.061 | 2.824 | 20.1 | CHOICE_BAND |
| blastoise | 5.37 | 2.46 | 100.0 | 1.359 | 1.259 | 7.125 | 19.5 | LEFTOVERS |
| togekiss | 4.06 | 2.36 | 70.8 | 1.004 | 0.954 | 3.509 | 23.7 | LEFTOVERS |
| bellossom | 0.14 | 2.04 | 50.0 | 1.014 | 0.793 | 3.03 | 21.6 | LEFTOVERS |
| azumarill | -2.02 | 1.65 | 61.1 | 1.081 | 0.737 | 3.712 | 20.5 | LEFTOVERS |
| wigglytuff | -2.81 | 1.5 | 77.8 | 1.179 | 0.859 | 4.592 | 17.9 | LEFTOVERS |
| corsola_plain | -3.03 | 2.51 | 48.6 | 1.038 | 0.689 | 3.305 | 21.2 | LEFTOVERS |
| meganium | -3.32 | 2.07 | 44.4 | 0.941 | 0.894 | 2.819 | 19.9 | LEFTOVERS |
| sudowoodo | -4.26 | 2.4 | 37.5 | 1.001 | 0.704 | 3.009 | 20.5 | LEFTOVERS |

## Support (35 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | status_infl | screens_set | stat_drops | phazes | Survives % | Item |
|---|---|---|---|---|---|---|---|---|---|
| gengar | 11.39 | 2.9 | 74.3 | 0.497 | 0.0 | 0.142 | 0.0 | 24.7 | ASSAULT_VEST |
| weavile | 8.2 | 4.36 | 55.0 | 0.158 | 0.109 | 0.0 | 0.0 | 31.7 | LEFTOVERS |
| electivire | 6.56 | 3.09 | 46.4 | 0.095 | 0.033 | 0.0 | 0.0 | 18.0 | LEFTOVERS |
| alakazam | 3.88 | 1.87 | 65.7 | 0.234 | 0.177 | 0.11 | 0.0 | 28.8 | TWISTEDSPOON |
| slowking_galarian | 3.65 | 2.76 | 65.7 | 0.277 | 0.088 | 0.054 | 0.0 | 25.3 | LEFTOVERS |
| sneasler | 2.65 | 3.19 | 48.6 | 0.098 | 0.061 | 0.0 | 0.0 | 27.7 | FOCUS_SASH |
| electrode_hisuian | -6.46 | 2.74 | 79.3 | 0.216 | 0.285 | 0.156 | 0.0 | 24.6 | LIGHT_CLAY |
| corsola_plain | -6.79 | 4.01 | 63.6 | 0.173 | 0.241 | 0.0 | 0.0 | 22.2 | LIGHT_CLAY |
| magcargo | -7.34 | 3.75 | 56.4 | 0.164 | 0.158 | 0.0 | 0.0 | 22.6 | LIGHT_CLAY |
| slowbro_plain | -7.44 | 2.31 | 67.9 | 0.266 | 0.105 | 0.062 | 0.0 | 19.3 | LEFTOVERS |
| wigglytuff | -8.09 | 1.51 | 85.7 | 0.461 | 0.311 | 0.0 | 0.0 | 30.2 | LIGHT_CLAY |
| shuckle | -9.71 | 2.12 | 67.9 | 0.882 | 0.0 | 0.0 | 0.0 | 15.7 | LEFTOVERS |

## Hazard setter (10 builds)



| Mon | Impact | ± | Job | hazards_set | status_infl | Survives % | Item |
|---|---|---|---|---|---|---|---|
| omastar | 6.43 | 4.31 | 35.0 | 0.234 | 0.199 | 21.6 | LEFTOVERS |
| skarmory | 6.3 | 2.11 | 60.0 | 0.47 | 0.271 | 14.9 | LEFTOVERS |
| beedrill | 1.28 | 2.52 | 25.0 | 0.228 | 0.156 | 21.5 | LEFTOVERS |
| tentacruel | 0.36 | 3.21 | 80.0 | 0.415 | 0.56 | 15.5 | LEFTOVERS |
| overqwil | -0.21 | 2.39 | 80.0 | 0.668 | 0.388 | 29.1 | LEFTOVERS |
| qwilfish_plain | -1.14 | 2.96 | 75.0 | 0.701 | 0.307 | 27.3 | LEFTOVERS |
| forretress | -2.04 | 1.69 | 95.0 | 0.864 | 0.398 | 23.1 | LEFTOVERS |
| sudowoodo | -6.19 | 3.62 | 15.0 | 0.196 | 0.119 | 22.2 | LEFTOVERS |
| cloyster | -7.86 | 2.99 | 45.0 | 0.375 | 0.239 | 24.3 | LEFTOVERS |
| clodsire | -10.45 | 3.71 | 40.0 | 0.145 | 0.314 | 15.9 | LEFTOVERS |

## Cleric (7 builds)



| Mon | Impact | ± | Job | cures | heal_done | Survives % | Item |
|---|---|---|---|---|---|---|---|
| sylveon | 2.51 | 1.66 | 50.0 | 0.065 | 0.154 | 26.6 | LEFTOVERS |
| lapras | 2.23 | 2.93 | 85.7 | 0.178 | 0.247 | 21.3 | LEFTOVERS |
| ampharos | 1.54 | 3.73 | 50.0 | 0.087 | 0.128 | 24.1 | LEFTOVERS |
| vileplume | 0.56 | 2.45 | 14.3 | 0.017 | 0.088 | 18.7 | LEFTOVERS |
| miltank | -0.28 | 1.9 | 50.0 | 0.167 | 0.122 | 27.2 | LEFTOVERS |
| bellossom | -1.55 | 2.71 | 50.0 | 0.083 | 0.133 | 25.3 | LEFTOVERS |
| blissey | -7.02 | 1.86 | 100.0 | 0.456 | 0.261 | 25.4 | LEFTOVERS |

## Pivot (38 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | pivots | dmg_dealt | Survives % | Item |
|---|---|---|---|---|---|---|---|
| crobat | 16.38 | 2.9 | 100.0 | 0.687 | 1.363 | 45.4 | LEFTOVERS |
| magnezone | 15.7 | 3.7 | 71.1 | 0.223 | 1.226 | 25.6 | LEFTOVERS |
| sneasler | 12.46 | 2.83 | 81.6 | 0.267 | 1.241 | 33.6 | LEFTOVERS |
| jolteon | 10.58 | 2.61 | 78.9 | 0.328 | 1.148 | 36.7 | LEFTOVERS |
| perrserker | 10.25 | 3.58 | 64.5 | 0.184 | 1.165 | 31.1 | CHOICE_SCARF |
| annihilape | 10.03 | 2.26 | 42.1 | 0.023 | 1.116 | 21.4 | CHOICE_BAND |
| slowbro_plain | -0.78 | 2.39 | 11.8 | 0.0 | 0.788 | 18.1 | LEFTOVERS |
| forretress | -1.06 | 1.7 | 56.6 | 0.323 | 0.948 | 19.9 | LEFTOVERS |
| slowking_plain | -4.18 | 2.36 | 7.9 | 0.0 | 0.734 | 14.7 | LEFTOVERS |
| ambipom | -5.09 | 1.9 | 28.9 | 0.173 | 0.846 | 26.1 | LEFTOVERS |
| raticate_plain | -5.69 | 1.8 | 21.1 | 0.124 | 0.762 | 22.0 | FLAME_ORB |
| farfetch_d_plain | -9.38 | 2.62 | 18.4 | 0.132 | 0.646 | 15.6 | LEFTOVERS |

## Weather setter (46 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | weather_set | dmg_dealt | Survives % | Item |
|---|---|---|---|---|---|---|---|
| vaporeon | 14.06 | 1.67 | 92.6 | 0.898 | 1.172 | 31.7 | CHOICE_SCARF |
| aerodactyl | 10.51 | 2.76 | 50.0 | 0.022 | 1.152 | 25.6 | SMOOTH_ROCK |
| glaceon | 10.32 | 2.79 | 92.6 | 0.976 | 1.036 | 40.4 | CHOICE_SPECS |
| politoed | 9.5 | 1.4 | 95.7 | 0.98 | 1.12 | 28.2 | CHOICE_SCARF |
| blastoise | 7.6 | 3.24 | 71.3 | 0.328 | 0.804 | 25.6 | DAMP_ROCK |
| feraligatr | 6.31 | 3.17 | 55.3 | 0.255 | 0.709 | 28.2 | DAMP_ROCK |
| rapidash_plain | -6.53 | 2.29 | 25.5 | 0.131 | 0.638 | 20.3 | HEAT_ROCK |
| sudowoodo | -7.0 | 3.54 | 10.6 | 0.025 | 0.563 | 21.4 | SMOOTH_ROCK |
| jynx | -7.85 | 2.78 | 22.3 | 0.165 | 0.584 | 22.5 | ICY_ROCK |
| dewgong | -8.91 | 2.69 | 31.9 | 0.247 | 0.439 | 27.5 | DAMP_ROCK |
| arcanine_hisuian | -9.07 | 2.6 | 31.9 | 0.223 | 0.554 | 22.3 | HEAT_ROCK |
| corsola_plain | -10.74 | 3.44 | 39.4 | 0.302 | 0.515 | 18.6 | DAMP_ROCK |

## Trick room setter (10 builds)



| Mon | Impact | ± | Job | trick_rooms | dmg_dealt | Survives % | Item |
|---|---|---|---|---|---|---|---|
| slowbro_galarian | -1.08 | 2.77 | 55.0 | 0.218 | 0.724 | 17.7 | LEFTOVERS |
| slowbro_plain | -1.13 | 2.32 | 85.0 | 0.276 | 0.858 | 21.4 | LEFTOVERS |
| farigiraf | -1.83 | 1.93 | 75.0 | 0.149 | 0.859 | 18.5 | LEFTOVERS |
| slowking_plain | -1.95 | 2.44 | 85.0 | 0.367 | 0.84 | 18.0 | LEFTOVERS |
| wyrdeer | -3.53 | 1.69 | 30.0 | 0.058 | 0.708 | 19.2 | LEFTOVERS |
| mr__rime | -3.59 | 2.74 | 50.0 | 0.099 | 0.739 | 20.7 | LEFTOVERS |
| hypno | -3.65 | 1.79 | 45.0 | 0.272 | 0.62 | 15.4 | LEFTOVERS |
| slowking_galarian | -5.77 | 2.74 | 85.0 | 0.291 | 0.845 | 15.0 | LEFTOVERS |
| exeggutor_alolan | -6.13 | 2.61 | 10.0 | 0.049 | 0.564 | 23.0 | LEFTOVERS |
| exeggutor_plain | -6.41 | 2.92 | 30.0 | 0.061 | 0.65 | 16.4 | LEFTOVERS |

## Trapper (9 builds)



| Mon | Impact | ± | Job | traps | perish_kos | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|---|
| gengar | 8.0 | 2.89 | 92.6 | 0.0 | 0.0 | 1.071 | 20.3 | FOCUS_SASH |
| dugtrio_plain | 6.55 | 2.37 | 88.9 | 0.0 | 0.0 | 1.035 | 22.1 | CHOICE_BAND |
| magnezone | 6.49 | 3.87 | 81.5 | 0.0 | 0.0 | 0.918 | 26.0 | LEFTOVERS |
| wobbuffet | -1.59 | 1.83 | 85.2 | 0.0 | 0.0 | 0.969 | 18.9 | LEFTOVERS |
| crobat | -3.23 | 2.63 | 74.1 | 0.753 | 0.0 | 0.632 | 17.7 | LEFTOVERS |
| jynx | -4.11 | 2.74 | 74.1 | 0.0 | 0.0 | 0.738 | 20.8 | LIFE_ORB |
| golem_alolan | -5.04 | 3.5 | 77.8 | 0.0 | 0.0 | 0.744 | 26.1 | LEFTOVERS |
| ariados | -5.15 | 3.08 | 70.4 | 0.0 | 0.0 | 0.674 | 26.5 | LEFTOVERS |
| umbreon | -5.19 | 2.17 | 66.7 | 0.676 | 0.0 | 0.583 | 23.9 | LEFTOVERS |
