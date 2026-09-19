# Notice: Code vs. Data Licensing

This repository contains two different kinds of content, licensed differently.

## Code — MIT License

Everything under `scripts/` and any other original program files are
licensed under the MIT License (see [LICENSE](LICENSE)). You're free to
use, copy, modify, and redistribute the code under those terms.

## Data — no license granted

The following are **not** covered by the MIT License and are provided, if at
all, for personal use with this tool and its companion project,
[MTGA_Play-by-Play](https://github.com/), only:

- `collection.txt`, `collection.txt.bak`, `collection.txt.prev` — Arena
  collection exports
- `pool.json`, `.card_cache.json` — generated caches derived from the
  collection export and Scryfall lookups
- `owned-overrides.txt`, `wildcard-wishlist.md`
- `decks/**`, `paper/**` — deck lists and paper-collection tracking

These files contain personal account data and card data (names, mana costs,
Oracle text, rarities, etc.) sourced from the [Scryfall](https://scryfall.com)
API. No license is granted to redistribute, republish, or reuse this data
outside of use with MTGA-Deckbuilding and MTGA_Play-by-Play. If you want card
data for your own project, get it directly from Scryfall.

## Card data / Oracle text — Scryfall Terms of Service

Card names, Oracle text, mana costs, and other card data are sourced via the
Scryfall API and remain subject to
[Scryfall's Terms of Service](https://scryfall.com/docs/terms) and
[Wizards of the Coast's Fan Content Policy](https://company.wizards.com/en/legal/fancontentpolicy).
Magic: The Gathering and all card names/text are property of Wizards of the
Coast LLC. This project is unofficial Fan Content permitted under the Fan
Content Policy; it is not approved or endorsed by Wizards of the Coast.
