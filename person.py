import gym, numpy as np
import  pygame

class WorldEnvironment(gym.Env):
    def __init__(self, terrain_world):
        self.action_space = gym.spaces.Discrete(4)
        self.observation_space = gym.spaces.Box(low=0, high=255, shape=(84, 84, 1), dtype=np.uint8)

        self.position = (0, 0)
        self.fov = 10
        self.terrain_world = terrain_world

    def step(self, action):
        # get a matrix of the terrain
        terrain_matrix = np.matrix(np.zeros((self.fov, self.fov)))

        # actions: 0 = up, 1 = down, 2 = left, 3 = right
        if action == 0:
            # if the action is up, move the player up
            self.position = (self.position[0], self.position[1] - 1)
            # if the player is hitting the terrain, move the player back down
            if self.terrain_world.get_terrain_at(self.position[0], self.position[1]) != "air":
                self.position = (self.position[0], self.position[1] + 1)
                reward = -1
            # reward
            reward = 1
        elif action == 1:
            # if the action is down, move the player down
            self.position = (self.position[0], self.position[1] + 1)
            # if the player is hitting the terrain, move the player back up
            if self.terrain_world.get_terrain_at(self.position[0], self.position[1]) != "air":
                self.position = (self.position[0], self.position[1] - 1)
                reward = -1
            # reward
            reward = 1
        elif action == 2:
            # if the action is left, move the player left
            self.position = (self.position[0] - 1, self.position[1])
            # if the player is hitting the terrain, move the player back right
            if self.terrain_world.get_terrain_at(self.position[0], self.position[1]) != "air":
                self.position = (self.position[0] + 1, self.position[1])
                reward = -1
            # reward
            reward = 1
        elif action == 3:
            # if the action is right, move the player right
            self.position = (self.position[0] + 1, self.position[1])
            # if the player is hitting the terrain, move the player back left
            if self.terrain_world.get_terrain_at(self.position[0], self.position[1]) != "air":
                self.position = (self.position[0] - 1, self.position[1])
                reward = -1
            # reward
            reward = 1

    def reset(self):
        pass

class Boxlander:
    def __init__(self, name, parent):
        self.parent = parent
        self.name = name
        self.FOV = 10
        self.env = WorldEnvironment(self.parent)
        self.actions = [
            "move_left",
            "move_right",
            "move_up",
            "move_down",
        ]

        self.action_map = {
            "move_left": 0,
            "move_right": 1,
            "move_up": 2,
            "move_down": 3,
        }

    def render(self, window):
        pygame.draw.rect(window, (255, 255, 255), (self.env.position[0] - self.FOV, self.env.position[1] - self.FOV, self.FOV * 2, self.FOV * 2))
        self.env.step()
