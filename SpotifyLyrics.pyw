from PyQt5 import QtCore, QtGui, QtWidgets
import backend
import time
import threading
import ctypes
import os

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
        self.label_songname = QtWidgets.QLabel(Form)
        self.label_songname.setObjectName("label_songname")
        self.verticalLayout_2.addWidget(self.label_songname, 0, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.textBrowser = QtWidgets.QTextBrowser(Form)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout_2.addWidget(self.textBrowser)
        self.gridLayout_2.addLayout(self.verticalLayout_2, 2, 0, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Spotify Lyrics"))
        Form.setWindowIcon(QtGui.QIcon(self.resource_path('icon.png')))
        self.label_songname.setText(_translate("Form", "Spotify"))
        self.textBrowser.setText(_translate("Form", "Loading..."))

    def lyrics_thread(self, comm):
        oldsongname = ""
        while True:
            songname = backend.getwindowtitle()
            if oldsongname != songname:
                oldsongname = songname
                if songname != "Spotify":
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
    Form.show()
    sys.exit(app.exec_())
