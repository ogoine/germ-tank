"""Classes for actually running a tank simulation"""

import sys
import tkinter as tk
import signal
from abc import ABC, abstractmethod
from time import time_ns
import _thread
from itertools import chain
from pprint import pprint

from germ_tank import GermTank, TANK_WIDTH, TANK_HEIGHT

def paint(image, pixels, scale=1):
    image.put(" ".join(["{" + " ".join(chain(*zip(*[row for _ in range(scale)]))) + "}" for row in pixels for _ in range(scale)]),
              (0, 0, TANK_WIDTH * scale, TANK_HEIGHT * scale))

class TankRunner(ABC):
    """Base class for tank runners"""

    def __init__(self, germ_tank):
        """Class constructor"""

        self.stop_requested = False
        self.pause = False
        self.frames_executed = 0
        self.frame_timings = []
        signal.signal(signal.SIGINT, self.stop_execution)
        signal.signal(signal.SIGTERM, self.stop_execution)
        self.tank = germ_tank

    def stop_execution(self, signum, frame):
        """Called when the process receives a stop signal"""

        self.stop_requested = True

    def print_stats(self):
        """Dump statistical data for stdout once 50 frames worth of data gathered"""

        stats = self.tank.get_stats()
        fps = 50 * 1000000000.0 / sum(self.frame_timings)
        tps = stats['germ_count'] * fps
        print("STATS")
        print(f'Frames elapsed: {stats["frames_elapsed"] / 1000}k')
        print(f'Energy density: {stats["energy_density"]}')
        print(f'Frames per second: {fps}')
        print(f'Turns per second: {tps}')
        print('==================================================')

    def run(self):
        """Repeatedly calls do_frame and dumps stats to stdout every 10k frames"""

        while not self.stop_requested:
            if not self.pause:
                start_time = time_ns()
                self.do_frame()
                elapsed = time_ns() - start_time
                self.frames_executed += 1
                # On frame 100, start gathering timing data, then print stats when 50 entries gathered
                if self.frames_executed % 10000 == 100 or self.frame_timings:
                    self.frame_timings.append(elapsed)
                    if len(self.frame_timings) >= 50:
                        self.print_stats()
                        self.frame_timings = []
        self.close()

    def toggle_pause(self, event):
        """Pauses or unpauses the tank"""

        self.pause = not self.pause

    @abstractmethod
    def do_frame(self):
        """Will be called each frame"""

    @abstractmethod
    def close(self):
        """Will be called when the app is closing"""

class HeadlessRunner(TankRunner):
    """Allows for running a tank without visual feedback for faster performance"""

    def __init__(self):
        """Class constructor"""

        try:
            with open('autosave.json') as fileobj:
                super().__init__(GermTank(fileobj.read()))
        except FileNotFoundError:
            super().__init__(GermTank())

    def do_frame(self):
        """Called every frame"""
        
        self.tank.update(False)

    def close(self):
        """Called when the app closes"""

        with open('autosave.json', 'w') as fileobj:
            fileobj.write(self.tank.to_json())

class VisualRunner(TankRunner):
    """Allows for running a tank with visual feedback"""

    def __init__(self, root=None):
        """Class constructor"""

        self.scale = 3
        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<space>", self.toggle_pause)
        self.root.bind("<Button-1>", self.inspect)
        self.frame = tk.Frame(self.root)
        self.frame.pack()
        self.photo = tk.PhotoImage(master=self.frame,
                                   width=TANK_WIDTH * self.scale,
                                   height=TANK_HEIGHT * self.scale)
        self.label = tk.Label(master=self.frame, image=self.photo)
        self.label.pack()
        try:
            with open('autosave.json') as fileobj:
                super().__init__(GermTank(fileobj.read()))
        except FileNotFoundError:
            super().__init__(GermTank())

    def do_frame(self):
        """Called every frame"""

        self.tank.update(False)
        try:
            paint(self.photo, self.tank.get_pixels(), self.scale)
        except tk.TclError:
            # window destroyed
            self.stop_requested = True

    def close(self):
        """Called when the app closes"""

        try:
            self.root.destroy()
        except tk.TclError:
            # app already destroyed
            self.stop_requested = True
        with open('autosave.json', 'w') as fileobj:
            fileobj.write(self.tank.to_json())

    def inspect(self, event):
        """Inspects the clicked cell when the tank is paused"""

        if self.pause:
            x = int(event.x / self.scale - 1)
            y = int(event.y / self.scale - 1)
            try:
                germ = self.tank.tank[y][x]
            except IndexError:
                return
            if germ and germ['brain']:
                print("\nGERM CODE:")
                pprint(germ['brain'].code)

def main(args):
    if len(args) > 1 and args[1] == "-H":
        runner = HeadlessRunner()
        runner.run()
    else:
        root = tk.Tk()
        runner = VisualRunner(root=root)
        _thread.start_new_thread(runner.run, tuple())
        root.mainloop()

if __name__ == "__main__":
    main(sys.argv)
