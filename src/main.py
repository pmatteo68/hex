"""Entry point for Hex."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# DPI awareness on Windows (must be called before Tkinter is imported)
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

import logging
import log_config
import sw_metadata as META

log_config.setup_logging()
_log = logging.getLogger(__name__)


def main() -> None:
    import config_ui  as CUI
    import ai_engine  as AE
    import config_game as CG

    _log.info("=" * 60)
    _log.info(
        "%s  v. %s  --  starting",
        META.getSWName(), META.getVersion(),
    )
    _log.info(
        "Python %s  |  platform: %s",
        sys.version.split()[0], sys.platform,
    )
    _log.info(
        "AI: %s  |  Skin: %s",
        AE.get_name(), CUI.get_name(),
    )
    _log.info(
        "Board default: %dx%d  range: %d-%d  (autoplay via start screen)",
        CG.BOARD_SIZE_DEFAULT, CG.BOARD_SIZE_DEFAULT,
        CG.BOARD_SIZE_MIN, CG.BOARD_SIZE_MAX,
    )
    _log.info("=" * 60)

    from ui_main import App
    app = App()
    app.mainloop()

    _log.info("=" * 60)
    _log.info("%s  --  exited normally", META.getSWName())
    _log.info("=" * 60)


if __name__ == "__main__":
    main()
