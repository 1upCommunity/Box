import gym, numpy as np
import  pygame, pymunk, logging, math, random

# get all loggers
logging.basicConfig(level=logging.ERROR)

class WorldEnvironment(gym.Env):
    def __init__(self, terrain_world, parent):
        self.action_space = gym.spaces.Discrete(13)
        self.observation_space = gym.spaces.Box(low=0, high=255, shape=(84, 84, 1), dtype=np.uint8)

        self.velocity = (0, 0)
        self.position = (0, 0)
        self.terrain_world = terrain_world
        self.parent = parent

        self.inventory = []
        self.time_lapsed = 0

    def play_sound(self):
        # play self.parent.parent.parent.assets.get("coin.wav")
        sound = self.parent.parent.parent.textures.get("coin.wav")
        pygame.mixer.Sound.play(sound)

    def step(self, action):
        # get a matrix of the terrain and store it in the observation space
        try:
            observation = self.parent.parent.get_terrain_matrix(self.position, fov=25)
            # convert all strings to hash values
            observation = np.array(observation, dtype=np.uint8)
            observation = observation.reshape((25*2+1, 25*2+1, 1))
        
            if action > 8 and action < 13 and random.randint(0, 10) == 0:
                self.play_sound()

        except Exception as e:
            print(e)

        self.time_lapsed += 1
        reward = 0
        if action == 0:
            self.velocity = (self.velocity[0] + 40, self.velocity[1])
        elif action == 1:
            self.velocity = (self.velocity[0] - 40, self.velocity[1])
        elif action == 2:
            self.velocity = (self.velocity[0], self.velocity[1] - 400)

        
        elif action == 3:
            self.velocity = (self.velocity[0] + 40, self.velocity[1] - 400)
        elif action == 4:
            self.velocity = (self.velocity[0] - 40, self.velocity[1] - 400)

        elif action == 5:
            # break block above
            pos = int(self.position[0] / 32), int(self.position[1] / 32)
            block = self.parent.parent.remove_block(pos)
            if block is not None:
                self.inventory.append(block)
        elif action == 6:
            # break block below
            pos = int(self.position[0] / 32), int(self.position[1] / 32)
            block = self.parent.parent.remove_block((pos[0], pos[1] + 1))
            if block is not None:
                self.inventory.append(block)
        elif action == 7:
            # break block left
            pos = int(self.position[0] / 32), int(self.position[1] / 32)
            block = self.parent.parent.remove_block((pos[0]-1, pos[1]))
            if block is not None:
                self.inventory.append(block)
        elif action == 8:
            # break block right
            pos = int(self.position[0] / 32), int(self.position[1] / 32)
            block = self.parent.parent.remove_block((pos[0]+1, pos[1]))
            if block is not None:
                self.inventory.append(block)

        elif action == 9:
            # place block above
            try:
                pos = int(self.position[0] / 32), int(self.position[1] / 32)
                if len(self.inventory) > 0:
                    block = self.inventory.pop()
                    self.parent.parent.place_block(pos, block)
            except Exception as e:
                print(e)
        elif action == 10:
            # place block below
            try:
                pos = int(self.position[0] / 32), int(self.position[1] / 32)
                if len(self.inventory) > 0:
                    block = self.inventory.pop()
                    self.parent.parent.place_block((pos[0], pos[1] + 1), block)
            except Exception as e:
                print(e)
        elif action == 11:
            # place block left
            try:
                pos = int(self.position[0] / 32), int(self.position[1] / 32)
                if len(self.inventory) > 0:
                    block = self.inventory.pop()
                    self.parent.parent.place_block((pos[0]-1, pos[1]), block)
            except Exception as e:
                print(e)
        elif action == 12:
            # place block right
            try:
                pos = int(self.position[0] / 32), int(self.position[1] / 32)
                if len(self.inventory) > 0:
                    block = self.inventory.pop()
                    self.parent.parent.place_block((pos[0]+1, pos[1]), block)
            except Exception as e:
                print(e)
        
        if self.position[1] > 10000:
            reward += -100
            self.reset()
            print(f"[{self.parent.name}] fell off the world")

        # if the player is touching the box, give a reward
        try:
            reward += 100 * 1 / self.time_lapsed
        except Exception as e:
            print(e)

        # get distance to (0, 0)
        distance = math.dist((0, 0), self.position)
        if distance > 1000:
            reward += 1 * distance / 1000
        else:
            reward += -1 * distance / 1000

        # sort the inventory
        self.inventory = sorted(self.inventory, key=lambda x: x)

        return observation, reward, False, {}

    def reset(self):
        self.parent.reset()

class Boxlander:
    def __init__(self, name, parent):
        self.parent = parent
        self.name = name
        self.FOV = 10
        self.env = WorldEnvironment(self.parent, self)

        self.frame = 0

        self.body = pymunk.Body(1, 1)
        self.body.position = (0, 0)
        self.body.velocity = (0, 0)
        self.body.angle = 0

        self.shape = pymunk.Circle(self.body, 10)
        self.shape.collision_type = 1
        self.shape.color = (255, 255, 255)
        self.shape.elasticity = 0.95
        
        self.parent.space.add(self.body, self.shape)

    def reset(self):
        self.body.position = (0, 0)
        self.body.velocity = (0, 0)
        self.body.angle = 0
        self.frame = 0

    def render(self, window):
        if self.frame % 60 == 0:
            self.env.step(self.env.action_space.sample())
        # apply force
        # clamp velocity
        self.body.velocity = self.body.velocity[0] + self.env.velocity[0], self.body.velocity[1] + self.env.velocity[1]
        self.env.position = int(self.body.position[0]), int(self.body.position[1])
        self.env.velocity = (0, 0)

        #print(self.body.position)

        self.frame += 1

        pygame.draw.circle(window, (255, 255, 255), (int(self.body.position[0] - self.parent.parent.x), int(self.body.position[1]) - self.parent.parent.y), 10)
        # nametag
        font = pygame.font.SysFont("comicsansms", 20)
        text = font.render(self.name, True, (255, 255, 255))
        window.blit(text, (int(self.body.position[0] - self.parent.parent.x) - text.get_width() // 2, int(self.body.position[1]) - self.parent.parent.y + 32 - text.get_height() // 2))
