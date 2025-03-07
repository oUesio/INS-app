import numpy as np
from ins_tools.util import *
from ins_tools.INS_realtime import INS

class RealTime:
    def __init__(self, ins, win, thresh):
        self.x = None
        self.ins = ins # ins first batch
        self.zv = None
        self.batch_pointer = 0
        self.win = win
        self.thresh = thresh

    def estimates(self, imudata):
        # Get zv estimates for batch
        print ('Batch pointer: '+str(self.batch_pointer))
        batch = imudata[self.batch_pointer:]
        zv = self.ins.Localizer.compute_zv_lrt(imudata=batch, W=self.win, G=self.thresh)
        # Get position estimates
        x = self.ins.baseline(imudata=batch, zv=zv)
        self.batch_pointer = len(imudata) # save last end position CHANGE THIS TO LAST TRUE 
        if self.x is None and self.zv is None:
            self.x, self.zv = x, zv
            print ('intial x and zv')
        else:
            print ('add x and zv')
            self.x = np.concatenate((self.x, x))
            self.zv = np.concatenate((self.zv, zv))
        return self.x, self.batch_pointer



