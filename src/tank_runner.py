"""Classes for actually running a tank simulation"""

import sys
import tkinter as tk

from germ_tank import GermTank, TANK_WIDTH, TANK_HEIGHT

def paint(image, pixels):
    """Paint a list of pixels in form (x, y, r, g, b) on a black background to an image"""

    def pixel_color(px, py):
        if pixels and px == pixels[0][0] and py == pixels[0][1]:
            pixel = pixels.pop(0)
            return pixel[2], pixel[3], pixel[4]
        else:
            return (0, 0, 0)

    pixels = sorted(pixels, key=lambda p: p[0] + p[1] * image.width())
    data = " ".join(["{" + " ".join(["#%02x%02x%02x" % pixel_color(x, y) for x in range(image.width())]) + "}"
                     for y in range(image.height())])
    image.put(data)

class VisualRunner(tk.Frame):
    """Allows for running a tank with visual feedback"""

    def __init__(self, master=None):
        """Class constructor"""

        super().__init__(master)
        self.master = master
        self.pack()
        self.photo = tk.PhotoImage(width=TANK_WIDTH, height=TANK_HEIGHT)
        self.photo = tk.PhotoImage(width=32, height=32)
        self.label = tk.Label(image=self.photo)
        self.label.pack()

def main(*args):
    VisualRunner(master=tk.Tk()).mainloop()

if __name__ == "__main__":
    main(sys.argv)
