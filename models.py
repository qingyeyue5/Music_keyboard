from dataclasses import dataclass
from pathlib import Path


@dataclass
class NoteEvent:
    """
    一个待播放的音符事件。

    midi:
        MIDI 音高编号。C4 = 60。
        None 表示休止符。

    beats:
        音符长度，单位是拍。
        例如 1 表示一拍，0.5 表示半拍，2 表示两拍。
    """
    midi: int | None
    beats: float = 1.0


@dataclass
class Song:
    title: str
    key: str
    bpm: int
    base_octave: int
    notes: list[NoteEvent]
    file_path: Path
