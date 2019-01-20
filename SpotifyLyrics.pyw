#!/usr/bin/env python3

import os
import re
import threading
import time

import pylrc
from PyQt5 import QtCore, QtGui, QtWidgets

import backend

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
                if not numPixels.isNull():
                    sign = 1 if numPixels.y() > 0 else -1
                    ui.change_fontsize(sign * factor)
                elif not numDegrees.isNull():
                    sign = 1 if numDegrees.y() > 0 else -1
                    ui.change_fontsize(sign * factor)
            else:
                super(QtWidgets.QTextBrowser, self).wheelEvent(e)
        except:
            pass


brackets = re.compile(r'\[.+?\]')
html_tags = re.compile(r'<.+?>')


class Ui_Form(object):
    sync = False
    ontop = False
    open_spotify = False
    changed = False
    darktheme = False
    infos = False
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
        self.horizontalLayout_1 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_1.setObjectName("horizontalLayout_1")
        self.label_songname = QtWidgets.QLabel(Form)
        self.label_songname.setObjectName("label_songname")
        self.label_songname.setOpenExternalLinks(True)
        self.horizontalLayout_2.addWidget(self.label_songname, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)

        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setText("Change Lyrics")
        self.pushButton.clicked.connect(self.change_lyrics)
        self.horizontalLayout_2.addWidget(self.pushButton, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.saveButton = QtWidgets.QPushButton(Form)
        self.saveButton.setObjectName("saveButton")
        self.saveButton.setText("Save Lyrics")
        self.saveButton.clicked.connect(self.save_lyrics)
        self.horizontalLayout_2.addWidget(self.saveButton, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

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
        self.comboBox.addItem("")
        self.horizontalLayout_2.addWidget(self.comboBox, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.fontBox = QtWidgets.QSpinBox(Form)
        self.fontBox.setMinimum(1)
        self.fontBox.setProperty("value", 10)
        self.fontBox.setObjectName("fontBox")
        self.horizontalLayout_2.addWidget(self.fontBox, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.textBrowser = LyricsTextBrowserWidget(Form)
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser.setAcceptRichText(True)
        self.textBrowser.setStyleSheet("font-size: %spt;" % self.fontBox.value() * 2)
        self.textBrowser.setFontPointSize(self.fontBox.value())
        self.horizontalLayout_1.addWidget(self.textBrowser)
        self.infoTable = QtWidgets.QTableWidget(Form)
        self.infoTable.setStyleSheet("font-size: %spt;" % self.fontBox.value() * 2)
        self.infoTable.setColumnCount(2)
        self.infoTable.verticalHeader().setVisible(False)
        self.infoTable.horizontalHeader().setVisible(False)
        self.infoTable.horizontalHeader().setStretchLastSection(True)
        self.infoTable.setVisible(False)
        self.horizontalLayout_1.addWidget(self.infoTable)
        self.verticalLayout_2.addLayout(self.horizontalLayout_1)
        self.gridLayout_2.addLayout(self.verticalLayout_2, 2, 0, 1, 1)
        self.retranslateUi(Form)
        self.fontBox.valueChanged.connect(self.update_fontsize)
        self.comboBox.currentIndexChanged.connect(self.options_changed)
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
                            size = line.split("=", 1)[1].strip()
                            try:
                                self.fontBox.setValue(int(size))
                            except ValueError:
                                pass
                        if "openspotify" in lcline:
                            if "true" in lcline:
                                self.open_spotify = True
                            else:
                                self.open_spotify = False
                        if "darktheme" in lcline:
                            if "true" in lcline:
                                self.darktheme = True
                            else:
                                self.darktheme = False
                        if "infos" in lcline:
                            self.infos = "true" in lcline
            else:
                directory = os.path.dirname(settingsfile)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open(settingsfile, 'w+') as settings:
                    settings.write(
                        "[settings]\nSyncedLyrics=False\nAlwaysOnTop=False\nFontSize=10\nOpenSpotify=False\nDarkTheme"
                        "=False\nInfos=False")
            if self.darktheme:
                self.set_darktheme()
            if self.sync:
                self.comboBox.setItemText(2, "Synced Lyrics (on)")
            if self.ontop:
                Form.setWindowFlags(Form.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
                self.comboBox.setItemText(3, "Always on Top (on)")
                Form.show()
            if self.open_spotify:
                self.comboBox.setItemText(4, "Open Spotify (on)")
            if self.infos:
                self.comboBox.setItemText(5, "Infos (on)")
                self.infoTable.setVisible(True)
        else:
            with open(settingsfile, 'w+') as settings:
                settings.write("[settings]\n")
                if self.sync:
                    settings.write("SyncedLyrics=True\n")
                else:
                    settings.write("SyncedLyrics=False\n")
                if self.ontop:
                    settings.write("AlwaysOnTop=True\n")
                else:
                    settings.write("AlwaysOnTop=False\n")
                if self.open_spotify:
                    settings.write("OpenSpotify=True\n")
                else:
                    settings.write("OpenSpotify=False\n")
                if self.darktheme:
                    settings.write("DarkTheme=True\n")
                else:
                    settings.write("DarkTheme=False\n")
                if self.infos:
                    settings.write("Infos=True\n")
                else:
                    settings.write("Infos=False\n")
                settings.write("FontSize=%s" % str(self.fontBox.value()))

    def options_changed(self):
        current_index = self.comboBox.currentIndex()
        if current_index == 1:
            if self.darktheme is False:
                self.set_darktheme()
            else:
                self.darktheme = False
                self.textBrowser.setStyleSheet("")
                self.label_songname.setStyleSheet("")
                self.comboBox.setStyleSheet("")
                self.fontBox.setStyleSheet("")
                self.pushButton.setStyleSheet("")
                self.saveButton.setStyleSheet("")
                self.chordsButton.setStyleSheet("")
                self.infoTable.setStyleSheet("")
                self.comboBox.setItemText(1, ("Dark Theme"))
                text = re.sub("color:.*?;", "color: black;", self.label_songname.text())
                self.label_songname.setText(text)
                Form.setWindowOpacity(1.0)
                Form.setStyleSheet("")
                self.set_style()
        elif current_index == 2:
            if self.sync:
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
            if self.open_spotify:
                self.open_spotify = False
                self.comboBox.setItemText(4, ("Open Spotify"))
            else:
                self.open_spotify = True
                self.comboBox.setItemText(4, ("Open Spotify (on)"))
        elif current_index == 5:
            if self.infos:
                self.infos = False
                self.comboBox.setItemText(5, ("Infos"))
                self.infoTable.setVisible(False)
            else:
                self.infos = True
                self.comboBox.setItemText(5, ("Infos (on)"))
                self.infoTable.setVisible(True)
        elif current_index == 6:
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
                            align = setting.split("=", 1)[1].strip()
                        except IndexError:
                            align = ""
                        if "lyricstextalign" in lcsetting:
                            if align == "center":
                                self.lyricsTextAlign = QtCore.Qt.AlignCenter
                            elif align == "right":
                                self.lyricsTextAlign = QtCore.Qt.AlignRight
                            else:
                                pass
                        if "windowopacity" in lcsetting:
                            windowopacity = float(align)
                        if lcsetting.startswith("backgroundcolor"):
                            backgroundcolor = align
                        if "lyricsbackgroundcolor" in lcsetting:
                            style = self.textBrowser.styleSheet()
                            style = style + "background-color: %s;" % align
                            self.textBrowser.setStyleSheet(style)
                        if "lyricstextcolor" in lcsetting:
                            style = self.textBrowser.styleSheet()
                            style = style + "color: %s;" % align
                            self.textBrowser.setStyleSheet(style)
                        if "lyricsfont" in lcsetting:
                            style = self.textBrowser.styleSheet()
                            style = style + "font-family: %s;" % align
                            self.textBrowser.setStyleSheet(style)
                        if "songnamecolor" in lcsetting:
                            style = self.label_songname.styleSheet()
                            style = style + "color: %s;" % align
                            self.label_songname.setStyleSheet(style)
                            text = re.sub("color:.*?;", "color: %s;" % align, self.label_songname.text())
                            self.label_songname.setText(text)
                        if "fontboxbackgroundcolor" in lcsetting:
                            style = self.fontBox.styleSheet()
                            style = style + "background-color: %s;" % align
                            self.comboBox.setStyleSheet(style)
                            self.fontBox.setStyleSheet(style)
                            self.pushButton.setStyleSheet(style)
                            self.saveButton.setStyle(style)
                            self.chordsButton.setStyleSheet(style)
                        if "fontboxtextcolor" in lcsetting:
                            style = self.fontBox.styleSheet()
                            style = style + "color: %s;" % align
                            self.comboBox.setStyleSheet(style)
                            self.fontBox.setStyleSheet(style)
                            self.pushButton.setStyleSheet(style)
                            self.saveButton.setStyleSheet(style)
                            self.chordsButton.setStyleSheet(style)
                        if "songnameunderline" in lcsetting:
                            if "true" in align.lower():
                                style = self.label_songname.styleSheet()
                                style = style + "text-decoration: underline;"
                                self.label_songname.setStyleSheet(style)

                    Form.setWindowOpacity(windowopacity)
                    Form.setStyleSheet("background-color: %s;" % backgroundcolor)

                except Exception:
                    pass
        else:
            self.label_songname.setStyleSheet("color: black; text-decoration: underline;")
            pass

    def set_darktheme(self):
        self.darktheme = True
        self.textBrowser.setStyleSheet("background-color: #181818; color: #ffffff;")
        self.label_songname.setStyleSheet("color: #9c9c9c; text-decoration: underline;")
        text = re.sub("color:.*?;", "color: #9c9c9c;", self.label_songname.text())
        self.label_songname.setText(text)
        self.comboBox.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.fontBox.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.pushButton.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.saveButton.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.chordsButton.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.infoTable.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.comboBox.setItemText(1, "Dark Theme (on)")
        Form.setWindowOpacity(1.0)
        Form.setStyleSheet("background-color: #282828;")

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
        self.fontBox.setValue(self.fontBox.value() + offset)
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
        if backend.check_version():
            self.label_songname.setText(_translate("Form", "Spotify Lyrics"))
        else:
            self.label_songname.setText(_translate("Form",
                                                   "Spotify Lyrics <style type=\"text/css\">a {text-decoration: "
                                                   "none}</style><a "
                                                   "href=\"https://github.com/SimonIT/spotifylyrics/releases\"><sup>("
                                                   "update)</sup></a>"))
        self.textBrowser.setText(_translate("Form", "Play a song in Spotify to fetch lyrics."))
        self.fontBox.setToolTip(_translate("Form", "Font Size"))
        self.comboBox.setItemText(0, _translate("Form", "Options"))
        self.comboBox.setItemText(1, _translate("Form", "Dark Theme"))
        self.comboBox.setItemText(2, _translate("Form", "Synced Lyrics"))
        self.comboBox.setItemText(3, _translate("Form", "Always on Top"))
        self.comboBox.setItemText(4, _translate("Form", "Open Spotify"))
        self.comboBox.setItemText(5, _translate("Form", "Infos"))
        self.comboBox.setItemText(6, _translate("Form", "Save Settings"))

    def add_service_name_to_lyrics(self, lyrics, service_name):
        return '''<span style="font-size:%spx; font-style:italic;">Lyrics loaded from: %s</span>\n\n%s''' % (
            (self.fontBox.value() - 2) * 2, service_name, lyrics)

    def lyrics_thread(self, comm):
        oldsongname = ""
        while True:
            songname = backend.get_window_title()
            self.changed = False
            if oldsongname != songname:
                if songname != "Spotify" and songname != "":
                    oldsongname = songname
                    comm.signal.emit(songname, "Loading...")
                    start = time.time()
                    backend.set_song(songname)
                    if self.sync:
                        lyrics, url, service_name, timed = backend.get_lyrics(sync=True)
                    else:
                        lyrics, url, service_name, timed = backend.get_lyrics()
                    if self.infos:
                        threading.Thread(target=backend.load_infos).start()
                    if url == "":
                        header = songname
                    else:
                        style = self.label_songname.styleSheet()
                        if style == "":
                            color = "color: black"
                        else:
                            color = style
                        header = '''<style type="text/css">a {text-decoration: none; %s}</style><a href="%s">%s</a>''' \
                                 % (color, url, songname)
                    if timed:
                        lrc = pylrc.parse(lyrics)
                        if lrc.album != "":
                            backend.song.album = lrc.album
                        lyricsclean = '\n'.join(e.text for e in lrc)
                        comm.signal.emit(header, self.add_service_name_to_lyrics(lyricsclean, service_name))
                        count = -1
                        for line in lrc:
                            if not self.sync:
                                self.change_lyrics()
                                break
                            if self.changed:
                                self.changed = False
                                break
                            count += 1
                            lrc[count - 1].text = html_tags.sub("", lrc[count - 1].text)
                            lrc[count].text = "<b>%s</b>" % line.text
                            if count - 2 > 0:
                                lrc[count - 3].text = html_tags.sub("", lrc[count - 3].text)
                                lrc[count - 2].text = "<a name=\"#scrollHere\">%s</a>" % lrc[count - 2].text
                            boldlyrics = '<br>'.join(e.text for e in lrc)
                            while True:
                                style = self.label_songname.styleSheet()
                                if style == "":
                                    color = "color: black"
                                else:
                                    color = style
                                header = '''<style type="text/css">a {text-decoration: none; %s}</style><a 
                                href="%s">%s</a>''' % (color, url, songname)
                                if line.time - (lrc.offset / 1000) <= time.time() - start \
                                        and backend.get_window_title() != "Spotify":
                                    if self.changed or not self.sync:
                                        break
                                    boldlyrics = '<style type="text/css">p {font-size: %spt}</style><p>' % \
                                                 self.fontBox.value() * 2 + boldlyrics + '</p>'
                                    comm.signal.emit(header,
                                                     self.add_service_name_to_lyrics(boldlyrics, service_name))
                                    time.sleep(0.5)
                                    break
                                elif backend.get_window_title() == "Spotify":
                                    time.sleep(0.2)
                                    start = start + 0.2
                                else:
                                    if songname != backend.get_window_title():
                                        break
                                    else:
                                        time.sleep(0.2)
                            if songname != backend.get_window_title() and backend.get_window_title() != "Spotify":
                                break
                    else:
                        comm.signal.emit(header, self.add_service_name_to_lyrics(lyrics, service_name))
            time.sleep(1)

    def start_thread(self):
        lyricsthread = threading.Thread(target=self.lyrics_thread, args=(self.comm,))
        lyricsthread.daemon = True
        lyricsthread.start()

    def refresh_lyrics(self, songname, lyrics):
        _translate = QtCore.QCoreApplication.translate
        if backend.get_window_title() != "":
            self.label_songname.setText(_translate("Form", songname))
        self.set_lyrics_with_alignment(_translate("Form", lyrics))
        self.textBrowser.scrollToAnchor("#scrollHere")
        self.refresh_info()

    def refresh_info(self):
        self.infoTable.clearContents()
        self.infoTable.setRowCount(8)
        song = backend.song
        index = 0

        self.infoTable.setItem(index, 0, QtWidgets.QTableWidgetItem("name"))
        self.infoTable.setItem(index, 1, QtWidgets.QTableWidgetItem(song.name))
        index += 1

        self.infoTable.setItem(index, 0, QtWidgets.QTableWidgetItem("artist"))
        self.infoTable.setItem(index, 1, QtWidgets.QTableWidgetItem(song.artist))
        index += 1

        if song.album != "UNKNOWN":
            self.infoTable.setItem(index, 0, QtWidgets.QTableWidgetItem("album"))
            self.infoTable.setItem(index, 1, QtWidgets.QTableWidgetItem(song.album))
            index += 1

        if song.genre != "UNKNOWN":
            self.infoTable.setItem(index, 0, QtWidgets.QTableWidgetItem("genre"))
            self.infoTable.setItem(index, 1, QtWidgets.QTableWidgetItem(song.genre))
            index += 1

        if song.year != -1:
            self.infoTable.setItem(index, 0, QtWidgets.QTableWidgetItem("year"))
            self.infoTable.setItem(index, 1, QtWidgets.QTableWidgetItem(str(song.year)))
            index += 1

        if song.cycles_per_minute != -1:
            self.infoTable.setItem(index, 0, QtWidgets.QTableWidgetItem("cycles per minute"))
            self.infoTable.setItem(index, 1, QtWidgets.QTableWidgetItem(str(song.cycles_per_minute)))
            index += 1

        if song.beats_per_minute != -1:
            self.infoTable.setItem(index, 0, QtWidgets.QTableWidgetItem("beats per minute"))
            self.infoTable.setItem(index, 1, QtWidgets.QTableWidgetItem(str(song.beats_per_minute)))
            index += 1

        if len(song.dances) > 0:
            self.infoTable.setItem(index, 0, QtWidgets.QTableWidgetItem("dances"))
            self.infoTable.setItem(index, 1, QtWidgets.QTableWidgetItem("\n".join(song.dances)))

        self.infoTable.resizeRowsToContents()
        self.infoTable.resizeColumnsToContents()

    def get_chords(self):
        _translate = QtCore.QCoreApplication.translate
        if self.label_songname.text() not in ("", "Spotify", "Spotify Lyrics"):
            backend.load_chords()
        else:
            self.textBrowser.append(_translate("Form", "I'm sorry, Dave. I'm afraid I can't do that."))

    def change_lyrics(self):
        _translate = QtCore.QCoreApplication.translate
        if self.label_songname.text() not in ("", "Spotify", "Spotify Lyrics"):
            self.changed = True
            changethread = threading.Thread(target=self.change_lyrics_thread)
            changethread.start()
        else:
            self.textBrowser.append(_translate("Form", "I'm sorry, Dave. I'm afraid I can't do that."))

    def change_lyrics_thread(self):
        songname = backend.get_window_title()
        self.comm.signal.emit(songname, "Loading...")
        style = self.label_songname.styleSheet()

        if style == "":
            color = "color: black"
        else:
            color = style

        lyrics, url, service_name, timed = backend.next_lyrics()
        if url == "":
            header = songname
        else:
            header = '''<style type="text/css">a {text-decoration: none; %s}</style><a href="%s">%s</a>''' % (
                color, url, songname)

        self.comm.signal.emit(header, self.add_service_name_to_lyrics(lyrics, service_name))

    def save_lyrics(self):
        with open(backend.song.artist + " - " + backend.song.name + ".txt", "w", encoding="utf-8") as lyrics_file:
            lyrics_file.write(self.textBrowser.toPlainText())

    @staticmethod
    def spotify():
        backend.open_spotify()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("fusion")
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    Form.show()
    sys.exit(app.exec_())
