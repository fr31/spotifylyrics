#!/usr/bin/env python3
import configparser
import os
import re
import subprocess
import threading
import time

import pathvalidate
import pylrc
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QSystemTrayIcon, QAction, QMenu, qApp, QMessageBox

import backend
from services import SETTINGS_DIR, LYRICS_DIR

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
                num_pixels = e.pixelDelta()
                num_degrees = e.angleDelta()
                factor = 1
                if not num_pixels.isNull():
                    sign = 1 if num_pixels.y() > 0 else -1
                    UI.change_fontsize(sign * factor)
                elif not num_degrees.isNull():
                    sign = 1 if num_degrees.y() > 0 else -1
                    UI.change_fontsize(sign * factor)
            else:
                super(QtWidgets.QTextBrowser, self).wheelEvent(e)
        except:
            pass


BRACKETS = re.compile(r'\[.+?\]')
HTML_TAGS = re.compile(r'<.+?>')


class UiForm:
    sync = False
    ontop = False
    open_spotify = False
    changed = False
    dark_theme = False
    info = False
    minimize_to_tray = False

    tray_icon = None

    streaming_services = [backend.SpotifyStreamingService(), backend.VlcMediaPlayer(), backend.TidalStreamingService()]

    def __init__(self):
        self.is_loading_settings = False
        self.comm = Communicate()
        self.comm.signal.connect(self.refresh_lyrics)

        FORM.setObjectName("Form")
        FORM.resize(550, 610)
        FORM.setMinimumSize(QtCore.QSize(350, 310))
        self.grid_layout_2 = QtWidgets.QGridLayout(FORM)
        self.grid_layout_2.setObjectName("gridLayout_2")
        self.vertical_layout_2 = QtWidgets.QVBoxLayout()
        self.vertical_layout_2.setObjectName("verticalLayout_2")
        self.horizontal_layout_2 = QtWidgets.QHBoxLayout()
        self.horizontal_layout_2.setObjectName("horizontalLayout_2")
        self.horizontal_layout_1 = QtWidgets.QHBoxLayout()
        self.horizontal_layout_1.setObjectName("horizontalLayout_1")
        self.label_song_name = QtWidgets.QLabel(FORM)
        self.label_song_name.setObjectName("label_song_name")
        self.label_song_name.setOpenExternalLinks(True)
        self.horizontal_layout_2.addWidget(self.label_song_name, 0, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        spacer_item = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontal_layout_2.addItem(spacer_item)

        self.sync_adjustment_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, parent=FORM)
        self.sync_adjustment_slider.setGeometry(QtCore.QRect(160, 120, 69, 22))
        self.sync_adjustment_slider.setMinimum(-30)
        self.sync_adjustment_slider.setMaximum(30)
        self.sync_adjustment_slider.setSingleStep(1)
        self.sync_adjustment_slider.setToolTipDuration(5000)
        self.sync_adjustment_slider.valueChanged.connect(self.changed_slider)
        self.horizontal_layout_2.addWidget(self.sync_adjustment_slider, 0,
                                           QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.streaming_services_box = QtWidgets.QComboBox(FORM)
        self.streaming_services_box.setGeometry(QtCore.QRect(160, 120, 69, 22))
        self.streaming_services_box.addItems(str(n) for n in self.streaming_services)
        self.streaming_services_box.setCurrentIndex(0)
        self.streaming_services_box.currentIndexChanged.connect(self.options_changed)
        self.horizontal_layout_2.addWidget(self.streaming_services_box, 0,
                                           QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.change_lyrics_button = QtWidgets.QPushButton(FORM)
        self.change_lyrics_button.setObjectName("pushButton")
        self.change_lyrics_button.setText("Change Lyrics")
        self.change_lyrics_button.clicked.connect(self.change_lyrics)
        self.horizontal_layout_2.addWidget(self.change_lyrics_button, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.save_button = QtWidgets.QPushButton(FORM)
        self.save_button.setObjectName("saveButton")
        self.save_button.setText("Save Lyrics")
        self.save_button.clicked.connect(self.save_lyrics)
        self.horizontal_layout_2.addWidget(self.save_button, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # Open Tab Button
        self.chords_button = QtWidgets.QPushButton(FORM)
        self.chords_button.setObjectName("chordsButton")
        self.chords_button.setText("Chords")
        self.chords_button.clicked.connect(self.get_chords)
        self.horizontal_layout_2.addWidget(self.chords_button, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.options_combobox = QtWidgets.QComboBox(FORM)
        self.options_combobox.setGeometry(QtCore.QRect(160, 120, 69, 22))
        self.options_combobox.setObjectName("comboBox")
        self.options_combobox.addItem("")
        self.options_combobox.addItem("")
        self.options_combobox.addItem("")
        self.options_combobox.addItem("")
        self.options_combobox.addItem("")
        self.options_combobox.addItem("")
        self.options_combobox.addItem("")

        self.tray_icon = QSystemTrayIcon(FORM)
        self.tray_icon.setIcon(QtGui.QIcon(self.get_resource_path('icon.png')))

        show_action = QAction("Show", FORM)
        quit_action = QAction("Exit", FORM)
        show_action.triggered.connect(FORM.show)
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(FORM.icon_activated)

        if os.name == "nt":
            self.options_combobox.addItem("")
        self.horizontal_layout_2.addWidget(self.options_combobox, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.font_size_box = QtWidgets.QSpinBox(FORM)
        self.font_size_box.setMinimum(1)
        self.font_size_box.setProperty("value", 10)
        self.font_size_box.setObjectName("fontBox")
        self.horizontal_layout_2.addWidget(self.font_size_box, 0, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.vertical_layout_2.addLayout(self.horizontal_layout_2)
        self.text_browser = LyricsTextBrowserWidget(FORM)
        self.text_browser.setObjectName("textBrowser")
        self.text_browser.setAcceptRichText(True)
        self.text_browser.setStyleSheet("font-size: %spt;" % self.font_size_box.value() * 2)
        self.text_browser.setFontPointSize(self.font_size_box.value())
        self.horizontal_layout_1.addWidget(self.text_browser)
        self.info_table = QtWidgets.QTableWidget(FORM)
        self.info_table.setStyleSheet("font-size: %spt;" % self.font_size_box.value() * 2)
        self.info_table.setColumnCount(2)
        self.info_table.setMaximumWidth(300)
        self.info_table.verticalHeader().setVisible(False)
        self.info_table.horizontalHeader().setVisible(False)
        self.info_table.horizontalHeader().setStretchLastSection(True)
        self.info_table.setVisible(False)
        self.horizontal_layout_1.addWidget(self.info_table)
        self.vertical_layout_2.addLayout(self.horizontal_layout_1)
        self.grid_layout_2.addLayout(self.vertical_layout_2, 2, 0, 1, 1)
        self.retranslate_ui(FORM)
        self.font_size_box.valueChanged.connect(self.update_fontsize)
        self.options_combobox.currentIndexChanged.connect(self.options_changed)
        QtCore.QMetaObject.connectSlotsByName(FORM)
        FORM.setTabOrder(self.text_browser, self.options_combobox)
        FORM.setTabOrder(self.options_combobox, self.font_size_box)

        self.set_style()
        self.load_save_settings()
        self.spotify()
        self.start_thread()
        self.song = None

        if not self.sync:
            self.sync_adjustment_slider.setVisible(False)

    def changed_slider(self, value) -> None:
        self.sync_adjustment_slider.setToolTip("%d seconds" % value)

    def streaming_service_changed(self) -> None:
        self.spotify()
        self.load_save_settings(save=True)

    def get_current_streaming_service(self) -> backend.StreamingService:
        return self.streaming_services[self.streaming_services_box.currentIndex()]

    def load_save_settings(self, save=False) -> None:
        if self.is_loading_settings:
            return

        settings_file = SETTINGS_DIR + "settings.ini"
        section = "settings"

        if not os.path.exists(settings_file):
            directory = os.path.dirname(settings_file)
            if not os.path.exists(directory):
                os.makedirs(directory)

        if not save:
            self.is_loading_settings = True
            config = configparser.ConfigParser()
            config.read(settings_file)

            self.sync = config.getboolean(section, "syncedlyrics", fallback=False)
            self.ontop = config.getboolean(section, "alwaysontop", fallback=False)
            self.open_spotify = config.getboolean(section, "openspotify", fallback=False)
            self.dark_theme = config.getboolean(section, "darktheme", fallback=False)
            self.info = config.getboolean(section, "info", fallback=False)
            self.minimize_to_tray = config.getboolean(section, "minimizetotray", fallback=False)
            self.font_size_box.setValue(config.getint(section, "fontsize", fallback=10))

            streaming_service_name = config.get(section, "StreamingService", fallback=None)
            if streaming_service_name:
                for i in range(len(self.streaming_services)):
                    if str(self.streaming_services[i]) == streaming_service_name:
                        self.streaming_services_box.setCurrentIndex(i)
                        break

            FORM.move(config.getint(section, "X", fallback=FORM.pos().x()),
                      config.getint(section, "Y", fallback=FORM.pos().y()))
            if config.getboolean(section, "FullScreen", fallback=False):
                FORM.showFullScreen()
            elif config.getboolean(section, "Maximized", fallback=False):
                FORM.showMaximized()
            else:
                FORM.resize(config.getint(section, "Width", fallback=FORM.width().real),
                            config.getint(section, "Height", fallback=FORM.height().real))

            if self.dark_theme:
                self.set_dark_theme()
            if self.sync:
                self.options_combobox.setItemText(2, "Synced Lyrics (on)")
            if self.ontop:
                FORM.setWindowFlags(FORM.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
                self.options_combobox.setItemText(3, "Always on Top (on)")
                FORM.show()
            if self.open_spotify:
                self.options_combobox.setItemText(4, "Open Spotify (on)")
            if self.info:
                self.options_combobox.setItemText(5, "Info (on)")
                self.info_table.setVisible(True)
            if self.minimize_to_tray:
                self.options_combobox.setItemText(7, "Minimize to Tray (on)")
        else:
            config = configparser.ConfigParser()

            config.add_section(section)
            config[section]["SyncedLyrics"] = str(self.sync)
            config[section]["AlwaysOnTop"] = str(self.ontop)
            config[section]["OpenSpotify"] = str(self.open_spotify)
            config[section]["DarkTheme"] = str(self.dark_theme)
            config[section]["Info"] = str(self.info)
            config[section]["MinimizeToTray"] = str(self.minimize_to_tray)
            config[section]["FontSize"] = str(self.font_size_box.value())
            config[section]["StreamingService"] = str(self.get_current_streaming_service())
            config[section]["FullScreen"] = str(FORM.isFullScreen())
            config[section]["Maximized"] = str(FORM.isMaximized())
            config[section]["X"] = str(FORM.pos().x())
            config[section]["Y"] = str(FORM.pos().y())
            config[section]["Width"] = str(FORM.width().real)
            config[section]["Height"] = str(FORM.height().real)

            with open(settings_file, 'w+') as settings:
                config.write(settings)
        self.is_loading_settings = False

    def options_changed(self) -> None:
        current_index = self.options_combobox.currentIndex()
        if current_index == 1:
            if self.dark_theme is False:
                self.set_dark_theme()
            else:
                self.dark_theme = False
                self.text_browser.setStyleSheet("")
                self.label_song_name.setStyleSheet("")
                self.options_combobox.setStyleSheet("")
                self.font_size_box.setStyleSheet("")
                self.sync_adjustment_slider.setStyleSheet("")
                self.streaming_services_box.setStyleSheet("")
                self.change_lyrics_button.setStyleSheet("")
                self.save_button.setStyleSheet("")
                self.chords_button.setStyleSheet("")
                self.info_table.setStyleSheet("")
                self.options_combobox.setItemText(1, "Dark Theme")
                text = re.sub("color:.*?;", "color: black;", self.label_song_name.text())
                self.label_song_name.setText(text)
                FORM.setWindowOpacity(1.0)
                FORM.setStyleSheet("")
                self.set_style()
        elif current_index == 2:
            if self.sync:
                self.sync = False
                self.options_combobox.setItemText(2, "Synced Lyrics")
            else:
                self.sync = True
                self.options_combobox.setItemText(2, "Synced Lyrics (on)")
        elif current_index == 3:
            if self.ontop is False:
                self.ontop = True
                FORM.setWindowFlags(FORM.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
                self.options_combobox.setItemText(3, "Always on Top (on)")
                FORM.show()
            else:
                self.ontop = False
                FORM.setWindowFlags(FORM.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
                self.options_combobox.setItemText(3, "Always on Top")
                FORM.show()
        elif current_index == 4:
            if self.open_spotify:
                self.open_spotify = False
                self.options_combobox.setItemText(4, "Open Spotify")
            else:
                self.open_spotify = True
                self.spotify()
                self.options_combobox.setItemText(4, "Open Spotify (on)")
        elif current_index == 5:
            if self.info:
                self.info = False
                self.options_combobox.setItemText(5, "Info")
                self.info_table.setVisible(False)
            else:
                self.info = True
                self.options_combobox.setItemText(5, "Info (on)")
                self.info_table.setVisible(True)
        elif current_index == 6:
            if os.name == "nt":
                subprocess.Popen(r'explorer "' + LYRICS_DIR + '"')
        elif current_index == 7:
            if self.minimize_to_tray:
                self.minimize_to_tray = False
                self.options_combobox.setItemText(7, "Minimize to System Tray")
            else:
                self.minimize_to_tray = True
                self.options_combobox.setItemText(7, "Minimize to System Tray (on)")
        else:
            pass
        self.options_combobox.setCurrentIndex(0)
        self.load_save_settings(save=True)

    def set_style(self):
        self.lyrics_text_align = QtCore.Qt.AlignLeft
        if os.path.exists(SETTINGS_DIR + "theme.ini"):
            theme_file = SETTINGS_DIR + "theme.ini"
        else:
            theme_file = "theme.ini"

        if not os.path.exists(theme_file):
            self.label_song_name.setStyleSheet("color: black; text-decoration: underline;")
            return

        section = "theme"
        config = configparser.ConfigParser()

        with open(theme_file, 'r') as theme:
            config.read_string("[%s]\n%s" % (section, theme.read()))

        align = config.get(section, "lyricstextalign", fallback="")
        if align:
            if align == "center":
                self.lyrics_text_align = QtCore.Qt.AlignCenter
            elif align == "right":
                self.lyrics_text_align = QtCore.Qt.AlignRight

        FORM.setWindowOpacity(config.getfloat(section, "windowopacity", fallback=1))

        background = config.get(section, "backgroundcolor", fallback="")
        if background:
            FORM.setStyleSheet("background-color: %s;" % background)

        style = self.text_browser.styleSheet()

        text_background = config.get(section, "lyricsbackgroundcolor", fallback="")
        if text_background:
            style = style + "background-color: %s;" % text_background

        text_color = config.get(section, "lyricstextcolor", fallback="")
        if text_color:
            style = style + "color: %s;" % text_color

        text_font = config.get(section, "lyricsfont", fallback="")
        if text_font:
            style = style + "font-family: %s;" % text_font

        self.text_browser.setStyleSheet(style)

        style = self.label_song_name.styleSheet()

        label_color = config.get(section, "songnamecolor", fallback="")
        if label_color:
            style = style + "color: %s;" % label_color
            text = re.sub("color:.*?;", "color: %s;" % label_color, self.label_song_name.text())
            self.label_song_name.setText(text)

        label_underline = config.getboolean(section, "songnameunderline", fallback=False)
        if label_underline:
            style = style + "text-decoration: underline;"

        self.label_song_name.setStyleSheet(style)

        style = self.font_size_box.styleSheet()

        font_size_background = config.get(section, "fontboxbackgroundcolor", fallback="")
        if font_size_background:
            style = style + "background-color: %s;" % font_size_background

        font_size_color = config.get(section, "fontboxtextcolor", fallback="")
        if font_size_color:
            style = style + "color: %s;" % font_size_color

        self.streaming_services_box.setStyleSheet(style)
        self.options_combobox.setStyleSheet(style)
        self.font_size_box.setStyleSheet(style)
        self.change_lyrics_button.setStyleSheet(style)
        self.save_button.setStyleSheet(style)
        self.chords_button.setStyleSheet(style)

    def set_dark_theme(self):
        self.dark_theme = True
        self.text_browser.setStyleSheet("background-color: #181818; color: #ffffff;")
        self.label_song_name.setStyleSheet("color: #9c9c9c; text-decoration: underline;")
        text = re.sub("color:.*?;", "color: #9c9c9c;", self.label_song_name.text())
        self.label_song_name.setText(text)
        self.sync_adjustment_slider.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.streaming_services_box.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.options_combobox.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.font_size_box.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.change_lyrics_button.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.save_button.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.chords_button.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.info_table.setStyleSheet("background-color: #181818; color: #9c9c9c;")
        self.options_combobox.setItemText(1, "Dark Theme (on)")
        FORM.setWindowOpacity(1.0)
        FORM.setStyleSheet("background-color: #282828;")

    @staticmethod
    def get_resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def set_lyrics_with_alignment(self, lyrics):
        self.text_browser.clear()
        for line in lyrics.splitlines():
            self.text_browser.append(line)
            self.text_browser.setAlignment(self.lyrics_text_align)

    def change_fontsize(self, offset):
        self.font_size_box.setValue(self.font_size_box.value() + offset)

    def update_fontsize(self):
        self.text_browser.setFontPointSize(self.font_size_box.value())
        style = self.text_browser.styleSheet()
        style = style.replace('%s' % style[style.find("font"):style.find("pt;") + 3], '')
        style = style.replace('p ', '')
        self.text_browser.setStyleSheet(style + "p font-size: %spt;" % self.font_size_box.value() * 2)
        lyrics = self.text_browser.toPlainText()
        self.set_lyrics_with_alignment(lyrics)
        self.load_save_settings(save=True)

    def retranslate_ui(self, form):
        _translate = QtCore.QCoreApplication.translate
        form.setWindowTitle(_translate("Form", "Spotify Lyrics - {}".format(backend.get_version())))
        form.setWindowIcon(QtGui.QIcon(self.get_resource_path('icon.png')))
        if backend.check_version():
            self.label_song_name.setText(_translate("Form", "Spotify Lyrics"))
        else:
            self.label_song_name.setText(_translate("Form",
                                                    "Spotify Lyrics <style type=\"text/css\">a {text-decoration: "
                                                    "none}</style><a "
                                                    "href=\"https://github.com/SimonIT/spotifylyrics/releases\"><sup>("
                                                    "update)</sup></a>"))
        self.text_browser.setText(_translate("Form", "Play a song in Spotify to fetch lyrics."))
        self.font_size_box.setToolTip(_translate("Form", "Font Size"))
        self.options_combobox.setItemText(0, _translate("Form", "Options"))
        self.options_combobox.setItemText(1, _translate("Form", "Dark Theme"))
        self.options_combobox.setItemText(2, _translate("Form", "Synced Lyrics"))
        self.options_combobox.setItemText(3, _translate("Form", "Always on Top"))
        self.options_combobox.setItemText(4, _translate("Form", "Open Spotify"))
        self.options_combobox.setItemText(5, _translate("Form", "Info"))
        if os.name == "nt":
            self.options_combobox.setItemText(6, _translate("Form", "Open Lyrics Directory"))
        self.options_combobox.setItemText(7, _translate("Form", "Minimize to Tray"))

    def add_service_name_to_lyrics(self, lyrics, service_name):
        return '''<span style="font-size:%spx; font-style:italic;">Lyrics loaded from: %s</span>\n\n%s''' % (
            (self.font_size_box.value() - 2) * 2, service_name, lyrics)

    def display_lyrics(self, comm):
        old_song_name = ""
        while True:
            song_name = backend.get_window_title(self.get_current_streaming_service())
            if old_song_name != song_name \
                    and song_name not in self.get_current_streaming_service().get_not_playing_windows_title() or self.changed:
                self.sync_adjustment_slider.setValue(0)
                comm.signal.emit(song_name, "Loading...")
                if not self.changed:
                    old_song_name = song_name
                    start = time.time()
                    self.song = backend.Song.get_from_string(song_name)
                    if self.info:
                        backend.load_info(self, self.song)
                    lyrics_metadata = backend.get_lyrics(song=self.song, sync=self.sync)
                else:
                    lyrics_metadata = backend.next_lyrics(song=self.song, sync=self.sync)
                    self.changed = False
                self.lyrics = lyrics_metadata.lyrics
                self.timed = lyrics_metadata.timed
                if lyrics_metadata.url == "":
                    header = song_name
                else:
                    style = self.label_song_name.styleSheet()
                    if style == "":
                        color = "color: black"
                    else:
                        color = style
                    header = '''<style type="text/css">a {text-decoration: none; %s}</style><a href="%s">%s</a>''' \
                             % (color, lyrics_metadata.url, song_name)
                lyrics_clean = lyrics_metadata.lyrics
                if lyrics_metadata.timed:
                    lrc = pylrc.parse(lyrics_metadata.lyrics)
                    if lrc.album:
                        self.song.album = lrc.album
                    lyrics_clean = '\n'.join(e.text for e in lrc)
                    comm.signal.emit(header,
                                     self.add_service_name_to_lyrics(lyrics_clean, lyrics_metadata.service_name))
                    count = 0
                    line_changed = True
                    while self.sync and not self.changed:
                        time_title_start = time.time()
                        window_title = backend.get_window_title(self.get_current_streaming_service())
                        time_title_end = time.time()
                        if window_title in self.get_current_streaming_service().get_not_playing_windows_title():
                            time.sleep(0.2)
                            start += 0.2 + time_title_end - time_title_start
                        elif song_name != window_title or not count + 1 < len(lrc):
                            self.sync_adjustment_slider.setValue(0)
                            break
                        else:
                            if lrc[count + 1].time - (lrc.offset / 1000) - self.sync_adjustment_slider.value() \
                                    <= time.time() - start:
                                count += 1
                                line_changed = True
                            if line_changed:
                                lrc[count - 1].text = HTML_TAGS.sub("", lrc[count - 1].text)
                                lrc[count].text = """<b style="font-size: %spt">%s</b>""" % \
                                                  (self.font_size_box.value() * 1.25, lrc[count].text)
                                if count - 2 > 0:
                                    lrc[count - 3].text = HTML_TAGS.sub("", lrc[count - 3].text)
                                    lrc[count - 2].text = "<a name=\"#scrollHere\">%s</a>" % lrc[count - 2].text
                                bold_lyrics = '<style type="text/css">p {font-size: %spt}</style><p>%s</p>' % \
                                              (
                                                  self.font_size_box.value(),
                                                  '<br>'.join(e.text for e in lrc)
                                              )
                                comm.signal.emit(
                                    header,
                                    self.add_service_name_to_lyrics(bold_lyrics, lyrics_metadata.service_name)
                                )
                                line_changed = False
                                time.sleep(0.5)
                            else:
                                time.sleep(0.2)
                comm.signal.emit(
                    header,
                    self.add_service_name_to_lyrics(lyrics_clean, lyrics_metadata.service_name))
            time.sleep(1)

    def start_thread(self):
        lyrics_thread = threading.Thread(target=self.display_lyrics, args=(self.comm,))
        lyrics_thread.daemon = True
        lyrics_thread.start()

    def refresh_lyrics(self, song_name, lyrics):
        _translate = QtCore.QCoreApplication.translate
        if backend.get_window_title(self.get_current_streaming_service()):
            self.label_song_name.setText(_translate("Form", song_name))
        self.set_lyrics_with_alignment(_translate("Form", lyrics))
        self.text_browser.scrollToAnchor("#scrollHere")
        self.refresh_info()

    def refresh_info(self):
        self.info_table.clearContents()

        if not self.song:
            return

        self.info_table.setRowCount(8)
        index = 0

        self.info_table.setItem(index, 0, QtWidgets.QTableWidgetItem("Title"))
        self.info_table.setItem(index, 1, QtWidgets.QTableWidgetItem(self.song.name))
        index += 1

        self.info_table.setItem(index, 0, QtWidgets.QTableWidgetItem("Artist"))
        self.info_table.setItem(index, 1, QtWidgets.QTableWidgetItem(self.song.artist))
        index += 1

        if self.song.album != "UNKNOWN":
            self.info_table.setItem(index, 0, QtWidgets.QTableWidgetItem("Album"))
            self.info_table.setItem(index, 1, QtWidgets.QTableWidgetItem(self.song.album))
            index += 1

        if self.song.genre != "UNKNOWN":
            self.info_table.setItem(index, 0, QtWidgets.QTableWidgetItem("Genre"))
            self.info_table.setItem(index, 1, QtWidgets.QTableWidgetItem(self.song.genre))
            index += 1

        if self.song.year != -1:
            self.info_table.setItem(index, 0, QtWidgets.QTableWidgetItem("Year"))
            self.info_table.setItem(index, 1, QtWidgets.QTableWidgetItem(str(self.song.year)))
            index += 1

        if self.song.cycles_per_minute != -1:
            self.info_table.setItem(index, 0, QtWidgets.QTableWidgetItem("Cycles Per Minute"))
            self.info_table.setItem(index, 1, QtWidgets.QTableWidgetItem(str(self.song.cycles_per_minute)))
            index += 1

        if self.song.beats_per_minute != -1:
            self.info_table.setItem(index, 0, QtWidgets.QTableWidgetItem("Beats Per Minute"))
            self.info_table.setItem(index, 1, QtWidgets.QTableWidgetItem(str(self.song.beats_per_minute)))
            index += 1

        if self.song.dances:
            self.info_table.setItem(index, 0, QtWidgets.QTableWidgetItem("Dances"))
            self.info_table.setItem(index, 1, QtWidgets.QTableWidgetItem("\n".join(self.song.dances)))

        self.info_table.resizeRowsToContents()
        self.info_table.resizeColumnsToContents()

    def get_chords(self):
        _translate = QtCore.QCoreApplication.translate
        if self.label_song_name.text() not in self.get_current_streaming_service().get_not_playing_windows_title():
            backend.load_chords(self.song)
        else:
            self.text_browser.append(_translate("Form", "I'm sorry, Dave. I'm afraid I can't do that."))

    def change_lyrics(self):
        _translate = QtCore.QCoreApplication.translate
        if self.label_song_name.text() not in self.get_current_streaming_service().get_not_playing_windows_title():
            self.changed = True
        else:
            self.text_browser.append(_translate("Form", "I'm sorry, Dave. I'm afraid I can't do that."))

    def save_lyrics(self):
        if not self.song:
            return

        if not os.path.exists(LYRICS_DIR):
            os.makedirs(LYRICS_DIR)

        artist = pathvalidate.sanitize_filename(self.song.artist)
        name = pathvalidate.sanitize_filename(self.song.name)

        new_lyrics_file = None

        for lyrics_file in os.listdir(LYRICS_DIR):
            lyrics_file = os.path.join(LYRICS_DIR, lyrics_file)
            if os.path.isfile(lyrics_file):
                file_parts = os.path.splitext(lyrics_file)
                file_extension = file_parts[1].lower()
                if file_extension in (".txt", ".lrc"):
                    file_name = file_parts[0].lower()
                    if name.lower() in file_name and artist.lower() in file_name:
                        msg = QMessageBox()
                        msg.setWindowIcon(FORM.windowIcon())
                        msg.setIcon(QMessageBox.Information)

                        msg.setText("You got already saved lyrics for the song %s by %s!" %
                                    (self.song.name, self.song.artist))
                        msg.setInformativeText("Do you want overwrite them?")
                        msg.setWindowTitle("Lyrics already saved")
                        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

                        retval = msg.exec_()
                        if retval == QMessageBox.Yes:
                            new_lyrics_file = file_name
                            break
                        else:
                            return

        if not new_lyrics_file:
            new_lyrics_file = os.path.join(LYRICS_DIR, "%s - %s" % (artist, name))

        if self.lyrics:
            if self.timed:
                lyrics_file = new_lyrics_file + ".lrc"
            else:
                lyrics_file = new_lyrics_file + ".txt"
            text = self.lyrics
        else:
            lyrics_file = new_lyrics_file + ".txt"
            text = self.text_browser.toPlainText()

        with open(lyrics_file, "w", encoding="utf-8") as lyrics_file:
            lyrics_file.write(text)

    def spotify(self) -> None:
        if not self.open_spotify:
            return
        backend.open_spotify(self.get_current_streaming_service())


class FormWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

    def closeEvent(self, event):
        UI.load_save_settings(save=True)
        if UI.minimize_to_tray:
            event.ignore()
            self.hide()

    def icon_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.show()

    def moveEvent(self, a0: QtGui.QMoveEvent) -> None:
        try:
            UI.load_save_settings(save=True)
        except:
            pass

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        try:
            UI.load_save_settings(save=True)
        except:
            pass


if __name__ == "__main__":
    import sys

    APP = QtWidgets.QApplication(sys.argv)
    APP.setStyle("fusion")
    FORM = FormWidget()
    UI = UiForm()
    FORM.show()
    sys.exit(APP.exec_())
