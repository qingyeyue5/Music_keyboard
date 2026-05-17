from pynput import keyboard


class KeyboardTrigger:
    """
    全局键盘触发器。

    特点：
    1. 不保存具体按键内容。
    2. 不输出具体按键内容。
    3. 不上传任何数据。
    4. 长按同一个键时，只识别第一次。
    5. 既支持控制台阻塞运行，也支持 GUI 后台运行。
    """

    def __init__(self, on_trigger, on_toggle_pause, on_reset, on_exit):
        self.on_trigger = on_trigger
        self.on_toggle_pause = on_toggle_pause
        self.on_reset = on_reset
        self.on_exit = on_exit

        self.pressed_keys = set()
        self.listener = None
        self.running = False

    def run(self):
        """
        控制台版本使用：阻塞运行。
        """
        self.running = True
        with keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        ) as listener:
            self.listener = listener
            listener.join()

    def start(self):
        """
        GUI 版本使用：后台运行。
        """
        if self.running:
            return

        self.pressed_keys.clear()
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self.listener.start()
        self.running = True

    def stop(self):
        """
        停止监听。
        """
        self.running = False
        self.pressed_keys.clear()

        if self.listener is not None:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None

    def _on_press(self, key):
        if key in self.pressed_keys:
            return

        self.pressed_keys.add(key)

        if key == keyboard.Key.esc:
            self.on_exit()
            self.running = False
            return False

        if key == keyboard.Key.f8:
            self.on_toggle_pause()
            return

        if key == keyboard.Key.f9:
            self.on_reset()
            return

        try:
            self.on_trigger()
        except Exception as exc:
            print("播放时出错：", exc)

    def _on_release(self, key):
        self.pressed_keys.discard(key)
