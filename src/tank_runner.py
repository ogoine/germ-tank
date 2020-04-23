"""Classes for actually running a tank simulation"""

import sys
import tkinter as tk

from germ_tank import GermTank, TANK_WIDTH, TANK_HEIGHT

def paint(image, pixels, scale=1):

    image.put('black', (0, 0, TANK_WIDTH * scale, TANK_HEIGHT * scale))
    for x, y, r, g, b in pixels:
        image.put("#%02x%02x%02x" % (r, g, b),
                  (x * scale, y * scale, x * scale + scale, y * scale + scale))

class VisualRunner(tk.Frame):
    """Allows for running a tank with visual feedback"""

    def __init__(self, master=None):
        """Class constructor"""

        super().__init__(master)
        self.master = master
        self.pack()
        self.scale = 3
        self.photo = tk.PhotoImage(width=TANK_WIDTH * self.scale, height=TANK_HEIGHT * self.scale)
        self.label = tk.Label(image=self.photo)
        self.label.pack()
        self.tank = GermTank()

    def do_frame(self):
        self.tank.update(False)
        paint(self.photo, self.tank.get_pixels(), self.scale)
        self.master.update_idletasks()
        self.master.update()

def main(*args):
    runner = VisualRunner(master=tk.Tk())
    while True:
        runner.do_frame()

if __name__ == "__main__":
    main(sys.argv)
