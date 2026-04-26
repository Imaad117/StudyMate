from __future__ import annotations
from pathlib import Path
import app_config as cfg
from ui.theme import THEME, load_and_apply_theme
from resource_path import resource_path

SETTINGS_FILE = cfg.APP_DATA_DIR / "settings.json"
# resource_path handles both normal runs and PyInstaller exe
_ICO = resource_path("studymate.ico")


def _set_icon(window):
    if _ICO.exists():
        try:
            window.iconbitmap(str(_ICO))
        except Exception:
            pass


def main():
    load_and_apply_theme(SETTINGS_FILE)

    from ui.splash_screen import SplashScreen
    splash = SplashScreen()
    _set_icon(splash)
    splash.mainloop()

    from ui.login_window import LoginWindow
    login = LoginWindow()
    _set_icon(login)
    login.mainloop()

    if login.get_chosen_profile() is None:
        return

    from ui.main_window import StudyMateApp
    app = StudyMateApp()
    _set_icon(app)
    app.mainloop()


if __name__ == "__main__":
    main()
