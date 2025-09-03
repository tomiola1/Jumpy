import pygame
import random
from settings import *
from sprites import *
from os import path

#vid 17 - using collisions masks to improve and make "pixel perfect" collisions

#pg.sprite.collide_rect() - AABB (Acis-aligned Bounding Box)
#pg.sprite.collie_circle() - Circular Bound Box

#vid 18 - scrolling background (clouds)

class Game:
    def __init__(self):
        # initialize game window
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.font_name = pygame.font.match_font(FONT_NAME)
        self.load_data()

    def load_data(self):
        # load high score
        self.dir = path.dirname(__file__)
        with open(path.join(self.dir, HS_FILE), 'r') as f:
            try:
                self.highscore = int(f.read())
            except:
                self.highscore = 0
        # load spritesheet image
        img_dir = path.join(self.dir, 'img')
        self.spritesheet = Spritesheet(path.join(img_dir, SPRITESHEET))
        #cloud images
        self.cloud_images = []
        for i in range(1, 4):
            self.cloud_images.append(pygame.image.load(path.join(img_dir, 'cloud{}.png'.format(i))).convert())


    def new(self):
        # start a new game
        self.score = 0
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.platforms = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.mobs = pygame.sprite.Group()
        self.clouds = pygame.sprite.Group()
        self.player = Player(self) #instansiation - a new player
        for plat in PLATFORM_LIST:
            Platform(self, *plat)
        self.mob_timer = 0 #keeps track of last spawned enemy to spawn another
        for i in range(5): #this spawns a few clouds on our start screen
            c = Cloud(self)
            c.rect.y += 150 #reset the y of the cloud because they spawn off the top of the screen
        self.run()

    def run(self):
        #main game loop
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()

    def update(self):
        # game loop - update
        self.all_sprites.update()

        #spawn a mob/enemy
        now = pygame.time.get_ticks()
        if now - self.mob_timer > 5000 + random.choice([-1000, -500, 0, 500, 1000]):
            self.mob_timer = now
            Mob(self)

        # check if player hits/lands on a platform (only if falling)
        if self.player.vel.y > 0:
            hits = pygame.sprite.spritecollide(self.player, self.platforms, False)
            if hits:
                lowest = hits[0]
                for hit in hits:
                    if hit.rect.bottom > lowest.rect.bottom:
                        lowest = hit
                #improved platform collision - stops player "floating" beside platform due to hitboxes
                if self.player.pos.x < lowest.rect.right + 10 and \
                        self.player.pos.x > lowest.rect.left - 10:
                    if self.player.pos.y < lowest.rect.centery:
                        self.player.pos.y = lowest.rect.top
                        self.player.vel.y = 0
                        self.player.jumping = False

        # if player reaches a certain part of screen, scroll window
        if self.player.rect.top <= HEIGHT / 4:
            if random.randrange(100) < 15:
                Cloud(self)
            self.player.pos.y += max(abs(self.player.vel.y), 2)
            for cloud in self.clouds:
                cloud.rect.y += max(abs(self.player.vel.y / 2), 2)
            for mob in self.mobs:
                mob.rect.y += max(abs(self.player.vel.y), 2)
            for plat in self.platforms:
                plat.rect.y += max(abs(self.player.vel.y), 2)
                if plat.rect.top >= HEIGHT:
                    plat.kill()
                    self.score += 10

        # if player hits powerup
        pow_hits = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for pow in pow_hits:
            if pow.type == 'boost':
                self.player.vel.y = -BOOST_POWER
                self.player.jumping = False

        #if player hits an enemy/mob
        mob_hits = pygame.sprite.spritecollide(self.player, self.mobs, False, pygame.sprite.collide_mask)
        if mob_hits:
            self.playing = False

        #if player dies/falls off screen
        if self.player.rect.bottom > HEIGHT:
            for sprite in self.all_sprites:
                sprite.rect.y -= max(self.player.vel.y, 10)
                if sprite.rect.bottom < 0:
                    sprite.kill()
        if len(self.platforms) == 0:
            self.playing = False

        #spawn new platforms to replace killed ones
        while len(self.platforms) < 6:
            width = random.randrange(50, 100)
            Platform(self, random.randrange(0, WIDTH - width),
                     random.randrange(-75, -30))

    def events(self):
        #game loop - events
        for event in pygame.event.get():
            #check for closing window
            if event.type == pygame.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.player.jump()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    self.player.jump_cut()

    def draw(self):
        #game loop - draw
        self.screen.fill(BGCOLOR)
        self.all_sprites.draw(self.screen)
        self.draw_text(str(self.score), 22, WHITE, WIDTH / 2, 15)
        #after drawing everything, flip the display
        pygame.display.flip()

    def show_start_screen(self):
        #game splash/start screen
        self.screen.fill(BGCOLOR)
        self.draw_text(TITLE, 48, WHITE, WIDTH / 2, HEIGHT / 4)
        self.draw_text("Left and right arrows to move!", 22, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text("Long press space bar for a bigger jump!", 22, WHITE, WIDTH / 2, HEIGHT * 2 / 3.5)
        self.draw_text("Press s to change settings...", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
        self.draw_text("OR press a key to play!", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 3.7)
        self.draw_text("High Score: " + str(self.highscore), 22, WHITE, WIDTH / 2, 15)
        pygame.display.flip()
        self.wait_for_key()

    def show_settings(self):
        self.screen.fill()

    def show_go_screen(self):
        #game over/continue
        if not self.running:
            return
        self.screen.fill(BGCOLOR)
        self.draw_text("GAME OVER :(", 48, WHITE, WIDTH / 2, HEIGHT / 4)
        self.draw_text("Score: " + str(self.score), 22, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text("Press a key to play again...", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
        if self.score > self.highscore:
            self.highscore = self.score
            self.draw_text("NEW HIGH SCORE!", 22, WHITE, WIDTH / 2, HEIGHT / 2 + 40)
            with open(path.join(self.dir, HS_FILE), 'w') as f:
                f.write(str(self.score))
        else:
            self.draw_text("High Score: " + str(self.highscore), 22, WHITE, WIDTH / 2, HEIGHT / 2 + 40)
        pygame.display.flip()
        self.wait_for_key()


    def wait_for_key(self):
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False #makes the whole program end
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        waiting = False


    def draw_text(self, text, size, color, x, y):
        font = pygame.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)

g = Game() #an example of instantation - creatign a new object
g.show_start_screen()
while g.running:
    g.new()
    g.show_go_screen()

pygame.quit()

