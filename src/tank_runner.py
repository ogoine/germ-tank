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
        self.master.protocol("WM_DELETE_WINDOW", self.close)
        self.pack()
        self.scale = 3
        self.photo = tk.PhotoImage(master=self,
                                   width=TANK_WIDTH * self.scale,
                                   height=TANK_HEIGHT * self.scale)
        self.label = tk.Label(master=self, image=self.photo)
        self.label.pack()
        try:
            with open('autosave.json') as fileobj:
                self.tank = GermTank(fileobj.read())
        except FileNotFoundError:
            self.tank = GermTank()

    def do_frame(self):
        self.tank.update(False)
        paint(self.photo, self.tank.get_pixels(), self.scale)
        self.master.update_idletasks()
        self.master.update()

    def close(self):
        with open('autosave.json', 'w') as fileobj:
            fileobj.write(self.tank.to_json())
        self.master.destroy()

def main(*args):
    runner = VisualRunner(master=tk.Tk())
    while True:
        runner.do_frame()

if __name__ == "__main__":
    main(sys.argv)
