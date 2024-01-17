import wx
import wx.gizmos as gizmos
import wx.media
import sys, argparse, time
import os.path


class MusicPlayer:
    def __init__(self, parent) -> None:
        self.musicFiles = []
        self.pos = None
        self.player = wx.media.MediaCtrl(parent, -1)
        parent.Bind(wx.media.EVT_MEDIA_STOP, self.OnMediaStop, self.player)
        parent.Bind(wx.media.EVT_MEDIA_LOADED, self.OnMediaLoaded, self.player)
        self.shouldplay = False
          
    def OnMediaStop(self, event):
        print ("OnMediaStop", event, self.shouldplay)
        if self.shouldplay:
            ret = self.player.Load(self.__getNextSong())
    
    def OnMediaLoaded(self, event):
        print ("OnMediaStop", event)
        ret = self.player.Play()

    allowedExts = [".flac", ".mp3", ".ogg"]
    def __checkExt(self, filename):
        return os.path.splitext(filename)[1].lower() in self.allowedExts

    @staticmethod
    def __normPath(filename):
        return os.path.normpath(filename)

    def addMusicFromDir(self, dir):
        files = os.listdir(dir)
        files = [ self.__normPath(os.path.join(dir, file)) for file in files if self.__checkExt(file)]
        files.sort()
        self.musicFiles += files
        if not self.pos:
            self.pos = 0

    def addMusicFromFile(self, filename):
        if not self.__checkExt(filename):
            raise Exception("Extension not supported", filename)
        self.musicFiles.append(self.__normPath(filename))
        if not self.pos:
            self.pos = 0

    def startPlay(self):
        if not self.musicFiles:
            raise Exception("No files in playlist!")
        ret = self.player.Load(self.__getNextSong())
        self.shouldplay = True


    def stopPlay(self):
        self.shouldplay = False
        self.player.Stop()
        

    def fadeout(self, seconds):
        self.shouldplay = False
        vol = self.player.GetVolume()
        step = vol / seconds / 200.0
        for nextVol in range(int(seconds * 200)):
            self.player.SetVolume(vol-step*nextVol)
            time.sleep(1/200.0)
        self.player.Stop()
        self.player.SetVolume(vol)

    @staticmethod
    def volToIntern(vol):
        return vol / 100.0

    @staticmethod
    def internToVol(vol):
        return int (vol * 100 + 0.5)

    def volUp(self, inc=5):
        volOld = self.player.GetVolume() 
        vol = self.volToIntern(self.internToVol(volOld) + inc)
        self.player.SetVolume(vol)
        print ("volUp", inc, volOld, vol, self.player.GetVolume() )

    def volDown(self, dec = 5):
        self.volUp(inc = -dec)

    def __getNextSong(self):
        if not self.musicFiles:
            raise Exception("No files in playlist!")
        filename = self.musicFiles[self.pos]
        self.pos = (self.pos + 1) % len(self.musicFiles)
        return filename      

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
        pos = wx.DefaultPosition
        wx.Frame.__init__(self, parent, id, title=f'Timer - {self.fmtTimer(self.timerCount)}', pos=pos, size=(600, 300))
        self.musicPlayer = MusicPlayer(self)
        
        self.menu = wx.Menu()
        self.menuitems = [ 
            (wx.MenuItem(self.menu, wx.NewIdRef(), 'Start'),  self.OnStartTimer),
            (wx.MenuItem(self.menu, wx.NewIdRef(), 'Reset'),  lambda event : self.StopTimer()),
            (wx.MenuItem(self.menu, wx.NewIdRef(), 'Timer einstellen'),  self.OnSetTimer),
            (wx.MenuItem(self.menu, wx.NewIdRef(), 'Lauter'), lambda event : self.musicPlayer.volUp()), 
            (wx.MenuItem(self.menu, wx.NewIdRef(), 'Leiser'), lambda event : self.musicPlayer.volDown()),  
        ]
                           
        for menuitem, handler in self.menuitems:
          self.menu.Append(menuitem)
          if handler is not None:
            self.Bind(wx.EVT_MENU, handler, menuitem)

        size = wx.Size(450, 170)
        style = gizmos.LED_ALIGN_CENTER | wx.BORDER_NONE | wx.NO_BORDER # | gizmos.LED_DRAW_FADED
        self.SetDoubleBuffered(True)
        bSizer1 = wx.BoxSizer( wx.VERTICAL )

        self.led = LEDCtrl(self, -1, pos, size, style)

        bSizer1.Add( self.led, 1, wx.ALL|wx.EXPAND, 50 )


        self.SetSizer( bSizer1 )
        self.SetBackgroundColour(wx.BLACK)
        
        self.timer = wx.Timer(self, -1)
        self.Paint()

        self.led.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.led.Bind(wx.EVT_LEFT_UP, self.OnStartTimer)        
        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)
        self.Bind(wx.EVT_LEFT_UP, self.OnStartTimer)        
        self.led.Bind(wx.EVT_CHAR, self.onKeyPressed)
        self.Bind(wx.EVT_CHAR, self.onKeyPressed)
        
        self.Bind(wx.EVT_TIMER, self.OnTimer)


        self.led.SetBackgroundColour(wx.BLACK)
        self.led.SetForegroundColour(wx.LIGHT_GREY)
        self.led.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        
    def fmtTimer(self, value):
        value = int(value)
        return f'{value // 60:01}:{value % 60:02}'

    def onKeyPressed(self, event):
        print ("Key Pressed:", event.GetKeyCode(), ord('+'), ord('-'))
        key = event.GetKeyCode()
        if ord('+') == key:
            self.musicPlayer.volUp()
        elif ord('-') == key:
            self.musicPlayer.volDown()

    def OnContextMenu(self, event):
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.menu, pos)

    def OnSetTimer(self, event):
        pass

    def OnStartTimer(self, event=None):
        if not self.started:
            try:
                self.musicPlayer.startPlay()
            except Exception as exc:
                print (exc)
            self.starttime = time.time()
            self.started = True
            self.Paint()
            self.timer.Start(1000)

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
                self.musicPlayer.fadeout(1)
                self.timer.Stop()
                self.started = False
    
    def StopTimer(self):
        if self.started:
            self.musicPlayer.fadeout(0.5)
            self.timer.Stop()
            self.started = False
            self.Paint()

        
def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--minutes", type=float, default=2.0)
    parser.add_argument("-d", "--dir", help="Directory to use for music")
    parser.add_argument("-f", "--files", help="File to use for music. Could be given multiple time", default=[], action="append")
    args = parser.parse_args(argv[1:])

    app = wx.App()
    frame = LEDTimer(None, -1, timer=args.minutes)
    app.Bind(wx.EVT_CHAR, frame.onKeyPressed)

    if args.dir:
        frame.musicPlayer.addMusicFromDir(args.dir)
    for filename in args.files:
        frame.musicPlayer.addMusicFromFile(filename)
    frame.Show(True)
    app.SetTopWindow(frame)
    app.MainLoop()

if __name__ == '__main__':
    args = sys.argv
    #args = [sys.argv[0]] + ["-d", "/home/thias/Desktop/LSL/music/Hasta La Blister/", "-m.2" ]
    args = [sys.argv[0]] + ["-d", "/home/thias/Desktop/LSL/music/guitar/", "-m10" ]
    sys.exit(main(args))