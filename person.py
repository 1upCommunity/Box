import gym, numpy as np
import  pygame, pymunk, logging, math, random

# get all loggers
logging.basicConfig(level=logging.ERROR)

class QTable:
    def __init__(self, env):
        self.env = env

        self._init = False

        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 0.1

    def choose_action(self, state):
        try:
            if self._init:
                if random.randint(0, 100) > self.epsilon * 100 - 50:
                    return self.env.action_space.sample()
                else:
                    return np.argmax(self.table[state])
        except Exception as e:
            print(e)
            return self.env.action_space.sample()

    def update(self, state, action, reward, next_state):
        if not self._init:
            _ = len(np.array(self.env.get_observation()).flatten())
            self.table = np.zeros([_, self.env.action_space.n])
            self._init = True
        self.table[state][action] = (1 - self.alpha) * self.table[state][action] + self.alpha * (reward + self.gamma * np.max(self.table[next_state]))

    def get_table(self):
        if self._init:
            return self.table

class WorldEnvironment(gym.Env):
    def __init__(self, terrain_world, parent):
        self.action_space = gym.spaces.Discrete(15)
        self.observation_space = gym.spaces.Box(low=0, high=255, shape=(84, 84, 1), dtype=np.uint8)

        self.velocity = (0, 0)
        self.position = (0, 0)
        self.terrain_world = terrain_world
        self.parent = parent

        self.inventory = []
        self.scheduled_rewards = []
        self.time_lapsed = 0
        self.health = 100

        self.qtable = QTable(self)
        self.observation = self.get_observation()

    def play_sound(self):
        # play self.parent.parent.parent.assets.get("coin.wav")
        sound = self.parent.parent.parent.textures.get("coin.wav")
        pygame.mixer.Sound.play(sound)

    def get_observation(self):
        _ = int(self.position[0] / 32), int(self.position[1] / 32)
        observation = self.parent.parent.get_terrain_matrix(_, fov=25)
        # convert dict to numpy array
        observation = np.array(list(observation.values()), dtype=np.uint8)
        self.observation = observation
        # add health to observation
        observation = np.append(observation, np.array([self.health]))
        return observation

    def step(self, action):
        self.position = self.parent.body.position
        if action is not None:
            if action > 8 and action < 13 and random.randint(0, 10) == 0:
                self.play_sound()

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
                pass
        elif action == 10:
            # place block below
            try:
                pos = int(self.position[0] / 32), int(self.position[1] / 32)
                if len(self.inventory) > 0:
                    block = self.inventory.pop()
                    self.parent.parent.place_block((pos[0], pos[1] + 1), block)
            except Exception as e:
                pass
        elif action == 11:
            # place block left
            try:
                pos = int(self.position[0] / 32), int(self.position[1] / 32)
                if len(self.inventory) > 0:
                    block = self.inventory.pop()
                    self.parent.parent.place_block((pos[0]-1, pos[1]), block)
            except Exception as e:
                pass
        elif action == 12:
            # place block right
            try:
                pos = int(self.position[0] / 32), int(self.position[1] / 32)
                if len(self.inventory) > 0:
                    block = self.inventory.pop()
                    self.parent.parent.place_block((pos[0]+1, pos[1]), block)
            except Exception as e:
                pass

        # 13, 14: attack left, right
        elif action == 13:
            pos = int(self.position[0] / 32), int(self.position[1] / 32)
            _ = self.parent.parent.attack((pos[0]-1, pos[1]))
            if _ == None:
                reward -= 10
            else:
                print(f'{_} was attacked by {self.parent.name}')
        elif action == 14:
            pos = int(self.position[0] / 32), int(self.position[1] / 32)
            _ = self.parent.parent.attack((pos[0]+1, pos[1]))
            if _ == None:
                reward -= 10
            else:
                print(f'{_} was attacked by {self.parent.name}')
        
        if self.position[1] > 10000:
            reward += -100
            self.reset()
            print(f"[{self.parent.name}] fell off the world")

        if len(self.scheduled_rewards) > 0:
            reward += self.scheduled_rewards.pop(0)

        reward += 100 * 1 / self.time_lapsed

        # get distance to (0, 0)
        distance = math.dist((0, 0), self.position)
        if distance > 1000:
            reward += 1 * distance / 1000
        else:
            reward += -1 * distance / 1000

        # If a block exists at the player's position, the player is suffocated
        if self.parent.parent.get_terrain_at(self.position) != 0:
            reward += -100
            self.reset()
            print(f"[{self.parent.name}] suffocated at {self.position}")

        # sort the inventory
        self.inventory = sorted(self.inventory, key=lambda x: x)
        observation = self.get_observation()

        # Health is 0 if the player is dead
        if self.health <= 0:
            reward += -100
            self.reset()

        # give reward for maintaining health
        reward += (self.health - 50) * 0.1

        self.qtable.update(self.observation, action, reward, self.qtable.choose_action(self.get_observation()))
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
        self.previous_velocity = (0, 0)
        
        self.parent.space.add(self.body, self.shape)
        self.collision_handler = self.parent.space.add_collision_handler(1, 1)
        self.collision_handler.begin = self.begin_collision

    def begin_collision(self, arbiter, space, data):
        # if the collision normal is pointing down, the player was hit by a block
        # Score the damage based of self.env.velocity
        if self.shape in arbiter.shapes:
            if arbiter.normal[1] > 0.8 and self.previous_velocity[1] < 1.2:
                self.env.health += self.previous_velocity[1]/100
                if self.previous_velocity[1]/100 > 0.01:
                    print(f'[{self.name}] fall damage: {-self.body.velocity[1]/10}')
                    self.env.scheduled_rewards.append(self.previous_velocity[1])
        return True

    def reset(self):
        self.body.position = (0, 0)
        self.body.velocity = (0, 0)
        self.body.angle = 0
        self.frame = 0
        self.health = 100

    def render(self, window):
        if self.frame % 60 == 0:
            self.env.step(self.env.qtable.choose_action(self.env.get_observation()))
        # apply force
        # clamp velocity
        self.body.velocity = self.body.velocity[0] + self.env.velocity[0], self.body.velocity[1] + self.env.velocity[1]
        self.env.velocity = (0, 0)
        self.env.position = self.body.position

        self.frame += 1

        # if the current body velocity is not 0, set the previous velocity to the current body velocity
        if self.body.velocity[0] != 0 and self.body.velocity[1] != 0:
            self.previous_velocity = self.body.velocity

        pygame.draw.circle(window, (255, 255, 255), (int(self.body.position[0] - self.parent.parent.x), int(self.body.position[1]) - self.parent.parent.y), 10)
        # nametag
        font = pygame.font.SysFont("comicsansms", 20)
        text = font.render(self.name, True, (255, 255, 255))
        window.blit(text, (int(self.body.position[0] - self.parent.parent.x) - text.get_width() // 2, int(self.body.position[1]) - self.parent.parent.y + 32 - text.get_height() // 2))
        # draw health bar
        pygame.draw.rect(window, (255, 255, 255), (int(self.body.position[0] - self.parent.parent.x) - 10, int(self.body.position[1]) - self.parent.parent.y - 32, 20, 10))
        color = (0, 255, 0) if self.env.health > 75 else (255, 255, 0) if self.env.health > 50 else (255, 0, 0)
        pygame.draw.rect(window, color, (int(self.body.position[0] - self.parent.parent.x) - 10, int(self.body.position[1]) - self.parent.parent.y - 32, 20 * self.env.health / 100, 10))
