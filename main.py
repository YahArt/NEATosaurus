import pygame as pg
import os

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
GREEN_COLOR = (159, 188, 77)
CACTUS_SPAWN_RATE = 3000
CACTUS_MOVEMENT_SPEED = -0.3
JUMP_HEIGHT = 150
JUMP_FORCE = 0.6

class Sprite():
	def __init__(self, x, y, image):
		self.x = x
		self.y = y
		self.image = image

	def draw(self, window):
		window.blit(self.image, (self.x, self.y))

	def width(self):
		return self.image.get_width()

	def height(self):
		return self.image.get_height()


class AnimatedSprite(Sprite):
	def __init__(self, x, y, image, single_image_width, single_image_height):
		Sprite.__init__(self, x, y, image)
		self.single_image_width = single_image_width
		self.single_image_height = single_image_height
		self.animations = {}
		self.current_animation = []
		self.animation_duration = 0
		self.animation_index = 0
		self.animation_ticks = 0

	
	def create_animation_rectangles(self, surface, indices):
		animation_rects = []
		for index in indices:
			x = index * self.single_image_width
			y = 0
			rect = pg.Rect(x, y, self.single_image_width, self.single_image_height)
			animation_rects.append(rect)
		return animation_rects

	def add_animation(self, name, indices, animation_duration):
		self.animations[name] = {
			"rectangles": self.create_animation_rectangles(self.image, indices),
			"duration": animation_duration
		}

	def set_current_animation(self, name):
		self.current_animation = self.animations[name]["rectangles"]
		self.animation_duration = self.animations[name]["duration"]

	def update(self, dt):
		self.animation_ticks += dt
		if self.animation_ticks > self.animation_duration:
			self.animation_index += 1
			self.animation_ticks = 0
		if self.animation_index > len(self.current_animation) - 1:
			self.animation_index = 0

	def draw(self, window):
		window.blit(self.image, (self.x, self.y), area = self.current_animation[self.animation_index])

class ParallaxSprite(Sprite):
	def __init__(self, x, y, image, horizontal_speed):
		Sprite.__init__(self, x, y, image)
		self.horizontal_speed = horizontal_speed

	def update(self, dt):
		self.x += self.horizontal_speed * dt

class Dinosaur():

	def __init__(self, x, y):
		self.sprite = AnimatedSprite(x, y, pg.image.load(os.path.join("assets", "dinosaur_green.png")), 72, 72)
		self.sprite.add_animation("run", [17, 18, 19, 20], 125)
		self.sprite.set_current_animation("run")
		self.max_jump_height = self.sprite.y - JUMP_HEIGHT
		self.ground_pos = self.sprite.y
		self.is_grounded = True
		self.is_jumping = False
		self.is_falling = False

	def update(self, dt):
		# When we jump we actually need to subtract from your y position as the top left is 0/0
		if self.is_jumping and self.sprite.y > self.max_jump_height:
			self.sprite.y -= JUMP_FORCE * dt

		# Once we have reached our max jump height we fall
		elif self.sprite.y < self.max_jump_height and self.is_jumping:
			self.is_falling = True
			self.is_jumping = False

		# Fall for as long as we are not at our original ground position
		if self.is_falling and self.sprite.y < self.ground_pos:
			self.sprite.y += JUMP_FORCE * dt

		# Once we have reached our ground position stop falling
		if self.sprite.y >= self.ground_pos and self.is_falling:
			self.is_falling = False
			self.is_grounded = True
			self.sprite.y = self.ground_pos

		self.sprite.update(dt)

	def jump(self):
		# Only allow jumping when grounded
		if self.is_grounded:
			self.is_grounded = False
			self.is_jumping = True

	def draw(self, window):
		self.sprite.draw(window)


def run():
	# Setup PyGame
	pg.init()
	pg.font.init()

	# Setup window
	window = pg.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT), 0)
	
	# Setup font
	font = pg.font.Font(os.path.join("assets", "game_font.ttf"), 16)

	# Setup objects
	dinosaur = Dinosaur(0, 260)

	cacti = [ParallaxSprite(round(WINDOW_WIDTH * 0.8), 250, pg.image.load(os.path.join("assets", "cactus_green.png")), CACTUS_MOVEMENT_SPEED)]
	floor = ParallaxSprite(0, 300, pg.image.load(os.path.join("assets", "floor_green.png")), -0.1)
	floor_second = ParallaxSprite(floor.width(), 300, pg.image.load(os.path.join("assets", "floor_green.png")), -0.1)

	pg.display.set_caption("NEAToSaurus")
	clock = pg.time.Clock()
	spawn_timer = 0
	game_timer = 0
	running = True

	while running:
		clock.tick(60)
		dt = clock.get_time()
		spawn_timer += dt
		game_timer += dt

		# Check if we need to spawn a new cactus
		if spawn_timer > CACTUS_SPAWN_RATE:
			spawn_timer = 0
			cacti.append(ParallaxSprite(WINDOW_WIDTH, 250, pg.image.load(os.path.join("assets", "cactus_green.png")), CACTUS_MOVEMENT_SPEED))

		# Update objects
		cacti_to_delete = []
		for cactus in cacti:
			if cactus.x + cactus.width() < 0:
				cacti_to_delete.append(cactus)
			else:
				cactus.update(dt)
		floor.update(dt)
		floor_second.update(dt)
		dinosaur.update(dt)

		# Wrap the floor back if it leaves the screen
		if floor.x + floor.width()  < 0:
			floor.x = floor_second.x + floor_second.width()
		if floor_second.x + floor_second.width() < 0:
			floor_second.x = floor.x + floor.width()

		# Delete objects which are outside of the screen
		for cactus in cacti_to_delete:
			cacti.remove(cactus)

		# Process events
		for event in pg.event.get():
			if event.type == pg.QUIT:
				running = False
			if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
				dinosaur.jump()

		# Draw
		window.fill((255, 255, 255))
		current_time_text = font.render(str(game_timer), 0, (0, 0, 0))

		window.blit(current_time_text, (WINDOW_WIDTH - current_time_text.get_width() - 10, 10))
		floor.draw(window)
		floor_second.draw(window)

		for cactus in cacti:
			cactus.draw(window)
		dinosaur.draw(window)
		pg.display.flip()

	pg.quit()



if __name__ == "__main__":
	run()