"""Main module that contains the GermTank class"""

from math import sqrt

TANK_WIDTH = 1000
TANK_HEIGHT = 500
TANK_WRAP = True           # whether the sides of the tank wrap
SOLAR_POWER = 5.0          # energy imparted by sunlight per turn per column of cells
GERM_OPACITY = 0.5         # max energy each germ can absorb and block
MAX_GERM_ENERGY = 100.0    # max energy each germ can store
INIT_GERM_ENERGY = 30.0    # starting energy of germ: must commit this + BIRTH_COST to reproduce
GERM_ABSORB_RATE = 0.5     # What proportion of a prey's energy is gained by a predator
GERM_BASE_ABSORB = 5.0     # Base amount of energy gained by a predator
GERM_STAMINA = 15.0        # max stamina each germ can have
GERM_STAMINA_REGEN = 1.0   # amount of stamina germ regenerates each standard turn
CANCER_RATE = 0.00001      # chance a germ has of self-mutating each standard turn

# energy costs
# moving one square always costs 1 energy, as a baseline
UPKEEP_COST = 0.1         # flat cost of staying alive each turn
BURST_COST = 1.0          # cost of taking a burst turn
ATTACK_BASE_COST = 1.0    # base cost of taking attack action
ATTACK_POWER_COST = 1.0   # how much energy it costs per unit of power to attack
BIRTH_COST = 10.0         # how much energy is lost in birthing process

STARTING_CODE = [['if', ['>', 'energy', 70], 2],
                 ['ret'],
                 ['ax', 1],
                 ['bir']]

class GermTank:
    """Handles the data and execution of the germs in the tank"""

    def __init__(self):
        """Class constructor"""

        self.tank = [[None] * TANK_HEIGHT] * TANK_WIDTH
        self.id_registry = set()
        # TODO: add germs

    def new_id(self):
        """Creates and returns a new uid"""

        all_ids = set(range(max(self.id_registry)))
        new_id = min(all_ids - self.id_registry)
        self.id_registry.add(new_id)
        return new_id

    def kill_germ(self, x, y):
        """Destroys a germ at the given location"""

        if not self.tank[x][y]:
            raise RuntimeError(f'Location ({x}, {y}) is empty')
        self.id_registry.remove(self.tank[x][y]['uid'])
        self.tank[x][y] = None

    def add_germ(self, x, y, germ_brain):
        """Creates a new germ at the given location"""

        if self.tank[x][y]:
            raise RuntimeError(f'Location ({x}, {y}) already occupied')
        self.tank[x][y] = {
            'brain':germ_brain,
            'energy':INIT_GERM_ENERGY,
            'stamina':GERM_STAMINA,
            'success':True,
            'burst':False,
            'pain':0,
            'uid':self.new_id(),
            'view_ids':dict()}

    def get_view(self, x, y):
        """Returns a view object for a germ at the given location.

        Returns (list of dict): All germs within viewing distance in order of nearness.
        """

        # TODO: implement
        return []

    def get_birth_loc(x, y, dx, dy):
        """Gets a suitable birth location relative to (x, y) as close as possible to request"""

        # TODO: implement
        pass

    def get_relative_loc(x, y, dx, dy):
        """Gets a new location relative to (x, y) accounting for tank dimensions"""

        new_x = x + dx
        if TANK_WRAP:
            if new_x >= TANK_WIDTH:
                new_x = 0
            elif new_x < 0:
                new_x = TANK_WIDTH - 1
        else:
            new_x = min(new_x, TANK_WIDTH - 1)
            new_x = max(new_x, 0)
        new_y = y + dy
        new_y = min(new_y, TANK_HEIGHT - 1)
        new_y = max(new_y, 0)
        return new_x, new_y

    def get_sunlight(self, x, y):
        """Returns amount of sunlight energy at the given location"""

        cell_opacity = SOLAR_POWER / float(TANK_HEIGHT)
        opacity = 0
        for iy in range(y):
            if self.tank[x][iy]:
                opacity += GERM_OPACITY
            else:
                opacity += cell_opacity
        return min(SOLAR_POWER - opacity, GERM_OPACITY)

    def process_request(self, request, germ, x, y):
        """Process a request returned by a germ"""

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
            if self.tank[new_x][new_y]:
                germ['success'] = False
            else:
                germ['success'] = True
                germ['energy'] -= sqrt(request['x'] ** 2 + request['y'] ** 2)
                self.tank[new_x][new_y] = germ
                self.tank[x][y] = None
        elif request['action'] == 'birth':
            new_x, new_y = self.get_birth_loc(x, y, request['x'], request['y'])
            if new_x == -1 or germ['energy'] < INIT_GERM_ENERGY + BIRTH_COST + 1:
                germ['success'] = False
            else:
                germ['success'] = True
                germ['energy'] -= INIT_GERM_ENERGY + BIRTH_COST
                self.add_germ(new_x, new_y, GermBrain(germ['brain'].code, random_mutations()))
        elif request['action'] == 'attack':
            tgt_x, tgt_y = self.get_relative_loc(x, y, request['x'], request['y'])
            cost = ATTACK_BASE_COST + ATTACK_POWER_COST * float(request['power'])
            target = self.tank[tgt_x][tgt_y]
            if not target or not request['power'] or cost > germ['energy']:
                germ['success'] = False
            else:
                germ['success'] = True
                germ['energy'] -= cost
                target['stamina'] -= request['power']
                target['pain'] += request['power']
                if target['stamina'] <= 0:
                    germ['energy'] += ((target['energy'] - GERM_BASE_ABSORB)
                        * GERM_ABSORB_RATE + GERM_BASE_ABSORB)
                    self.kill_germ(tgt_x, tgt_y)

    def update(self, burst_turn):
        """Gives all germs a turn.

        Arguments:
         - burst_turn (boolean): True if this is a burst turn; otherwise, a standard turn.
        """

        for x in range(TANK_WIDTH):
            for y in range(TANK_HEIGHT):
                germ = self.tank[x][y]
                if germ:
                    # on standard turns, do upkeep tasks
                    # TODO: implement cancer
                    if not burst_turn:
                        germ['energy'] += self.get_sunlight(x, y) - UPKEEP_COST
                        germ['stamina'] += GERM_STAMINA_REGEN
                        germ['stamina'] = min(germ['stamina'], GERM_STAMINA)
                        if germ['energy'] <= 0:
                            self.kill_germ(x, y)
                            continue
                        germ['energy'] = min(germ['energy'], MAX_GERM_ENERGY)

                    # if this is a standard turn or the germ paid for a burst, take action
                    if not burst_turn or germ['burst']:
                        brightness = int(100 * self.get_sunlight(x, y) / GERM_OPACITY)
                        request = germ['brain'].run(
                            {'energy':germ['energy'],
                             'brightness':brightness,
                             'stamina':germ['stamina'],
                             'pain':germ['pain'],
                             'view':self.get_view(x, y),
                             'success':germ['success']})
                        self.process_request(request, germ, x, y)

                        # pain only tracks since last turn; also recheck energy bounds
                        germ['pain'] = 0
                        if germ['energy'] <= 0:
                            self.kill_germ(x, y)
                            continue
                        germ['energy'] = min(germ['energy'], MAX_GERM_ENERGY)
