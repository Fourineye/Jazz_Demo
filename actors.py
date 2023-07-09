import json
import random

import pygame as pg

import Jazz.colliders as jcol
import Jazz.objects as jobj
import Jazz.user_interface as jui
from Jazz.baseObject import GameObject
from Jazz.components import AnimatedSprite, Button, Label, Sprite
from Jazz.utils import Vec2, clamp, direction_to, load_image
from weapon import ASSETS


class Upgrade(GameObject):
    WEAPON = 0
    HEALTH = 1
    AMMO = 2
    SPEED = 3
    NAMES = ["Weapon", "Health", "Ammo", "Speed"]

    def __init__(self, **kwargs):
        super().__init__(name="upgrade", **kwargs)
        self.timer = kwargs.get("timer", None)
        target_group = kwargs.get("target_group")
        self.add_child(
            jobj.Area(target_group=target_group, collision_layers="0010"),
            "upgrade_area",
        )
        self.upgrade_area.add_child(jcol.CircleCollider(7), "collider")
        self._bonus = kwargs.get("bonus", 1)
        self._type = kwargs.get("type", 1)
        sprite = AnimatedSprite(
            spritesheet="./Assets/topdown_shooter/other/powerup.png",
            sprite_dim=(16, 16),
            animation_fps=8,
        )
        sprite._frame = random.randint(0, 4)
        self.add_child(sprite, "sprite")
        label = Label(pos=(0, -15), text=self.NAMES[self._type], font=jui.DEFAULT_FONT)
        self.add_child(label)

    def update(self, delta):
        if self.timer is not None:
            self.timer -= delta
            if self.timer <= 1:
                self.sprite.visible = not self.sprite.visible
            if self.timer <= 0:
                self.queue_kill()

        for obj in self.upgrade_area.entered:
            obj.apply_upgrade(self._bonus, self._type)
            print(obj.weapon)
            self.queue_kill()


class WeaponPickup(GameObject):
    SNIPER = 0
    ASSAULT = 1
    SHOTGUN = 2
    SMG = 3
    NAMES = ["Sniper", "Assault", "Shotgun", "SMG"]

    def __init__(self, **kwargs):
        super().__init__(name="upgrade", **kwargs)
        self.timer = kwargs.get("timer", None)
        target_group = kwargs.get("target_group")
        self.add_child(
            jobj.Area(target_group=target_group, collision_layers="0010"),
            "upgrade_area",
        )
        self.upgrade_area.add_child(jcol.CircleCollider(7), "collider")
        self._level = kwargs.get("level", 0)
        self._type = kwargs.get("type", 0)
        sprite = Sprite(
            asset=ASSETS.get(self.NAMES[self._type], None),
        )
        self.add_child(sprite, "sprite")
        label = Label(
            pos=(0, -15),
            text=self.NAMES[self._type] + " " + str(self._level),
            font=jui.DEFAULT_FONT,
        )
        self.add_child(label)

    def update(self, delta):
        if self.timer is not None:
            self.timer -= delta
            if self.timer <= 1:
                self.sprite.visible = not self.sprite.visible
            if self.timer <= 0:
                self.queue_kill()

        for obj in self.upgrade_area.entered:
            obj.weapon.set_type(self.NAMES[self._type], self._level)
            print(obj.weapon)
            self.queue_kill()


class Map(Sprite):
    def __init__(self, name="map", **kwargs):
        super().__init__(
            name, asset="./Assets/Maps/map.png", background_layer=True, **kwargs
        )
        with open("./Assets/Maps/map.tmj") as map_json:
            map_data = json.load(map_json)
        self.map_size = (map_data["width"], map_data["height"])
        self.tile_size = (map_data["tilewidth"], map_data["tileheight"])

        self.spawn_zones = []
        self.spawn_area = 0

        self.positions = {}

        for layer in map_data["layers"]:
            if layer.get("name", None) == "Walls":
                for wall in layer["objects"]:
                    wall_object = jobj.Body(
                        pos=(
                            wall["x"] + wall["width"] / 2,
                            wall["y"] + wall["height"] / 2,
                        ),
                        layers="0101",
                        static=True,
                    )
                    wall_object.add_child(
                        jcol.RectCollider(wall["width"], wall["height"]), "collider"
                    )
                    self.add_child(wall_object)
            if layer["name"] == "SpawnZones":
                for area in layer["objects"]:
                    area["area"] = area["width"] * area["height"]
                    self.spawn_zones.append(area)
                    self.spawn_area += area["area"]
            if layer["name"] == "Positions":
                for position in layer["objects"]:
                    self.positions.setdefault(
                        position["name"], Vec2(position["x"], position["y"])
                    )

    def _draw(self, surface, offset=None):
        if offset is None:
            offset = Vec2()
        draw_pos = self.sub_image(offset)
        surface.blit(self.image, draw_pos)

    def sub_image(self, offset):
        x = clamp(-offset[0], 0, self.source.get_width() - self.scene.width)
        y = clamp(-offset[1], 0, self.source.get_height() - self.scene.height)
        self.image = self.source.subsurface(
            (x, y), (self.scene.width, self.scene.height)
        )
        return Vec2(x, y) + offset

    def get_spawn_point(self):
        choice = random.uniform(0, self.spawn_area)
        for zone in self.spawn_zones:
            choice -= zone["area"]
            if choice <= 0:
                return (
                    random.uniform(zone["x"], zone["x"] + zone["width"]),
                    random.uniform(zone["y"], zone["y"] + zone["height"]),
                )
        return None


class UI(GameObject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.showing_wave_card = False
        self.card_timer = 0
        self.enemy_flags = []
        self.add_child(Label(text="Wave", pos=(0, -16), visible=False), "wave")
        self.add_child(Label(text="Completed", pos=(0, 8), visible=False), "completed")

        self.showing_timer = False
        self.add_child(Label(text="", pos=(0, 32), visible=False), "timer")

    def show_card(self, time=3):
        self.showing_wave_card = True
        self.card_timer = time
        self.wave.visible = True
        self.completed.visible = True

    def hide_card(self):
        self.showing_wave_card = False
        self.card_timer = 0
        self.wave.visible = False
        self.completed.visible = False

    def show_timer(self):
        self.timer.visible = True

    def hide_timer(self):
        self.timer.visible = False

    def update_timer(self, time):
        self.timer.set_text(str(round(time, 2)))

    def _draw(self, surface, offset=None):
        if offset is None:
            offset = Vec2()
        for enemy in self.enemy_flags:
            pg.draw.circle(surface, "red", self.pos + enemy * 25 + offset, 3)

    def update(self, delta: float):
        self.enemy_flags = []
        if self.showing_wave_card:
            self.card_timer -= delta
            if self.card_timer <= 0:
                self.hide_card()
        if len(self.scene["enemies"]) < 5:
            for enemy in self.scene["enemies"]:
                self.enemy_flags.append(direction_to(self.scene.camera.pos, enemy.pos))


class PauseMenu(GameObject):
    def __init__(self, name="pause menu", **kwargs):
        super().__init__(name, **kwargs)
        self.screen_layer = True
        self.pause_process = True
        self.add_child(Sprite(asset="./Assets/UI/pause_menu.png"))
        self.add_child(
            Button(
                pos=(0, -38),
                size=(96, 28),
                unpressed="./Assets/UI/continue_button_0.png",
                hover="./Assets/UI/continue_button_1.png",
                pressed="./Assets/UI/continue_button_2.png",
                pause_process=True,
                on_release=True,
            ),
            "continue_button",
        )
        self.add_child(
            Button(
                pos=(0, 0),
                size=(80, 28),
                unpressed="./Assets/UI/restart_button_0.png",
                hover="./Assets/UI/restart_button_1.png",
                pressed="./Assets/UI/restart_button_2.png",
                pause_process=True,
                on_release=True,
            ),
            "restart_button",
        )
        self.add_child(
            Button(
                pos=(0, 38),
                size=(64, 28),
                unpressed="./Assets/UI/quit_button_0.png",
                hover="./Assets/UI/quit_button_1.png",
                pressed="./Assets/UI/quit_button_2.png",
                pause_process=True,
                on_release=True,
            ),
            "quit_button",
        )


# class Explosion(jobj.GameObject):
#     def __init__(self, pos, **kwargs):
#         super().__init__(pos, "Explosion", **kwargs)
#         self._frames = [load_image(f"Assets/Type 1/{i}.png") for i in range(1, 8)]
#         self._frame = 1
#         self.source = self._frames[self._frame]

#     def process(self, delta):
#         self._frame = (self._frame + 1) % (len(self._frames) * 5)
#         self.source = self._frames[self._frame // 5]
#         if self._frame == len(self._frames) * 5 - 1:
#             self.kill()

#     def draw(self, surface, offset=None):
#         if offset is None:
#             offset = Vec2()
#         surface.blit(
#             self.source,
#             self.pos
#             - Vec2(self.source.get_width() / 2, self.source.get_height() / 2)
#             + offset,
#         )
