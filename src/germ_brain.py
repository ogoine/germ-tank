"""Classes and methods related to germ code"""

MAX_EXECUTIONS = 10000
MEMORY_SIZE = 100

class GermBrain:
    """Manages and runs code for a single organism"""

    def __init__(self, parent_code, mutations):
        """Class constructor.

        Params:
         - parent_code (ordered dict): Object representing the parent's code to be inherited
         - mutations (int): Apply this many mutations to the parent_code
        """

        self.code = mutate(parent_code, mutations)
        self.memory = [0] * MEMORY_SIZE
        self.state = None

    def resolve_value(self, expression):
        """Determines the numerical value of expr.

         - If expr is a list, then it's an operation to further resolve.
         - If expr is a float, then it's a literal.
         - If expr is a str, then it's a special value relating to the germ state.
        """

        if typeof(expr) == float:
            return expr
        elif typeof(expr) == str:
            if expr in self.state.keys() and expr != 'view':
                return self.state[expr]
            else:
                raise KeyError(f'"{expr}" is not a valid special value"')
        elif typeof(expr) == list:
            if expr[0] == '+':
                return resolve_value(expr[1]) + resolve_value(expr[2])
            elif expr[0] == '-':
                return resolve_value(expr[1]) - resolve_value(expr[2])
            elif expr[0] == '*':
                return resolve_value(expr[1]) * resolve_value(expr[2])
            elif expr[0] == '/':
                return resolve_value(expr[1]) / resolve_value(expr[2])

            elif expr[0] == '&':
                return resolve_value(expr[1]) and resolve_value(expr[2])
            elif expr[0] == '|':
                return resolve_value(expr[1]) or resolve_value(expr[2])
            elif expr[0] == '!':
                return not resolve_value(expr[1])

            elif expr[0] == '<':
                return resolve_value(expr[1]) < resolve_value(expr[2])
            elif expr[0] == '>':
                return resolve_value(expr[1]) > resolve_value(expr[2])
            elif expr[0] == '==':
                return resolve_value(expr[1]) == resolve_value(expr[2])
            elif expr[0] == '!=':
                return resolve_value(expr[1]) != resolve_value(expr[2])

            elif expr[0] == 'm':
                register = int(resolve_value(expr[1])) % len(self.memory)
                return self.memory[register]

            elif expr[0] == 'ix':
                # i(x|y) gives the (x|y) direction of a nearby germ identified by index
                # Result is -1 or 1
                index = int(resolve_value(expr[1])) % len(self.state.view)
                return self.state.view(index)['dx']
            elif expr[0] == 'iy':
                index = int(resolve_value(expr[1])) % len(self.state.view)
                return self.state.view(index)['dy']
            elif expr[0] == 'ux':
                # u(x|y) gives the (x|y) direction of a nearby germ identified by uid
                # Result is -1 or 1. 0 is given if the identified germ doesn't exist in view
                uid = int(resolve_value(expr[1]))
                try:
                    return next(i['dx'] for i in self.state.view if i['id'] == uid)
                except StopIteration:
                    return 0
            elif expr[0] == 'uy':
                uid = int(resolve_value(expr[1]))
                try:
                    return next(i['dy'] for i in self.state.view if i['id'] == uid)
                except StopIteration:
                    return 0

            else:
                raise KeyError(f'"{expr}" is not a valid operator')
        else:
            raise TypeError(f'"{repr(expr)}" is not a valid expr type '
                            f'({typeof(expr)})')

    def run(self, state):
        """Execute code and decide what to do next.

        Params:
         - state (dict): The current state of the germ. Keys are:
             - energy (float): Amount of energy remaining
             - brightness (float): Amount of "sunlight" energy gained per standard frame
             - stamina (float): Amount of stamina remaining
             - pain (float): Amount of damage taken since last turn
             - view (list of dict): Data about other germs in the vicinity
             - success (boolean): False if an action was taken last turn resulting
                in no change of state; otherwise True.

        Returns (dict): Data about what action to take, if any. Possible keys are:
         - x (int): X-axis direction of action, either -1, 0, or 1
         - y (int): Y-axis direction of action, either -1, 0, or 1
         - action (str): Action to take. Either "move", "birth", or "attack".
            "halt" indicates an execution limit was exceeded.
         - burst (boolean): If true, spend extra energy to take an extra turn.
         - power (int): Power committed to attack. Range 0 - 5.
        """

        head = 0
        ax = 0
        ay = 0
        burst = False
        power = 0
        executed = 0
        self.state = state
        try:
            while head < len(self.code):
                executed += 1
                if executed > MAX_EXECUTIONS:
                    return {'action':'halt'}
                cmd = self.code[head][0]

                if cmd == 'set':
                    # set the value of a variable
                    register = int(self.resolve_value(self.code[head][1])) % len(self.memory)
                    value = int(self.resolve_value(self.code[head][2]))
                    self.memory[register] = value
                elif cmd == 'if':
                    # if expr is true, jump head to a new spot
                    expr = self.resolve_value(self.code[head][1]))
                    dest = int(self.resolve_value(self.code[head][2]))
                    if dest != 0 and expr:
                        head += dest
                        head = max(head, 0)
                        head = min(head, len(self.code) - 1)
     
                 elif cmd == 'ax':
                     # set the x-direction of the action to be taken
                     new_x = self.resolve_value(self.code[head][1])
                     if new_x < 0:
                         ax = -1
                     elif new_x > 0:
                         ax = 1
                     else: ax = 0
                 elif cmd == 'ay':
                     # set the y-direction of the action to be taken
                     new_y = self.resolve_value(self.code[head][1])
                     if new_y < 0:
                         ay = -1
                     elif new_y > 0:
                         ay = 1
                     else: ay = 0
                 elif cmd == 'bst':
                     # set burst value for action request
                     burst = self.resolve_value(self.code[head][1]) == True
                 elif cmd == 'pwr':
                     # set power value for action request
                     power = int(self.resolve_value(self.code[head][1])) % 6

                 elif cmd == 'mv':
                     # return and take the move action
                     return {'x':ax, 'y':ay, 'action':'move', 'burst':burst}
                 elif cmd == 'bir':
                     # return and take the birth action
                     return {'x':ax, 'y':ay, 'action':'birth', 'burst':burst}
                 elif cmd == 'att':
                     # return and take the attack action
                     return {'x':ax, 'y':ay, 'action':'attack', 'burst':burst, 'power':power}
                 elif cmd == 'ret':
                     # return and take no action (always successful)
                     return dict()

        except Exception as err:
            raise RuntimeError(f'Exception raised from germ code (line {head})') from err
