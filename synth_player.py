import math
import threading
import time

import numpy as np
import pygame

from models import NoteEvent, Song


SAMPLE_RATE = 44100


class BaseSongPlayer:
    """
    两种播放器的共同基础类。

    子类：
    - LockedStepPlayer：完整音模式
    - InstantStepPlayer：即时演奏模式

    本版新增：
    - 按键触发时自动跳过休止符、0 时值音符、异常空音符。
    - 这样不会出现“按了一次键但没有声音”的情况。
    """

    def __init__(self):
        init_mixer_once()

        self.song: Song | None = None
        self.index = 0
        self.paused = False
        self.lock = threading.Lock()
        self.cache: dict[tuple[int | None, float, int], pygame.mixer.Sound] = {}

    def load_song(self, song: Song):
        with self.lock:
            self.song = song
            self.index = 0
            self.paused = False
            self.cache.clear()
            self._after_load_song()

    def _after_load_song(self):
        pass

    def play_next(self):
        raise NotImplementedError

    def reset(self):
        with self.lock:
            self.index = 0
            self._after_reset()

        pygame.mixer.stop()
        print("已回到歌曲开头。")

    def _after_reset(self):
        pass

    def toggle_pause(self):
        with self.lock:
            self.paused = not self.paused
            paused = self.paused
            self._after_toggle_pause(paused)

        if paused:
            pygame.mixer.stop()
            print("已暂停。")
        else:
            print("已继续。")

    def _after_toggle_pause(self, paused: bool):
        pass

    def stop_all(self):
        pygame.mixer.stop()

    def _take_next_event(self):
        """
        从曲谱里取出下一个“有声音”的音符，同时把指针往后移。

        关键修复：
        - event.midi is None 表示休止符，跳过。
        - event.beats <= 0 表示 0 时值或异常时值，跳过。
        - 最多扫描整首歌一圈，避免全是休止符时死循环。
        """
        if self.song is None or not self.song.notes:
            return None, None

        total = len(self.song.notes)

        for _ in range(total):
            event = self.song.notes[self.index]
            bpm = self.song.bpm
            self.index = (self.index + 1) % total

            if self._is_audible_event(event):
                return event, bpm

        # 整首歌都没有可播放音符
        return None, None

    @staticmethod
    def _is_audible_event(event: NoteEvent) -> bool:
        if event is None:
            return False

        if event.midi is None:
            return False

        if event.beats is None:
            return False

        if event.beats <= 0:
            return False

        return True

    def _get_sound(self, event: NoteEvent, bpm: int):
        cache_key = (event.midi, event.beats, bpm)

        if cache_key not in self.cache:
            self.cache[cache_key] = self._make_sound(event, bpm)

        return self.cache[cache_key]

    def _make_sound(self, event: NoteEvent, bpm: int):
        beat_seconds = 60.0 / bpm

        # 根据乐谱时值生成声音长度。
        # 完整音模式会用这个长度做锁定。
        # 即时演奏模式不会等待这个长度，但声音本身仍自然播放完。
        duration = max(0.04, event.beats * beat_seconds * 0.85)

        freq = midi_to_freq(event.midi)

        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)

        wave = np.sin(2 * math.pi * freq * t)
        wave += 0.22 * np.sin(2 * math.pi * freq * 2 * t)
        wave += 0.08 * np.sin(2 * math.pi * freq * 3 * t)

        envelope = np.ones_like(wave)
        attack = min(int(0.012 * SAMPLE_RATE), len(envelope))
        release = min(int(0.065 * SAMPLE_RATE), len(envelope))

        if attack > 0:
            envelope[:attack] = np.linspace(0, 1, attack)

        if release > 0:
            envelope[-release:] = np.linspace(1, 0, release)

        audio = wave * envelope * 0.32
        audio = np.int16(audio * 32767)

        audio = match_mixer_channels(audio)
        return pygame.sndarray.make_sound(audio)


class LockedStepPlayer(BaseSongPlayer):
    """
    版本一：完整音模式。

    规则：
    - 按一次键，播放曲谱里的下一个有声音的音。
    - 当前音完整播放期间，其他按键全部无效。
    - 当前音一结束，下一次按键立刻有效。
    """

    def __init__(self):
        super().__init__()
        self.busy_until = 0.0

    def _after_load_song(self):
        self.busy_until = 0.0

    def _after_reset(self):
        self.busy_until = 0.0

    def _after_toggle_pause(self, paused: bool):
        if paused:
            self.busy_until = 0.0

    def stop_all(self):
        with self.lock:
            self.busy_until = 0.0
        super().stop_all()

    def play_next(self):
        now = time.monotonic()

        with self.lock:
            if self.paused:
                return

            # 当前音还没播完，忽略本次按键。
            if now < self.busy_until:
                return

            event, bpm = self._take_next_event()
            if event is None:
                return

            sound = self._get_sound(event, bpm)

            # 用真实 sound 长度判断什么时候允许下一次触发。
            self.busy_until = now + sound.get_length()

        play_sound_on_free_channel(sound, force=False)


class InstantStepPlayer(BaseSongPlayer):
    """
    版本二：即时演奏模式。

    规则：
    - 每次新按键，立刻播放曲谱里的下一个有声音的音。
    - 不等待上一个音结束。
    - 多个音可以自然重叠，手感更像弹钢琴。
    - 如果通道已满，会强制找一个通道播放，保证本次按键立刻出声。
    - 长按同一个键导致的系统自动连发由 keyboard_listener.py 过滤。
    """

    def play_next(self):
        with self.lock:
            if self.paused:
                return

            event, bpm = self._take_next_event()
            if event is None:
                return

            sound = self._get_sound(event, bpm)

        play_sound_on_free_channel(sound, force=True)


def init_mixer_once():
    """
    初始化 pygame mixer。

    有些 Windows 声卡会把单声道自动改成双声道。
    所以后面 make_sound 前会通过 match_mixer_channels 自动匹配声道数。
    """
    if pygame.mixer.get_init() is not None:
        return

    pygame.mixer.pre_init(
        frequency=SAMPLE_RATE,
        size=-16,
        channels=1,
        buffer=512,
        allowedchanges=0,
    )

    pygame.mixer.init(
        frequency=SAMPLE_RATE,
        size=-16,
        channels=1,
        buffer=512,
        allowedchanges=0,
    )

    # 默认通道数较少，快速连续按键时可能占满。
    # 增加通道后，即时演奏模式可以更稳定地重叠播放。
    pygame.mixer.set_num_channels(64)

    print("当前 pygame mixer 音频格式：", pygame.mixer.get_init())
    print("当前 pygame mixer 通道数量：", pygame.mixer.get_num_channels())


def play_sound_on_free_channel(sound: pygame.mixer.Sound, force: bool = False):
    """
    在空闲通道上播放声音。

    force=False:
        没有空闲通道时，pygame 可能不播放新声音。
        适合完整音模式。

    force=True:
        没有空闲通道时，也强制找一个通道播放。
        适合即时演奏模式，保证新按键立刻出声。
    """
    channel = pygame.mixer.find_channel(force=force)

    if channel is not None:
        channel.play(sound)
    else:
        sound.play()


def match_mixer_channels(audio: np.ndarray) -> np.ndarray:
    mixer_info = pygame.mixer.get_init()

    if mixer_info is None:
        raise RuntimeError("pygame mixer 未初始化。")

    _, _, channels = mixer_info

    if channels == 1:
        if audio.ndim == 2:
            audio = audio[:, 0]
        return np.ascontiguousarray(audio, dtype=np.int16)

    if channels == 2:
        if audio.ndim == 1:
            audio = np.column_stack((audio, audio))
        return np.ascontiguousarray(audio, dtype=np.int16)

    raise RuntimeError(f"暂不支持的声道数：{channels}")


def midi_to_freq(midi: int) -> float:
    return 440.0 * (2 ** ((midi - 69) / 12))
