# Contributing

This is a personal deckbuilding toolkit for one Arena account, not a
general-purpose product, but fixes and improvements to the scripts are
welcome.

## Before you open a PR

- Keep changes to `scripts/` scoped and focused — this repo intentionally
  has no test suite or CI, so keep diffs easy to review by hand.
- Don't commit personal data. `collection.txt`, `pool.json`,
  `.card_cache.json`, and the `decks/`/`paper/` contents reflect one
  person's Arena account and are not meant to be replaced by contributors.
- Run the relevant script against your own `collection.txt`/`pool.json`
  before submitting to confirm it still behaves as documented in
  [README.md](README.md).

## Reporting issues

Open a GitHub issue describing the script, the command you ran, and the
expected vs. actual output. Include relevant `pool.json`/log snippets if
they're not personally sensitive.

## License

By contributing code, you agree it will be licensed under the repository's
[MIT License](LICENSE). See [NOTICE.md](NOTICE.md) for how that differs from
the data files in this repo.
