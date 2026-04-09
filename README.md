# Open Worship Songs

A community-driven collection of worship songs with lyrics and chords in ChordPro format. Multi-language: English, Spanish, Portuguese, Catalan.

## About

This repository provides free, open-source worship songs for worship teams. Each song is a `.cho` file in standard [ChordPro format](https://www.chordpro.org/), ready to be imported into any compatible worship software.

## Structure

```
├── es/
│   ├── himnos/          # Himnos clásicos (dominio público)
│   └── popular/         # Canciones populares de worship
├── en/
│   └── hymns/           # Classic hymns (public domain)
├── pt/
│   └── hinos/           # Hinos clássicos (domínio público)
└── ca/                  # Himnes (coming soon)
```

## Song Count

| Language | Folder | Songs |
|----------|--------|-------|
| 🇪🇸 Spanish | `es/himnos/` | 17 |
| 🇪🇸 Spanish | `es/popular/` | 2 |
| 🇬🇧 English | `en/hymns/` | 20 |
| 🇧🇷 Portuguese | `pt/hinos/` | 20 |

## ChordPro Format

Each `.cho` file looks like this:

```
{title: Amazing Grace}
{artist: John Newton}
{key: G}

{comment: Verse 1}
[G]Amazing [G7]grace, how [C]sweet the [G]sound
That [G]saved a [Em]wretch like [D]me
[G]I once [G7]was lost, but [C]now am [G]found
Was [G]blind, but [D]now I [G]see
```

### Supported Directives

- `{title:}` or `{t:}` — Song title
- `{artist:}` or `{subtitle:}` — Author/artist
- `{key:}` — Original key
- `{ccli:}` — CCLI song number
- `{comment:}` or `{c:}` — Section label (Verse 1, Chorus, Bridge, etc.)

Chords use inline notation: `[Am]word [G]next`

## Contributing

Contributions are welcome! To add a song:

1. Create a `.cho` file with the song in ChordPro format
2. Name the file using lowercase with hyphens: `song-title.cho`
3. Place it in the correct language/category folder
4. Open a Pull Request

### Guidelines

- Songs must be **public domain** (published before 1928) or **Creative Commons** licensed for the `hymns/himnos/hinos` folders
- Popular/modern songs go in the `popular/` folder
- Use **American chord notation** (C, D, E, F, G, A, B — not Do, Re, Mi)
- Include `{title:}`, `{artist:}`, and `{key:}` directives at minimum
- Use `{comment:}` to mark sections (Verse 1, Chorus, Bridge, etc.)

## License

The songs in the `hymns/himnos/hinos` folders are in the **public domain**. Songs in `popular/` folders may have their own copyright — contributors are responsible for ensuring they have the rights to share. This repository structure and tooling is licensed under [MIT](LICENSE).

## Disclaimer

This is a community project. If you believe any content infringes your copyright, please open an issue and we will remove it promptly.
