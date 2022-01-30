import pygame, opensimplex, random

noise = opensimplex.OpenSimplex(seed=random.randint(0, 1000000))

class Blocktype:
    def __init__(self, name, parent, texture):
        self.parent = parent
        self.name = name
        self.texture = texture
        self.instances = []

    def add_instance(self, position):
        self.instances.append([position, self.add_to_parent(position)])
        
    def add_to_parent(self, position):
        return self.parent.add_block(self, position, self.texture)

def load_blocks(parent):
    blocks = {}
    blocks['grass'] = Blocktype('grass', parent, parent.parent.textures['grass.png'])
    blocks['dirt'] = Blocktype('dirt', parent, parent.parent.textures['dirt.png'])
    blocks['stone'] = Blocktype('stone', parent, parent.parent.textures['stone.png'])
    return blocks

class Chunk:
    def __init__(self, parent, position):
        self.parent= parent
        self.blocks = load_blocks(self)
        self.position = position
        self.position = [int(position[0]) * 32, int(position[1]) * 32]

        self.spritegroup = pygame.sprite.Group()
        self.block_instances = {}


    def add_block(self, blocktype, position):
        position = (position[0] * 32, position[1] * 32)
        sprite = pygame.sprite.Sprite()
        sprite.image = self.blocks[blocktype].texture
        sprite.rect = pygame.Rect(position[0], position[1], 32, 32)
        self.spritegroup.add(sprite)
        self.block_instances[position] = [sprite, blocktype]
        return sprite

    def draw(self, window):
        self.spritegroup.draw(window)

    def generate(self):
        for x in range(self.position[0], self.position[0] + 32):
            grassnoise = 10 + abs(int(noise.noise2(x/20, 0) * 10))
            self.add_block('grass', (x, grassnoise))

            dirtnoise = grassnoise + 1 + abs(int(noise.noise2(x / 22, grassnoise / 200) * 5))
            for y in range(grassnoise + 1, dirtnoise):
                self.add_block('dirt', (x, y))
            
            stonenoise = dirtnoise + abs(int(noise.noise2(x / 200, dirtnoise / 200) * 50)) + 40
            for y in range(dirtnoise , stonenoise):
                self.add_block('stone', (x, y))

class CloudDisplay:
    def __init__(self, window, texture):
        self.window = window
        self.clouds = []
        self.texture = texture
        self.frame = 0
    
    def add_cloud(self, position):
        self.clouds.append(Cloud(self.window, position, img=self.texture))

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
    def __init__(self, window, position, img):
        self.window = window
        self.position = list(position)
        self.sprite = pygame.sprite.Sprite()
        self.sprite.image = img
        self.sprite.rect = pygame.Rect(position[0], position[1], 32, 32)
        self.speed = 0.8 + random.random() * 2

    def update(self):
        self.position[0] += self.speed / 10
        self.sprite.rect.x = self.position[0]
        self.sprite.rect.y = self.position[1]

    def draw(self, window):
        window.blit(self.sprite.image, self.sprite.rect)

class World:
    def __init__(self, window, textures):
        self.window = window
        self.textures = textures
        self.chunks = {}

        self.chunks[(0, 0)] = self.add_chunk((0, 0))
        self.chunks[(1, 0)] = self.add_chunk((1, 0))

        self.sky_color = (63, 128, 186)
        self.cloud_display = CloudDisplay(self.window, self.textures['cloud.png'])

    def add_chunk(self, position):
        chunk = Chunk(self, position)
        self.chunks[position] = chunk
        return chunk

    def draw(self):
        self.window.fill(self.sky_color)
        for chunk in self.chunks.values():
            chunk.draw(self.window)
        self.cloud_display.draw()

    def generate(self):
        for chunk in self.chunks.values():
            chunk.generate()

    def update(self):
        self.cloud_display.update()
