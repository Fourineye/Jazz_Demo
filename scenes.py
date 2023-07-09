import random

import pygame

import Jazz
import Jazz.colliders as jcol
import Jazz.objects as jobj
import Jazz.user_interface as jui
from actors import UI, Map, PauseMenu, Upgrade, WeaponPickup
from enemies import Chaser, Target, Tower
from Jazz.components import Label, ProgressBar, Sprite
from Jazz.global_dict import Game_Globals
from Jazz.utils import dist_to
from player import Player


class MainMenu(Jazz.Scene):
    name = "Main Menu"

    def on_load(self, data):
        self.add_ui("Title", jui.TextBox(360, 240, 200, 100, "Main Menu"))
        self.camera.set_bg_color((64, 64, 64))


class Test(Jazz.Scene):
    name = "Test Scene"

    def on_load(self, data):
        self.upgrade_phase = True
        self.game_over = False
        self.game_over_timer = 5
        self.wave = 0
        self.wave_count = 10
        self.difficulty = 1
        self.wave_timer = 0
        self.enemy_timer = 0

        pygame.mouse.set_visible(False)

        self.make_sprite_sheet("./Assets/Bullet.png", (7, 7))
        self.make_sprite_sheet("./Assets/enemy_bullet.png", (8, 8))

        self.add_group("enemies")
        self.add_group("_player")
        self.add_group("level_upgrade")
        self.add_group("level_weapons")

        self.add_object(Map(visible=True, z=-1), "map")
        spawn_checker = jobj.Body(pos=(0, 0), layers="0000", collision_layers="1111")
        spawn_checker.add_child(jcol.CircleCollider(32), "collider")
        self.add_object(
            spawn_checker,
            "spawn_checker",
        )
        self.add_object(
            Player(
                pos=self.map.positions["player_spawn"],
                color=(255, 0, 0),
                groups=[self["_player"]],
                target_group=self["enemies"],
            ),
            "player",
        )

        # UI
        self.add_object(
            ProgressBar(
                self.player._hp,
                self.player._max_hp,
                size=(150, 8),
                pos=(11, self.height - 80),
                rotation=-90,
                color="red",
                background_color="red",
                line_width=1,
                screen_layer=True,
            ),
            "hp_bar",
        )
        self.add_object(
            Sprite(
                pos=(11, self.height - 8),
                scale=(2, 2),
                asset="Assets/UI/heart.png",
                screen_layer=True,
            )
        )

        self.add_object(
            ProgressBar(
                self.player.weapon._ammo,
                self.player.weapon._max_ammo,
                size=(150, 8),
                pos=(28, self.height - 80),
                rotation=-90,
                color="yellow",
                background_color="orange",
                line_width=1,
                screen_layer=True,
            ),
            "ammo_bar",
        )

        self.add_object(
            Label(
                text=str(self.wave),
                pos=(self.width / 2, 16),
                screen_layer=True,
                visible=False,
            ),
            "wave_label",
        )

        self.add_object(
            UI(pos=(self.width / 2, self.height / 2), screen_layer=True), "card"
        )

        self.add_object(
            PauseMenu(
                pos=(self.width / 2, self.height / 2),
                visible=False,
            ),
            "menu",
        )

        self.menu.continue_button.set_callback(self.toggle_pause)
        self.menu.restart_button.set_callback(self.restart)
        self.menu.quit_button.set_callback(self.app.stop)

        self.add_object(
            Label(
                text="Game Over",
                pos=(self.width / 2, self.height / 2),
                screen_layer=True,
                visible=False,
            ),
            "game_over_card",
        )

        self.add_object(
            Sprite(
                asset="./Assets/1crosshair.png",
                z=10,
                screen_layer=True,
            ),
            "cursor",
        )

        self.camera.set_bg_color((64, 64, 64))
        self.camera.set_target(self.player)
        self.camera.set_offset(self.player.pos)
        self.camera.set_bounds((0, 0, 1600 - self.width, 1600 - self.height))
        self.camera.follow_type = self.camera.SMOOTH

        self.spawn_weapons()
        # self.spawn_upgrades()
        # self.toggle_debug()

    def spawn_enemies(self, amount):
        spawners = [self.spawn_target, self.spawn_tower, self.spawn_chaser]
        for _ in range(amount):
            enemy_type = random.randint(0, len(spawners) - 1)
            spawners[enemy_type]()

    def spawn_target(self):
        self.add_object(
            Target(
                random.randint(5, 16),
                hp_max=self.difficulty * 10,
                pos=self.get_valid_spawn(),
                groups=[self["enemies"]],
            )
        )

    def spawn_tower(self):
        self.add_object(
            Tower(
                pos=self.get_valid_spawn(),
                hp_max=self.difficulty * 15,
                damage=self.difficulty + 3,
                rof=self.difficulty + 1.5,
                range=150 + 10 * self.difficulty,
                burst=3 + self.difficulty,
                burst_timer=max(2 - self.difficulty * 0.2, 0.5),
                target_group=self["_player"],
                groups=[self["enemies"]],
            )
        )

    def spawn_chaser(self):
        self.add_object(
            Chaser(
                pos=self.get_valid_spawn(),
                hp_max=self.difficulty * 20,
                damage=self.difficulty * 5,
                speed=self.difficulty * 25 + 100,
                target_group=self["_player"],
                friend_group=self["enemies"],
                groups=[self["enemies"]],
            )
        )

    def spawn_upgrades(self):
        pos = self.map.positions["upgrade_spawn"]
        for x in range(len(Upgrade.NAMES)):
            self.add_object(
                Upgrade(
                    pos=(pos.x - 50 + x * 50, pos.y),
                    bonus=1,
                    type=x,
                    target_group=self["_player"],
                    groups=[self["level_upgrade"]],
                )
            )
        self.upgrade_phase = True
        if self.player is not None:
            self.player.upgrade_health(5)

    def spawn_weapons(self):
        pos = self.map.positions["upgrade_spawn"]
        for x in range(len(WeaponPickup.NAMES)):
            self.add_object(
                WeaponPickup(
                    pos=(pos.x - 75 + x * 50, pos.y + 100),
                    type=x,
                    target_group=self["_player"],
                    groups=[self["level_weapons"]],
                )
            )
        self.upgrade_phase = True

    def get_valid_spawn(self):
        spawn_pos = None
        while spawn_pos is None:
            spawn_pos = self.map.get_spawn_point()
            if spawn_pos is None:
                continue
            if dist_to(spawn_pos, self.player.pos) > 72:
                self.spawn_checker.pos = spawn_pos
                collisions = self.get_AABB_collisions(self.spawn_checker)
                if collisions:
                    spawn_pos = None
            else:
                spawn_pos = None
        return spawn_pos

    def state_logic(self, delta):
        if self.game_over:
            self.game_over_card.visible = True
            self.game_over_timer -= delta
            if self.game_over_timer <= 0:
                self.restart()
            return
        if self._paused:
            return

        if self.upgrade_phase:
            if 0 < len(self["level_weapons"]) < 4:
                for weapon in self["level_weapons"]:
                    weapon.queue_kill()
                self.wave_timer = 3
                self.card.show_timer()
                self.card.update_timer(self.wave_timer)

            if 0 < len(self["level_upgrade"]) < len(Upgrade.NAMES):
                for upgrade in self["level_upgrade"]:
                    upgrade.queue_kill()
                self.wave_timer = 3
                self.card.show_timer()
                self.card.update_timer(self.wave_timer)

            if (
                not self["level_upgrade"]
                and not self["level_weapons"]
                and self.wave_timer <= 0
            ):
                self.card.hide_timer()
                self.wave += 1
                self.wave_label.visible = True
                self.wave_label.set_text(str(self.wave))
                self.wave_count = int(self.difficulty * 10)
                self.spawn_enemies(5)
                self.wave_count -= 5
                self.upgrade_phase = False
            elif self.wave_timer > 0:
                self.card.update_timer(self.wave_timer)
                self.wave_timer -= delta
        else:
            if not self["enemies"] and self.wave_count <= 0:
                self.card.show_card()
                self.difficulty += 0.5
                self.spawn_upgrades()
            elif self.enemy_timer <= 0 and self.wave_count > 0:
                self.spawn_enemies(1 + int(self.difficulty // 2))
                self.wave_count -= 1 + int(self.difficulty // 2)
                self.enemy_timer = max(1.5 - self.difficulty * 0.05, 0.5)
            else:
                self.enemy_timer -= delta

    def toggle_pause(self):
        self._paused = not self._paused
        self.menu.visible = self._paused

    def toggle_debug(self):
        self.camera.debug = not self.camera.debug

    def update_ui(self):
        pygame.display.set_caption(str(self.app._clock.get_fps()))
        # pygame.display.set_caption(str(self.app._clock.get_fps()))
        if not self.game_over:
            self.hp_bar.update_value(self.player._hp)
            self.ammo_bar.update_value(self.player.weapon._ammo)

    def update(self, delta):
        self.cursor.pos = Game_Globals["Input"].mouse.pos

        if Game_Globals["Input"].key.press("tab"):
            self.toggle_pause()
        if Game_Globals["Input"].key.press("/"):
            self.toggle_debug()
        if Game_Globals["Input"].key.press("escape"):
            self.app.stop()

        if not self["_player"]:
            self.game_over = True

        self.state_logic(delta)

        self.update_ui()

    def on_unload(self):
        for key, value in self.__dict__.items():
            print(key)
            print(value)
