from pathlib import Path

from jianpu_parser import parse_song_file
from models import Song


class SongLibrary:
    def __init__(self, songs_dir: Path):
        self.songs_dir = songs_dir
        self.songs: list[Song] = []

    def load_all(self):
        self.songs.clear()
        self.songs_dir.mkdir(parents=True, exist_ok=True)

        for file_path in sorted(self.songs_dir.glob("*.jianpu")):
            try:
                song = parse_song_file(file_path)
                self.songs.append(song)
            except Exception as exc:
                print(f"跳过无法解析的歌曲：{file_path.name}")
                print(f"原因：{exc}")

    def list_songs(self) -> list[Song]:
        return self.songs
