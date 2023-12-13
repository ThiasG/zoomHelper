import pygame.mixer
import threading, os, time


class MusicPlayer:
    def __init__(self) -> None:
        pygame.init()
        self.endEvent =  pygame.event.custom_type()
        pygame.mixer.music.set_endevent( self.endEvent )
        self.musicFiles = []
        self.pos = None
        self.playerThread = None
        self._threadStopEvent = threading.Event()
        self._threadStopLock = threading.RLock()
        
    def __del__(self):
        self.__threadStop()
        pygame.quit()
    
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
        pygame.mixer.music.load(self.__getNextSong())
        pygame.mixer.music.queue(self.__getNextSong())
        pygame.mixer.music.play()
        if not self.playerThread:
            self._threadStopEvent.clear()
            self.playerThread = threading.Thread(target=self.__playerThreadFunc, name="PlayerThread")
            self.playerThread.start()

    def stopPlay(self):
        self.__threadStop()
        pygame.mixer.music.stop()

    def fadeout(self, seconds):
        self.__threadStop()
        pygame.mixer.music.fadeout(seconds)

    def __threadStop(self):
        self._threadStopLock.acquire()
        try:
            if self.playerThread:
                self._threadStopEvent.set()
                self.playerThread.join()
                self.__playerThreadFunc = None
        finally:
            self._threadStopLock.release()

    def __getNextSong(self):
        if not self.musicFiles:
            raise Exception("No files in playlist!")
        filename = self.musicFiles[self.pos]
        self.pos = (self.pos + 1) % len(self.musicFiles)
        return filename      

    def __playerThreadFunc(self):
        while self._threadStopEvent.wait(0.5) is not True:
            for event in pygame.event.get():
                if event.type == self.endEvent:
                    time.sleep(5)
                    try:
                        pygame.mixer.music.queue(self.__getNextSong())
                    except:
                        pass
        



            
        





    