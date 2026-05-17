# Keyboard Song Player

一个 Windows 键盘演奏器：按任意键触发曲谱中的下一个音。

## 重要说明

本仓库只保存程序代码，不保存歌曲文件。

歌曲文件请自行放在程序同级目录的 `songs/` 文件夹中：

```text
MusicKeyboard.exe
songs/
  小星星.jianpu
  霜雪千年.jianpu
```

开发运行时：

```text
main.py
songs/
  小星星.jianpu
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
build_exe.bat
```

或者手动执行：

```bash
python -m PyInstaller --onefile --name MusicKeyboard main.py
mkdir dist\songs
```

打包后结构：

```text
dist/
  MusicKeyboard.exe
  songs/
```

把 `.jianpu` 放进 `dist/songs/` 后运行 exe。

## 播放模式

启动后可以选择：

```text
1. 完整音模式：一个音完整播放期间，其他按键无效；一结束立刻响应
2. 即时演奏模式：每按一次键立刻播放下一个音，像弹钢琴一样，可连续触发
```

两个模式都已处理长按：一直按住同一个键，只会识别第一次。
