"""Classes for actually running a tank simulation"""

import sys
import tkinter as tk
import signal
from abc import ABC, abstractmethod
from time import time_ns

from germ_tank import GermTank, TANK_WIDTH, TANK_HEIGHT

def paint(image, pixels, scale=1):

    image.put('black', (0, 0, TANK_WIDTH * scale, TANK_HEIGHT * scale))
    for x, y, r, g, b in pixels:
        image.put("#%02x%02x%02x" % (r, g, b),
                  (x * scale, y * scale, x * scale + scale, y * scale + scale))

class TankRunner(ABC):
    """Base class for tank runners"""

    def __init__(self, germ_tank):
        """Class constructor"""

        self.stop_requested = False
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
            start_time = time_ns()
            self.do_frame()
            elapsed = time_ns() - start_time
            self.frames_executed += 1
            # After first 500 frames, print stats every 10k frames
            # On frame 200, start gathering timing data, then print stats when 50 entries gathered
            if self.frames_executed % 10000 == 200 or self.frame_timings:
                self.frame_timings.append(elapsed)
                if len(self.frame_timings) >= 50:
                    self.print_stats()
                    self.frame_timings = []
        self.close()

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

class VisualRunner(tk.Frame, TankRunner):
    """Allows for running a tank with visual feedback"""

    def __init__(self, master=None):
        """Class constructor"""

        super(tk.Frame, self).__init__(master)
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
                super(TankRunner, self).__init__(GermTank(fileobj.read()))
        except FileNotFoundError:
            super(TankRunner, self).__init__(GermTank())

    def do_frame(self):
        """Called every frame"""

        self.tank.update(False)
        paint(self.photo, self.tank.get_pixels(), self.scale)
        self.master.update_idletasks()
        self.master.update()

    def close(self):
        """Called when the app closes"""

        with open('autosave.json', 'w') as fileobj:
            fileobj.write(self.tank.to_json())
        self.master.destroy()

def main(args):
    if len(args) > 1 and args[1] == "-H":
        runner = HeadlessRunner()
    else:
        runner = VisualRunner(master=tk.Tk())
    runner.run()

if __name__ == "__main__":
    main(sys.argv)
