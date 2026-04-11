import os
import shutil
import subprocess
import sys

CLICK_SOUND_FILE = os.path.join(os.path.dirname(__file__), "assets", "sounds", "button-click.mp3")
ERROR_SOUND_FILE = os.path.join(os.path.dirname(__file__), "assets", "sounds", "error.mp3")
RESULT_SOUND_FILE = os.path.join(os.path.dirname(__file__), "assets", "sounds", "zelda-chest.mp3")
PLAYER = shutil.which("ffplay")


def _play_sound(path):
    if not PLAYER or not os.path.exists(path):
        return
    try:
        subprocess.Popen(
            [PLAYER, "-nodisp", "-autoexit", "-loglevel", "quiet", path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


def play_click_sound():
    _play_sound(CLICK_SOUND_FILE)


def play_error_sound():
    _play_sound(ERROR_SOUND_FILE)


def play_result_sound():
    _play_sound(RESULT_SOUND_FILE)


def disable_sound(widget):
    try:
        widget.unbind("<ButtonPress-1>")
    except Exception:
        pass


def install_tk_button_sound():
    try:
        import tkinter as tk
    except Exception:
        return

    def patch_widget(widget_cls):
        orig_init = widget_cls.__init__

        def new_init(self, master=None, cnf=None, **kw):
            disabled = kw.pop("sound_disabled", False)
            orig_init(self, master, cnf, **kw)
            if disabled:
                return
            try:
                self.bind("<ButtonPress-1>", lambda event: play_click_sound(), add="+")
            except Exception:
                pass

        widget_cls.__init__ = new_init

    for cls_name in ["Button", "Menubutton", "Checkbutton", "Radiobutton"]:
        widget_cls = getattr(tk, cls_name, None)
        if widget_cls is not None:
            patch_widget(widget_cls)


# Install sound hooks when this module is imported.
install_tk_button_sound()
