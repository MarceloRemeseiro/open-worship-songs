export interface SongSection {
  type: "verse" | "chorus" | "bridge" | "pre_chorus" | "intro" | "outro" | "interlude" | "tag" | "other";
  label: string;
  content: string;
  position: number;
  isInstrumental: boolean;
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
}

export interface SongFull extends SongMeta {
  sections: SongSection[];
}
