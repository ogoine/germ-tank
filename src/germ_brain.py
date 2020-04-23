"""Classes and methods related to germ code"""

import sys
from copy import deepcopy
from random import randrange, choice

MAX_EXECUTIONS = 10000          # Commands to execute before halting; stops infinite loops
MEMORY_SIZE = 100               # Variables germs can store in memory
DIVIDE_BY_ZERO = 1000000        # What any number divided by zero should equal in germ code

class GermBrain:
    """Manages and runs code for a single organism"""

    def __init__(self, parent_code, mutations):
        """Class constructor.

        Params:
         - parent_code (list of lists): Object representing the parent's code to be inherited
         - mutations (int): Apply this many mutations to the parent_code
        """

        self.code = deepcopy(parent_code)
        self.memory = [0] * MEMORY_SIZE
        self.state = None
        # collect mark ids present in code
        # note that mark ids are string in the format f'm{mark_id}'
        self.mark_ids = {int(i[1][1:]) for i in self.code if i[0] == 'mrk'}
        for i in range(mutations):
            self.mutate()

    def to_dict(self):
        """Returns a dict representing the code and memory"""

        return {'code':self.code, 'memory':self.memory}

    @staticmethod
    def from_dict(d):
        """Returns a new GermBrain object based on a dict representation"""

        out = GermBrain(d['code'], 0)
        out.memory = d['memory']
        return out


    # ---------- METHODS FOR CODE MUTATION ------------------------------

    def mutate(self):
        """Randomly change code in a single way"""

        flat_code = []
        for i, elem in enumerate(self.code):
            flat_code += flatten(elem, [i])
        if not flat_code:
            # TODO: Handle case where code becomes empty
            return
        elem_to_mutate = choice(flat_code)
        if elem_to_mutate[0] == "cmd":
            self.mutate_command(elem_to_mutate[1:])
        elif elem_to_mutate[0] in ["oper", "val"]:
            self.mutate_expression(elem_to_mutate[1:])
        else:
            raise KeyError(f'"{elem_to_mutate[0]}" is not a valid element type descriptor')

    def mutate_command(self, address):
        """Implement command-level mutation at the specified address"""

        command = self.code[address[0]]
        if choice([True, False]):
            # Delete this command
            self.code.pop(address[0])
            # if statements require special handling
            if command[0] == 'if':
                # find and remove the mark whose first argument (the mark id) matches
                # the if statement's second argument
                self.mark_ids.remove(int(command[2][1:]))
                self.code.remove(['mrk', command[2]])
        else:
            # Insert a new command before or after
            index = address[0] + choice([0, 1])
            self.code.insert(index, self.rand_command())


    def mutate_expression(self, address):
        """Implement expression-level mutation at the specified address"""

        # Change this expression to either a new value or a new operator
        # Except if we're close to max recursion depth, then don't add another layer
        if len(address) < sys.getrecursionlimit() - 10:
            new_elem = choice([self.rand_value, self.rand_operator])()
        else:
            new_elem = self.rand_value()
        elem = self.code
        for i in address[:-1]:
            elem = elem[i]
        elem[address[-1]] = new_elem

    def add_rand_mark(self):
        """Insert a new mark (used by if command) randomly in the code and return its unique id"""

        if self.mark_ids:
            all_ids = set(range(max(self.mark_ids) + 2))
            new_id = min(all_ids - self.mark_ids)
        else:
            new_id = 0
        self.code.insert(randrange(len(self.code) + 1), ['mrk', f'm{new_id}'])
        self.mark_ids.add(new_id)
        return f'm{new_id}'

    def rand_value(self):
        """Returns a random int literal or str special value"""

        cat = randrange(3)
        if cat == 0:
            # important integer
            return randrange(-1, 1)
        elif cat == 1:
            # any integer
            return randrange(-500, 500)
        else:
            # special value
            # note: special values cannot start with 'm', as this format is reserved for mark ids
            return choice(['energy',
                           'brightness',
                           'stamina',
                           'pain',
                           'success'])

    def rand_operator(self):
        """Returns a list representing a random operator and args"""

        return choice([['+', self.rand_value(), self.rand_value()],
                       ['-', self.rand_value(), self.rand_value()],
                       ['*', self.rand_value(), self.rand_value()],
                       ['/', self.rand_value(), self.rand_value()],
                       ['&', self.rand_value(), self.rand_value()],
                       ['|', self.rand_value(), self.rand_value()],
                       ['!', self.rand_value()],
                       ['<', self.rand_value(), self.rand_value()],
                       ['>', self.rand_value(), self.rand_value()],
                       ['==', self.rand_value(), self.rand_value()],
                       ['!=', self.rand_value(), self.rand_value()],
                       ['m', self.rand_value()],
                       ['gix', self.rand_value()],
                       ['giy', self.rand_value()],
                       ['fix', self.rand_value()],
                       ['fiy', self.rand_value()]])

    def rand_command(self):
        """Returns a list representing a random command and args"""

        return choice([['set', self.rand_value(), self.rand_value()],
                       ['if', self.rand_value(), self.add_rand_mark()],
                       ['ax', self.rand_value()],
                       ['ay', self.rand_value()],
                       ['bst', self.rand_value()],
                       ['pwr', self.rand_value()],
                       ['mv'],
                       ['bir'],
                       ['att'],
                       ['ret']])


    # ---------- METHODS FOR CODE EXECUTION ------------------------------

    def resolve_value(self, expr):
        """Determines the numerical value of expr.

         - If expr is a list, then it's an operation to further resolve.
         - If expr is an int, then it's a literal.
         - If expr is a str, then it's a special value relating to the germ state.
        """

        if type(expr) == int:
            return expr
        elif type(expr) == str:
            if expr in self.state.keys() and expr != 'view':
                return int(self.state[expr])
            else:
                raise KeyError(f'"{expr}" is not a valid special value"')
        elif type(expr) == list:
            if expr[0] == '+':
                return self.resolve_value(expr[1]) + self.resolve_value(expr[2])
            elif expr[0] == '-':
                return self.resolve_value(expr[1]) - self.resolve_value(expr[2])
            elif expr[0] == '*':
                return self.resolve_value(expr[1]) * self.resolve_value(expr[2])
            elif expr[0] == '/':
                try:
                    return int(self.resolve_value(expr[1]) / self.resolve_value(expr[2]))
                except ZeroDivisionError:
                    return DIVIDE_BY_ZERO

            elif expr[0] == '&':
                return self.resolve_value(expr[1]) and self.resolve_value(expr[2])
            elif expr[0] == '|':
                return self.resolve_value(expr[1]) or self.resolve_value(expr[2])
            elif expr[0] == '!':
                return not self.resolve_value(expr[1])

            elif expr[0] == '<':
                return self.resolve_value(expr[1]) < self.resolve_value(expr[2])
            elif expr[0] == '>':
                return self.resolve_value(expr[1]) > self.resolve_value(expr[2])
            elif expr[0] == '==':
                return self.resolve_value(expr[1]) == self.resolve_value(expr[2])
            elif expr[0] == '!=':
                return self.resolve_value(expr[1]) != self.resolve_value(expr[2])

            elif expr[0] == 'm':
                register = self.resolve_value(expr[1]) % len(self.memory)
                return self.memory[register]

            elif expr[0] == 'gix':
                try:
                    index = self.resolve_value(expr[1]) % len(self.state['view']['germs'])
                    return self.state['view']['germs'][index]['dx']
                except ZeroDivisionError:
                    # view is empty
                    return 0
            elif expr[0] == 'giy':
                try:
                    index = self.resolve_value(expr[1]) % len(self.state['view']['germs'])
                    return self.state['view']['germs'][index]['dy']
                except ZeroDivisionError:
                    # view is empty
                    return 0
            elif expr[0] == 'fix':
                try:
                    index = self.resolve_value(expr[1]) % len(self.state['view']['food'])
                    return self.state['view']['food'][index]['dx']
                except ZeroDivisionError:
                    # view is empty
                    return 0
            elif expr[0] == 'fiy':
                try:
                    index = self.resolve_value(expr[1]) % len(self.state['view']['food'])
                    return self.state['view']['food'][index]['dy']
                except ZeroDivisionError:
                    # view is empty
                    return 0

            else:
                raise KeyError(f'"{expr}" is not a valid operator')
        else:
            raise TypeError(f'"{repr(expr)}" is not a valid expr type '
                            f'({type(expr)})')

    def run(self, state):
        """Execute code and decide what to do next.

        Params:
         - state (dict): The current state of the germ. Keys are:
             - energy (int): Amount of energy remaining
             - brightness (int): Amount of sunlight available (inverse of upkeep cost)
                Scale of 0 to 100 indicating percent of GERM_OPACITY
             - stamina (int): Amount of stamina remaining
             - pain (int): Amount of damage taken since last turn
             - view (list of dict): Data about other objects in the vicinity. Keys are:
                - id (int): the view identifier for this object
                - dx (int): the relative x coordinate of the object
                - dy (int): relative y coordinate
                - fd (boolean): whether this is a food particle
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
            while executed < MAX_EXECUTIONS:
                executed += 1
                if head >= len(self.code):
                    # code end: return and take no action (always successful)
                    return dict()
                cmd = self.code[head][0]

                if cmd == 'set':
                    # set the value of a variable
                    register = self.resolve_value(self.code[head][1]) % len(self.memory)
                    value = self.resolve_value(self.code[head][2])
                    self.memory[register] = value
                elif cmd == 'if':
                    # if expr is false, branch head to the corresponding "mark"
                    expr = self.resolve_value(self.code[head][1])
                    dest = self.code[head][2]
                    if not expr:
                        found = False
                        for i, elem in enumerate(self.code):
                            if elem[0] == "mrk" and elem[1] == dest:
                                head = i
                                found = True
                                break
                        if not found:
                            raise KeyError(f'Mark "{dest}" not found')
                elif cmd == 'mrk':
                    # destination of an if statement; does nothing by itself
                    pass

                elif cmd == 'ax':
                    # set the x-direction of the action to be taken
                    new_x = self.resolve_value(self.code[head][1])
                    if new_x < 0:
                        ax = -1
                    elif new_x > 0:
                        ax = 1
                    else:
                        ax = 0
                elif cmd == 'ay':
                    # set the y-direction of the action to be taken
                    new_y = self.resolve_value(self.code[head][1])
                    if new_y < 0:
                        ay = -1
                    elif new_y > 0:
                        ay = 1
                    else:
                        ay = 0
                elif cmd == 'bst':
                    # set burst value for action request
                    burst = self.resolve_value(self.code[head][1]) == True
                elif cmd == 'pwr':
                    # set power value for action request
                    power = self.resolve_value(self.code[head][1]) % 6

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
                else:
                    raise KeyError(f'"{cmd}" is not a valid command')
                head += 1
            # execution limit exceeded
            return {'action':'halt'}

        except Exception as err:
            msg = f'Exception raised from germ code (line {head})\n'
            for i, e in enumerate(self.code):
                msg += f'{i}: {e}\n'
            raise RuntimeError(msg) from err

def flatten(code_elem, address):
    """Recursive function that 'flattens' code into a one-dimensional list off mutable elements.

    Mutable elements here include any command except 'mrk', any value except a mark id, or any
    operator with only value args. These are the elements that are eligible for mutation. By
    excluding operators with further operators nested within them, we ensure only incremental
    changes are made to the code during mutation.

    Arguments:
     - code_elem: A list, int, or str representing a single command, operator, or value.
     - address: The address to the supplied code element (see explanation of address below).

    Returns: A list of lists, where each sublist represents the address of a single mutable element
        found within code_elem. The first element of each sublist is either "cmd", "oper", or "val",
        indicating the type of mutable element. The following elements represent the series of
        indices necessary to locate the element starting from the parent list which contains
        code_elem.

        Example: ['val', 27, 3, 2] represents a value reachable at complete_code[27][3][2].
    """

    if type(code_elem) is str or type(code_elem) is int:
        # Value reached; end of recursion
        # if code_elem is a mark id, return an empty list to show no mutable elements
        if type(code_elem) is str and code_elem[0] == 'm':
            return []
        return [['val'] + address]
    elif type(code_elem) is list:
        if len(address) == 1:
            # code_elem is directly accessible from the parent code list, meaning it's a command
            # if code_elem is a mrk command, return an empty list to show no mutable elements
            if code_elem[0] == 'mrk':
                return []
            # Otherwise start the list with the list-address to this command
            out = [['cmd'] + address]
        else:
            # otherwise, it's a operator
            # check if all arguments are values (not lists): if so, the operator is also "mutable"
            mutable = True
            for elem in code_elem[1:]:
                if type(elem) is list:
                    mutable = False
                    break
            # include this operator's address if it is mutable
            if mutable:
                out = [['oper'] + address]
            else:
                out = []
        # now include addresses of any arguments for both commands and operators
        for i, elem in enumerate(code_elem[1:]):
            out = out + flatten(elem, address + [i + 1])
        return out
    else:
        raise TypeError(f'code_elem has an unexpected type: {type(code_elem)}')
