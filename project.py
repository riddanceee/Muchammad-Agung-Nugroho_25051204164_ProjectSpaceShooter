import pygame
import random
import sys
pygame.init()

SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS           = 60

WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)
RED     = (220,  50,  50)
GREEN   = (50,  200,  80)
BLUE    = (50,  120, 220)
YELLOW  = (255, 220,  50)
CYAN    = (50,  220, 220)
ORANGE  = (255, 140,   0)
GRAY    = (100, 100, 100)
PURPLE  = (180,  50, 220)
DKBLUE  = (10,   15,  40)

class GameObject:

    def __init__(self, x: float, y: float, width: int, height: int, color: tuple):
        self.x      = x
        self.y      = y
        self.width  = width
        self.height = height
        self.color  = color
        self.active = True

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen: pygame.Surface):
        pygame.draw.rect(screen, self.color, self.rect)

    def update(self):
        pass

    def is_colliding(self, other: "GameObject") -> bool:
        return self.active and other.active and self.rect.colliderect(other.rect)

class Star(GameObject):
    def __init__(self):
        x     = random.randint(0, SCREEN_WIDTH)
        y     = random.randint(0, SCREEN_HEIGHT)
        size  = random.randint(1, 3)
        speed = random.uniform(0.5, 2.0)
        color = random.choice([WHITE, CYAN, (200, 200, 255)])
        super().__init__(x, y, size, size, color)
        self.speed = speed

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT:
            self.y = 0
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, screen: pygame.Surface):
        pygame.draw.circle(screen, self.color,
                           (int(self.x), int(self.y)), max(1, self.width // 2))

class Bullet(GameObject):
    def __init__(self, x: float, y: float, speed: float, color: tuple, direction: int = -1):
        super().__init__(x - 3, y, 6, 14, color)
        self.speed     = speed
        self.direction = direction

    def update(self):
        self.y += self.speed * self.direction
        if self.y < -20 or self.y > SCREEN_HEIGHT + 20:
            self.active = False

    def draw(self, screen: pygame.Surface):
        rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        pygame.draw.ellipse(screen, self.color, rect)
        glow_rect = rect.inflate(4, 6)
        glow_surf = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
        glow_color = (*self.color[:3], 60)
        pygame.draw.ellipse(glow_surf, glow_color, glow_surf.get_rect())
        screen.blit(glow_surf, glow_rect.topleft)

class Player(GameObject):
    def __init__(self):
        w, h = 48, 48
        x = SCREEN_WIDTH  // 2 - w // 2
        y = SCREEN_HEIGHT - h - 20
        super().__init__(x, y, w, h, CYAN)

        self.speed         = 5
        self.hp            = 3
        self.max_hp        = 3
        self.score         = 0
        self.bullets: list = []
        self.shoot_cooldown = 0
        self.shoot_delay    = 18
        self.invincible     = 0

    def draw(self, screen: pygame.Surface):
        cx = int(self.x + self.width  // 2)
        cy = int(self.y + self.height // 2)

        body = [
            (cx,          int(self.y)),
            (cx + 22,     int(self.y + 42)),
            (cx + 10,     int(self.y + 30)),
            (cx,          int(self.y + 38)),
            (cx - 10,     int(self.y + 30)),
            (cx - 22,     int(self.y + 42)),
        ]
        if self.invincible % 6 < 3:
            pygame.draw.polygon(screen, CYAN,  body)
            pygame.draw.polygon(screen, WHITE, body, 2)

        if random.random() > 0.4:
            flame_h = random.randint(8, 18)
            flame = [
                (cx - 6,  int(self.y + 40)),
                (cx + 6,  int(self.y + 40)),
                (cx,      int(self.y + 40 + flame_h)),
            ]
            pygame.draw.polygon(screen, YELLOW, flame)
            pygame.draw.polygon(screen, ORANGE, flame, 1)

        for b in self.bullets:
            b.draw(screen)

    def update(self, keys):
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.x > 0:
            self.x -= self.speed
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed
        if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.y > 0:
            self.y -= self.speed
        if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.y < SCREEN_HEIGHT - self.height:
            self.y += self.speed

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if keys[pygame.K_SPACE] and self.shoot_cooldown == 0:
            self._shoot()

        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.active]

        if self.invincible > 0:
            self.invincible -= 1

    def _shoot(self):
        bx = self.x + self.width  // 2
        by = self.y
        self.bullets.append(Bullet(bx, by, speed=9, color=CYAN))
        self.shoot_cooldown = self.shoot_delay

    def take_damage(self):
        if self.invincible == 0:
            self.hp -= 1
            self.invincible = 80

class Enemy(GameObject):

    def __init__(self, x: float, y: float, width: int, height: int,
                 color: tuple, speed: float, hp: int, score_val: int):
        super().__init__(x, y, width, height, color)
        self.speed      = speed
        self.hp         = hp
        self.score_val  = score_val
        self.bullets: list = []
        self.shoot_timer   = random.randint(60, 180)

    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT + 10:
            self.active = False

        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self._shoot()
            self.shoot_timer = random.randint(90, 200)

        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.active]

    def _shoot(self):
        bx = self.x + self.width  // 2
        by = self.y + self.height
        self.bullets.append(Bullet(bx, by, speed=4, color=RED, direction=1))

    def take_damage(self, dmg: int = 1):
        self.hp -= dmg
        if self.hp <= 0:
            self.active = False

    def draw(self, screen: pygame.Surface):
        cx = int(self.x + self.width // 2)
        body = [
            (cx,                    int(self.y + self.height)),
            (int(self.x),           int(self.y)),
            (int(self.x + self.width), int(self.y)),
        ]
        pygame.draw.polygon(screen, self.color, body)
        pygame.draw.polygon(screen, WHITE, body, 1)

        bar_w = self.width
        bar_h = 4
        bx    = int(self.x)
        by    = int(self.y) - 8
        pygame.draw.rect(screen, GRAY, (bx, by, bar_w, bar_h))
        filled = int(bar_w * (self.hp / self._max_hp()))
        pygame.draw.rect(screen, GREEN, (bx, by, filled, bar_h))

        for b in self.bullets:
            b.draw(screen)

    def _max_hp(self):
        return 1

class FastEnemy(Enemy):
    def __init__(self, x: float, y: float):
        super().__init__(x, y,
                         width=32, height=32,
                         color=YELLOW,
                         speed=random.uniform(2.5, 4.0),
                         hp=1,
                         score_val=10)

    def _max_hp(self):
        return 1

    def draw(self, screen: pygame.Surface):
        cx = int(self.x + self.width  // 2)
        cy = int(self.y + self.height // 2)
        pts = [
            (cx,              int(self.y)),
            (int(self.x + self.width), cy),
            (cx,              int(self.y + self.height)),
            (int(self.x),    cy),
        ]
        pygame.draw.polygon(screen, YELLOW, pts)
        pygame.draw.polygon(screen, WHITE,  pts, 1)

        for b in self.bullets:
            b.draw(screen)

class TankEnemy(Enemy):
    MAX_HP = 5

    def __init__(self, x: float, y: float):
        super().__init__(x, y,
                         width=56, height=48,
                         color=PURPLE,
                         speed=random.uniform(0.8, 1.5),
                         hp=TankEnemy.MAX_HP,
                         score_val=50)

    def _max_hp(self):
        return TankEnemy.MAX_HP

    def draw(self, screen: pygame.Surface):
        rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        pygame.draw.rect(screen, PURPLE, rect, border_radius=6)
        pygame.draw.rect(screen, WHITE,  rect, 2, border_radius=6)

        cx = int(self.x + self.width  // 2)
        cy = int(self.y + self.height // 2)
        pygame.draw.line(screen, WHITE, (cx - 10, cy), (cx + 10, cy), 2)
        pygame.draw.line(screen, WHITE, (cx, cy - 10), (cx, cy + 10), 2)

        bar_w = self.width
        bar_h = 5
        bx    = int(self.x)
        by    = int(self.y) - 10
        pygame.draw.rect(screen, GRAY,  (bx, by, bar_w, bar_h))
        filled = int(bar_w * (self.hp / TankEnemy.MAX_HP))
        pygame.draw.rect(screen, ORANGE, (bx, by, filled, bar_h))

        for b in self.bullets:
            b.draw(screen)

class Game:
    def __init__(self):
        self.screen  = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("⭐ Space Shooter — PBO Demo")
        self.clock   = pygame.time.Clock()

        self.font_big   = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_med   = pygame.font.SysFont("consolas", 28)
        self.font_small = pygame.font.SysFont("consolas", 20)

        self._reset()

    def _reset(self):
        self.player   = Player()
        self.enemies: list  = []
        self.stars: list    = [Star() for _ in range(120)]
        self.state          = "playing"
        self.wave           = 1
        self.wave_timer     = 0
        self.wave_interval  = 300
        self.total_killed   = 0
        self.win_score      = 500

    def run(self):
        while True:
            self._handle_events()

            if self.state == "playing":
                keys = pygame.key.get_pressed()
                self._update(keys)

            self._draw()
            self.clock.tick(FPS)

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.state != "playing":
                    self._reset()
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

    def _update(self, keys):
        for s in self.stars:
            s.update()

        self.player.update(keys)

        self.wave_timer += 1
        if self.wave_timer >= self.wave_interval:
            self._spawn_wave()
            self.wave_timer = 0
            self.wave += 1

        for e in self.enemies:
            e.update()

        self.enemies = [e for e in self.enemies if e.active]

        for bullet in self.player.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.is_colliding(enemy):
                    bullet.active = False
                    enemy.take_damage(1)
                    if not enemy.active:
                        self.player.score += enemy.score_val
                        self.total_killed += 1

        for enemy in self.enemies:
            for bullet in enemy.bullets[:]:
                if bullet.is_colliding(self.player):
                    bullet.active = False
                    self.player.take_damage()

            if enemy.is_colliding(self.player):
                self.player.take_damage()
                enemy.active = False

        if self.player.hp <= 0:
            self.state = "game_over"
        if self.player.score >= self.win_score:
            self.state = "win"

    def _spawn_wave(self):
        count = min(3 + self.wave, 10)
        for _ in range(count):
            x = random.randint(20, SCREEN_WIDTH - 60)
            y = random.randint(-100, -20)
            r = random.random()
            if r < 0.55:
                self.enemies.append(FastEnemy(x, y))
            elif r < 0.85:
                self.enemies.append(Enemy(x, y,
                                          width=40, height=36,
                                          color=GREEN,
                                          speed=random.uniform(1.5, 2.5),
                                          hp=2, score_val=20))
            else:
                self.enemies.append(TankEnemy(x, y))

    def _draw(self):
        self.screen.fill(DKBLUE)
        for s in self.stars:
            s.draw(self.screen)

        if self.state == "playing":
            for e in self.enemies:
                e.draw(self.screen)

            self.player.draw(self.screen)

            self._draw_hud()

        elif self.state == "game_over":
            self._draw_overlay("GAME OVER", RED, "Tekan R untuk main lagi")

        elif self.state == "win":
            self._draw_overlay("YOU WIN! ", YELLOW, "Tekan R untuk main lagi")

        pygame.display.flip()

    def _draw_hud(self):

        score_surf = self.font_med.render(f"SCORE: {self.player.score}", True, WHITE)
        self.screen.blit(score_surf, (10, 10))

        wave_surf = self.font_small.render(f"Wave: {self.wave}", True, CYAN)
        self.screen.blit(wave_surf, (10, 42))

        target_surf = self.font_small.render(f"Target: {self.win_score}", True, GRAY)
        self.screen.blit(target_surf, (10, 62))

        hp_x = SCREEN_WIDTH - 160
        hp_surf = self.font_med.render("HP:", True, WHITE)
        self.screen.blit(hp_surf, (hp_x, 10))
        for i in range(self.player.max_hp):
            color = RED if i < self.player.hp else GRAY
            pygame.draw.rect(self.screen, color,
                             (hp_x + 50 + i * 35, 12, 28, 22), border_radius=4)

        ctrl = self.font_small.render("Arrow/WASD: Gerak   SPACE: Tembak", True, GRAY)
        self.screen.blit(ctrl, (SCREEN_WIDTH // 2 - ctrl.get_width() // 2,
                                SCREEN_HEIGHT - 24))

    def _draw_overlay(self, title: str, color: tuple, subtitle: str):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        t  = self.font_big.render(title, True, color)
        s1 = self.font_med.render(f"Skor Akhir: {self.player.score}", True, WHITE)
        s2 = self.font_small.render(subtitle, True, CYAN)
        s3 = self.font_small.render("ESC: Keluar", True, GRAY)

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2
        self.screen.blit(t,  (cx - t.get_width()  // 2, cy - 100))
        self.screen.blit(s1, (cx - s1.get_width() // 2, cy - 30))
        self.screen.blit(s2, (cx - s2.get_width() // 2, cy + 20))
        self.screen.blit(s3, (cx - s3.get_width() // 2, cy + 55))

if __name__ == "__main__":
    game = Game()
    game.run()
