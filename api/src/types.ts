export interface SongSection {
  type: "verse" | "chorus" | "bridge" | "pre_chorus" | "intro" | "outro" | "interlude" | "tag" | "other";
  label: string;
  content: string;
  position: number;
  isInstrumental: boolean;
}

export interface MetaEntry {
  name: string;
  value: string;
}

export interface SongMeta {
  id: string;
  title: string;
  artist: string | null;
  key: string;
  tempo: number | null;
  lang: string;
  category: string;
  filename: string;
  /** Optional extras parsed from the .cho directives. */
  capo?: number | null;
  ccli?: string | null;
  time?: string | null;
  meta?: MetaEntry[];
}

export interface SongFull extends SongMeta {
  sections: SongSection[];
}
