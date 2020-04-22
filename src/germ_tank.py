"""Classes and functions built around the tank simulation itself"""

from math import sqrt
from random import random, randrange, choice
from operator import itemgetter

from germ_brain import GermBrain

TANK_WIDTH = 400
TANK_HEIGHT = 200
TANK_WRAP = True           # whether the sides of the tank wrap
MAX_FOOD_DENSITY = 0.02    # max amount of food per pixel spawned
FOOD_GROWTH_RATE = 10      # max number of food spawned per frame
FOOD_ENERGY = 20.0         # amount of energy earned per food particle
MAX_GERM_ENERGY = 100.0    # max energy each germ can store
INIT_GERM_ENERGY = 30.0    # starting energy of germ: must commit this + BIRTH_COST to reproduce
GERM_ABSORB_RATE = 0.5     # What proportion of a prey's energy is gained by a predator
GERM_BASE_ABSORB = 5.0     # Base amount of energy gained by a predator
GERM_STAMINA = 10.0        # max stamina each germ can have
GERM_STAMINA_REGEN = 0.5   # amount of stamina germ regenerates each standard turn
DEATH_RATE = 0.0001        # chance a germ has of self-destructing each standard turn
MUTATION_RATE = 0.15       # chance that offspring has of developing mutations
MULTI_MUT_RATE = 0.5       # chance of developing each additional mutation beyon the first

# energy costs
# moving one square always costs 1 energy, as a baseline
UPKEEP_COST = 0.2         # flat cost of staying alive each turn. Germs pay 10% of this at top
                          # of tank and 100% at bottom, scaling linearly
BURST_COST = 1.0          # cost of taking a burst turn
ATTACK_BASE_COST = 1.0    # base cost of taking attack action
ATTACK_POWER_COST = 0.5   # how much energy it costs per unit of power to attack
BIRTH_COST = 10.0         # how much energy is lost in birthing process

STARTING_CODE = [['if', ['>', 'energy', 70], 'm0'],
                 ['ax', 1],
                 ['bir'],
                 ['mrk', 'm0']]

def random_mutations():
    if random() < MUTATION_RATE:
        count = 1
        while random() < MULTI_MUT_RATE:
            count += 1
        return count
    else:
        return 0

class GermTank:
    """Handles the data and execution of the germs in the tank"""

    def __init__(self):
        """Class constructor"""

        self.tank = [[None] * TANK_HEIGHT for i in range(TANK_WIDTH)]
        self.id_registry = dict()
        self.new_germs = []
        # add a starting number of germs and food each equal to TANK_WIDTH
        # set comprehension ensure rare duplicates are removed
        self.food_count = TANK_WIDTH
        locs = {(randrange(TANK_WIDTH), randrange(TANK_HEIGHT)) for i in range(TANK_WIDTH * 2)}
        c = 0
        for x, y in locs:
            if c < TANK_WIDTH:
                self.new_id(self.add_germ(x, y, GermBrain(STARTING_CODE, 0)))
            else:
                # germs with no brain are food particles
                self.new_id(self.add_germ(x, y, None))
            c += 1

    def get_pixels(self):
        """Returns a list of pixels representing germs in the form (x, y, r, g, b)"""

        return [(i['x'], i['y'], 255, 255, 255) for i in self.id_registry.values()]

    def new_id(self, germ):
        """Registers a new germ and gives it a uid"""

        if self.id_registry:
            all_ids = set(range(max(self.id_registry.keys()) + 2))
            new_id = min(all_ids - self.id_registry.keys())
        else:
            new_id = 0
        germ['uid'] = new_id
        self.id_registry[new_id] = germ

    def kill_germ(self, germ):
        """Destroys the given germ"""

        if not germ['brain']:
            self.food_count -= 1
        del self.id_registry[germ['uid']]
        self.tank[germ['x']][germ['y']] = None

    def add_germ(self, x, y, germ_brain):
        """Creates a new germ at the given location"""

        if self.tank[x][y]:
            raise RuntimeError(f'Location ({x}, {y}) already occupied')
        if germ_brain:
            germ = {
                'brain':germ_brain,
                'alive':True,
                'x':x,
                'y':y,
                'energy':INIT_GERM_ENERGY,
                'stamina':GERM_STAMINA,
                'success':True,
                'burst':False,
                'pain':0,
                'view_ids':dict()}
        else:
            # germs with no brain are food particles
            self.food_count += 1
            germ = {
                'brain':None,
                'alive':True,
                'x':x,
                'y':y}
        self.tank[x][y] = germ
        return germ

    def get_view(self, x, y):
        """Returns a view object for a germ at the given location.

        Returns (list of dict): All germs within viewing distance in order of nearness.
        """

        # TODO: implement
        return []

    def get_birth_loc(self, x, y, dx, dy):
        """Gets a suitable birth location relative to (x, y) as close as possible to request"""

        # each loc is a 3-tuple of x, y, and d, the distance from original request
        locs = []
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if not (i == 0 and j == 0):
                    locs.append((i, j, abs(dx - i) + abs(dy - j)))
        locs = sorted(locs, key=itemgetter(2))
        for ndx, ndy, d in locs:
            new_x, new_y = self.get_relative_loc(x, y, ndx, ndy)
            if new_x != -1 and not self.tank[new_x][new_y]:
                return new_x, new_y
        return -1, -1

    @staticmethod
    def get_relative_loc(x, y, dx, dy):
        """Gets a new location relative to (x, y) accounting for tank dimensions"""

        new_x = x + dx
        if TANK_WRAP:
            if new_x >= TANK_WIDTH:
                new_x = 0
            elif new_x < 0:
                new_x = TANK_WIDTH - 1
        elif new_x >= TANK_WIDTH or new_x < 0:
            return -1, -1
        new_y = y + dy
        if new_y >= TANK_HEIGHT or new_y < 0:
            return -1, -1
        return new_x, new_y

    def dine(self, germ):
        """Allow the supplied germ to consume one adjacent food particle"""

        locs = []
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                if not (i == 0 and j == 0):
                    locs.append((i, j))
        for dx, dy in locs:
            tgt_x, tgt_y = self.get_relative_loc(germ['x'], germ['y'], dx, dy)
            target = self.tank[tgt_x][tgt_y]
            if target and not target['brain'] and target['alive']:
                germ['energy'] += FOOD_ENERGY
                target['alive'] = False

    def process_request(self, request, germ, x, y):
        """Process a request returned by a germ"""

        # TODO: Don't spend burst if next turn is a standard
        if 'burst' in request and request['burst']:
            germ['energy'] -= BURST_COST
            germ['burst'] = True
        else:
            germ['burst'] = False

        if 'action' not in request:
            germ['success'] = True
        elif request['action'] == 'halt':
            germ['success'] = False
            germ['energy'] -= 1

        elif request['action'] == 'move':
            new_x, new_y = self.get_relative_loc(x, y, request['x'], request['y'])
            if new_x == -1 or self.tank[new_x][new_y]:
                germ['success'] = False
            else:
                germ['success'] = True
                germ['energy'] -= sqrt(request['x'] ** 2 + request['y'] ** 2)
                germ['x'] = new_x
                germ['y'] = new_y
                self.tank[new_x][new_y] = germ
                self.tank[x][y] = None

        elif request['action'] == 'birth':
            new_x, new_y = self.get_birth_loc(x, y, request['x'], request['y'])
            if new_x == -1 or germ['energy'] < INIT_GERM_ENERGY + BIRTH_COST + 1:
                germ['success'] = False
            else:
                germ['success'] = True
                germ['energy'] -= INIT_GERM_ENERGY + BIRTH_COST
                self.new_germs.append(self.add_germ(new_x, new_y, GermBrain(germ['brain'].code, random_mutations())))

        elif request['action'] == 'attack':
            tgt_x, tgt_y = self.get_relative_loc(x, y, request['x'], request['y'])
            cost = ATTACK_BASE_COST + ATTACK_POWER_COST * float(request['power'])
            target = self.tank[tgt_x][tgt_y]
            if not target or not target['alive'] or not request['power'] or cost > germ['energy']:
                germ['success'] = False
            else:
                germ['success'] = True
                germ['energy'] -= cost
                target['stamina'] -= request['power']
                target['pain'] += request['power']
                if target['stamina'] <= 0:
                    germ['energy'] += ((target['energy'] - GERM_BASE_ABSORB)
                        * GERM_ABSORB_RATE + GERM_BASE_ABSORB)
                    target['alive'] = False

    def update(self, burst_turn):
        """Gives all germs a turn.

        Arguments:
         - burst_turn (boolean): True if this is a burst turn; otherwise, a standard turn.
        """

        for germ in self.id_registry.values():
            # germ or food?
            if germ['brain']:
                # on standard turns, do upkeep tasks
                if not burst_turn:
                    if random() < DEATH_RATE:
                        germ['alive'] = False
                        continue
                    germ['energy'] -= UPKEEP_COST * (0.1 + 0.9 * (float(germ['y']) / TANK_HEIGHT))
                    germ['stamina'] += GERM_STAMINA_REGEN
                    germ['stamina'] = min(germ['stamina'], GERM_STAMINA)
                    if germ['energy'] <= 0:
                        germ['alive'] = False
                        continue
                    germ['energy'] = min(germ['energy'], MAX_GERM_ENERGY)

                # if this is a standard turn or the germ paid for a burst, take action
                if not burst_turn or germ['burst']:
                    self.dine(germ)
                    brightness = (1.0 -  0.9 * (float(germ['y']) / TANK_HEIGHT))
                    request = germ['brain'].run(
                        {'energy':germ['energy'],
                         'brightness':brightness,
                         'stamina':germ['stamina'],
                         'pain':germ['pain'],
                         'view':self.get_view(germ['x'], germ['y']),
                         'success':germ['success']})
                    self.process_request(request, germ, germ['x'], germ['y'])

                    # pain only tracks since last turn; also recheck energy bounds
                    germ['pain'] = 0
                    if germ['energy'] <= 0:
                        germ['alive'] = False
                    germ['energy'] = min(germ['energy'], MAX_GERM_ENERGY)

            # food particle
            elif not burst_turn:
                # it moves in a random direction if possible
                locs = []
                for i in [-1, 0, 1]:
                    for j in [-1, 0, 1]:
                        if not (i == 0 and j == 0):
                            locs.append((i, j))
                dx, dy = choice(locs)
                new_x, new_y = self.get_relative_loc(germ['x'], germ['y'], dx, dy)
                if new_x != -1 and not self.tank[new_x][new_y]:
                    germ['x'] = new_x
                    germ['y'] = new_y
                    self.tank[new_x][new_y] = germ
                    self.tank[germ['x']][germ['y']] = None


        # kill germs marked for death and register new ids
        to_kill = [i for i in self.id_registry.values() if not i['alive']]
        for i in to_kill:
            self.kill_germ(i)
        for i in self.new_germs:
            self.new_id(i)
        self.new_germs = []

        # regenerate food
        max_food =  TANK_WIDTH * TANK_HEIGHT * MAX_FOOD_DENSITY
        if self.food_count < max_food:
            to_add = min(FOOD_GROWTH_RATE, max_food - self.food_count)
            c = 0
            # check up to 1000 random locations for openings
            for i in range(1000):
                x = randrange(TANK_WIDTH)
                y = randrange(TANK_HEIGHT)
                if not self.tank[x][y]:
                    self.new_id(self.add_germ(x, y, None))
                    c += 1
                    if c >= to_add:
                        break
