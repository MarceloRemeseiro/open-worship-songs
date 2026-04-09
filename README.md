# Open Worship Songs

A community-driven collection of worship songs with lyrics and chords in ChordPro format. Multi-language: English, Spanish, Portuguese, Catalan.

## About

This repository provides free, open-source song packs for worship teams. Songs are formatted in JSON with ChordPro-style inline chords, ready to be imported into any compatible worship management software.

## Song Packs

| Pack | Language | Songs | Status |
|------|----------|-------|--------|
| Himnos Clásicos | 🇪🇸 Spanish | 20 | ✅ |
| Classic Hymns | 🇬🇧 English | 20 | ✅ |
| Hinos Clássicos | 🇧🇷 Portuguese | 20 | ✅ |
| Himnes Clàssics | 🇪🇸 Catalan | — | 🔜 |

## Format

Each pack is a JSON file with this structure:

```json
{
  "packId": "en-classic-hymns",
  "version": "1.0.0",
  "songs": [
    {
      "title": "Amazing Grace",
      "author": "John Newton",
      "originalKey": "G",
      "ccliNumber": "",
      "sections": [
        {
          "type": "verse",
          "label": "Verse 1",
          "content": "[G]Amazing [G7]grace, how [C]sweet the [G]sound...",
          "position": 0
        }
      ]
    }
  ]
}
```

Chords use inline ChordPro notation: `[Am]word [G]next`.

## Contributing

Contributions are welcome! You can:

1. Add new songs (please ensure they are public domain or you have the rights)
2. Fix lyrics or chords in existing songs
3. Add translations to new languages

### Guidelines

- Songs must be **public domain** (published before 1928) or **Creative Commons** licensed
- Use **ChordPro inline format** for chords: `[G]lyrics [C]here`
- Use **American chord notation** (C, D, E, F, G, A, B — not Do, Re, Mi)
- Include correct section types: `verse`, `chorus`, `bridge`, `pre_chorus`, `intro`, `outro`, `interlude`, `tag`, `other`
- One JSON file per language pack

## License

The songs in this repository are in the **public domain** or released under **Creative Commons** licenses. This repository itself is licensed under [MIT](LICENSE).

## Disclaimer

This is a community project. Contributors are responsible for ensuring they have the rights to share any content they add. If you believe any content infringes your copyright, please open an issue and we will remove it promptly.
