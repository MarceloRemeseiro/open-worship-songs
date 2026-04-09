# Open Worship Songs

A community-driven collection of worship songs with lyrics and chords in ChordPro format. Multi-language: English, Spanish, Portuguese.

## Song Count

| Language | Hymns | Popular | Total |
|----------|-------|---------|-------|
| 🇪🇸 Spanish | 138 | 247 | **385** |
| 🇬🇧 English | 30 | 619 | **649** |
| 🇧🇷 Portuguese | 40 | — | **40** |
| **Total** | **208** | **866** | **1,074** |

## Structure

```
├── es/
│   ├── himnos/          # Himnos clásicos de himnario
│   └── popular/         # Canciones contemporáneas de worship
├── en/
│   ├── hymns/           # Classic hymns
│   └── popular/         # Contemporary worship songs
├── pt/
│   └── hinos/           # Hinos e louvor
└── README.md
```

## ChordPro Format

Each `.cho` file uses standard [ChordPro format](https://www.chordpro.org/):

```
{title: Amazing Grace}
{artist: John Newton}
{key: G}
{ccli: 22025}

{comment: Verse 1}
Am[G]azing Gr[G7]ace, how [C]sweet the so[G]und,
That s[G]aved a wr[G7]etch like [D]me.
```

### Supported Directives

| Directive | Description |
|-----------|-------------|
| `{title:}` | Song title |
| `{artist:}` | Author / artist |
| `{key:}` | Original key |
| `{ccli:}` | CCLI song number |
| `{comment:}` | Section label (Verse 1, Chorus, Bridge, etc.) |

Chords use inline notation: `[Am]word [G]next`

## Sources

- **Spanish**: [OpenSong](https://worshipleaderapp.com/) community database
- **English**: [mattgraham/worship](https://github.com/mattgraham/worship) (OnSong format, 130+ stars)
- **Portuguese**: [OpenSong](https://worshipleaderapp.com/) community database

## Contributing

To add a song:

1. Create a `.cho` file in ChordPro format
2. Name the file using lowercase with hyphens: `song-title.cho`
3. Place it in the correct language and category folder
4. Open a Pull Request

### Guidelines

- Include `{title:}`, `{artist:}`, and `{key:}` directives at minimum
- Use **American chord notation** (C, D, E, F, G, A, B)
- Use `{comment:}` to mark sections (Verse 1, Chorus, Bridge, etc.)
- Chords should be present in **all** sections, not just the first verse
- Hymns go in `hymns/himnos/hinos` folders, contemporary songs in `popular/`

## License

This repository structure and tooling is licensed under [MIT](LICENSE). Individual songs may have their own copyright — contributors are responsible for ensuring they have the rights to share.

## Disclaimer

This is a community project. If you believe any content infringes your copyright, please open an issue and we will remove it promptly.
