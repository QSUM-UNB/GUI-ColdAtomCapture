from PyQt6 import QtCore, QtWidgets, uic
import sys
import matplotlib as plt
plt.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import AcquireAndDisplay
import Trigger
import PySpin
import threading
import os
import datetime
import subprocess
import MotTemp
import numpy as np

class MplCanvasCam(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=100, height=100, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, constrained_layout=True)
        gs = fig.add_gridspec(3,3)
        self.axes = []
        self.axes.append(fig.add_subplot(gs[1:,:2]))
        self.axes.append(fig.add_subplot(gs[0,:2]))
        self.axes.append(fig.add_subplot(gs[1:,2]))
        self.axes[0].title.set_text("Camera View")
        self.axes[1].title.set_text("X-Axis Profile")
        self.axes[2].title.set_text("Y-Axis Profile")
        super(MplCanvasCam, self).__init__(fig)

class MplCanvasAnalysis(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=100, height=100, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, constrained_layout=True)
        self.axes = fig.subplots(nrows=3, ncols=2, sharex=True)
        self.axes[0][0].title.set_text("X-Axis Amplitude")
        self.axes[0][1].title.set_text("Y-Axis Amplitude")
        self.axes[1][0].title.set_text("X-Axis Centre")
        self.axes[1][1].title.set_text("Y-Axis Centre")
        self.axes[2][0].title.set_text("X-Axis Sigma")
        self.axes[2][1].title.set_text("Y-Axis Sigma")
        self.axes[2][0].set_xlabel("Time (s)")
        self.axes[2][1].set_xlabel("Time (s)")
        self.axes[0][0].set_ylabel("Pixel Intensity")
        self.axes[1][0].set_ylabel("Position (m)")
        self.axes[2][0].set_ylabel("Position (m)")
        super(MplCanvasAnalysis, self).__init__(fig)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kargs):
        super(MainWindow, self).__init__(*args, **kargs)
        uic.loadUi("mainwindow.ui", self)
        curDate = datetime.datetime.now(datetime.timezone.utc)
        datePath = curDate.strftime("%Y/%m/%d/")
        self.trigPath = f"{os.getcwd()}/Data/{datePath}"
        if os.path.exists(self.trigPath):
            self.runCount = 1
            while os.path.exists(f"{self.trigPath}Run{self.runCount}"):
                self.runCount += 1
        else:
            self.runCount = 1
        self.camRunButton.pressed.connect(self.runCameraTrigger)
        self.camModeCombo.currentIndexChanged.connect(self.camModeChanged)
        toolbar = NavigationToolbar2QT(self.analysisWidget, self)
        self.analysisLayout.addWidget(toolbar)
        curDay = curDate.day
        curMonth = curDate.month
        curYear = curDate.year
        dateObj = QtCore.QDate(curYear, curMonth, curDay)
        self.recallDateBox.setDate(dateObj)
        self.loadTofCheck.stateChanged.connect(self.loadTofChanged)
    def camModeChanged(self, index):
        change = True if index == 0 else False
        self.exposureBox.setEnabled(change)
        self.recallDateBox.setEnabled(not change)
        self.recallRunBox.setEnabled(not change)
        self.loadTofCheck.setEnabled(not change)
        self.loadTofBox.setEnabled(not change and self.loadTofCheck.isChecked())
    def loadTofChanged(self):
        self.loadTofBox.setEnabled(self.loadTofCheck.isChecked())
    def runCameraTrigger(self):
        if self.tofStartBox.value() == 0.0 or self.tofEndBox.value() == 0.0 or self.tofSplitBox.value() == 0:
            QtWidgets.QMessageBox.warning(
                self,
                "TOF Warning",
                "One of the TOF fields is empty. Please verify and run again.",
                buttons=QtWidgets.QMessageBox.StandardButton.Ok,
                defaultButton=QtWidgets.QMessageBox.StandardButton.Ok
            )
            return
        timeSplit = list(np.linspace(self.tofStartBox.value(), self.tofEndBox.value(), self.tofSplitBox.value()))
        if self.camModeCombo.currentIndex() == 0:
            for i in range(3):
                for j in range(2):
                    self.analysisWidget.axes[i][j].clear()
            os.makedirs(f"{self.trigPath}Run{self.runCount}")
            self.statusbar.showMessage("Initializing camera...")
            self.camThread = Trigger.CamTrigger(self.tofSplitBox.value(), f"{self.trigPath}Run{self.runCount}/", self.exposureBox.value(), timeSplit, self.sigmaBox.value(), self)
            self.runCount += 1
            self.camThread.start()
            
        else:
            date = self.recallDateBox.date().toPyDate()
            run = self.recallRunBox.value()
            dayString = str(date.day) if date.day > 9 else f"0{date.day}"
            monthString = str(date.month) if date.month > 9 else f"0{date.month}"
            baseDir = f"{os.getcwd()}/Data/{date.year}/{monthString}/{dayString}/Run{run}/"
            if not os.path.exists(baseDir):
                QtWidgets.QMessageBox.warning(
                    self,
                    "Recall Warning",
                    "The specified date and run combination does not exist. Please verify and run again.",
                    buttons=QtWidgets.QMessageBox.StandardButton.Ok,
                    defaultButton=QtWidgets.QMessageBox.StandardButton.Ok
                )
                return
            self.camThread = threading.Thread(None, MotTemp.main, None, [baseDir, self.tofSplitBox.value(), self, timeSplit, self.sigmaBox.value()])
            self.camThread.start()

def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    app.exec()

if __name__ == '__main__':
    main()