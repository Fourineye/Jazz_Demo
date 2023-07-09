import pygame as pg

import Jazz.animation as janim
import Jazz.colliders as jcol
from Jazz.global_dict import Game_Globals
import Jazz.objects as jobj
import Jazz.user_interface as jui
from actors import Upgrade
from Jazz.baseObject import GameObject
from Jazz.components import AnimatedSprite, Label, ProgressBar, Sprite
from Jazz.utils import (Vec2, angle_from_vec, clamp, direction_to, dist_to,
                        load_image)
from weapon import Weapon


class Player(jobj.Body):
    IDLE = 0
    MOVING = 1
    HURT = 2
    STATES = ("idle", "moving", "hurt")
    IDLE_ANIM = [f"Assets/player/elf_f_idle_anim_f{i}.png" for i in range(4)]
    MOVE_ANIM = [f"Assets/player/elf_f_run_anim_f{i}.png" for i in range(4)]
    HURT_ANIM = ["Assets/player/elf_f_hit_anim_f0.png"]
    ANIMS = [IDLE_ANIM, MOVE_ANIM, HURT_ANIM]

    def __init__(self, **kwargs):
        super().__init__(name="player", size=(16, 16), **kwargs)
        self.add_child(
            AnimatedSprite(spritesheet=self.IDLE_ANIM, animation_fps=10, pos=(0, -12)),
            "sprite",
        )
        self.add_child(
            Weapon(
                type="None",
            ),
            "weapon",
        )

        self.weapon.sprite.scale = (1, 1)
        self._layers = "0011"
        self.add_child(jcol.RectCollider(16, 16), "collider")
        self._max_hp = 25
        self._hp = self._max_hp
        self._speed = 150
        self._vel = Vec2()
        self._dir = Vec2()
        self._invincibility = 0
        self._last_state = self.IDLE
        self._state = self.IDLE

    def update(self, delta):
        self._dir = Vec2(0)
        if self._state != self.HURT:
            if Game_Globals["Input"].key.held("d"):
                self._dir.x += 1
            if Game_Globals["Input"].key.held("a"):
                self._dir.x -= 1
            if Game_Globals["Input"].key.held("s"):
                self._dir.y += 1
            if Game_Globals["Input"].key.held("w"):
                self._dir.y -= 1
            if self._dir.magnitude_squared() != 0:
                self._dir.normalize_ip()

        firing = False
        new_facing = Vec2()
        if Game_Globals["Input"].key.held("right"):
            new_facing.x += 1
            firing = True
        if Game_Globals["Input"].key.held("left"):
            new_facing.x -= 1
            firing = True
        if Game_Globals["Input"].key.held("up"):
            new_facing.y -= 1
            firing = True
        if Game_Globals["Input"].key.held("down"):
            new_facing.y += 1
            firing = True

        if new_facing.magnitude_squared() == 0:
            new_facing = Game_Globals["Input"].mouse.global_pos - self.pos

        if Game_Globals["Input"].mouse.held(0):
            firing = True
        self.weapon.facing = new_facing
        if self.weapon.rotation < -90 or self.weapon.rotation > 90:
            self.sprite.flip_x = True
        else:
            self.sprite.flip_x = False

        if firing:
            self.weapon.fire()

        self._vel += (self._dir * self._speed - self._vel) / 10
        if self._vel.magnitude_squared() < 10 and self._invincibility == 0:
            self._state = self.IDLE
        elif self._invincibility == 0:
            self._state = self.MOVING
        else:
            self._state = self.HURT
            self._invincibility = max(self._invincibility - delta, 0)

        self.move_and_collide(self._vel * delta)

        if self._state != self.MOVING:
            self.sprite.animation_fps = 10
        else:
            self.sprite.animation_fps = (
                self._vel.magnitude_squared() / self._speed**2 * 10
            )

        if self._last_state != self._state:
            self.sprite.update_animation(self.ANIMS[self._state])
            self._last_state = self._state

    def apply_upgrade(self, amount, stat):
        if stat == Upgrade.HEALTH:
            self.heal(amount * 10)
        elif stat == Upgrade.AMMO:
            self.weapon.reload(amount * 20)
        elif stat == Upgrade.SPEED:
            self._speed += amount * 25
        else:
            self.weapon.upgrade(amount)

    def heal(self, amount):
        self._hp = min(self._hp + amount, self._max_hp)

    def upgrade_health(self, amount):
        self._max_hp += amount
        self.heal(amount)

    def take_damage(self, damage, source):
        if self.do_kill:
            return
        if self._invincibility == 0:
            self._invincibility = 0.2
            self._hp -= damage
            if self._hp <= 0:
                self.queue_kill()

    def knockback(self, amount, source):
        if self._state == self.HURT:
            direction = direction_to(source.pos, self.pos)
            self._vel += direction * amount
