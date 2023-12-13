import wx
import wx.gizmos as gizmos
import sys, argparse, time
import musicPlayer



class LEDCtrl (gizmos.LEDNumberCtrl):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        c = self.const
        self.const.DIGITS['9'] = c.LINE1 | c.LINE2 | c.LINE3 | c.LINE6 | c.LINE7 | c.LINE4

class LEDTimer(wx.Frame):
    """
    create nice LED clock showing the current time
    """
    def __init__(self, parent, id, timer = 2):
        self._lastCurrSec = 0
        self.starttime = None
        self.timerCount = 60 * timer
        self.started = False
        self.musicPlayer = musicPlayer.MusicPlayer()
        pos = wx.DefaultPosition
        wx.Frame.__init__(self, parent, id, title=f'Timer - {self.fmtTimer(self.timerCount)}', pos=pos, size=(600, 300))
        size = wx.Size(450, 170)
        style = gizmos.LED_ALIGN_CENTER | wx.BORDER_NONE | wx.NO_BORDER | gizmos.LED_DRAW_FADED
        self.SetDoubleBuffered(True)
        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        self.led = LEDCtrl(self, -1, pos, size, style)

        bSizer1.Add( self.led, 1, wx.ALL|wx.EXPAND, 50 )


        self.SetSizer( bSizer1 )
        self.SetBackgroundColour(wx.BLACK)
        
        self.timer = wx.Timer(self, -1)
        self.Paint()

        self.led.Bind(wx.EVT_RIGHT_UP, self.StartTimer)
        self.led.Bind(wx.EVT_LEFT_UP, self.StartTimer)        
        self.Bind(wx.EVT_RIGHT_UP, self.StartTimer)
        self.Bind(wx.EVT_LEFT_UP, self.StartTimer)        
        self.Bind(wx.EVT_TIMER, self.OnTimer)

        self.led.SetBackgroundColour(wx.BLACK)
        self.led.SetForegroundColour(wx.LIGHT_GREY)
        self.led.SetBackgroundStyle(wx.BG_STYLE_PAINT)

    def fmtTimer(self, value):
        return f'{value // 60:01}:{value % 60:02}'

    def StartTimer(self, event):
        if not self.started:
            self.timer.Start(100)
            try:
                self.musicPlayer.startPlay()
            except Exception:
                pass
            self.starttime = time.time()
            self.started = True

    def Paint(self):
        alreadyRun = 0
        if self.started:
            alreadyRun = time.time()-self.starttime
        currSec = int(self.timerCount - alreadyRun)
        if currSec < 0: 
            currSec = 0
        if self._lastCurrSec != currSec:
            self.led.SetValue(self.fmtTimer(currSec))
        self._lastCurrSec = currSec
        return currSec

    def OnTimer(self, event):
        currSec = self.Paint()
        if self.started:
            if currSec == 0:
                self.musicPlayer.fadeout(1000)
                self.timer.Stop()
                self.started = False

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--minutes", type=int, default=2)
    parser.add_argument("-d", "--dir", help="Directory to use for music")
    parser.add_argument("-f", "--files", help="File to use for music. Could be given multiple time", default=[], action="append")
    args = parser.parse_args(argv[1:])

    app = wx.App()
    frame = LEDTimer(None, -1, timer=args.minutes)
    if args.dir:
        frame.musicPlayer.addMusicFromDir(args.dir)
    for filename in args.files:
        frame.musicPlayer.addMusicFromFile(filename)
    frame.Show(True)
    app.SetTopWindow(frame)
    app.MainLoop()
    frame.musicPlayer.stopPlay()

if __name__ == '__main__':
    sys.exit(main(sys.argv))