import numpy as np
from ins_tools.util import *
from ins_tools.INS_realtime import INS

class RealTime:
    def __init__(self, ins, win, thresh):
        self.ins = ins # ins first batch
        self.win = win
        self.thresh = thresh

    def estimates(self, imubatch, init):
        zv = self.ins.Localizer.compute_zv_lrt(imudata=imubatch, W=self.win, G=self.thresh)
        x = self.ins.baseline(imudata=imubatch, zv=zv, init=init)
        
        #self.x, self.zv = (x, zv) if self.x is None and self.zv is None else (np.concatenate((self.x, x[1:])), np.concatenate((self.zv, zv[1:])))
        # zv might be useful to plot as well

        # remove the extra from previous batch
        return x if init else x[1:] 



