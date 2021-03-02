import pygame as pg
import os
import neat
import random

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
GREEN_COLOR = (159, 188, 77)
CACTUS_SPAWN_RATE = 1000
CACTUS_MOVEMENT_SPEED = -0.8
JUMP_HEIGHT = 150
JUMP_FORCE = 0.9

class Sprite():
	def __init__(self, x, y, image):
		self.x = x
		self.y = y
		self.image = image
		self.debug_draw = False

	def set_debug_draw(self, debug_draw):
		self.debug_draw = debug_draw

	def draw(self, window):
		window.blit(self.image, (self.x, self.y))
		if self.debug_draw:
			pg.draw.rect(window, (255, 0, 0), self.rect(), 3)

	def width(self):
		return self.image.get_width()

	def height(self):
		return self.image.get_height()

	def rect(self):
		image_rect = self.image.get_rect()
		return pg.Rect(self.x, self.y, image_rect.width, image_rect.height)


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
		self.collision_rect = None
		self.x_offset = 0
		self.y_offset = 0
		self.rect_width = 0
		self.rect_height = 0

	def set_collision_rect(self, rect_width, rect_height, x_offset, y_offset):
		self.rect_width = rect_width
		self.rect_height = rect_height
		self.x_offset = x_offset
		self.y_offset = y_offset

	
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

	def rect(self):
		return pg.Rect(self.x + self.x_offset, self.y + self.y_offset, self.rect_width, self.rect_height)

	def draw(self, window):
		window.blit(self.image, (self.x, self.y), area = self.current_animation[self.animation_index])
		if self.debug_draw:
			pg.draw.rect(window, (255, 0, 0), self.rect(), 3)


class ParallaxSprite(Sprite):
	def __init__(self, x, y, image, horizontal_speed):
		Sprite.__init__(self, x, y, image)
		self.horizontal_speed = horizontal_speed

	def update(self, dt):
		self.x += self.horizontal_speed * dt

class Dinosaur():

	def __init__(self, x, y, color):
		self.sprite = AnimatedSprite(x, y, pg.image.load(os.path.join("assets", "dinosaur_" + color + ".png")), 72, 72)
		self.sprite.set_collision_rect(40, 40, 30, 10)
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

	def has_collided(self, cactus):
		if self.sprite.rect().colliderect(cactus.rect()):
			return True
		return False

	def jump(self):
		# Only allow jumping when grounded
		if self.is_grounded:
			self.is_grounded = False
			self.is_jumping = True

	def set_debug_draw(self, debug_draw):
		self.sprite.set_debug_draw(debug_draw)

	def draw(self, window):
		self.sprite.draw(window)
		if self.sprite.debug_draw:
			pg.draw.rect(window, (255, 0, 0), self.sprite.rect(), 3)



def run(genomes, config):
	# Setup PyGame
	pg.init()
	pg.font.init()

	debug_draw = False

	dinosaurs = []
	networks = []
	ge = []

	dinosaur_colors = ["green", "blue", "red", "yellow"]
	for _, g in genomes:
		network = neat.nn.FeedForwardNetwork.create(g, config)
		networks.append(network)
		random_color_index = random.randint(0, len(dinosaur_colors) - 1)
		color = dinosaur_colors[random_color_index]
		dinosaurs.append(Dinosaur(random.randint(0, 50), 260, color))
		g.fitness = 0
		ge.append(g)

	# Setup window
	window = pg.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT), 0)
	
	# Setup font
	font = pg.font.Font(os.path.join("assets", "game_font.ttf"), 16)

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

		# Check if any dinosaurs are still alive:
		if len(dinosaurs) <= 0:
			running = False

		# Check if we need to spawn a new cactus
		if spawn_timer > CACTUS_SPAWN_RATE:
			spawn_timer = 0
			new_cactus = ParallaxSprite(WINDOW_WIDTH, 250, pg.image.load(os.path.join("assets", "cactus_green.png")), CACTUS_MOVEMENT_SPEED)
			new_cactus.set_debug_draw(debug_draw)
			cacti.append(new_cactus)

		# Update objects
		cacti_to_delete = []
		for cactus in cacti:
			if cactus.x + cactus.width() < 0:
				cacti_to_delete.append(cactus)
			else:
				cactus.update(dt)
		floor.update(dt)
		floor_second.update(dt)

		for dinosaur in dinosaurs:
			dinosaur.update(dt)

		# Wrap the floor back if it leaves the screen
		if floor.x + floor.width()  < 0:
			floor.x = floor_second.x + floor_second.width()
		if floor_second.x + floor_second.width() < 0:
			floor_second.x = floor.x + floor.width()

		# Delete objects which are outside of the screen
		for cactus in cacti_to_delete:
			cacti.remove(cactus)

		# Check collissions
		if len(cacti) > 0:
			# We only ever need to check the collission with the cactus which is closest to the player (e.g the first one in the  list)
			for index, dinosaur in enumerate(dinosaurs): 
				if dinosaur.has_collided(cacti[0]):
					ge[index].fitness -= 0.05
					dinosaurs.pop(index)
					networks.pop(index)
					ge.pop(index)
				elif dinosaur.sprite.x < cacti[0].x + cacti[0].width():
					ge[index].fitness += 0.1


		# Process events
		for event in pg.event.get():
			if event.type == pg.QUIT:
				running = False
				pg.quit()
				quit()
			# Spacebar to jump
			if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
				dinosaur.jump()

			# Enable debug draw
			if event.type == pg.KEYDOWN and event.key == pg.K_d:
				# Toggle Debug Draw
				debug_draw = not debug_draw
				for dinosaur in dinosaurs:
					dinosaur.set_debug_draw(debug_draw)
				for cactus in cacti:
					cactus.set_debug_draw(debug_draw)

		# Run NEAT
		if len(cacti) > 0:
			for index, dinosaur in enumerate(dinosaurs):
				output = networks[index].activate((dinosaur.sprite.x, abs(dinosaur.sprite.x - cacti[0].x)))

				if output[0] > 0.5:
					dinosaur.jump()

		# Draw
		window.fill((255, 255, 255))
		current_time_text = font.render(str(game_timer), 0, (0, 0, 0))
		debug_draw_text = font.render("Press d to toggle debug draw mode", 0, (0, 0, 0))

		window.blit(current_time_text, (WINDOW_WIDTH - current_time_text.get_width() - 10, 10))
		window.blit(debug_draw_text, (WINDOW_WIDTH - debug_draw_text.get_width() - 10, 50))
		floor.draw(window)
		floor_second.draw(window)

		for cactus in cacti:
			cactus.draw(window)
		for dinosaur in dinosaurs:
			dinosaur.draw(window)
		pg.display.flip()

	pg.quit()

def main(config_path):
	config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

	population = neat.Population(config)
	population.add_reporter(neat.StdOutReporter(True))
	stats = neat.StatisticsReporter()
	population.add_reporter(stats)

	winner = population.run(run, 10)

if __name__ == "__main__":
	local_dir = os.path.dirname(__file__)
	config_path = os.path.join(local_dir, "config-feedforward.txt")
	main(config_path)