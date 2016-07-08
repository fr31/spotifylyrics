from PyQt5 import QtCore, QtGui, QtWidgets
import backend
import time
import threading
import os

if os.name == "nt":
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("spotifylyrics.version01")

class Communicate(QtCore.QObject):
    signal = QtCore.pyqtSignal(str, str)

class Ui_Form(object):
    def __init__(self):
        super().__init__()

        self.comm = Communicate()
        self.comm.signal.connect(self.change_lyrics)
        self.start_thread()

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(550, 610)
        Form.setMinimumSize(QtCore.QSize(550, 610))
        self.gridLayout_2 = QtWidgets.QGridLayout(Form)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_songname = QtWidgets.QLabel(Form)
        self.label_songname.setObjectName("label_songname")
        self.horizontalLayout_2.addWidget(self.label_songname, 0, QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.fontBox = QtWidgets.QSpinBox(Form)
        self.fontBox.setMinimum(1)
        self.fontBox.setProperty("value", 10)
        self.fontBox.setObjectName("fontBox")
        self.horizontalLayout_2.addWidget(self.fontBox, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.checkBox = QtWidgets.QCheckBox(Form)
        self.checkBox.setText("")
        self.checkBox.setObjectName("checkBox")
        self.horizontalLayout_2.addWidget(self.checkBox, 0, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.textBrowser = QtWidgets.QTextBrowser(Form)
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser.setFontPointSize(self.fontBox.value())
        self.verticalLayout_2.addWidget(self.textBrowser)
        self.gridLayout_2.addLayout(self.verticalLayout_2, 2, 0, 1, 1)

        self.retranslateUi(Form)
        self.fontBox.valueChanged.connect(self.update_fontsize)
        self.checkBox.toggled.connect(self.alwaysontop)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def set_style(self):
        if os.path.exists("theme.ini"):
            self.textBrowser.setStyleSheet("")
            self.fontBox.setStyleSheet("")
            with open('theme.ini', 'r') as theme:
                try:
                    for setting in theme.readlines():
                        try:
                            set = setting.split("=",1)[1].strip()
                        except IndexError:
                            set = ""
                        if "WindowOpacity" in setting:
                            Form.setWindowOpacity(float(set))
                        if "BackgroundColor" in setting:
                            Form.setStyleSheet("background-color: %s" % set)
                        if "LyricsBackgroundColor" in setting:
                            style = self.textBrowser.styleSheet()
                            style = style + "background-color: %s;" % set
                            self.textBrowser.setStyleSheet(style)
                        if "LyricsTextColor" in setting:
                            style = self.textBrowser.styleSheet()
                            style = style + "color: %s;" % set
                            self.textBrowser.setStyleSheet(style)
                        if "SongNameColor" in setting:
                            self.label_songname.setStyleSheet("color: %s" % set)
                        if "FontBoxBackgroundColor" in setting:
                            style = self.fontBox.styleSheet()
                            style = style + "background-color: %s;" % set
                            self.fontBox.setStyleSheet(style)
                        if "FontBoxTextColor" in setting:
                            style = self.fontBox.styleSheet()
                            style = style + "color: %s;" % set
                            self.fontBox.setStyleSheet(style)
                except Exception:
                    pass
        else:
            pass

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def alwaysontop(self):
        if self.checkBox.isChecked():
            Form.setWindowFlags(Form.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            Form.show()
        else:
            Form.setWindowFlags(Form.windowFlags() & ~QtCore.Qt.WindowStaysOnTopHint)
            Form.show()

    def update_fontsize(self):
        self.textBrowser.setFontPointSize(self.fontBox.value())
        lyrics = self.textBrowser.toPlainText()
        self.textBrowser.setText(lyrics)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Spotify Lyrics"))
        Form.setWindowIcon(QtGui.QIcon(self.resource_path('icon.png')))
        self.label_songname.setText(_translate("Form", "Spotify Lyrics"))
        self.textBrowser.setText(_translate("Form", "Play a song in Spotify to fetch lyrics."))
        self.fontBox.setToolTip(_translate("Form", "Font Size"))
        self.checkBox.setToolTip(_translate("Form", "Always on Top"))

    def lyrics_thread(self, comm):
        oldsongname = ""
        while True:
            songname = backend.getwindowtitle()
            if oldsongname != songname:
                if songname != "Spotify" and songname != "":
                    oldsongname = songname
                    comm.signal.emit(songname, "Loading...")
                    lyrics = backend.getlyrics(songname)
                    comm.signal.emit(songname, lyrics)
            time.sleep(1)

    def start_thread(self):
        my_Thread = threading.Thread(target=self.lyrics_thread, args=(self.comm,))
        my_Thread.daemon = True
        my_Thread.start()

    def change_lyrics(self, songname, lyrics):
        _translate = QtCore.QCoreApplication.translate
        self.label_songname.setText(_translate("Form", songname))
        self.textBrowser.setText(_translate("Form", lyrics))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    ui.set_style()
    Form.show()
    sys.exit(app.exec_())