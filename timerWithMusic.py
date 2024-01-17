import wx
import wx.gizmos as gizmos
import wx.media
import wx.lib.agw.floatspin as FS
import sys, argparse, time
import os.path


class MusicPlayer:
    def __init__(self, parent) -> None:
        self.musicFiles = []
        self.pos = 0
        self.player = wx.media.MediaCtrl(parent, -1)
        parent.Bind(wx.media.EVT_MEDIA_STOP, self.OnMediaStop, self.player)
        parent.Bind(wx.media.EVT_MEDIA_LOADED, self.OnMediaLoaded, self.player)
        self.shouldplay = False
        self.vol = None
          
    def OnMediaStop(self, event):
        print ("OnMediaStop", event, self.shouldplay, self.player.GetState())
        if self.shouldplay:
            ret = self.player.Load(self.__getNextSong())
    
    def OnMediaLoaded(self, event):
        print ("OnMediaLoaded", event, self.player.GetState())
        if self.vol is not None:
            self.setVol(self.vol)
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

    def addMusicFromFile(self, filename):
        if not self.__checkExt(filename):
            raise Exception("Extension not supported", filename)
        self.musicFiles.append(self.__normPath(filename))

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
        print ("volUp", inc, volOld * 100.0, vol * 100.0, self.player.GetVolume() * 100.0 )

    def volDown(self, dec = 5):
        self.volUp(inc = -dec)

    def setPosition(self, pos):
        self.pos = self.pos % len(self.musicFiles)

    def setVol(self, vol = 100):
        if self.player.GetVolume() < 0.00001 and  self.player.GetState() == wx.media.MEDIASTATE_STOPPED:
            self.vol = vol
        else:
            self.player.SetVolume(self.volToIntern(vol))
        print ("volUp", vol, self.player.GetVolume() * 100.0, self.player.GetState() )
        

    def __getNextSong(self):
        if not self.musicFiles:
            raise Exception("No files in playlist!")
        filename = self.musicFiles[self.pos]
        self.pos = (self.pos + 1) % len(self.musicFiles)
        return filename      

class InputTimeDialog ( wx.Dialog ):
    def __init__( self, parent, startValue = 2.0, setter = None ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.DEFAULT_DIALOG_STYLE )
        self.setter = setter
        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
        bSizer1 = wx.BoxSizer( wx.VERTICAL )
        bSizer2 = wx.BoxSizer( wx.HORIZONTAL )
        self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"Zeit in Minuten", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_staticText1.Wrap( -1 )
        bSizer2.Add( self.m_staticText1, 0, wx.ALL, 5 )
        self.floatspin = FS.FloatSpin(self, -1, pos=(50, 50), min_val=0.1, max_val=60,
                                 increment=0.5, value=startValue, agwStyle=FS.FS_LEFT)
        self.floatspin.SetFormat("%f")
        self.floatspin.SetDigits(1)    
        bSizer2.Add( self.floatspin, 0, wx.ALL, 5 )
        bSizer1.Add( bSizer2, 1, wx.EXPAND, 5 )
        bSizer1.Add( ( 0, 0), 1, wx.EXPAND, 5 )
        bSizer3 = wx.BoxSizer( wx.HORIZONTAL )
        bSizer3.Add( ( 0, 0), 1, wx.EXPAND, 5 )
        self.m_button1 = wx.Button( self, wx.ID_ANY, u"OK", wx.DefaultPosition, wx.DefaultSize, 0 )
        bSizer3.Add( self.m_button1, 0, wx.ALL, 5 )
        self.m_button1.Bind(wx.EVT_BUTTON, self.OnClose)
        self.m_button2 = wx.Button( self, wx.ID_ANY, u"Abbrechen", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.m_button2.Bind(wx.EVT_BUTTON, self.OnClose)
        bSizer3.Add( self.m_button2, 0, wx.ALL, 5 )
        bSizer1.Add( bSizer3, 1, wx.EXPAND, 5 )
        self.SetSizer( bSizer1 )
        self.Layout()
        bSizer1.Fit( self )
        self.Centre( wx.BOTH )

    def OnClose(self, event):
        if self.m_button1 == event.EventObject and self.setter is not None:
            # OK button pressed. Call setter
            self.setter(self.floatspin.GetValue())
        self.Destroy()

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
        else:
            event.Skip()

    def OnContextMenu(self, event):
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.menu, pos)

    def ChangeTimer ( self, val):
        self.timerCount = 60 * val
        self.SetTitle(title=f'Timer - {self.fmtTimer(self.timerCount)}')
        self.Paint()

    def OnSetTimer(self, event):
        dialog = InputTimeDialog(self, startValue = self.timerCount / 60, setter = self.ChangeTimer)
        dialog.ShowModal()
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
    parser.add_argument("-p", "--position", help="With which music file to start playing. 0 ist the first file", type=int)
    parser.add_argument("-v", "--volume", help="Volume in Percent", type=int)
    args = parser.parse_args(argv[1:])

    app = wx.App()
    frame = LEDTimer(None, -1, timer=args.minutes)
    app.Bind(wx.EVT_CHAR, frame.onKeyPressed)

    if args.dir:
        frame.musicPlayer.addMusicFromDir(args.dir)
    for filename in args.files:
        frame.musicPlayer.addMusicFromFile(filename)
    if args.position:
        frame.musicPlayer.setPosition(args.position)
    if args.volume:
        frame.musicPlayer.setVol(args.volume)
    frame.Show(True)
    app.SetTopWindow(frame)
    app.MainLoop()

if __name__ == '__main__':
    args = sys.argv
    #args = [sys.argv[0]] + ["-d", "/home/thias/Desktop/LSL/music/MaartenSchellekens/", "-m2" "-v15"]
    #args = [sys.argv[0]] + ["-d", "/home/thias/Desktop/LSL/music/guitar/", "-m10", "-v10" ]
    sys.exit(main(args))