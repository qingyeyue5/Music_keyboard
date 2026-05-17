from pathlib import Path
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from keyboard_listener import KeyboardTrigger
from song_library import SongLibrary
from synth_player import LockedStepPlayer, InstantStepPlayer


APP_NAME = "天依音律"
THEME = "#66CCFF"
THEME_DARK = "#269ED8"
BG = "#F2FBFF"
CARD = "#FFFFFF"
TEXT = "#1F2D3D"


def get_app_dir() -> Path:
    """
    开发时读取：
        项目根目录/songs/

    打包成 exe 后读取：
        exe 同级目录/songs/

    songs 文件夹不需要打包进 exe。
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def get_songs_dir() -> Path:
    return get_app_dir() / "songs"


class TianyiYinlvApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("760x560")
        self.root.minsize(720, 520)
        self.root.configure(bg=BG)

        self.songs_dir = get_songs_dir()
        self.library = SongLibrary(self.songs_dir)
        self.songs = []
        self.song_display_values = []

        self.player = None
        self.listener = None
        self.is_listening = False

        self.selected_song_var = tk.StringVar()
        self.mode_var = tk.StringVar(value="locked")
        self.status_var = tk.StringVar(value="请选择歌曲和模式，然后点击开始。")
        self.path_var = tk.StringVar(value=f"歌曲目录：{self.songs_dir}")

        self._setup_style()
        self._build_ui()
        self._disable_ui_keyboard_control()
        self.refresh_songs()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_style(self):
        self.style = ttk.Style()

        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure("TFrame", background=BG)
        self.style.configure("Card.TFrame", background=CARD)
        self.style.configure(
            "TLabel",
            background=BG,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 10),
        )
        self.style.configure(
            "Card.TLabel",
            background=CARD,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 10),
        )
        self.style.configure(
            "Primary.TButton",
            background=THEME,
            foreground="white",
            font=("Microsoft YaHei UI", 10, "bold"),
            padding=(14, 8),
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", THEME_DARK), ("pressed", THEME_DARK)],
            foreground=[("active", "white"), ("pressed", "white")],
        )
        self.style.configure(
            "Soft.TButton",
            background="#E7F8FF",
            foreground=TEXT,
            font=("Microsoft YaHei UI", 10),
            padding=(12, 7),
        )
        self.style.map(
            "Soft.TButton",
            background=[("active", "#D3F2FF"), ("pressed", "#BCEBFF")],
        )
        self.style.configure(
            "TCombobox",
            padding=7,
            font=("Microsoft YaHei UI", 10),
        )
        self.style.configure(
            "TRadiobutton",
            background=CARD,
            foreground=TEXT,
            font=("Microsoft YaHei UI", 10),
        )

    def _build_ui(self):
        header = tk.Frame(self.root, bg=THEME, height=120)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text=APP_NAME,
            bg=THEME,
            fg="white",
            font=("Microsoft YaHei UI", 28, "bold"),
        )
        title.pack(anchor="w", padx=34, pady=(24, 0))

        subtitle = tk.Label(
            header,
            text="Luo Tianyi Keyboard Melody Player · 任意键触发旋律",
            bg=THEME,
            fg="white",
            font=("Microsoft YaHei UI", 10),
        )
        subtitle.pack(anchor="w", padx=36, pady=(4, 0))

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=28, pady=24)

        song_card = self._card(main)
        song_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            song_card,
            text="歌曲选择",
            bg=CARD,
            fg=TEXT,
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 8))

        song_row = tk.Frame(song_card, bg=CARD)
        song_row.pack(fill="x", padx=18, pady=(0, 16))

        self.song_combo = ttk.Combobox(
            song_row,
            textvariable=self.selected_song_var,
            state="readonly",
            width=52,
            takefocus=False,
        )
        self.song_combo.pack(side="left", fill="x", expand=True)
        self.song_combo.bind("<<ComboboxSelected>>", self.on_song_selected, add="+")

        self.refresh_button = ttk.Button(
            song_row,
            text="刷新歌曲",
            style="Soft.TButton",
            command=self.refresh_songs,
            takefocus=False,
        )
        self.refresh_button.pack(side="left", padx=(12, 0))

        mode_card = self._card(main)
        mode_card.pack(fill="x", pady=(0, 14))

        tk.Label(
            mode_card,
            text="播放模式",
            bg=CARD,
            fg=TEXT,
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 8))

        mode_row = tk.Frame(mode_card, bg=CARD)
        mode_row.pack(fill="x", padx=18, pady=(0, 16))

        self.locked_radio = ttk.Radiobutton(
            mode_row,
            text="完整音模式：音没播完时忽略其他按键",
            variable=self.mode_var,
            value="locked",
            takefocus=False,
        )
        self.locked_radio.pack(anchor="w", pady=4)

        self.instant_radio = ttk.Radiobutton(
            mode_row,
            text="即时演奏模式：每次新按键立刻触发下一个音",
            variable=self.mode_var,
            value="instant",
            takefocus=False,
        )
        self.instant_radio.pack(anchor="w", pady=4)

        control_card = self._card(main)
        control_card.pack(fill="x", pady=(0, 14))

        button_row = tk.Frame(control_card, bg=CARD)
        button_row.pack(fill="x", padx=18, pady=18)

        self.start_button = ttk.Button(
            button_row,
            text="开始演奏",
            style="Primary.TButton",
            command=self.start,
            takefocus=False,
        )
        self.start_button.pack(side="left", padx=(0, 10))

        self.pause_button = ttk.Button(
            button_row,
            text="暂停 / 继续",
            style="Soft.TButton",
            command=self.toggle_pause,
            takefocus=False,
        )
        self.pause_button.pack(side="left", padx=(0, 10))

        self.reset_button = ttk.Button(
            button_row,
            text="回到开头",
            style="Soft.TButton",
            command=self.reset,
            takefocus=False,
        )
        self.reset_button.pack(side="left", padx=(0, 10))

        self.stop_button = ttk.Button(
            button_row,
            text="停止监听",
            style="Soft.TButton",
            command=self.stop,
            takefocus=False,
        )
        self.stop_button.pack(side="left")

        status_card = self._card(main)
        status_card.pack(fill="both", expand=True)

        tk.Label(
            status_card,
            text="状态",
            bg=CARD,
            fg=TEXT,
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(anchor="w", padx=18, pady=(16, 8))

        self.status_label = tk.Label(
            status_card,
            textvariable=self.status_var,
            bg=CARD,
            fg=TEXT,
            justify="left",
            anchor="w",
            font=("Microsoft YaHei UI", 10),
        )
        self.status_label.pack(fill="x", padx=18, pady=(0, 8))

        self.path_label = tk.Label(
            status_card,
            textvariable=self.path_var,
            bg=CARD,
            fg="#5D6D7E",
            justify="left",
            anchor="w",
            font=("Microsoft YaHei UI", 9),
        )
        self.path_label.pack(fill="x", padx=18, pady=(0, 16))

        tips = (
            "界面只允许鼠标操作：键盘不会切换歌曲、模式或按钮。\n"
            "开始监听后：按任意键播放下一音；F8 暂停/继续；F9 回到开头；Esc 停止监听。\n"
            "两个模式都已处理长按：一直按住同一个键，只会识别第一次。"
        )

        tk.Label(
            status_card,
            text=tips,
            bg=CARD,
            fg="#5D6D7E",
            justify="left",
            anchor="w",
            font=("Microsoft YaHei UI", 9),
        ).pack(fill="x", padx=18, pady=(0, 16))

    def _card(self, parent):
        return tk.Frame(
            parent,
            bg=CARD,
            highlightthickness=1,
            highlightbackground="#D9F3FF",
            highlightcolor="#D9F3FF",
        )

    def _disable_ui_keyboard_control(self):
        """
        禁止键盘操控 Tkinter 界面。

        修复说明：
        上一版为了清除焦点，绑定了全局鼠标点击后 root.focus_set。
        这个动作会干扰 Combobox 的鼠标选择，导致选完歌曲后又回到第一首。
        本版已经移除那个全局鼠标焦点绑定，只保留键盘事件拦截。
        """

        def block_key_event(event):
            return "break"

        keyboard_sequences = (
            "<KeyPress>",
            "<KeyRelease>",
            "<Return>",
            "<KP_Enter>",
            "<space>",
            "<Tab>",
            "<ISO_Left_Tab>",
            "<Up>",
            "<Down>",
            "<Left>",
            "<Right>",
            "<Prior>",
            "<Next>",
            "<Home>",
            "<End>",
        )

        def apply_to_widget(widget):
            try:
                widget.configure(takefocus=False)
            except tk.TclError:
                pass

            try:
                tags = widget.bindtags()
                custom_tag = "NoKeyboardControl"

                if custom_tag not in tags:
                    widget.bindtags((custom_tag,) + tags)
            except tk.TclError:
                pass

            for child in widget.winfo_children():
                apply_to_widget(child)

        for seq in keyboard_sequences:
            self.root.bind_class("NoKeyboardControl", seq, block_key_event, add=False)

        apply_to_widget(self.root)

    def refresh_songs(self):
        previous_value = self.selected_song_var.get()

        self.library = SongLibrary(self.songs_dir)
        self.library.load_all()
        self.songs = self.library.list_songs()

        self.song_display_values = [f"{song.title}  ({song.file_path.name})" for song in self.songs]
        self.song_combo["values"] = self.song_display_values

        if self.song_display_values:
            if previous_value in self.song_display_values:
                new_index = self.song_display_values.index(previous_value)
            else:
                new_index = 0

            self.song_combo.current(new_index)
            self.selected_song_var.set(self.song_display_values[new_index])
            self.status_var.set(f"已找到 {len(self.song_display_values)} 首歌曲。当前选择：{self.songs[new_index].title}")
        else:
            self.selected_song_var.set("")
            self.song_combo.set("")
            self.status_var.set("没有找到 .jianpu 歌曲文件。请把歌曲放进 songs 文件夹。")

        self.path_var.set(f"歌曲目录：{self.songs_dir}")

    def on_song_selected(self, event=None):
        song = self.get_selected_song()
        if song is not None:
            self.status_var.set(f"已选择歌曲：{song.title}")

    def get_selected_song(self):
        """
        修复版：
        优先用 combobox.current() 获取当前索引，避免文本匹配失效。
        """
        if not self.songs:
            return None

        index = self.song_combo.current()

        if 0 <= index < len(self.songs):
            return self.songs[index]

        selected = self.selected_song_var.get()
        for i, value in enumerate(self.song_display_values):
            if selected == value and i < len(self.songs):
                return self.songs[i]

        return None

    def create_player(self):
        mode = self.mode_var.get()

        if mode == "locked":
            return LockedStepPlayer()

        return InstantStepPlayer()

    def start(self):
        song = self.get_selected_song()

        if song is None:
            messagebox.showwarning(APP_NAME, "没有选择歌曲。请先把 .jianpu 文件放进 songs 文件夹，并点击刷新歌曲。")
            return

        self.stop(silent=True)

        self.player = self.create_player()
        self.player.load_song(song)

        self.listener = KeyboardTrigger(
            on_trigger=self.player.play_next,
            on_toggle_pause=self._listener_toggle_pause,
            on_reset=self._listener_reset,
            on_exit=self._listener_exit,
        )
        self.listener.start()
        self.is_listening = True

        mode_text = "完整音模式" if self.mode_var.get() == "locked" else "即时演奏模式"
        self.status_var.set(f"正在监听键盘：{song.title}｜{mode_text}")

    def stop(self, silent=False):
        if self.listener is not None:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None

        if self.player is not None:
            try:
                self.player.stop_all()
            except Exception:
                pass

        self.is_listening = False

        if not silent:
            self.status_var.set("已停止监听。")

    def toggle_pause(self):
        if self.player is None:
            self.status_var.set("还没有开始演奏。")
            return

        self.player.toggle_pause()
        if getattr(self.player, "paused", False):
            self.status_var.set("已暂停。")
        else:
            self.status_var.set("已继续监听键盘。")

    def reset(self):
        if self.player is None:
            self.status_var.set("还没有开始演奏。")
            return

        self.player.reset()
        self.status_var.set("已回到歌曲开头。")

    def _listener_toggle_pause(self):
        self.root.after(0, self.toggle_pause)

    def _listener_reset(self):
        self.root.after(0, self.reset)

    def _listener_exit(self):
        if self.player is not None:
            self.player.stop_all()
        self.root.after(0, self._mark_stopped_by_esc)

    def _mark_stopped_by_esc(self):
        self.is_listening = False
        self.listener = None
        self.status_var.set("已按 Esc 停止监听。")

    def on_close(self):
        self.stop(silent=True)
        self.root.destroy()


def main():
    root = tk.Tk()
    TianyiYinlvApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
