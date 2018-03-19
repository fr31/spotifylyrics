#!/usr/bin/env python3

from PyQt5 import QtCore, QtGui, QtWidgets
import backend
import time
import threading
import os
import re

if os.name == "nt":
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("spotifylyrics.version1")

class Communicate(QtCore.QObject):
    signal = QtCore.pyqtSignal(str, str)
   
class LyricsTextBrowserWidget(QtWidgets.QTextBrowser):
    wheelSignal = QtCore.pyqtSignal()
    
    def wheelEvent(self, e):
        try:
            modifiers = e.modifiers()
            if modifiers == QtCore.Qt.ControlModifier:
                numPixels = e.pixelDelta()
                numDegrees = e.angleDelta()
                factor = 1
                if( not numPixels.isNull()):
                    sign = 1 if numPixels.y() > 0 else -1
                    ui.change_fontsize(sign * factor)
                elif( not numDegrees.isNull()):
                    sign = 1 if numDegrees.y() > 0 else -1
                    ui.change_fontsize(sign * factor)
            else:
                super(QtWidgets.QTextBrowser, self).wheelEvent(e)
        except:
            pass
                    
class Ui_Form(object):
               
    sync = False
    ontop = False
    open_spotify = False
    changed = False
    darktheme = False
    if os.name == "nt":
        settingsdir = os.getenv("APPDATA") + "\\SpotifyLyrics\\"
    else:
        settingsdir = os.path.expanduser("~") + "/.SpotifyLyrics/"
    def __init__(self):
        super().__init__()

        self.comm = Communicate()
        self.comm.signal.connect(self.refresh_lyrics)
        self.setupUi(Form)
        self.set_style()
        self.load_save_settings()
        if self.open_spotify:
            self.spotify()
        self.start_thread()

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(550, 610)
        Form.setMinimumSize(QtCore.QSize(350, 310))
        self.gridLayout_2 = QtWidgets.QGridLayout(Form)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_songname = QtWidgets.QLabel(Form)
        self.label_songname.setObjectName("label_songname")
        self.label_songname.setOpenExternalLinks(True)
        self.horizontalLayout_2.addWidget(self.label_songname, 0, QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)

        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText("Change Lyrics")
        self.pushButton.clicked.connect(self.change_lyrics)
        self.horizontalLayout_2.addWidget(self.pushButton, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        
        # Open Tab Button
        self.chordsButton = QtWidgets.QPushButton(Form)
        self.chordsButton.setObjectName("chordsButton")
        self.chordsButton.setText("Chords")
        self.chordsButton.clicked.connect(self.get_chords)
        self.horizontalLayout_2.addWidget(self.chordsButton, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.comboBox = QtWidgets.QComboBox(Form)
        self.comboBox.setGeometry(QtCore.QRect(160, 120, 69, 22))
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.horizontalLayout_2.addWidget(self.comboBox, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.fontBox = QtWidgets.QSpinBox(Form)
        self.fontBox.setMinimum(1)
        self.fontBox.setProperty("value", 10)
        self.fontBox.setObjectName("fontBox")
        self.horizontalLayout_2.addWidget(self.fontBox, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.textBrowser = LyricsTextBrowserWidget(Form)
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser.setAcceptRichText(True)
        self.textBrowser.setStyleSheet("font-size: %spt;" % self.fontBox.value() * 2)
        self.textBrowser.setFontPointSize(self.fontBox.value())
        self.verticalLayout_2.addWidget(self.textBrowser)
        self.gridLayout_2.addLayout(self.verticalLayout_2, 2, 0, 1, 1)

        self.retranslateUi(Form)
        self.fontBox.valueChanged.connect(self.update_fontsize)
        self.comboBox.currentIndexChanged.connect(self.optionschanged)
        QtCore.QMetaObject.connectSlotsByName(Form)
        Form.setTabOrder(self.textBrowser, self.comboBox)
        Form.setTabOrder(self.comboBox, self.fontBox)

    def load_save_settings(self, save=False):
        settingsfile = self.settingsdir + "settings.ini"
        if save is False:
            if os.path.exists(settingsfile):
                with open(settingsfile, 'r') as settings:
                    for line in settings.readlines():
                        lcline = line.lower()
                        if "syncedlyrics" in lcline:
                            if "true" in lcline:
                                self.sync = True
                            else:
                                self.sync = False
                        if "alwaysontop" in lcline:
                            if "true" in lcline:
                                self.ontop = True
                            else:
                                self.ontop = False
                        if "fontsize" in lcline:
                            set = line.split("=",1)[1].strip()
                            try:
                                self.fontBox.setValue(int(set))
                            except ValueError:
                                pass
                        if "openspotify" in lcline:
                            if "true" in lcline:
                                self.open_spotify = True
                            else:
                                self.open_spotify = False
                        if "darktheme" in lcline:
                            if "true" in lcline:
                                self.set_darktheme()
                            else:
                                pass
            else:
                directory = os.path.dirname(settingsfile)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open(settingsfile, 'w+') as settings:
                    settings.write("[settings]\nSyncedLyrics=False\nAlwaysOnTop=False\nFontSize=10\nOpenSpotify=False")
            if self.sync is True:
                self.comboBox.setItemText(2, ("Synced Lyrics (on)"))
            if self.ontop is True:
                Form.setWindowFlags(Form.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
                self.comboBox.setItemText(3, ("Always on Top (on)"))
                Form.show()
            if self.open_spotify is True:
                self.comboBox.setItemText(4, ("Open Spotify (on)"))
        else:
            with open(settingsfile, 'w+') as settings:
                settings.write("[settings]\n")
                if self.sync is True:
                    settings.write("SyncedLyrics=True\n")
                else:
                    settings.write("SyncedLyrics=False\n")
                if self.ontop is True:
                    settings.write("AlwaysOnTop=True\n")
                else:
                    settings.write("AlwaysOnTop=False\n")
                if self.open_spotify is True:
                    settings.write("OpenSpotify=True\n")
                else:
                    settings.write("OpenSpotify=False\n")
                if self.darktheme is True:
                    settings.write("DarkTheme=True\n")
                else:
                    settings.write("DarkTheme=False\n")
                settings.write("FontSize=%s" % str(self.fontBox.value()))

    def optionschanged(self):
        current_index = self.comboBox.currentIndex()
        if current_index == 1:
            if self.darktheme is False:
                self.set_darktheme()
            else:
                self.darktheme = False
                Form.setWindowOpacity(1.0)
                Form.setStyleSheet("")
                self.textBrowser.setStyleSheet("")
                self.label_songname.setStyleSheet("")
                self.comboBox.setStyleSheet("")
                self.fontBox.setStyleSheet("")
                self.pushButton.setStyleSheet("")
                self.chordsButton.setStyleSheet("")
                self.comboBox.setItemText(1, ("Dark Theme"))
                self.set_style()
        elif current_index == 2:
            if self.sync is True:
                self.sync = False
                self.comboBox.setItemText(2, ("Synced Lyrics"))
            else:
                self.sync = True
                self.comboBox.setItemText(2, ("Synced Lyrics (on)"))
        elif current_index == 3:
            if self.ontop is False:
                self.ontop = True
                Form.setWindowFlags(Form.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
                self.comboBox.setItemText(3, ("Always on Top (on)"))
                Form.show()
            else:
                self.ontop = False
                Form.setWindowFlags(Form.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
                self.comboBox.setItemText(3, ("Always on Top"))
                Form.show()
        elif current_index == 4:
            if self.open_spotify is True:
                self.open_spotify = False
                self.comboBox.setItemText(4, ("Open Spotify"))
            else:
                self.open_spotify = True
                self.comboBox.setItemText(4, ("Open Spotify (on)"))
        elif current_index == 5:
            self.load_save_settings(save=True)
        else:
            pass
        self.comboBox.setCurrentIndex(0)

    def set_style(self):
        self.lyricsTextAlign = QtCore.Qt.AlignLeft
        if os.path.exists(self.settingsdir + "theme.ini"):
            themefile = self.settingsdir + "theme.ini"
        else:
            themefile = "theme.ini"
        if os.path.exists(themefile):
            with open(themefile, 'r') as theme:
                try:
                    for setting in theme.readlines():
                        lcsetting = setting.lower()
                        try:
                            set = setting.split("=",1)[1].strip()
                        except IndexError:
                            set = ""
                        if "lyricstextalign" in lcsetting:
                            if set == "center":
                                self.lyricsTextAlign = QtCore.Qt.AlignCenter
                            elif set == "right":
                                self.lyricsTextAlign = QtCore.Qt.AlignRight
                            else:
                                pass
                        if "windowopacity" in lcsetting:
                            Form.setWindowOpacity(float(set))
                        if lcsetting.startswith("backgroundcolor"):
                            Form.setStyleSheet("background-color: %s;" % set)
                        if "lyricsbackgroundcolor" in lcsetting:
                            style = self.textBrowser.styleSheet()
                            style = style + "background-color: %s;" % set
                            self.textBrowser.setStyleSheet(style)
                        if "lyricstextcolor" in lcsetting:
                            style = self.textBrowser.styleSheet()
                            style = style + "color: %s;" % set
                            self.textBrowser.setStyleSheet(style)
                        if "lyricsfont" in lcsetting:
                            style = self.textBrowser.styleSheet()
                            style = style + "font-family: %s;" % set
                            self.textBrowser.setStyleSheet(style)
                        if "songnamecolor" in lcsetting:
                            style = self.label_songname.styleSheet()
                            style = style + "color: %s;" % set
                            self.label_songname.setStyleSheet(style)
                        if "fontboxbackgroundcolor" in lcsetting:
                            style = self.fontBox.styleSheet()
                            style = style + "background-color: %s;" % set
                            self.comboBox.setStyleSheet(style)
                            self.fontBox.setStyleSheet(style)
                            self.pushButton.setStyleSheet(style)
                            self.chordsButton.setStyleSheet(style)
                        if "fontboxtextcolor" in lcsetting:
                            style = self.fontBox.styleSheet()
                            style = style + "color: %s;" % set
                            self.comboBox.setStyleSheet(style)
                            self.fontBox.setStyleSheet(style)
                            self.pushButton.setStyleSheet(style)
                            self.chordsButton.setStyleSheet(style)
                        if "songnameunderline" in lcsetting:
                            if "true" in set.lower():
                                style = self.label_songname.styleSheet()
                                style = style + "text-decoration: underline;"
                                self.label_songname.setStyleSheet(style)
                except Exception:
                    pass
        else:
            self.label_songname.setStyleSheet("color: black; text-decoration: underline;")
            pass

    def set_darktheme(self):
        self.darktheme = True
        Form.setWindowOpacity(1.0)
        Form.setStyleSheet("background-color: #282828;")
        self.textBrowser.setStyleSheet("background-color: #181818; color: #ffffff;")
        self.label_songname.setStyleSheet("color: #9c9c9c; text-decoration: underline;")
        self.comboBox.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.fontBox.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.pushButton.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.chordsButton.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.comboBox.setItemText(1, ("Dark Theme (on)"))

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def set_lyrics_with_alignment(self, lyrics):
        self.textBrowser.clear()
        for line in lyrics.splitlines():
            self.textBrowser.append(line)
            self.textBrowser.setAlignment(self.lyricsTextAlign)
        
    def change_fontsize(self, offset):
        self.fontBox.setValue( self.fontBox.value() + offset)
        self.update_fontsize()
        
    def update_fontsize(self):
        self.textBrowser.setFontPointSize(self.fontBox.value())
        style = self.textBrowser.styleSheet()
        style = style.replace('%s' % style[style.find("font"):style.find("pt;") + 3], '')
        style = style.replace('p ', '')
        self.textBrowser.setStyleSheet(style + "p font-size: %spt;" % self.fontBox.value() * 2)
        lyrics = self.textBrowser.toPlainText()
        self.set_lyrics_with_alignment(lyrics)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Spotify Lyrics - {}".format(backend.version())))
        Form.setWindowIcon(QtGui.QIcon(self.resource_path('icon.png')))
        if backend.versioncheck() == True:
            self.label_songname.setText(_translate("Form", "Spotify Lyrics"))
        else:
            self.label_songname.setText(_translate("Form", "Spotify Lyrics <style type=\"text/css\">a {text-decoration: none}</style><a href=\"https://github.com/fr31/spotifylyrics/releases\"><sup>(update)</sup></a>"))
        self.textBrowser.setText(_translate("Form", "Play a song in Spotify to fetch lyrics."))
        self.fontBox.setToolTip(_translate("Form", "Font Size"))
        self.comboBox.setItemText(0, _translate("Form", "Options"))
        self.comboBox.setItemText(1, _translate("Form", "Dark Theme"))
        self.comboBox.setItemText(2, _translate("Form", "Synced Lyrics"))
        self.comboBox.setItemText(3, _translate("Form", "Always on Top"))
        self.comboBox.setItemText(4, _translate("Form", "Open Spotify"))
        self.comboBox.setItemText(5, _translate("Form", "Save Settings"))

    def add_service_name_to_lyrics(self, lyrics, service_name):
        return '''<span style="font-size:%spx; font-style:italic;">Lyrics loaded from: %s</span>\n\n%s''' % ((self.fontBox.value()-2) * 2, service_name, lyrics)

    def lyrics_thread(self, comm):
        oldsongname = ""
        style = self.label_songname.styleSheet()
        if style == "":
            color = "color: black"
        else:
            color = style
        while True:
            songname = backend.getwindowtitle()
            self.changed = False
            if oldsongname != songname:
                if songname != "Spotify" and songname != "":
                    oldsongname = songname
                    comm.signal.emit(songname, "Loading...")
                    start = time.time()
                    if self.sync == True:
                        lyrics, url, service_name, timed = backend.getlyrics(songname, sync=True)
                    else:
                        lyrics, url, service_name, timed = backend.getlyrics(songname)
                    if url == "":
                        header = songname
                    else:
                        header = '''<style type="text/css">a {text-decoration: none; %s}</style><a href="%s">%s</a>''' % (color, url, songname)
                    if timed == True:
                        lrc = []
                        lyricsclean = ""
                        firstline = False
                        for line in lyrics.splitlines():
                            lrc.append(line)
                            if line.startswith(("[0", "[1", "[2")):
                                firstline = True
                                regex = re.compile('\[.+?\]')
                                line = regex.sub('', line)
                                lyricsclean = lyricsclean + line.strip() + "\n"
                            elif line == "" and firstline == True:
                                lyricsclean = lyricsclean + "\n"
                        
                        
                        
                        comm.signal.emit(header, self.add_service_name_to_lyrics(lyricsclean, service_name))
                        count = -1
                        firstline = False
                        for line in lrc:
                            if self.sync == False:
                                self.change_lyrics()
                                break
                            if self.changed == True:
                                self.changed = False
                                break
                            if line == "" and firstline == True:
                                count += 1
                            if line.startswith(("[0", "[1", "[2")):
                                firstline = True
                                count += 1
                                ltime = line[line.find("[") + 1:line.find("]")]
                                add = float(ltime[0:2]) * 60
                                try:
                                    ltime = float(ltime[3:])
                                except ValueError:
                                    ltime = 0.0
                                rtime = add + ltime - 0.5
                                lyrics1 = lyricsclean.splitlines()
                                regex = re.compile('\[.+?\]')
                                line = regex.sub('', line)
                                regex = re.compile('\<.+?\>')
                                line = regex.sub('', line)
                                lyrics1[count] = "<b>%s</b>" % line.strip()
                                if count-2 > 0:
                                    lyrics1[count-2] = "<a name=\"#scrollHere\">%s</a>" % lyrics1[count-2].strip()
                                boldlyrics = '<br>'.join(lyrics1)
                                while True:
                                    if rtime <= time.time() - start and backend.getwindowtitle() != "Spotify":
                                        if self.changed == True or self.sync == False:
                                            break
                                        boldlyrics = '<style type="text/css">p {font-size: %spt}</style><p>' % self.fontBox.value() * 2 + boldlyrics + '</p>'
                                        comm.signal.emit(header, self.add_service_name_to_lyrics(boldlyrics, service_name))
                                        time.sleep(0.5)
                                        break
                                    elif backend.getwindowtitle() == "Spotify":
                                        time.sleep(0.2)
                                        start = start + 0.2
                                    else:
                                        if songname != backend.getwindowtitle():
                                            break
                                        else:
                                            time.sleep(0.2)
                            if songname != backend.getwindowtitle() and backend.getwindowtitle() != "Spotify":
                                break
                    if timed == False:
                        comm.signal.emit(header, self.add_service_name_to_lyrics(lyrics, service_name))
            time.sleep(1)

    def start_thread(self):
        lyricsthread = threading.Thread(target=self.lyrics_thread, args=(self.comm,))
        lyricsthread.daemon = True
        lyricsthread.start()

    def refresh_lyrics(self, songname, lyrics):
        _translate = QtCore.QCoreApplication.translate
        if backend.getwindowtitle() != "":
            self.label_songname.setText(_translate("Form", songname))
        self.set_lyrics_with_alignment(_translate("Form", lyrics))
        self.textBrowser.scrollToAnchor("#scrollHere")

    def get_chords(self):
        _translate = QtCore.QCoreApplication.translate
        if self.label_songname.text() not in ("", "Spotify", "Spotify Lyrics"):
            songname = backend.getwindowtitle()
            backend.load_chords()
        else:
            self.textBrowser.append(_translate("Form", "I'm sorry, Dave. I'm afraid I can't do that."))


    def change_lyrics(self):
        _translate = QtCore.QCoreApplication.translate
        if self.label_songname.text() not in  ("", "Spotify", "Spotify Lyrics"):
            self.changed = True
            changethread = threading.Thread(target=self.change_lyrics_thread)
            changethread.start()
        else:
            self.textBrowser.append(_translate("Form", "I'm sorry, Dave. I'm afraid I can't do that."))

    def change_lyrics_thread(self):
        songname = backend.getwindowtitle()
        self.comm.signal.emit(songname, "Loading...")
        oldsongname = ""
        style = self.label_songname.styleSheet()

        if style == "":
            color = "color: black"
        else:
            color = style

        lyrics, url, service_name, timed = backend.next_lyrics()
        if url == "":
            header = songname
        else:
            header = '''<style type="text/css">a {text-decoration: none; %s}</style><a href="%s">%s</a>''' % (color, url, songname)

        self.comm.signal.emit(header, self.add_service_name_to_lyrics(lyrics, service_name))

    def spotify(self):
        backend.open_spotify()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    Form.show()
    sys.exit(app.exec_())
