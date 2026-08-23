"""
Plants vs Zombies - Level State
===============================
Main gameplay: plant selection, grid placement, zombies, sun, bullets.
"""

__author__ = "marble_xu"

import json
import pygame as pg

from .. import constants as c
from .. import tool
from ..component import map, menubar, plant, zombie


class Level(tool.State):
    """Level gameplay state: map, plants, zombies, menubar."""
    def __init__(self):
        tool.State.__init__(self)
    
    def startup(self, current_time, persist):
        self.game_info = persist
        self.persist = self.game_info
        self.game_info[c.CURRENT_TIME] = current_time
        self.game_mode = self.game_info.get(c.GAME_MODE, c.MODE_ADVENTURE)
        self.map_y_len = c.GRID_Y_LEN
        self.map = map.Map(c.GRID_X_LEN, self.map_y_len)
        self.toast = ""
        self.toast_timer = 0
        self.star_font = pg.font.SysFont(None, 22)
        self.hint_font = pg.font.SysFont(None, 24)

        self.loadMap()
        self.setupBackground()
        self.initState()

    def loadMap(self):
        """Load Adventure level_N.json or Cross cross_N.json."""
        level_num = int(self.game_info.get(c.LEVEL_NUM, c.START_LEVEL_NUM))
        mode = self.game_info.get(c.GAME_MODE, c.MODE_ADVENTURE)
        max_level = c.MAX_CROSS_LEVEL if mode == c.MODE_CROSS else c.MAX_LEVEL
        if level_num < c.START_LEVEL_NUM or level_num > max_level:
            level_num = c.START_LEVEL_NUM
            self.game_info[c.LEVEL_NUM] = level_num

        if mode == c.MODE_CROSS:
            map_file = f"cross_{level_num}.json"
            range_msg = f"{c.START_LEVEL_NUM}–{c.MAX_CROSS_LEVEL}"
        else:
            map_file = f"level_{level_num}.json"
            range_msg = f"{c.START_LEVEL_NUM}–{c.MAX_LEVEL}"

        file_path = tool.res_data_path("map", map_file)
        try:
            with open(file_path, encoding="utf-8") as f:
                self.map_data = json.load(f)
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"Missing map '{map_file}'. Valid maps are {range_msg}."
            ) from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in level map: {file_path}") from exc
    
    def setupBackground(self):
        img_index = self.map_data[c.BACKGROUND_TYPE]
        self.background_type = img_index
        self.background = tool.GFX[c.BACKGROUND_NAME][img_index]
        self.bg_rect = self.background.get_rect()

        self.level = pg.Surface((self.bg_rect.w, self.bg_rect.h)).convert()
        self.viewport = tool.SCREEN.get_rect(bottom=self.bg_rect.bottom)
        self.viewport.x += c.BACKGROUND_OFFSET_X
    
    def setupGroups(self):
        self.sun_group = pg.sprite.Group()
        self.head_group = pg.sprite.Group()

        self.plant_groups = []
        self.zombie_groups = []
        self.hypno_zombie_groups = [] #zombies who are hypno after eating hypnoshroom
        self.bullet_groups = []
        for i in range(self.map_y_len):
            self.plant_groups.append(pg.sprite.Group())
            self.zombie_groups.append(pg.sprite.Group())
            self.hypno_zombie_groups.append(pg.sprite.Group())
            self.bullet_groups.append(pg.sprite.Group())
    
    def setupZombies(self):
        def takeTime(element):
            return element[0]

        self.zombie_list = []
        for data in self.map_data[c.ZOMBIE_LIST]:
            self.zombie_list.append((data['time'], data['name'], data['map_y']))
        self.zombie_start_time = 0
        self.zombie_list.sort(key=takeTime)

    def setupCars(self):
        self.cars = []
        for i in range(self.map_y_len):
            _, y = self.map.getMapGridPos(0, i)
            self.cars.append(plant.Car(-25, y+20, i))

    def update(self, surface, current_time, mouse_pos, mouse_click):
        self.current_time = self.game_info[c.CURRENT_TIME] = current_time
        if self.state == c.CHOOSE:
            self.choose(mouse_pos, mouse_click)
        elif self.state == c.PLAY:
            self.play(mouse_pos, mouse_click)

        self.draw(surface)

    def initBowlingMap(self):
        print('initBowlingMap')
        for x in range(3, self.map.width):
            for y in range(self.map.height):
                self.map.setMapGridType(x, y, c.MAP_EXIST)

    def initState(self):
        if c.CHOOSEBAR_TYPE in self.map_data:
            self.bar_type = self.map_data[c.CHOOSEBAR_TYPE]
        else:
            self.bar_type = c.CHOOSEBAR_STATIC

        if self.bar_type == c.CHOOSEBAR_STATIC:
            self.initChoose()
        else:
            card_pool = menubar.getCardPool(self.map_data[c.CARD_POOL])
            self.initPlay(card_pool)
            if self.bar_type == c.CHOOSEBAR_BOWLING:
                self.initBowlingMap()

    def initChoose(self):
        self.state = c.CHOOSE
        if c.CARD_POOL in self.map_data:
            card_list = menubar.getCardPool(self.map_data[c.CARD_POOL])
        else:
            card_list = menubar.all_card_list
        self.panel = menubar.Panel(card_list, self.map_data[c.INIT_SUN_NAME])

    def choose(self, mouse_pos, mouse_click):
        if mouse_pos and mouse_click[0]:
            self.panel.checkCardClick(mouse_pos)
            if self.panel.checkStartButtonClick(mouse_pos):
                self.initPlay(self.panel.getSelectedCards())

    def initPlay(self, card_list):
        self.state = c.PLAY
        if self.bar_type == c.CHOOSEBAR_STATIC:
            self.menubar = menubar.MenuBar(card_list, self.map_data[c.INIT_SUN_NAME])
        else:
            self.menubar = menubar.MoveBar(card_list)
        self.drag_plant = False
        self.hint_image = None
        self.hint_plant = False
        if self.background_type == c.BACKGROUND_DAY and self.bar_type == c.CHOOSEBAR_STATIC:
            self.produce_sun = True
        else:
            self.produce_sun = False
        self.sun_timer = self.current_time

        self.removeMouseImage()
        self.setupGroups()
        self.setupZombies()
        self.setupCars()

    def play(self, mouse_pos, mouse_click):
        if self.zombie_start_time == 0:
            self.zombie_start_time = self.current_time
        elif len(self.zombie_list) > 0:
            data = self.zombie_list[0]
            if  data[0] <= (self.current_time - self.zombie_start_time):
                self.createZombie(data[1], data[2])
                self.zombie_list.remove(data)

        for i in range(self.map_y_len):
            self.bullet_groups[i].update(self.game_info)
            self.plant_groups[i].update(self.game_info)
            self.zombie_groups[i].update(self.game_info)
            self.hypno_zombie_groups[i].update(self.game_info)
            for zombie in self.hypno_zombie_groups[i]:
                if zombie.rect.x > c.SCREEN_WIDTH:
                    zombie.kill()

        self.head_group.update(self.game_info)
        self.sun_group.update(self.game_info)
        
        if not self.drag_plant and mouse_pos and mouse_click[0]:
            result = self.menubar.checkCardClick(mouse_pos)
            if result:
                self.setupMouseImage(result[0], result[1])
        elif self.drag_plant:
            if mouse_click[1]:
                self.removeMouseImage()
            elif mouse_click[0]:
                if self.menubar.checkMenuBarClick(mouse_pos):
                    self.removeMouseImage()
                else:
                    self.addPlant()
            elif mouse_pos is None:
                self.setupHintImage()
        
        if self.produce_sun:
            if(self.current_time - self.sun_timer) > c.PRODUCE_SUN_INTERVAL:
                self.sun_timer = self.current_time
                map_x, map_y = self.map.getRandomMapIndex()
                x, y = self.map.getMapGridPos(map_x, map_y)
                self.sun_group.add(plant.Sun(x, 0, x, y))
        if not self.drag_plant and mouse_pos and mouse_click[0]:
            for sun in self.sun_group:
                if sun.checkCollision(mouse_pos[0], mouse_pos[1]):
                    self.menubar.increaseSunValue(sun.sun_value)

        for car in self.cars:
            car.update(self.game_info)

        self.menubar.update(self.current_time)

        self.checkBulletCollisions()
        self.checkZombieCollisions()
        self.checkPlants()
        self.checkCarCollisions()
        self.checkGameState()

    def createZombie(self, name, map_y):
        x, y = self.map.getMapGridPos(0, map_y)
        if name == c.NORMAL_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.NormalZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.CONEHEAD_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.ConeHeadZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.BUCKETHEAD_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.BucketHeadZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.FLAG_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.FlagZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.NEWSPAPER_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.NewspaperZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.CONE_BUCKET_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.ConeBucketZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.FLAG_PAPER_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.FlagPaperZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.EMBER_CONE_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.EmberConeZombie(c.ZOMBIE_START_X, y, self.head_group))

    def canSeedPlant(self):
        x, y = pg.mouse.get_pos()
        if self.game_mode == c.MODE_CROSS:
            return self.map.showPlantOrMerge(x, y)
        return self.map.showPlant(x, y)

    def _toast(self, msg: str, ms: int = 1800) -> None:
        self.toast = msg
        self.toast_timer = self.current_time + ms

    def getPlantAt(self, map_x, map_y):
        """Return the plant sprite on this grid cell, if any."""
        for p in self.plant_groups[map_y]:
            px, py = p.getPosition()
            mx, my = self.map.getMapIndex(px, py)
            if mx == map_x and my == map_y:
                return p
        return None

    def addPlant(self):
        from ..component.hybrids import fuse_plant_names

        pos = self.canSeedPlant()
        if pos is None:
            return

        if self.hint_image is None:
            self.setupHintImage()
        x, y = self.hint_rect.centerx, self.hint_rect.bottom
        map_x, map_y = self.map.getMapIndex(x, y)
        occupied = self.map.isOccupied(map_x, map_y)

        ctx = {
            "bullet_group": self.bullet_groups[map_y],
            "bullet_groups": self.bullet_groups,
            "sun_group": self.sun_group,
            "map_y": map_y,
            "zombie_group": self.zombie_groups[map_y],
            "level": self,
        }

        if occupied and self.game_mode == c.MODE_CROSS:
            existing = self.getPlantAt(map_x, map_y)
            if existing is None:
                return
            # Same-type star merge: more than double attack + variance
            if (
                existing.name == self.plant_name
                and getattr(existing, "star", 1) < c.MAX_PLANT_STAR
            ):
                existing.apply_star(existing.star + 1)
                self._consumeCard()
                self._toast(
                    f"Evolved x{existing.star}  (power ×{existing.power_mult:.2f})"
                )
                self.removeMouseImage()
                return
            # Any two different plants fuse into a new creature that keeps both traits
            from ..component.hybrids import fuse_plant_names

            cfg = fuse_plant_names(self.plant_name, existing.name, None, existing)
            existing.kill()
            new_plant = plant.spawn_plant(cfg.name, x, y, ctx, config=cfg)
            if new_plant.can_sleep and self.background_type == c.BACKGROUND_DAY:
                new_plant.setSleep()
            self.plant_groups[map_y].add(new_plant)
            self._consumeCard()
            self._toast(f"{cfg.display_name}!")
            self.removeMouseImage()
            return

        if occupied:
            return

        new_plant = plant.spawn_plant(self.plant_name, x, y, ctx)
        if new_plant.can_sleep and self.background_type == c.BACKGROUND_DAY:
            new_plant.setSleep()
        self.plant_groups[map_y].add(new_plant)
        self._consumeCard()
        if self.bar_type != c.CHOOSEBAR_BOWLING:
            self.map.setMapGridType(map_x, map_y, c.MAP_EXIST)
        self.removeMouseImage()

    def _consumeCard(self) -> None:
        if self.bar_type == c.CHOOSEBAR_STATIC:
            self.menubar.decreaseSunValue(self.select_plant.sun_cost)
            self.menubar.setCardFrozenTime(self.plant_name)
        else:
            self.menubar.deleteCard(self.select_plant)

    def setupHintImage(self):
        """Build a translucent placement ghost without a solid dark box."""
        pos = self.canSeedPlant()
        if pos and self.mouse_image:
            if (self.hint_image and pos[0] == self.hint_rect.x and
                pos[1] == self.hint_rect.y):
                return
            width, height = self.mouse_rect.w, self.mouse_rect.h
            # SRCALPHA keeps transparent padding clear; multiply fades the plant.
            image = pg.Surface((width, height), pg.SRCALPHA)
            image.blit(self.mouse_image, (0, 0))
            image.fill((255, 255, 255, 160), special_flags=pg.BLEND_RGBA_MULT)
            self.hint_image = image
            self.hint_rect = image.get_rect()
            self.hint_rect.centerx = pos[0]
            self.hint_rect.bottom = pos[1]
            self.hint_plant = True
        else:
            self.hint_plant = False

    def setupMouseImage(self, plant_name, select_plant):
        frame_list = tool.GFX[plant_name]
        if not isinstance(frame_list, list) or not frame_list:
            return
        if plant_name in tool.PLANT_RECT:
            data = tool.PLANT_RECT[plant_name]
            x, y, width, height = data['x'], data['y'], data['width'], data['height']
        else:
            x, y = 0, 0
            rect = frame_list[0].get_rect()
            width, height = rect.w, rect.h

        if (plant_name == c.POTATOMINE or plant_name == c.SQUASH or
            plant_name == c.SPIKEWEED or plant_name == c.JALAPENO or
            plant_name == c.SCAREDYSHROOM or plant_name == c.SUNSHROOM or
            plant_name == c.ICESHROOM or plant_name == c.HYPNOSHROOM or
            plant_name == c.WALLNUTBOWLING or plant_name == c.REDWALLNUTBOWLING):
            color = c.WHITE
        else:
            color = c.BLACK
        self.mouse_image = tool.get_image(frame_list[0], x, y, width, height, color, 1)
        self.mouse_rect = self.mouse_image.get_rect()
        pg.mouse.set_visible(False)
        self.drag_plant = True
        self.plant_name = plant_name
        self.select_plant = select_plant

    def removeMouseImage(self):
        pg.mouse.set_visible(True)
        self.drag_plant = False
        self.mouse_image = None
        self.hint_image = None
        self.hint_plant = False

    def checkBulletCollisions(self):
        collided_func = pg.sprite.collide_circle_ratio(0.7)
        for i in range(self.map_y_len):
            torch_plants = [
                p for p in self.plant_groups[i]
                if getattr(p, "is_torch", False) and p.health > 0
            ]
            for bullet in self.bullet_groups[i]:
                if bullet.state != c.FLY:
                    continue
                # Torch-Nut: peas that pass a torch become fire (2x)
                if not getattr(bullet, "fire", False) and not bullet.ice:
                    for torch in torch_plants:
                        if bullet.rect.centerx >= torch.rect.centerx:
                            bullet.fire = True
                            bullet.damage = max(1, int(bullet.damage) * 2)
                            tinted = bullet.image.copy()
                            tinted.fill((255, 140, 40, 255), special_flags=pg.BLEND_RGBA_MULT)
                            bullet.image = tinted
                            break
                zombie = pg.sprite.spritecollideany(
                    bullet, self.zombie_groups[i], collided_func
                )
                if zombie and zombie.state != c.DIE:
                    zombie.setDamage(bullet.damage, bullet.ice)
                    bullet.setExplode()
    
    def checkZombieCollisions(self):
        if self.bar_type == c.CHOOSEBAR_BOWLING:
            ratio = 0.6
        else:
            ratio = 0.7
        collided_func = pg.sprite.collide_circle_ratio(ratio)
        for i in range(self.map_y_len):
            hypo_zombies = []
            for zombie in self.zombie_groups[i]:
                if zombie.state != c.WALK:
                    continue
                plant = pg.sprite.spritecollideany(zombie, self.plant_groups[i], collided_func)
                if plant:
                    if plant.name == c.WALLNUTBOWLING:
                        if plant.canHit(i):
                            zombie.setDamage(c.WALLNUT_BOWLING_DAMAGE)
                            plant.changeDirection(i)
                    elif plant.name == c.REDWALLNUTBOWLING:
                        if plant.state == c.IDLE:
                            plant.setAttack()
                    elif plant.name == c.SPIKEWEED:
                        pass
                    elif plant.name == c.POTATOMINE:
                        # Armed mines are stepped on (boom via checkPlant), not eaten.
                        # Unarmed mines can still be chewed like other plants.
                        if plant.is_init:
                            zombie.setAttack(plant)
                    elif plant.name == c.SPIKE_MINE:
                        if getattr(plant, "is_init", True):
                            zombie.setAttack(plant)
                    elif plant.name == c.TORCH_NUT:
                        zombie.setAttack(plant)
                    else:
                        zombie.setAttack(plant)
            for hypno_zombie in self.hypno_zombie_groups[i]:
                if hypno_zombie.health <= 0:
                    continue
                zombie_list = pg.sprite.spritecollide(hypno_zombie,
                               self.zombie_groups[i], False,collided_func)
                for zombie in zombie_list:
                    if zombie.state == c.DIE:
                        continue
                    if zombie.state == c.WALK:
                        zombie.setAttack(hypno_zombie, False)
                    if hypno_zombie.state == c.WALK:
                        hypno_zombie.setAttack(zombie, False)

    def checkCarCollisions(self):
        """Resolve lawn-mower hits; rebuild the car list after the loop."""
        collided_func = pg.sprite.collide_circle_ratio(0.8)
        for car in self.cars:
            zombies = pg.sprite.spritecollide(
                car, self.zombie_groups[car.map_y], False, collided_func
            )
            for zombie in zombies:
                if zombie and zombie.state != c.DIE:
                    car.setWalk()
                    zombie.setDie()
        # Avoid mutating the list while iterating (can skip cars / raise).
        self.cars = [car for car in self.cars if not car.dead]

    def boomZombies(self, x, map_y, y_range, x_range):
        for i in range(self.map_y_len):
            if abs(i - map_y) > y_range:
                continue
            for zombie in self.zombie_groups[i]:
                if abs(zombie.rect.centerx - x) <= x_range:
                    zombie.setBoomDie()

    def freezeZombies(self, plant):
        for i in range(self.map_y_len):
            for zombie in self.zombie_groups[i]:
                if zombie.rect.centerx < c.SCREEN_WIDTH:
                    zombie.setFreeze(plant.trap_frames[0])

    def killPlant(self, plant):
        x, y = plant.getPosition()
        map_x, map_y = self.map.getMapIndex(x, y)
        if self.bar_type != c.CHOOSEBAR_BOWLING:
            self.map.setMapGridType(map_x, map_y, c.MAP_EMPTY)
        boom_hybrid = bool(
            getattr(getattr(plant, "config", None), "explode", False)
        )
        if (plant.name == c.CHERRYBOMB or plant.name == c.JALAPENO or
            (plant.name == c.POTATOMINE and not plant.is_init) or
            (plant.name == c.SPIKE_MINE and not getattr(plant, "is_init", True)) or
            boom_hybrid or
            plant.name == c.REDWALLNUTBOWLING):
            y_range = getattr(plant, "explode_y_range", 0)
            x_range = getattr(plant, "explode_x_range", c.GRID_X_SIZE)
            self.boomZombies(plant.rect.centerx, map_y, y_range, x_range)
        elif plant.name == c.ICESHROOM and plant.state != c.SLEEP:
            self.freezeZombies(plant)
        elif plant.name == c.HYPNOSHROOM and plant.state != c.SLEEP:
            # Only convert when a zombie actually ate the shroom.
            hypno_target = getattr(plant, "kill_zombie", None)
            if hypno_target is not None:
                hypno_target.setHypno()
                _, map_y = self.map.getMapIndex(
                    hypno_target.rect.centerx, hypno_target.rect.bottom
                )
                self.zombie_groups[map_y].remove(hypno_target)
                self.hypno_zombie_groups[map_y].add(hypno_target)
        plant.kill()

    def checkPlant(self, plant, i):
        zombie_len = len(self.zombie_groups[i])
        if plant.name == c.THREEPEASHOOTER:
            if plant.state == c.IDLE:
                if zombie_len > 0:
                    plant.setAttack()
                elif (i-1) >= 0 and len(self.zombie_groups[i-1]) > 0:
                    plant.setAttack()
                elif (i+1) < self.map_y_len and len(self.zombie_groups[i+1]) > 0:
                    plant.setAttack()
            elif plant.state == c.ATTACK:
                if zombie_len > 0:
                    pass
                elif (i-1) >= 0 and len(self.zombie_groups[i-1]) > 0:
                    pass
                elif (i+1) < self.map_y_len and len(self.zombie_groups[i+1]) > 0:
                    pass
                else:
                    plant.setIdle()
        elif plant.name == c.CHOMPER:
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    plant.setAttack(zombie, self.zombie_groups[i])
                    break
        elif plant.name == c.POTATOMINE:
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    plant.setAttack()
                    break
        elif plant.name == c.SPIKE_MINE:
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    plant.setAttack(self.zombie_groups[i])
                    break
        elif plant.name == c.SQUASH:
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    plant.setAttack(zombie, self.zombie_groups[i])
                    break
        elif plant.name == c.SPIKEWEED:
            can_attack = False
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    can_attack = True
                    break
            if plant.state == c.IDLE and can_attack:
                plant.setAttack(self.zombie_groups[i])
            elif plant.state == c.ATTACK and not can_attack:
                plant.setIdle()
        elif plant.name == c.SCAREDYSHROOM:
            need_cry = False
            can_attack = False
            for zombie in self.zombie_groups[i]:
                if plant.needCry(zombie):
                    need_cry = True
                    break
                elif plant.canAttack(zombie):
                    can_attack = True
            if need_cry:
                if plant.state != c.CRY:
                    plant.setCry()
            elif can_attack:
                if plant.state != c.ATTACK:
                    plant.setAttack()
            elif plant.state != c.IDLE:
                plant.setIdle()
        elif(plant.name == c.WALLNUTBOWLING or
             plant.name == c.REDWALLNUTBOWLING):
            pass
        else:
            can_attack = False
            if (plant.state == c.IDLE and zombie_len > 0):
                for zombie in self.zombie_groups[i]:
                    if plant.canAttack(zombie):
                        can_attack = True
                        break
            if plant.state == c.IDLE and can_attack:
                plant.setAttack()
            elif (plant.state == c.ATTACK and not can_attack):
                plant.setIdle()

    def checkPlants(self):
        for i in range(self.map_y_len):
            for plant in self.plant_groups[i]:
                if plant.state != c.SLEEP:
                    self.checkPlant(plant, i)
                if plant.health <= 0:
                    self.killPlant(plant)

    def checkVictory(self):
        if len(self.zombie_list) > 0:
            return False
        for i in range(self.map_y_len):
            if len(self.zombie_groups[i]) > 0:
                return False
        return True
    
    def checkLose(self):
        for i in range(self.map_y_len):
            for zombie in self.zombie_groups[i]:
                if zombie.rect.right < 0:
                    return True
        return False

    def checkGameState(self):
        """Advance to victory/lose screens; cap progression by active mode."""
        if self.checkVictory():
            next_level = int(self.game_info[c.LEVEL_NUM]) + 1
            self.game_info[c.LEVEL_NUM] = next_level
            self.next = c.GAME_VICTORY
            self.done = True
        elif self.checkLose():
            self.next = c.GAME_LOSE
            self.done = True

    def drawMouseShow(self, surface):
        if self.hint_plant:
            surface.blit(self.hint_image, self.hint_rect)
        x, y = pg.mouse.get_pos()
        self.mouse_rect.centerx = x
        self.mouse_rect.centery = y
        surface.blit(self.mouse_image, self.mouse_rect)

    def drawZombieFreezeTrap(self, i, surface):
        for zombie in self.zombie_groups[i]:
            zombie.drawFreezeTrap(surface)

    def drawPlantStars(self, surface):
        badge = tool.GFX.get(c.DNA_BADGE)
        for i in range(self.map_y_len):
            for p in self.plant_groups[i]:
                star = getattr(p, "star", 1)
                is_cross = getattr(p, "config", None) is not None
                if star <= 1 and not is_cross:
                    continue
                x = p.rect.centerx - 14
                y = p.rect.top - 16
                if isinstance(badge, pg.Surface):
                    surface.blit(badge, (x, y))
                label = "*" * max(1, star) if star > 1 else "+"
                txt = self.star_font.render(label, True, c.GOLD)
                surface.blit(txt, (x + 30, y + 2))

    def draw(self, surface):
        self.level.blit(self.background, self.viewport, self.viewport)
        surface.blit(self.level, (0,0), self.viewport)
        if self.state == c.CHOOSE:
            self.panel.draw(surface)
        elif self.state == c.PLAY:
            self.menubar.draw(surface)
            for i in range(self.map_y_len):
                self.plant_groups[i].draw(surface)
                self.zombie_groups[i].draw(surface)
                self.hypno_zombie_groups[i].draw(surface)
                self.bullet_groups[i].draw(surface)
                self.drawZombieFreezeTrap(i, surface)
            self.drawPlantStars(surface)
            for car in self.cars:
                car.draw(surface)
            self.head_group.draw(surface)
            self.sun_group.draw(surface)

            if self.drag_plant:
                self.drawMouseShow(surface)

            if self.game_mode == c.MODE_CROSS:
                banner = tool.GFX.get(c.CROSS_BANNER)
                if isinstance(banner, pg.Surface):
                    br = banner.get_rect(midbottom=(c.SCREEN_WIDTH // 2 + 40, c.SCREEN_HEIGHT - 6))
                    surface.blit(banner, br)
                else:
                    hint = self.hint_font.render(
                        "Drop on any plant to fuse traits or evolve (power > 2x)",
                        True,
                        c.LIGHTYELLOW,
                    )
                    surface.blit(hint, (160, c.SCREEN_HEIGHT - 28))

            if self.toast and self.current_time < self.toast_timer:
                toast = self.star_font.render(self.toast, True, c.GOLD)
                glow = tool.GFX.get(c.FUSION_GLOW)
                bg = pg.Surface((toast.get_width() + 28, toast.get_height() + 14), pg.SRCALPHA)
                bg.fill((12, 40, 20, 200))
                rect = bg.get_rect(center=(c.SCREEN_WIDTH // 2, 90))
                surface.blit(bg, rect)
                if isinstance(glow, pg.Surface):
                    surface.blit(glow, glow.get_rect(midright=(rect.left + 8, rect.centery)))
                surface.blit(toast, toast.get_rect(center=rect.center))
            else:
                self.toast = ""
