# 天依音律 Tianyi Yinlv

一个和洛天依相关的 Windows 键盘音律小工具。

按任意键触发曲谱中的下一个音。  
主题色：`#66CCFF`

## 功能

- 读取外置 `songs/` 文件夹里的 `.jianpu` 简谱文件
- 支持两种演奏模式：
  - 完整音模式：一个音完整播放期间，其他按键无效；一结束立刻响应
  - 即时演奏模式：每次新按键立刻播放下一个音
- 长按同一个键只识别第一次
- `F8` 暂停/继续
- `F9` 回到开头
- `Esc` 停止监听

## 项目结构

```text
TianyiYinlv/
├─ main.py
├─ keyboard_listener.py
├─ synth_player.py
├─ song_library.py
├─ jianpu_parser.py
├─ models.py
├─ requirements.txt
├─ .gitignore
└─ build_gui_exe.bat
```

本仓库不上传 `songs/` 文件夹。歌曲文件由用户自己放在程序旁边：

```text
TianyiYinlv.exe
songs/
  霜雪千年.jianpu
  三月雨.jianpu
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行源码

```bash
python main.py
```

## 打包 exe

```bash
python -m PyInstaller --onefile --windowed --name TianyiYinlv main.py
```

或者运行：

```bash
build_gui_exe.bat
```

打包后：

```text
dist/
├─ TianyiYinlv.exe
└─ songs/
```

把 `.jianpu` 文件放进 `dist/songs/`，然后运行 `TianyiYinlv.exe`。
