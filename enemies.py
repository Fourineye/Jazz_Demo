import random

import pygame as pg

import Jazz.colliders as jcol
import Jazz.objects as jobj
from actors import Upgrade
from Jazz.components import AnimatedSprite, ProgressBar
from Jazz.utils import Vec2, direction_to, dist_to
from weapon import Weapon


class Enemy(jobj.Body):
    IDLE = 0
    ATTACKING = 1
    STATES = ["idle", "attacking"]

    def __init__(self, **kwargs):
        kwargs.setdefault("name", "Enemy")
        super().__init__(**kwargs)
        self._layers = "0101"
        self._drop_chance = kwargs.get("drop_chance", 15)
        self._radius = kwargs.get("radius", 8)
        self._hp_max = kwargs.get("hp_max", 10)
        self._hp = self._hp_max
        self._state = self.IDLE
        self._last_state = self.IDLE

        self.add_child(jcol.CircleCollider(self._radius, pos=(0, 0)), "collider")
        self.add_child(
            ProgressBar(
                self._hp,
                self._hp_max,
                size=Vec2(32, 6),
                line_width=1,
                pos=(0, -32),
                visible=False,
                color="red",
            ),
            "hp_bar",
        )

    def update(self, delta):
        self.state_logic(delta)
        self._state = self.get_state_change(delta)
        if self._state != self._last_state:
            self.change_state(delta)
            self._last_state = self._state

    def state_logic(self, delta):
        ...

    def get_state_change(self, delta):
        ...

    def change_state(self, delta):
        ...

    def spawn_upgrade(self):
        upgrade_type = random.randint(1, len(Upgrade.NAMES) - 1)
        upgrade = Upgrade(
            target_group=self.scene["_player"], type=upgrade_type, pos=self.pos, timer=5
        )
        self.scene.add_object(upgrade)

    def take_damage(self, damage, source):
        if self.do_kill or source.name != "player":
            return
        self._hp -= damage
        if self._hp <= 0:
            self.scene.camera.add_shake(0.2 * self._radius / 8)
            if random.randint(1, 100) < self._drop_chance:
                self.spawn_upgrade()
            self.queue_kill()
        else:
            self.hp_bar.visible = True
            self.hp_bar.update_value(self._hp)


class Target(Enemy):
    def __init__(self, radius, **kwargs):
        super().__init__(
            name="target",
            color=(0, 255, 0),
            static=True,
            radius=radius,
            **kwargs,
        )

    def _draw(self, surface, offset=None):
        if offset is None:
            offset = Vec2()
        pg.draw.circle(surface, "red", self.pos + offset, self._radius)
        pg.draw.circle(surface, "white", self.pos + offset, self._radius * 0.66)
        pg.draw.circle(surface, "red", self.pos + offset, self._radius * 0.33)


class Tower(Enemy):
    IDLE_ANIM = [f"Assets/enemies/wogol_idle_anim_f{i}.png" for i in range(4)]
    ATTACKING_ANIM = [f"Assets/enemies/wogol_run_anim_f{i}.png" for i in range(4)]

    def __init__(self, range=160, **kwargs):
        super().__init__(name="Tower", radius=8, static=True, **kwargs)
        self.target_group = kwargs.get("target_group")
        self.add_child(
            AnimatedSprite(pos=(0, -4), spritesheet=self.IDLE_ANIM, animation_fps=10),
            "sprite",
        )
        self.add_child(
            jobj.Area(target_group=self.target_group, collision_layers="0010"), "sight"
        )
        self.sight.add_child(jcol.CircleCollider(range), "collider")
        self.add_child(
            Weapon(
                target_layers="0011",
                damage=kwargs.get("damage", 5),
                bullet_asset="./Assets/enemy_bullet.png",
                asset_dimension=8,
                velocity=75,
                rof=kwargs.get("rof", 3),
            ),
            "weapon",
        )
        self.idle_timer = 0
        self.idle_rotation = 0
        self._layers = "0100"
        self.target = None
        self.burst = kwargs.get("burst_size", 3)
        self._burst_count = self.burst
        self.burst_cooldown = kwargs.get("burst_cooldown", 1)
        self._burst_timer = self.burst_cooldown

    def state_logic(self, delta):
        if self._state == self.IDLE:
            if self.idle_timer <= 0:
                self.idle_rotation = [135, 90, 45, 0, -45, -90, -135][
                    random.randint(0, 6)
                ]
                self.idle_timer = random.uniform(0.5, 2)
            else:
                self.idle_timer -= delta
                self.weapon.rotate(self.idle_rotation * delta)
        elif self._state == self.ATTACKING:
            self.weapon.facing = direction_to(self.pos, self.target.pos)

            if self._burst_timer > 0:
                self._burst_timer = max(self._burst_timer - delta, 0)
            else:
                if self._burst_count < self.burst:
                    if self.weapon.fire():
                        self._burst_count += 1
                else:
                    self._burst_count = 0
                    self._burst_timer = self.burst_cooldown

        self.sprite.flip_x = not -90 < self.weapon.rotation < 90

    def get_state_change(self, delta):
        if self._state == self.IDLE:
            if self.sight.entered:
                return self.ATTACKING
            else:
                return self.IDLE
        if self._state == self.ATTACKING:
            if not self.sight.entered:
                return self.IDLE
            else:
                return self.ATTACKING

    def change_state(self, delta):
        if self._state == self.IDLE:
            self.target = None
            self.idle_timer = random.uniform(0.5, 2)
        if self._state == self.ATTACKING:
            self.target = self.sight.entered[0]
            self._burst_timer = self.burst_cooldown / 2


class Chaser(Enemy):
    IDLE_ANIM = [f"Assets/enemies/chort_idle_anim_f{i}.png" for i in range(4)]
    ATTACKING_ANIM = [f"Assets/enemies/chort_run_anim_f{i}.png" for i in range(4)]

    def __init__(self, range=250, **kwargs):
        super().__init__(name="Chaser", radius=8, static=True, **kwargs)
        self._color = (255, 0, 0)
        self.target_group = kwargs.get("target_group")
        self.friend_group = kwargs.get("friend_group")
        self.add_child(
            AnimatedSprite(pos=(0, -4), spritesheet=self.IDLE_ANIM, animation_fps=10),
            "sprite",
        )
        self.add_child(
            jobj.Area(target_group=self.target_group, collision_layers="0010"), "sight"
        )
        self.sight.add_child(jcol.CircleCollider(range), "collider")
        self.add_child(
            jobj.Area(target_group=self.friend_group, collision_layers="0100"),
            "friend_sight",
        )
        self.friend_sight.add_child(jcol.CircleCollider(24), "collider")
        self.idle_timer = 0
        self.aggro_timer = 0
        self.aggro_target = None
        self._layers = "0101"
        self._vel = Vec2()
        self.damage = kwargs.get("damage", 5)
        self.speed = kwargs.get("speed", 100)

    def update(self, delta):
        desired_vel = Vec2()
        if self.aggro_timer > 0:
            desired_vel = direction_to(self.pos, self.aggro_target.pos) * self.speed
            self.aggro_timer -= delta
            if self.aggro_timer <= 0:
                self.aggro_timer = 0
                self.aggro_target = None
        if self.sight.entered:
            desired_vel = direction_to(self.pos, self.sight.entered[0].pos) * self.speed
        for friend in self.friend_sight.entered:
            if friend is not self:
                desired_vel += (
                    (direction_to(friend.pos, self.pos) * self.speed / 3)
                    * 48**2
                    / (dist_to(self.pos, friend.pos)) ** 2
                )

        self._vel += (desired_vel - self._vel) / 10
        if self._vel.magnitude_squared() > self.speed**2:
            self._vel.scale_to_length(self.speed)
        collisions = self.move_and_collide(self._vel * delta)
        for obj, _data in collisions:
            if obj in self.target_group:
                obj.take_damage(self.damage, self.name)
                obj.knockback(self._vel.magnitude() + 32 * self.damage, self)

    # def _draw(self, surface, offset=None):
    #     if offset is None:
    #         offset = Vec2()
    #     pg.draw.circle(surface, self._color, self.pos + offset, self._radius)

    def knockback(self, amount, source):
        direction = direction_to(source.pos, self.pos)
        self._vel += direction * amount * 5

    def take_damage(self, damage, source):
        if source in self.target_group:
            self.aggro_target = source
            self.aggro_timer = 2
        return super().take_damage(damage, source)
