from pathlib import Path

from models import NoteEvent, Song


# 大调主音对应的 MIDI 编号，默认中音区。
# C4 = 60。
KEY_ROOT_MIDI = {
    "C": 60,
    "D": 62,
    "E": 64,
    "F": 65,
    "G": 67,
    "A": 69,
    "B": 71,
    "Bb": 70,
    "Eb": 63,
    "Ab": 68,
}

# 大调音阶内 1-7 相对主音的半音距离。
MAJOR_SCALE_OFFSETS = {
    "1": 0,
    "2": 2,
    "3": 4,
    "4": 5,
    "5": 7,
    "6": 9,
    "7": 11,
}


def parse_song_file(file_path: Path) -> Song:
    """
    解析 .jianpu 文件。

    文件示例：

        title=小星星
        key=C
        bpm=120
        base_octave=4

        1 1 5 5 6 6 5:2
        4 4 3 3 2 2 1:2

    规则：
        1       一拍 do
        1:2     两拍 do
        1:0.5   半拍 do
        1'      高八度 do
        1,      低八度 do
        #4      升 fa
        b7      降 si
        0 或 -  休止符
    """
    metadata = {
        "title": file_path.stem,
        "key": "C",
        "bpm": "120",
        "base_octave": "4",
    }

    note_tokens: list[str] = []

    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if "=" in line:
            name, value = line.split("=", 1)
            metadata[name.strip().lower()] = value.strip()
            continue

        # 允许用 | 分隔小节，解析时忽略。
        line = line.replace("|", " ")
        note_tokens.extend(line.split())

    key = metadata["key"]
    bpm = int(float(metadata["bpm"]))
    base_octave = int(float(metadata["base_octave"]))

    notes = [parse_note_token(token, key=key, base_octave=base_octave) for token in note_tokens]

    return Song(
        title=metadata["title"],
        key=key,
        bpm=bpm,
        base_octave=base_octave,
        notes=notes,
        file_path=file_path,
    )


def parse_note_token(token: str, key: str = "C", base_octave: int = 4) -> NoteEvent:
    beats = 1.0

    if ":" in token:
        token, beat_text = token.split(":", 1)
        beats = float(beat_text)

    if token in {"0", "-", "rest", "R"}:
        return NoteEvent(midi=None, beats=beats)

    accidental = 0
    if token.startswith("#"):
        accidental = 1
        token = token[1:]
    elif token.startswith("b"):
        accidental = -1
        token = token[1:]

    if not token:
        raise ValueError("发现空音符。")

    number = token[0]
    if number not in MAJOR_SCALE_OFFSETS:
        raise ValueError(f"无法识别音符：{token}")

    octave_shift = 0

    # 支持 1'、1'' 表示升高一或两个八度。
    # 支持 1,、1,, 表示降低一或两个八度。
    suffix = token[1:]
    for char in suffix:
        if char == "'":
            octave_shift += 1
        elif char == ",":
            octave_shift -= 1
        else:
            raise ValueError(f"无法识别音符后缀：{token}")

    root = KEY_ROOT_MIDI.get(key)
    if root is None:
        raise ValueError(f"暂不支持这个调：{key}")

    # KEY_ROOT_MIDI 默认按照 base_octave=4 设置。
    root += (base_octave - 4) * 12

    midi = root + MAJOR_SCALE_OFFSETS[number] + accidental + octave_shift * 12
    return NoteEvent(midi=midi, beats=beats)
