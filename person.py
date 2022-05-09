import time
import gym, numpy as np
import  pygame, pymunk, logging, math, random
# imports for DQNAgent
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout, Conv2D, MaxPooling2D, Activation, Flatten
from tensorflow.keras.optimizers import Adam
from keras.callbacks import TensorBoard
import tensorflow as tf
from collections import deque
import time
import random
import os

# Hide GPU from visible devices
tf.config.set_visible_devices([], 'GPU')

DISCOUNT = 0.99
REPLAY_MEMORY_SIZE = 50_000  # How many last steps to keep for model training
MIN_REPLAY_MEMORY_SIZE = 1_000  # Minimum number of steps in a memory to start training
MINIBATCH_SIZE = 64  # How many steps (samples) to use for training
UPDATE_TARGET_EVERY = 5  # Terminal states (end of episodes)
MODEL_NAME = 'BOX'

# Exploration settings
ELIPSON_DECAY = 0.099975
MIN_EPSILON = 0.001

# For stats
ep_rewards = [-200]

# For more repetitive results
random.seed(1)
np.random.seed(1)

# Memory fraction, used mostly when training multiple agents
#gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=MEMORY_FRACTION)
#backend.set_session(tf.Session(config=tf.ConfigProto(gpu_options=gpu_options)))

# Create models folder
if not os.path.isdir('models'):
    os.makedirs('models')


# Own Tensorboard class
class ModifiedTensorBoard(TensorBoard):

    # Overriding init to set initial step and writer (we want one log file for all .fit() calls)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.step = 1
        self.writer = tf.summary.create_file_writer(self.log_dir)

    # Overriding this method to stop creating default log writer
    def set_model(self, model):
        pass

    # Overrided, saves logs with our step number
    # (otherwise every .fit() will start writing from 0th step)
    def on_epoch_end(self, epoch, logs=None):
        self.update_stats(**logs)

    # Overrided
    # We train for one batch only, no need to save anything at epoch end
    def on_batch_end(self, batch, logs=None):
        pass

    # Overrided, so won't close writer
    def on_train_end(self, _):
        pass

    # Custom method for saving own metrics
    # Creates writer, writes custom metrics and closes writer
    def update_stats(self, **stats):
        self._write_logs(stats, self.step)


# Agent class
class DQNAgent:
    def __init__(self, env):
        self.env = env

        # Main model
        self.model = self.create_model()

        # Target network
        self.target_model = self.create_model()
        self.target_model.set_weights(self.model.get_weights())

        # An array with last n steps for training
        self.replay_memory = deque(maxlen=REPLAY_MEMORY_SIZE)

        # Custom tensorboard object
        self.tensorboard = ModifiedTensorBoard(log_dir="logs/{}-{}".format(MODEL_NAME, int(time.time())))

        # Used to count when to update target network with main network's weights
        self.target_update_counter = 0

    def create_model(self,):
        model = Sequential()

        observation_space = 60000, np.array(self.env.observation).shape[0], np.array(self.env.observation).shape[1], 1
        action_space = self.env.action_space.n

        model.add(Conv2D(32, (3, 3), activation='relu', input_shape=observation_space[1:]))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.2))

        model.add(Conv2D(256, (3, 3)))
        model.add(Activation('relu'))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.2))

        model.add(Flatten())  # this converts our 3D feature maps to 1D feature vectors
        model.add(Dense(64))

        model.add(Dense(action_space, activation='linear'))  # ACTION_SPACE_SIZE = how many choices (9)
        model.compile(loss="mse", optimizer=Adam(lr=0.001), metrics=['accuracy'])
        return model

    # Adds step's data to a memory replay array
    # (observation space, action, reward, new observation space, done)
    def update_replay_memory(self, transition):
        self.replay_memory.append(transition)

    # Trains main network every step during episode
    def train(self, terminal_state, step):

        # Start training only if certain number of samples is already saved
        if len(self.replay_memory) < MIN_REPLAY_MEMORY_SIZE:
            return

        # Get a minibatch of random samples from memory replay table
        minibatch = random.sample(self.replay_memory, MINIBATCH_SIZE)

        # Get current states from minibatch, then query NN model for Q values
        current_states = np.array([transition[0] for transition in minibatch])/255
        current_qs_list = self.model.predict(current_states)

        # Get future states from minibatch, then query NN model for Q values
        # When using target network, query it, otherwise main network should be queried
        new_current_states = np.array([transition[3] for transition in minibatch])/255
        future_qs_list = self.target_model.predict(new_current_states)

        X = []
        y = []

        # Now we need to enumerate our batches
        for index, (current_state, action, reward, new_current_state, done) in enumerate(minibatch):

            # If not a terminal state, get new q from future states, otherwise set it to 0
            # almost like with Q Learning, but we use just part of equation here
            if not done:
                max_future_q = np.max(future_qs_list[index])
                new_q = reward + DISCOUNT * max_future_q
            else:
                new_q = reward

            # Update Q value for given state
            current_qs = current_qs_list[index]
            current_qs[action] = new_q

            # And append to our training data
            X.append(current_state)
            y.append(current_qs)

        # Fit on all samples as one batch, log only on terminal state
        self.model.fit(np.array(X)/255, np.array(y), batch_size=MINIBATCH_SIZE, verbose=0, shuffle=False, callbacks=[self.tensorboard] if terminal_state else None)

        # Update target network counter every episode
        if terminal_state:
            self.target_update_counter += 1

        # If counter reaches set value, update target network with weights of main network
        if self.target_update_counter > UPDATE_TARGET_EVERY:
            self.target_model.set_weights(self.model.get_weights())
            self.target_update_counter = 0

    # Queries main network for Q values given current observation space (environment state)
    def get_qs(self, state):
        return self.model.predict(np.array(state).reshape(-1, *state.shape)/255)[0]


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

        self.observation = self.get_observation()
        self.last_state = self.observation

        self.agent = DQNAgent(self)

    def play_sound(self):
        # play self.parent.parent.parent.assets.get("coin.wav")
        sound = self.parent.parent.parent.textures.get("coin.wav")
        pygame.mixer.Sound.play(sound)

    def get_observation(self):
        _ = int(self.position[0] / 32), int(self.position[1] / 32)
        observation = self.parent.parent.get_terrain_matrix(_, fov=25)
        return observation

    def step(self, action):
        self.position = self.parent.body.position
        self.time_lapsed += 1
        reward = 0
        # generate action id from tensor
        if not isinstance(action, int):
            action = action.argmax()
            if action > 8 and action < 13 and random.randint(0, 3) == 0:
                self.play_sound()
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

        # reward on inventory size
        reward += len(self.inventory) / 10

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
        _ = (self.position[0] / 32, self.position[1] / 32)
        if self.parent.parent.get_terrain_at(_) != 0:
            reward += -100
            self.health -= 1

        # sort the inventory
        self.inventory = sorted(self.inventory, key=lambda x: x)
        observation = self.get_observation()

        # Health is 0 if the player is dead
        if self.health <= 0:
            reward += -100
            self.reset()
            print(f"[{self.parent.name}] died")

        # give reward for maintaining health
        reward += (self.health - 50) * 0.1

        # train DQNAgent
        self.agent.update_replay_memory((self.last_state, action, reward, observation, True))
        self.last_state = observation
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
        self.epsilon = 0.1

    def reset(self):
        self.body.position = (0, 0)
        self.body.velocity = (0, 0)
        self.body.angle = 0
        self.frame = 0
        self.env.health = 100

    def render(self, window):
        for i in range(len(self.parent.collisions)-1):
            try:
                if self.shape in self.parent.collisions[i].shapes:
                    _ = self.previous_velocity[1] / 5000 * 3
                    if _ > 0.01:
                        self.env.health -= _
                        self.env.scheduled_rewards.append(-_)
                    self.parent.collisions.remove(self.parent.collisions[i])
            except Exception as e:
                pass

        if self.frame % 20 == 0:
            if random.randint(0, 100) < self.epsilon * 100 and self.epsilon > MIN_EPSILON:
                self.env.step(self.env.action_space.sample())
                self.epsilon *= ELIPSON_DECAY
            else:
                _ = self.env.agent.get_qs(self.env.get_observation())
                self.env.step(_)
        # apply force
        # clamp velocity
        self.body.velocity = self.body.velocity[0] + self.env.velocity[0], self.body.velocity[1] + self.env.velocity[1]
        self.env.velocity = (0, 0)
        self.env.position = self.body.position

        self.frame += 1

        # if the current body velocity is not 0, set the previous velocity to the current body velocity
        if self.body.velocity[0] != 0 and self.body.velocity[1] != 0:
            self.previous_velocity = self.body.velocity

        # player color based on health
        if self.env.health > 50:
            c = (255, 255, 255)
        elif self.env.health > 25:
            c = (255, 255, 0)
        else:
            c = (255, abs(int(math.sin(self.frame / 10) * 255)), abs(int(math.sin(self.frame / 10) * 255)))
        pygame.draw.circle(window, c, (int(self.body.position[0] - self.parent.parent.x), int(self.body.position[1]) - self.parent.parent.y), 10)
        # nametag
        font = pygame.font.SysFont("comicsansms", 20)
        text = font.render(self.name, True, (255, 255, 255))
        window.blit(text, (int(self.body.position[0] - self.parent.parent.x) - text.get_width() // 2, int(self.body.position[1]) - self.parent.parent.y + 32 - text.get_height() // 2))
        # draw health bar
        pygame.draw.rect(window, (255, 255, 255), (int(self.body.position[0] - self.parent.parent.x) - 10, int(self.body.position[1]) - self.parent.parent.y - 32, 20, 10))
        color = (0, 255, 0) if self.env.health > 75 else (255, 255, 0) if self.env.health > 50 else (255, 0, 0)
        pygame.draw.rect(window, color, (int(self.body.position[0] - self.parent.parent.x) - 10, int(self.body.position[1]) - self.parent.parent.y - 32, 20 * self.env.health / 100, 10))
