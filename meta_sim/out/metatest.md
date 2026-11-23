# Meta test

30,000 battles (390,000 including swap-test replays), 611 builds over 159 mons, seed 0, 311s.

**Impact** = points of team win rate a build adds over a random other build of the same family (offense / speed / defense / utility), from replaying the same battle with it swapped out. Typical standard error here: ±2.4 points, so treat differences under ~5 points as noise. **Job** = average percentile, within the playstyle, on the metrics for that job. Builds with fewer than 150 swap samples are left out of the rankings (still in the CSV).

## Strongest builds overall

| Mon | Playstyle | Impact | ± | Win % | Job |
|---|---|---|---|---|---|
| overqwil | setup sweeper | 13.08 | 2.8 | 58.6 | 92.7 |
| sneasler | pivot | 12.88 | 3.48 | 58.3 | 81.6 |
| glaceon | special attacker | 12.33 | 2.13 | 61.9 | 93.2 |
| nidoking | revenge killer | 12.17 | 3.13 | 57.2 | 76.7 |
| aerodactyl | revenge killer | 12.0 | 3.51 | 61.1 | 100.0 |
| overqwil | physical attacker | 11.94 | 2.0 | 61.2 | 98.6 |
| mismagius | special attacker | 11.52 | 1.95 | 60.1 | 98.3 |
| pinsir | revenge killer | 11.33 | 2.91 | 55.8 | 98.6 |
| sneasler | support | 11.33 | 3.05 | 62.1 | 49.3 |
| dodrio | revenge killer | 10.88 | 3.1 | 58.2 | 87.0 |
| tauros_plain | physical attacker | 10.82 | 2.14 | 59.5 | 95.0 |
| dugtrio_alolan | weather setter | 10.71 | 3.55 | 51.2 | 56.4 |
| annihilape | pivot | 10.59 | 2.29 | 55.6 | 50.0 |
| vaporeon | weather setter | 10.37 | 1.77 | 60.8 | 94.7 |
| weavile | revenge killer | 10.33 | 3.52 | 63.1 | 83.6 |

## Weakest builds overall

| Mon | Playstyle | Impact | ± | Win % | Job |
|---|---|---|---|---|---|
| unown | physical attacker | -17.9 | 1.97 | 32.4 | 2.9 |
| corsola_plain | support | -14.56 | 3.78 | 43.0 | 63.6 |
| dewgong | weather setter | -11.67 | 2.98 | 43.3 | 29.8 |
| farfetch_d_plain | baton passer | -11.4 | 2.42 | 43.5 | 6.1 |
| shuckle | weather setter | -11.05 | 1.97 | 38.0 | 30.9 |
| sudowoodo | hazard setter | -10.86 | 4.08 | 41.1 | 20.0 |
| qwilfish_plain | weather setter | -10.59 | 2.69 | 42.7 | 35.1 |
| cloyster | hazard setter | -9.97 | 3.0 | 41.6 | 55.0 |
| rapidash_plain | baton passer | -9.74 | 3.38 | 36.3 | 9.1 |
| wigglytuff | support | -9.67 | 1.57 | 42.5 | 84.3 |
| clodsire | hazard setter | -9.09 | 4.04 | 42.6 | 40.0 |
| corsola_plain | pivot | -8.99 | 3.91 | 44.4 | 6.6 |
| muk_plain | setup sweeper | -8.89 | 3.17 | 41.3 | 21.9 |
| poliwrath | baton passer | -8.88 | 2.95 | 40.8 | 27.3 |
| umbreon | trapper | -8.87 | 2.37 | 42.1 | 66.7 |

## Overtuned candidates

Mons whose best playstyle is in the top 10% and clearly above an average teammate.

| Mon | Playstyle | Impact | ± | Win % | Job |
|---|---|---|---|---|---|
| overqwil | setup sweeper | 13.08 | 2.8 | 58.6 | 92.7 |
| sneasler | pivot | 12.88 | 3.48 | 58.3 | 81.6 |
| glaceon | special attacker | 12.33 | 2.13 | 61.9 | 93.2 |
| nidoking | revenge killer | 12.17 | 3.13 | 57.2 | 76.7 |
| aerodactyl | revenge killer | 12.0 | 3.51 | 61.1 | 100.0 |
| mismagius | special attacker | 11.52 | 1.95 | 60.1 | 98.3 |
| pinsir | revenge killer | 11.33 | 2.91 | 55.8 | 98.6 |
| dodrio | revenge killer | 10.88 | 3.1 | 58.2 | 87.0 |
| tauros_plain | physical attacker | 10.82 | 2.14 | 59.5 | 95.0 |
| dugtrio_alolan | weather setter | 10.71 | 3.55 | 51.2 | 56.4 |
| annihilape | pivot | 10.59 | 2.29 | 55.6 | 50.0 |
| vaporeon | weather setter | 10.37 | 1.77 | 60.8 | 94.7 |
| weavile | revenge killer | 10.33 | 3.52 | 63.1 | 83.6 |
| dugtrio_plain | trapper | 10.29 | 2.51 | 58.8 | 88.9 |
| kleavor | pivot | 9.78 | 2.5 | 58.3 | 64.5 |

## Undertuned candidates

Mons that are clearly worse than an average teammate even in their best playstyle.

| Mon | Playstyle | Impact | ± | Win % | Job |
|---|---|---|---|---|---|
| unown | physical attacker | -17.9 | 1.97 | 32.4 | 2.9 |
| blissey | cleric | -5.43 | 1.74 | 43.2 | 85.7 |
| parasect | physical attacker | -4.52 | 2.18 | 46.9 | 26.4 |
| exeggutor_alolan | mixed attacker | -4.46 | 2.06 | 45.0 | 7.1 |
| dewgong | special wall | -4.46 | 2.06 | 45.5 | 26.3 |
| sandslash_plain | weather sweeper | -4.21 | 1.3 | 44.2 | 8.7 |
| hypno | special wall | -4.0 | 1.49 | 45.2 | 16.7 |

## Not modelled

These mons rely on moves the engine does not simulate (Sketch, Transform outside Imposter), so they are left out of the rankings: smeargle.

## Physical attacker (69 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_dealt | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|
| overqwil | 11.94 | 2.0 | 98.6 | 1.287 | 1.072 | 7.3 | CHOICE_BAND |
| tauros_plain | 10.82 | 2.14 | 95.0 | 1.257 | 1.009 | 9.7 | CHOICE_BAND |
| sneasler | 9.97 | 2.2 | 96.4 | 1.284 | 1.015 | 15.2 | CHOICE_BAND |
| dugtrio_alolan | 8.0 | 2.13 | 73.6 | 1.096 | 0.855 | 10.1 | CHOICE_BAND |
| feraligatr | 7.82 | 2.03 | 80.0 | 1.073 | 0.92 | 9.4 | CHOICE_BAND |
| pinsir | 7.42 | 1.97 | 100.0 | 1.345 | 1.233 | 15.2 | CHOICE_BAND |
| victreebel | -5.68 | 2.11 | 28.6 | 0.831 | 0.709 | 7.8 | CHOICE_BAND |
| wyrdeer | -5.99 | 2.0 | 42.9 | 0.896 | 0.781 | 6.0 | CHOICE_BAND |
| sudowoodo | -7.41 | 2.14 | 24.3 | 0.789 | 0.708 | 9.3 | CHOICE_BAND |
| raticate_plain | -7.6 | 1.9 | 7.1 | 0.724 | 0.469 | 8.4 | FLAME_ORB |
| farfetch_d_plain | -7.89 | 2.04 | 17.1 | 0.824 | 0.614 | 3.2 | CHOICE_BAND |
| unown | -17.9 | 1.97 | 2.9 | 0.161 | 0.107 | 13.4 | CHOICE_BAND |

## Special attacker (59 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_dealt | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|
| glaceon | 12.33 | 2.13 | 93.2 | 1.171 | 1.016 | 18.5 | CHOICE_SPECS |
| mismagius | 11.52 | 1.95 | 98.3 | 1.299 | 1.008 | 7.8 | CHOICE_SPECS |
| jolteon | 8.11 | 2.1 | 95.8 | 1.238 | 0.972 | 12.0 | CHOICE_SPECS |
| espeon | 6.94 | 1.91 | 90.7 | 1.201 | 0.954 | 11.8 | CHOICE_SPECS |
| charizard | 6.32 | 2.03 | 76.3 | 1.099 | 0.872 | 5.7 | CHOICE_SPECS |
| porygon_z | 6.25 | 2.03 | 51.7 | 0.944 | 0.773 | 13.5 | CHOICE_SPECS |
| magcargo | -5.07 | 2.1 | 20.3 | 0.77 | 0.696 | 11.6 | CHOICE_SPECS |
| slowking_plain | -5.6 | 2.0 | 11.0 | 0.744 | 0.662 | 7.8 | CHOICE_SPECS |
| exeggutor_plain | -6.56 | 1.98 | 6.8 | 0.71 | 0.627 | 7.1 | CHOICE_SPECS |
| tangrowth | -6.62 | 2.14 | 5.1 | 0.74 | 0.608 | 7.5 | CHOICE_SPECS |
| exeggutor_alolan | -6.68 | 2.09 | 5.9 | 0.635 | 0.638 | 9.8 | CHOICE_SPECS |
| honchkrow | -6.99 | 2.07 | 2.5 | 0.701 | 0.559 | 10.8 | CHOICE_SPECS |

## Mixed attacker (14 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_dealt | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|
| flareon | 8.98 | 2.16 | 100.0 | 1.17 | 0.986 | 15.1 | CHOICE_SCARF |
| dragonite | 6.0 | 2.06 | 85.7 | 1.089 | 0.871 | 6.7 | LIFE_ORB |
| electivire | 4.79 | 2.13 | 92.9 | 1.161 | 0.902 | 9.7 | FOCUS_SASH |
| tyranitar | 3.73 | 2.13 | 67.9 | 0.911 | 0.845 | 23.6 | ASSAULT_VEST |
| honchkrow | 2.7 | 2.24 | 53.6 | 0.98 | 0.666 | 5.3 | LIFE_ORB |
| raichu_plain | 2.19 | 2.08 | 64.3 | 1.022 | 0.712 | 7.1 | LIFE_ORB |
| slowbro_galarian | -0.68 | 2.15 | 53.6 | 0.89 | 0.751 | 9.3 | LIFE_ORB |
| victreebel | -3.55 | 2.03 | 39.3 | 0.773 | 0.695 | 8.6 | LIFE_ORB |
| tangrowth | -3.96 | 2.06 | 17.9 | 0.695 | 0.568 | 9.5 | LIFE_ORB |
| exeggutor_alolan | -4.46 | 2.06 | 7.1 | 0.595 | 0.562 | 8.7 | LIFE_ORB |
| octillery | -6.97 | 2.05 | 17.9 | 0.718 | 0.564 | 5.2 | LIFE_ORB |
| wyrdeer | -8.77 | 1.98 | 28.6 | 0.759 | 0.636 | 7.3 | LIFE_ORB |

## Setup sweeper (89 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_dealt | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|
| overqwil | 13.08 | 2.8 | 92.7 | 1.178 | 1.136 | 18.3 | CHOICE_BAND |
| mismagius | 9.75 | 2.46 | 97.2 | 1.346 | 1.081 | 14.7 | FOCUS_SASH |
| ninetales_plain | 9.59 | 3.64 | 96.1 | 1.227 | 1.188 | 17.0 | CHOICE_SPECS |
| dugtrio_alolan | 8.96 | 3.29 | 90.4 | 1.254 | 1.019 | 20.9 | FOCUS_SASH |
| electrode_plain | 8.54 | 3.42 | 78.7 | 1.076 | 0.951 | 13.7 | CHOICE_SPECS |
| jolteon | 8.49 | 3.12 | 98.3 | 1.302 | 1.17 | 29.6 | FOCUS_SASH |
| slowking_galarian | -7.02 | 2.78 | 32.0 | 0.813 | 0.798 | 12.3 | FOCUS_SASH |
| hitmontop | -7.09 | 2.73 | 6.2 | 0.725 | 0.635 | 13.7 | FOCUS_SASH |
| snorlax | -7.16 | 2.52 | 20.8 | 0.698 | 0.797 | 15.9 | LIFE_ORB |
| pidgeot | -8.52 | 2.81 | 10.1 | 0.796 | 0.563 | 7.7 | FOCUS_SASH |
| furret | -8.64 | 2.61 | 8.4 | 0.755 | 0.622 | 15.1 | FOCUS_SASH |
| muk_plain | -8.89 | 3.17 | 21.9 | 0.793 | 0.762 | 17.1 | FOCUS_SASH |

## Revenge killer (73 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | kos | dmg_dealt | Survives % | Item |
|---|---|---|---|---|---|---|---|
| nidoking | 12.17 | 3.13 | 76.7 | 1.003 | 1.212 | 17.1 | CHOICE_SCARF |
| aerodactyl | 12.0 | 3.51 | 100.0 | 1.313 | 1.465 | 16.7 | EXPERT_BELT |
| pinsir | 11.33 | 2.91 | 98.6 | 1.241 | 1.402 | 18.4 | CHOICE_SCARF |
| dodrio | 10.88 | 3.1 | 87.0 | 1.065 | 1.317 | 11.2 | FOCUS_SASH |
| weavile | 10.33 | 3.52 | 83.6 | 1.111 | 1.194 | 25.5 | CHOICE_BAND |
| glaceon | 9.97 | 3.08 | 95.2 | 1.209 | 1.319 | 31.5 | CHOICE_SCARF |
| machamp | -5.25 | 2.49 | 12.3 | 0.73 | 0.852 | 11.0 | FLAME_ORB |
| farfetch_d_plain | -5.68 | 3.26 | 26.7 | 0.767 | 0.945 | 8.2 | CHOICE_SCARF |
| persian_plain | -6.64 | 2.54 | 2.1 | 0.572 | 0.73 | 14.4 | CHOICE_SCARF |
| furret | -6.65 | 2.47 | 16.4 | 0.758 | 0.876 | 13.1 | CHOICE_SCARF |
| pidgeot | -7.47 | 2.82 | 3.4 | 0.592 | 0.796 | 10.4 | CHOICE_SCARF |
| kabutops | -8.31 | 3.2 | 8.2 | 0.698 | 0.851 | 16.3 | CHOICE_SCARF |

## Weather sweeper (23 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_dealt | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|
| overqwil | 4.48 | 1.4 | 100.0 | 1.15 | 0.978 | 12.8 | LIFE_ORB |
| kingdra | 3.81 | 1.0 | 91.3 | 0.999 | 0.945 | 20.4 | LIFE_ORB |
| venusaur | 2.24 | 1.87 | 87.0 | 1.088 | 0.79 | 8.2 | CHOICE_SCARF |
| charizard | 0.41 | 1.84 | 93.5 | 1.094 | 0.9 | 8.2 | LIFE_ORB |
| sandslash_alolan | 0.34 | 1.32 | 65.2 | 0.819 | 0.785 | 24.9 | CHOICE_BAND |
| dugtrio_alolan | -0.07 | 1.5 | 84.8 | 0.989 | 0.795 | 15.7 | LIFE_ORB |
| mantine | -4.48 | 1.41 | 56.5 | 0.841 | 0.666 | 11.0 | LIFE_ORB |
| seaking | -5.05 | 1.66 | 47.8 | 0.787 | 0.666 | 14.4 | LIFE_ORB |
| steelix | -5.14 | 1.43 | 26.1 | 0.708 | 0.641 | 13.2 | LIFE_ORB |
| tangrowth | -5.17 | 1.83 | 19.6 | 0.723 | 0.615 | 10.8 | LIFE_ORB |
| exeggutor_plain | -5.5 | 1.91 | 17.4 | 0.668 | 0.62 | 8.6 | LIFE_ORB |
| bellossom | -7.17 | 1.83 | 37.0 | 0.768 | 0.649 | 10.5 | LIFE_ORB |

## Baton passer (33 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | passes | subs_made | Survives % | Item |
|---|---|---|---|---|---|---|---|
| ninetales_plain | 5.76 | 3.24 | 43.9 | 0.086 | 0.263 | 28.1 | LEFTOVERS |
| glaceon | 4.05 | 3.18 | 68.2 | 0.14 | 0.324 | 37.4 | ASSAULT_VEST |
| alakazam | 4.0 | 2.56 | 28.8 | 0.074 | 0.16 | 24.4 | LIFE_ORB |
| beedrill | 2.2 | 3.09 | 47.0 | 0.053 | 0.39 | 26.7 | LEFTOVERS |
| espeon | 0.9 | 2.56 | 57.6 | 0.094 | 0.339 | 26.5 | LEFTOVERS |
| ninetales_alolan | 0.57 | 2.66 | 77.3 | 0.129 | 0.425 | 30.5 | LEFTOVERS |
| delibird | -8.43 | 3.04 | 50.0 | 0.069 | 0.373 | 21.7 | LEFTOVERS |
| ambipom | -8.46 | 2.42 | 25.8 | 0.027 | 0.283 | 24.1 | LEFTOVERS |
| farigiraf | -8.86 | 2.52 | 75.8 | 0.112 | 0.427 | 24.2 | LEFTOVERS |
| poliwrath | -8.88 | 2.95 | 27.3 | 0.056 | 0.249 | 18.3 | LEFTOVERS |
| rapidash_plain | -9.74 | 3.38 | 9.1 | 0.019 | 0.146 | 13.5 | LEFTOVERS |
| farfetch_d_plain | -11.4 | 2.42 | 6.1 | 0.023 | 0.114 | 20.7 | LEFTOVERS |

## Physical wall (32 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_taken | turns_active | heal_done | Survives % | Item |
|---|---|---|---|---|---|---|---|---|
| skarmory | 8.62 | 1.79 | 90.6 | 1.054 | 5.566 | 0.242 | 24.0 | LEFTOVERS |
| overqwil | 5.47 | 1.87 | 70.8 | 0.976 | 4.692 | 0.184 | 27.7 | ASSAULT_VEST |
| magnezone | 5.32 | 2.79 | 100.0 | 1.353 | 7.588 | 0.286 | 23.3 | LEFTOVERS |
| ursaluna_bloodmoon | 4.87 | 2.16 | 31.2 | 0.872 | 2.928 | 0.107 | 26.4 | ASSAULT_VEST |
| miltank | 4.49 | 1.62 | 50.0 | 0.828 | 3.674 | 0.15 | 25.2 | LEFTOVERS |
| donphan | 4.27 | 1.86 | 47.9 | 0.996 | 2.918 | 0.116 | 26.6 | LEFTOVERS |
| magcargo | -3.19 | 2.74 | 33.3 | 0.962 | 3.066 | 0.079 | 26.0 | LEFTOVERS |
| rhyperior | -3.58 | 2.3 | 36.5 | 0.962 | 3.073 | 0.088 | 30.9 | LEFTOVERS |
| cloyster | -4.28 | 2.14 | 57.3 | 0.994 | 3.389 | 0.108 | 21.7 | LEFTOVERS |
| sandslash_plain | -5.53 | 1.8 | 32.3 | 0.982 | 2.73 | 0.094 | 21.6 | LEFTOVERS |
| sandslash_alolan | -5.75 | 2.26 | 61.5 | 0.992 | 3.857 | 0.107 | 27.2 | LEFTOVERS |
| weezing_galarian | -6.37 | 1.99 | 68.8 | 1.032 | 3.574 | 0.125 | 22.7 | LEFTOVERS |

## Special wall (38 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_taken | turns_active | heal_done | Survives % | Item |
|---|---|---|---|---|---|---|---|---|
| ampharos | 8.45 | 2.5 | 36.8 | 0.99 | 3.548 | 0.14 | 31.7 | LEFTOVERS |
| clodsire | 7.3 | 2.6 | 67.5 | 1.092 | 4.367 | 0.214 | 18.1 | ASSAULT_VEST |
| venusaur | 6.12 | 1.86 | 19.3 | 0.986 | 3.37 | 0.038 | 19.6 | LEFTOVERS |
| vaporeon | 5.35 | 1.58 | 41.2 | 1.001 | 3.59 | 0.144 | 26.9 | LEFTOVERS |
| blastoise | 4.57 | 2.4 | 88.6 | 1.193 | 6.711 | 0.233 | 31.8 | LEFTOVERS |
| sylveon | 3.58 | 1.47 | 41.2 | 1.036 | 3.595 | 0.129 | 24.6 | LEFTOVERS |
| corsola_plain | -3.29 | 2.35 | 21.1 | 0.988 | 2.86 | 0.095 | 22.8 | LEFTOVERS |
| mr__rime | -3.77 | 2.03 | 47.4 | 1.05 | 4.4 | 0.118 | 20.6 | LEFTOVERS |
| hypno | -4.0 | 1.49 | 16.7 | 0.912 | 3.565 | 0.0 | 21.7 | LEFTOVERS |
| dewgong | -4.46 | 2.06 | 26.3 | 0.981 | 3.537 | 0.104 | 23.6 | LEFTOVERS |
| bellossom | -4.62 | 1.85 | 36.0 | 0.987 | 4.0 | 0.12 | 25.6 | LEFTOVERS |
| blissey | -6.65 | 1.55 | 84.2 | 1.092 | 7.349 | 0.225 | 24.8 | LEFTOVERS |

## Bulky tank (24 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | dmg_taken | dmg_dealt | turns_active | Survives % | Item |
|---|---|---|---|---|---|---|---|---|
| kingdra | 6.57 | 1.51 | 44.4 | 0.833 | 1.031 | 2.742 | 18.5 | CHOICE_BAND |
| lickilicky | 6.19 | 1.55 | 50.0 | 0.945 | 0.838 | 3.334 | 25.0 | LEFTOVERS |
| ampharos | 6.03 | 2.54 | 72.2 | 1.03 | 1.007 | 3.263 | 18.5 | LEFTOVERS |
| poliwrath | 5.34 | 2.06 | 31.9 | 0.839 | 0.936 | 2.301 | 17.9 | CHOICE_BAND |
| dragonite | 4.89 | 2.08 | 77.8 | 1.041 | 1.022 | 3.383 | 18.1 | LEFTOVERS |
| ursaluna_plain | 4.52 | 2.13 | 26.4 | 0.768 | 0.894 | 2.322 | 23.1 | FLAME_ORB |
| magcargo | -2.05 | 2.59 | 44.4 | 0.99 | 0.828 | 3.059 | 22.8 | LEFTOVERS |
| sudowoodo | -2.21 | 2.32 | 23.6 | 0.948 | 0.65 | 2.681 | 22.1 | LEFTOVERS |
| bellossom | -2.22 | 2.02 | 51.4 | 1.009 | 0.833 | 3.089 | 23.1 | LEFTOVERS |
| wigglytuff | -3.07 | 1.49 | 80.6 | 1.199 | 0.867 | 4.519 | 18.0 | LEFTOVERS |
| azumarill | -5.94 | 1.62 | 70.8 | 1.179 | 0.802 | 4.53 | 19.8 | LEFTOVERS |
| corsola_plain | -7.48 | 2.48 | 51.4 | 1.009 | 0.751 | 3.385 | 19.2 | LEFTOVERS |

## Support (35 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | status_infl | screens_set | stat_drops | phazes | Survives % | Item |
|---|---|---|---|---|---|---|---|---|---|
| sneasler | 11.33 | 3.05 | 49.3 | 0.136 | 0.071 | 0.0 | 0.0 | 33.7 | FOCUS_SASH |
| ampharos | 9.25 | 3.61 | 61.4 | 0.278 | 0.115 | 0.0 | 0.0 | 25.1 | LEFTOVERS |
| weavile | 6.43 | 4.39 | 50.0 | 0.082 | 0.105 | 0.0 | 0.0 | 27.5 | LEFTOVERS |
| gengar | 6.41 | 3.15 | 75.0 | 0.542 | 0.0 | 0.157 | 0.0 | 25.7 | ASSAULT_VEST |
| crobat | 4.65 | 2.75 | 68.6 | 0.619 | 0.0 | 0.058 | 0.0 | 21.5 | LEFTOVERS |
| alakazam | 4.25 | 1.79 | 68.6 | 0.242 | 0.176 | 0.107 | 0.0 | 29.3 | TWISTEDSPOON |
| togekiss | -6.38 | 2.73 | 75.0 | 0.287 | 0.299 | 0.0 | 0.0 | 26.4 | LIGHT_CLAY |
| raichu_alolan | -6.69 | 3.08 | 76.4 | 0.288 | 0.241 | 0.097 | 0.0 | 29.4 | FOCUS_SASH |
| hypno | -7.25 | 1.72 | 84.3 | 0.379 | 0.206 | 0.128 | 0.0 | 24.1 | LIGHT_CLAY |
| shuckle | -7.83 | 2.42 | 67.9 | 0.852 | 0.0 | 0.0 | 0.0 | 16.5 | LEFTOVERS |
| wigglytuff | -9.67 | 1.57 | 84.3 | 0.485 | 0.273 | 0.0 | 0.0 | 30.9 | LIGHT_CLAY |
| corsola_plain | -14.56 | 3.78 | 63.6 | 0.241 | 0.196 | 0.0 | 0.0 | 27.2 | LIGHT_CLAY |

## Hazard setter (10 builds)



| Mon | Impact | ± | Job | hazards_set | status_infl | Survives % | Item |
|---|---|---|---|---|---|---|---|
| tentacruel | 4.2 | 3.21 | 75.0 | 0.305 | 0.527 | 19.5 | LEFTOVERS |
| beedrill | 3.96 | 2.59 | 30.0 | 0.252 | 0.198 | 25.0 | LEFTOVERS |
| skarmory | 3.27 | 2.03 | 55.0 | 0.513 | 0.252 | 15.4 | LEFTOVERS |
| overqwil | 2.33 | 2.56 | 90.0 | 0.789 | 0.416 | 24.9 | LEFTOVERS |
| qwilfish_plain | 0.0 | 3.41 | 75.0 | 0.788 | 0.36 | 26.3 | LEFTOVERS |
| omastar | -3.83 | 3.97 | 20.0 | 0.137 | 0.208 | 17.5 | LEFTOVERS |
| forretress | -4.04 | 1.68 | 90.0 | 0.928 | 0.388 | 20.9 | LEFTOVERS |
| clodsire | -9.09 | 4.04 | 40.0 | 0.167 | 0.344 | 15.3 | LEFTOVERS |
| cloyster | -9.97 | 3.0 | 55.0 | 0.44 | 0.326 | 22.7 | LEFTOVERS |
| sudowoodo | -10.86 | 4.08 | 20.0 | 0.189 | 0.131 | 22.9 | LEFTOVERS |

## Cleric (7 builds)



| Mon | Impact | ± | Job | cures | heal_done | Survives % | Item |
|---|---|---|---|---|---|---|---|
| sylveon | 1.56 | 1.68 | 71.4 | 0.087 | 0.241 | 27.6 | LEFTOVERS |
| miltank | 0.0 | 1.82 | 57.1 | 0.123 | 0.114 | 24.4 | LEFTOVERS |
| ampharos | -0.92 | 3.67 | 42.9 | 0.05 | 0.14 | 23.4 | LEFTOVERS |
| lapras | -1.02 | 3.1 | 92.9 | 0.184 | 0.251 | 24.8 | LEFTOVERS |
| bellossom | -3.38 | 2.62 | 35.7 | 0.055 | 0.073 | 24.1 | LEFTOVERS |
| vileplume | -5.19 | 2.47 | 14.3 | 0.033 | 0.055 | 19.9 | LEFTOVERS |
| blissey | -5.43 | 1.74 | 85.7 | 0.329 | 0.227 | 27.4 | LEFTOVERS |

## Pivot (38 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | pivots | dmg_dealt | Survives % | Item |
|---|---|---|---|---|---|---|---|
| sneasler | 12.88 | 3.48 | 81.6 | 0.308 | 1.156 | 34.2 | LEFTOVERS |
| annihilape | 10.59 | 2.29 | 50.0 | 0.03 | 1.156 | 17.7 | CHOICE_BAND |
| kleavor | 9.78 | 2.5 | 64.5 | 0.228 | 1.14 | 23.0 | ASSAULT_VEST |
| crobat | 9.19 | 2.79 | 100.0 | 0.719 | 1.442 | 40.4 | LEFTOVERS |
| ampharos | 7.98 | 4.08 | 38.2 | 0.141 | 0.935 | 27.2 | LEFTOVERS |
| scizor | 7.8 | 1.8 | 52.6 | 0.121 | 1.104 | 22.9 | LEFTOVERS |
| persian_plain | -0.62 | 1.91 | 18.4 | 0.052 | 0.856 | 20.5 | CHOICE_BAND |
| ambipom | -0.97 | 1.79 | 32.9 | 0.178 | 0.874 | 24.9 | LEFTOVERS |
| farfetch_d_plain | -2.78 | 2.64 | 17.1 | 0.084 | 0.788 | 19.2 | LEFTOVERS |
| slowbro_plain | -3.12 | 2.21 | 7.9 | 0.0 | 0.755 | 17.8 | LEFTOVERS |
| raticate_plain | -4.19 | 1.89 | 19.7 | 0.087 | 0.808 | 22.4 | FLAME_ORB |
| corsola_plain | -8.99 | 3.91 | 6.6 | 0.0 | 0.632 | 18.5 | LEFTOVERS |

## Weather setter (46 builds)

Top and bottom by impact.

| Mon | Impact | ± | Job | weather_set | dmg_dealt | Survives % | Item |
|---|---|---|---|---|---|---|---|
| dugtrio_alolan | 10.71 | 3.55 | 56.4 | 0.056 | 1.173 | 19.4 | FOCUS_SASH |
| vaporeon | 10.37 | 1.77 | 94.7 | 0.942 | 1.163 | 28.2 | CHOICE_SCARF |
| politoed | 9.36 | 1.44 | 95.7 | 0.965 | 1.103 | 27.2 | CHOICE_SCARF |
| aerodactyl | 9.32 | 3.0 | 48.9 | 0.015 | 1.119 | 21.7 | SMOOTH_ROCK |
| charizard | 9.19 | 2.05 | 50.0 | 0.047 | 1.091 | 25.5 | ASSAULT_VEST |
| ninetales_plain | 8.82 | 2.56 | 89.4 | 0.943 | 0.954 | 23.5 | HEAT_ROCK |
| golem_alolan | -6.73 | 2.95 | 25.5 | 0.034 | 0.718 | 27.3 | SMOOTH_ROCK |
| magcargo | -7.01 | 2.49 | 19.1 | 0.145 | 0.558 | 25.3 | HEAT_ROCK |
| rapidash_plain | -7.25 | 2.27 | 27.7 | 0.149 | 0.645 | 21.2 | HEAT_ROCK |
| qwilfish_plain | -10.59 | 2.69 | 35.1 | 0.255 | 0.523 | 26.2 | DAMP_ROCK |
| shuckle | -11.05 | 1.97 | 30.9 | 0.245 | 0.303 | 13.1 | SMOOTH_ROCK |
| dewgong | -11.67 | 2.98 | 29.8 | 0.236 | 0.461 | 27.5 | DAMP_ROCK |

## Trick room setter (10 builds)



| Mon | Impact | ± | Job | trick_rooms | dmg_dealt | Survives % | Item |
|---|---|---|---|---|---|---|---|
| slowbro_plain | 2.2 | 2.35 | 75.0 | 0.275 | 0.785 | 20.4 | LEFTOVERS |
| slowking_plain | 1.36 | 2.41 | 95.0 | 0.343 | 0.812 | 20.1 | LEFTOVERS |
| slowking_galarian | 0.51 | 2.87 | 90.0 | 0.289 | 0.9 | 19.2 | LEFTOVERS |
| mr__rime | -1.41 | 2.78 | 45.0 | 0.155 | 0.751 | 17.8 | LEFTOVERS |
| farigiraf | -2.13 | 1.83 | 60.0 | 0.183 | 0.783 | 19.9 | LEFTOVERS |
| exeggutor_plain | -4.31 | 2.85 | 35.0 | 0.098 | 0.703 | 18.4 | LEFTOVERS |
| exeggutor_alolan | -5.1 | 2.52 | 10.0 | 0.049 | 0.607 | 22.3 | LEFTOVERS |
| wyrdeer | -5.23 | 1.65 | 25.0 | 0.079 | 0.691 | 18.5 | LEFTOVERS |
| hypno | -5.55 | 1.93 | 55.0 | 0.291 | 0.681 | 17.2 | LEFTOVERS |
| slowbro_galarian | -7.4 | 2.66 | 60.0 | 0.255 | 0.779 | 17.3 | LEFTOVERS |

## Trapper (9 builds)



| Mon | Impact | ± | Job | traps | perish_kos | kos | Survives % | Item |
|---|---|---|---|---|---|---|---|---|
| dugtrio_plain | 10.29 | 2.51 | 88.9 | 0.0 | 0.0 | 1.079 | 19.9 | CHOICE_BAND |
| gengar | 8.41 | 2.87 | 92.6 | 0.0 | 0.0 | 1.246 | 25.8 | FOCUS_SASH |
| magnezone | 4.18 | 3.69 | 81.5 | 0.0 | 0.0 | 0.874 | 24.7 | LEFTOVERS |
| crobat | 0.55 | 2.73 | 81.5 | 0.782 | 0.0 | 0.696 | 18.5 | LEFTOVERS |
| ariados | -0.33 | 3.04 | 70.4 | 0.0 | 0.0 | 0.643 | 21.3 | LEFTOVERS |
| jynx | -0.56 | 2.95 | 77.8 | 0.0 | 0.0 | 0.791 | 19.5 | LIFE_ORB |
| wobbuffet | -3.98 | 1.78 | 85.2 | 0.0 | 0.0 | 0.943 | 21.9 | LEFTOVERS |
| golem_alolan | -4.42 | 3.64 | 66.7 | 0.0 | 0.0 | 0.624 | 27.9 | LEFTOVERS |
| umbreon | -8.87 | 2.37 | 66.7 | 0.641 | 0.0 | 0.539 | 23.5 | LEFTOVERS |
