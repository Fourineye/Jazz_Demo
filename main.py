import pygame as pg

import Jazz
import Jazz.user_interface as jui
from scenes import MainMenu, Test

if __name__ == "__main__":
    app = Jazz.Application(720, 405, flags=Jazz.SCALED | Jazz.DOUBLEBUF)
    SCENES = [Test, MainMenu]
    for scene in SCENES:
        app.add_scene(scene)
    jui.set_default_font(pg.font.SysFont(pg.font.get_fonts()[5], 10))
    app.run()
