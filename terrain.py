import pygame, opensimplex, random, pymunk, numpy as np
from person import Boxlander

noise = opensimplex.OpenSimplex(seed=random.randint(0, 1000000))

default_props = {
    "breakable": True,
}

class Blocktype:
    def __init__(self, name, parent, texture):
        self.parent = parent
        self.name = name
        self.texture = texture
        self.instances = []

        self.props = default_props.copy()

    def add_instance(self, position):
        self.instances.append([position, self.add_to_parent(position)])
        
    def add_to_parent(self, position):
        return self.parent.add_block(self, position, self.texture)

class Structure:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

    def generate(self, position):
        self._generate(position)

class TreeGenerator(Structure):
    def __init__(self, parent):
        super().__init__("Tree", parent)
        
    def _generate(self, position):
        self.trunk_height = random.randint(5, 7)
        self.width = random.randint(2, 3) # width and height of the leafs
        self.height = random.randint(2, 3)

        for i in range(position[0]-self.width, position[0]+self.width):
            for j in range(position[1]-self.height, position[1]+self.height):
                if not i == position[0] and not j == position[1]:
                    self.parent.place_block((i, j), "leaf")
                else:
                    self.parent.place_block((i, j), "log")

def create_block(name, parent, texture, props=default_props.copy()):
    _ = Blocktype(name, parent, parent.parent.textures[texture],)
    _.props = props
    return _

def load_blocks(parent):
    blocks = {}
    blocks['grass'] = create_block('grass', parent, 'grass.png')
    blocks['dirt'] = create_block('dirt', parent, 'dirt.png')
    blocks['stone'] = create_block('stone', parent, 'stone.png')
    blocks['bedrock'] = create_block('bedrock', parent, 'bedrock.png', {"breakable": False})
    blocks['coal_ore'] = create_block('coal_ore', parent, 'coal_ore.png')
    blocks['iron_ore'] = create_block('iron_ore', parent, 'iron_ore.png')
    blocks['diamond_ore'] = create_block('diamond_ore', parent, 'diamond_ore.png')
    blocks['lapis_ore'] = create_block('lapis_ore', parent, 'lapis_ore.png')
    blocks['log'] = create_block('log_birch', parent, 'log_birch.png')
    blocks['leaf'] = create_block('leaf_birch', parent, 'double_plant_paeonia_bottom.png')
    return blocks

def to_id(type):
    if type == "grass":
        ret = 1
    elif type == "dirt":
        ret = 2
    elif type == "stone":
        ret = 3
    elif type == "bedrock":
        ret = 4
    elif type == "coal_ore":
        ret = 5
    elif type == "iron_ore":
        ret = 6
    elif type == "diamond_ore":
        ret = 7
    elif type == "lapis_ore":
        ret = 8
    elif type == "log":
        ret = 9
    elif type == "leaf":
        ret = 10
    return ret 

class Chunk:
    def __init__(self, parent, position, _parent):
        self.parent = parent
        self._parent = _parent
        self.blocks = load_blocks(self)
        self.position = position
        self.position = [int(position[0]) * 32, int(position[1]) * 32]
        self.x_translate = 0
        self.y_translate = 0
        self.x_translate_ = 0
        self.y_translate_ = 0

        self.spritegroup = pygame.sprite.Group()
        self.block_instances = {}

    def add_block(self, blocktype, position):
        index = position
        position = (position[0] * 32, position[1] * 32)
        sprite = pygame.sprite.Sprite()
        sprite.image = self.blocks[blocktype].texture
        sprite.rect = pygame.Rect(position[0], position[1], 32, 32)
        self.spritegroup.add(sprite)

        # create physics body
        body = pymunk.Body(body_type = pymunk.Body.STATIC)
        body.position = position[0], position[1]
        shape = pymunk.Poly.create_box(body, (32, 32))
        shape.friction = 0.5
        shape.collision_type = 1
        self.parent.space.add(body, shape)

        self.block_instances[index] = [sprite, blocktype, body, shape]

        self.parent.blocks[index] = self.block_instances[index]

        return sprite

    def remove_block(self, position):
        # check if block is breakable
        if self.blocks[self.block_instances[position][1]].props["breakable"]:
            self.block_instances[position][0].kill()
            self.parent.space.remove(self.block_instances[position][3], self.block_instances[position][2])
            del self.block_instances[position]

    def draw(self, window):
        self.spritegroup.draw(window)

    def get_cave_noise(self, position):
        return noise.noise2(position[0]/8, position[1]/8)

    def generate(self):
        for x in range(self.position[0], self.position[0] + 32):
            grassnoise = 10 + abs(int(noise.noise2(x/20, 0) * 10))
            treenoise = 10 + abs(int(noise.noise2(x/25, 0) * 10))

            if treenoise > grassnoise:
                self.parent.generators["tree"].generate((x, grassnoise))

            self.add_block('grass', (x, grassnoise))

            dirtnoise = grassnoise + 1 + abs(int(noise.noise2(x / 22, grassnoise / 200) * 5))
            for y in range(grassnoise + 1, dirtnoise):
                if not self.get_cave_noise((x, y)) > 0.3:
                    self.add_block('dirt', (x, y))
            
            stonenoise = dirtnoise + abs(int(noise.noise2(x / 200, dirtnoise / 200) * 50)) + 40
            for y in range(dirtnoise , stonenoise):
                if not self.get_cave_noise((x, y)) > 0.2:
                    self.add_block('stone', (x, y))
                    cave_noise = self.get_cave_noise((x, y))
                    if cave_noise < -0.52 and cave_noise > -0.54:
                        self.add_block('coal_ore', (x, y))
                    elif cave_noise < -0.54 and cave_noise > -0.56:
                        self.add_block('iron_ore', (x, y))
                    elif cave_noise < -0.56 and cave_noise > -0.58:
                        self.add_block('diamond_ore', (x, y))
                    elif cave_noise < -0.58 and cave_noise > -0.7:
                        self.add_block('lapis_ore', (x, y))
            # bedrock
            for i in range(0, 3):
                self.add_block('bedrock', (x, stonenoise - i))

    def update(self):
        self.x_translate = self._parent.x
        self.y_translate = self._parent.y

        if self.x_translate != self.x_translate_:
            self.x_translate_ = self.x_translate
            for block in self.block_instances:
                self.block_instances[block][0].rect.x = self.block_instances[block][2].position[0] - self.x_translate

        if self.y_translate != self.y_translate_:
            self.y_translate_ = self.y_translate
            for block in self.block_instances:
                self.block_instances[block][0].rect.y = self.block_instances[block][2].position[1] - self.y_translate

class CloudDisplay:
    def __init__(self, window, texture, world):
        self.window = window
        self.clouds = []
        self.texture = texture
        self.frame = 0
        self.world = world
    
    def add_cloud(self, position):
        self.clouds.append(Cloud(self.window, position, self.texture, self))

    def update(self):
        for cloud in self.clouds:
            cloud.update()
            if cloud.position[0] > self.window.get_width():
                self.clouds.remove(cloud)

        if self.frame % 2500 == 0:
            self.add_cloud([-250, random.randrange(0, 120)])

        self.frame += 1

    def draw(self):
        for cloud in self.clouds:
            cloud.draw(self.window)

class Cloud:
    def __init__(self, window, position, img, parent):
        self.parent = parent
        self.window = window
        self.position = list(position)
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = img
        self.sprite.rect = pygame.Rect(position[0], position[1], 32, 32)
        self.speed = 0.8 + random.random() * 2

    def update(self):
        self.position[0] += self.speed / 10
        self.sprite.rect.x = self.position[0] - self.parent.world.parent.x - 16
        self.sprite.rect.y = self.position[1] - self.parent.world.parent.y - 16

    def draw(self, window):
        window.blit(self.sprite.image, self.sprite.rect)

class World:
    def __init__(self, window, textures, parent):
        self.window = window
        self.textures = textures
        self.parent = parent
        self.chunks = {}
        self.boxlanders = {}
        self.entities = {}
        self.blocks = {}

        self.sky_color = (63, 128, 186)
        self.cloud_display = CloudDisplay(self.window, self.textures['cloud.png'], self)

        self.space = pymunk.Space()
        self.space.gravity = (0, 900)

        self.xpos = 0
        self.render_distance = 3

        self.generators = {"tree": TreeGenerator(self)}

        self.collision_handler = self.space.add_collision_handler(1, 1)
        self.collision_handler.begin = self.begin_collision

        for i in range(6):
            self.boxlanders[f"Boxy{i}"] = Boxlander(f"Boxy{i}", self)
        self.collisions = []

    def begin_collision(self, arbiter, space, data):
        self.collisions.append(arbiter)
        return True

    def add_chunk(self, position):
        chunk = Chunk(self, position, self.parent)
        self.chunks[position] = chunk
        return chunk

    def draw(self):
        self.window.fill(self.sky_color)
        for chunk in self.chunks.values():
            chunk.draw(self.window)
        self.cloud_display.draw()

        for i in self.boxlanders.values():
            i.render(self.window)

    def generate(self):
        self.chunks = {}

        for i in range(self.xpos - self.render_distance, self.xpos + self.render_distance):
            if i not in self.chunks:
                self.add_chunk((i, 0))

        for chunk in self.chunks.values():
            chunk.generate()

    def update(self):
        self.space.step(0.02) 
        self.cloud_display.update()
        for chunk in self.chunks.values():
            chunk.update()
        
    def get_terrain_at(self, position):
        for chunk in self.chunks.values():
            if position in chunk.block_instances:
                return to_id(chunk.block_instances[position][1])
        return 0

    def get_terrain_matrix(self, position, fov):
        position = list(position)
        position[0] = int(position[0] / 32)
        position[1] = int(position[1] / 32)
        matrix = np.array(np.zeros((fov*2+1, fov*2+1)))
        for i in range(-fov, fov):
            for j in range(-fov, fov):
                matrix[i + fov, j + fov] = self.get_terrain_at((position[0] + i, position[1] + j))
        return matrix

    def get_terrain_height_at(self, x):
        return 10 + abs(int(noise.noise2(x/20, 0) * 10))

    def remove_block(self, position):
        for chunk in self.chunks.values():
            try:
                # get the block name
                block_name = chunk.block_instances[position][1]
                chunk.remove_block(position)
                return block_name
            except:
                pass
        
        return None

    def place_block(self, position, block_name):
        try:
            for chunk in self.chunks.values():
                if position in chunk.block_instances:
                    return False
                else:
                    chunk.add_block(block_name, position)
                    return True
        except Exception as e:
            print(e)

    def attack(self, position, damage = 1):
        for _ in self.entities.values():
            entity = self.entities[_.name]
            # round the position to the nearest block
            _position = (int(entity.env.position[0] / 32) * 32, int(entity.env.position[1] / 32) * 32)
            if _position == position:
                entity.env.health -= damage
                print(entity.env.name)
                return entity.env.name
        return None
