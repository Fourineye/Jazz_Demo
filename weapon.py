import random

import pygame as pg

import Jazz.colliders as jcol
import Jazz.objects as jobj
import Jazz.user_interface as jui
from Jazz.baseObject import GameObject
from Jazz.components import AnimatedSprite, Sprite
from Jazz.utils import Vec2, angle_from_vec, clamp, load_image

WEAPON_TABLE = {
    "Sniper": [
        (15, 1, 1, 5),
        (20, 1.2, 1, 4.5),
        (25, 1.4, 1, 4),
        (35, 1.6, 1, 3.5),
        (40, 1.8, 1, 3),
        (45, 2, 1, 2.5),
        (55, 2.2, 1, 2),
        (60, 2.4, 1, 1.5),
        (65, 2.6, 1, 1),
        (75, 2.8, 1, 0.5),
        (90, 3, 1, 0),
    ],
    "Assault": [
        (4, 3, 1, 7),
        (7, 3.5, 1, 7),
        (10, 4, 1, 7),
        (13, 4.5, 1, 7),
        (16, 5, 1, 7),
        (19, 5.5, 1, 7),
        (22, 6, 1, 7),
        (25, 6.5, 1, 7),
        (28, 7, 1, 7),
        (31, 7.5, 1, 7),
        (34, 8, 1, 7),
    ],
    "Shotgun": [
        (2, 1, 6, 15),
        (2, 1.2, 6, 14),
        (2, 1.4, 6, 13),
        (4, 1.6, 7, 12),
        (4, 1.8, 7, 11),
        (4, 2, 7, 10),
        (6, 2.2, 8, 9),
        (6, 2.4, 8, 8),
        (6, 2.6, 8, 7),
        (8, 2.8, 9, 6),
        (10, 3, 10, 5),
    ],
    "SMG": [
        (3, 3, 1, 10),
        (3, 4.5, 1, 9.5),
        (3, 6, 1, 9),
        (6, 7.5, 1, 8.5),
        (6, 9, 1, 8),
        (6, 10.5, 1, 7.5),
        (9, 12, 1, 7),
        (9, 13.5, 1, 6.5),
        (9, 15, 1, 6),
        (12, 16.5, 1, 5.5),
        (15, 18, 1, 5),
    ],
}

ASSETS = {
    "Sniper": "./Assets/Guns/Sniper.png",
    "Assault": "./Assets/Guns/Assault.png",
    "Shotgun": "./Assets/Guns/Shotgun.png",
    "SMG": "./Assets/Guns/SMG.png",
    "Enemy": "./Assets/Guns/Enemy.png",
}


class Weapon(GameObject):
    def __init__(self, components=None, **kwargs):
        super().__init__("Weapon", **kwargs)
        weapon_type = kwargs.get("type", "Enemy")
        self.weapon_type = weapon_type
        level = clamp(kwargs.get("level", 0), 0, 10)
        self.level = level

        gun_asset = ASSETS.get(self.weapon_type, "./Assets/Guns/None.png")
        self.add_child(
            Sprite(asset=gun_asset, pos=(5, 0)),
            "sprite",
        )

        self.add_child(GameObject(pos=(9, 0)), "barrel")

        self._muzzle_velocity = kwargs.get("velocity", 300)
        if weapon_type in ["Sniper", "Assault", "Shotgun", "SMG"]:
            stats = WEAPON_TABLE[weapon_type][level]
            self._damage = stats[0]
            self._rof = stats[1]
            self._projectiles = stats[2]
            self._spread = stats[3]
        else:
            self._projectiles = kwargs.get("projectiles", 1)
            self._damage = kwargs.get("damage", 1)
            self._spread = kwargs.get("spread", 0)
            self._rof = kwargs.get("rof", 3)

        self._target_layers = kwargs.get("target_layers", "0100")
        self._cooldown = 0
        self._components = list(components) if components is not None else []
        self.bullet_sheet = kwargs.get("bullet_asset", "./Assets/Bullet.png")
        self._bullet_assets = []
        self._max_ammo = kwargs.get("ammo", 100)
        self._ammo = self._max_ammo // 2

    def on_load(self):
        self._bullet_assets = self.scene.load_resource(
            self.bullet_sheet, self.scene.SPRITE_SHEET
        )

    def __repr__(self):
        return f"L: {self.level} p:{self._projectiles} d:{self._damage} s:{self._spread} v:{self._muzzle_velocity} r:{self._rof}"

    def update(self, delta):
        if self._cooldown > 0:
            self._cooldown = max(self._cooldown - delta, 0)
        if self.rotation > 90 or self.rotation < -90:
            self.sprite.flip_y = True
        else:
            self.sprite.flip_y = False

    def set_type(self, weapon_type, level=0):
        self.level = clamp(level, 0, 10)
        self.weapon_type = weapon_type
        if weapon_type in ["Sniper", "Assault", "Shotgun", "SMG"]:
            stats = WEAPON_TABLE[weapon_type][self.level]
            self._damage = stats[0]
            self._rof = stats[1]
            self._projectiles = stats[2]
            self._spread = stats[3]
        else:
            self._projectiles = 1
            self._damage = 1
            self._spread = 0
            self._rof = 3
        self.sprite.source = ASSETS.get(self.weapon_type, "./Assets/Guns/None.png")

    def upgrade(self, amount):
        self.level = clamp(self.level + amount, 0, 10)
        if self.weapon_type in WEAPON_TABLE.keys():
            stats = WEAPON_TABLE[self.weapon_type][self.level]
            self._damage = stats[0]
            self._rof = stats[1]
            self._projectiles = stats[2]
            self._spread = stats[3]

    def reload(self, amount):
        self._ammo = clamp(self._ammo + amount, 0, self._max_ammo)

    def fire(self):
        if self._cooldown != 0 or self._ammo == 0 or self.weapon_type == "None":
            return False
        # self._ammo -= 1
        # self.scene.camera.add_shake((self._damage + self._projectiles) / 30)
        aim_dir = Vec2(self.facing)
        for _ in range(self._projectiles):
            aim_dir = Vec2(self.facing)
            shot_speed = self._muzzle_velocity
            if self._spread > 0:
                spread = random.uniform(-self._spread / 2, self._spread / 2)
                aim_dir.rotate_ip(spread)
            if self._projectiles > 1:
                shot_speed = self._muzzle_velocity * random.uniform(0.90, 1.0)
            self.scene.add_object(
                Bullet(
                    shot_speed,
                    damage=self.damage,
                    assets=self._bullet_assets,
                    rotation=angle_from_vec(aim_dir),
                    pos=self.barrel.pos,
                    collision_layers=self._target_layers,
                    source=self.root,
                )
            )
        self._cooldown = 1 / self.rof
        return True

    @property
    def damage(self):
        return self._damage

    @property
    def rof(self):
        return self._rof

    @property
    def spread(self):
        return self._spread


class Bullet(jobj.Body):
    def __init__(self, speed, **kwargs):
        super().__init__(
            name="bullet",
            color=(255, 255, 255),
            **kwargs,
        )
        self.add_child(jcol.CircleCollider(2), "collider")
        self._layers = "0000"
        self.source = kwargs.get("source", None)
        self._speed = speed
        self._damage = kwargs.get("damage", 1)
        self._life = kwargs.get("life", 2)
        self._z = -1
        self.add_child(
            AnimatedSprite(spritesheet=kwargs.get("assets"), animation_fps=10),
            "sprite",
        )

    def move_once(self, delta):
        collisions = self.move_and_collide(self.facing * self._speed * delta)
        for collider, _info in collisions:
            if hasattr(collider, "take_damage"):
                collider.take_damage(self._damage, self.source)
            if hasattr(collider, "knockback"):
                collider.knockback(self._damage, self)
                # self.scene.add_object(Explosion(target[1]))
            self.queue_kill()
            self.scene.add_object(HitParticle(pos=self.pos))
            return

    def update(self, delta):
        self.move_once(delta / 2)
        self.move_once(delta / 2)
        self._life -= delta
        if self._life <= 0:
            self.queue_kill()


class HitParticle(AnimatedSprite):
    def __init__(self, **kwargs):
        super().__init__(
            name="Hit Particle",
            spritesheet="Assets/HitParticleSheet.png",
            sprite_dim=(16, 16),
            animation_fps=60,
            oneshot=True,
            **kwargs,
        )

    def update(self, delta):
        super().update(delta)
        if not self._playing:
            self.queue_kill()
