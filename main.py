import sys
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QPushButton, QDialog, QLabel, QGroupBox, QProgressBar
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtGui import QFont
import _thread
import threading
import winsound
import time


class ValueDial(QtWidgets.QWidget):
    ''' Взято по адресу
    https://stackoverflow.com/questions/63698714/how-to-show-markings-on-qdial-in-pyqt5-python
    Изменено для текущего проекта (чуть-чуть)
    '''
    _dialProperties = ('minimum', 'maximum', 'value', 'singleStep', 'pageStep',
        'notchesVisible', 'tracking', 'wrapping',
        'invertedAppearance', 'invertedControls', 'orientation')
    _inPadding = 3
    _outPadding = 2
    valueChanged = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        # remove properties used as keyword arguments for the dial
        dialArgs = {k:v for k, v in kwargs.items() if k in self._dialProperties}
        for k in dialArgs.keys():
            kwargs.pop(k)
        super().__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout(self)
        self.dial = QtWidgets.QDial(self, **dialArgs)
        layout.addWidget(self.dial)
        self.dial.valueChanged.connect(self.valueChanged)
        # make the dial the focus proxy (so that it captures focus *and* key events)
        self.setFocusProxy(self.dial)

        # simple "monkey patching" to access dial functions
        self.value = self.dial.value
        self.setValue = self.dial.setValue
        self.minimum = self.dial.minimum
        self.maximum = self.dial.maximum
        self.wrapping = self.dial.wrapping
        self.notchesVisible = self.dial.notchesVisible
        self.setNotchesVisible = self.dial.setNotchesVisible
        self.setNotchTarget = self.dial.setNotchTarget
        self.notchSize = self.dial.notchSize
        self.invertedAppearance = self.dial.invertedAppearance
        self.setInvertedAppearance = self.dial.setInvertedAppearance
        self.updateSize()

    def setSize(self, width, height):
        self.setFixedSize(width, height)
        parent = self.parent()
        pos_x, pos_y = round(parent.width()/2)-round(self.width()/2), round(parent.height()/2)-round(self.height()/2)
        self.move(pos_x, pos_y)

    def inPadding(self):
        return self._inPadding

    def setInPadding(self, padding):
        self._inPadding = max(0, padding)
        self.updateSize()

    def outPadding(self):
        return self._outPadding

    def setOutPadding(self, padding):
        self._outPadding = max(0, padding)
        self.updateSize()

    # the following functions are required to correctly update the layout
    def setMinimum(self, minimum):
        self.dial.setMinimum(minimum)
        self.updateSize()

    def setMaximum(self, maximum):
        self.dial.setMaximum(maximum)
        self.updateSize()

    def setWrapping(self, wrapping):
        self.dial.setWrapping(wrapping)
        self.updateSize()

    def updateSize(self):
        # a function that sets the margins to ensure that the value strings always
        # have enough space
        try:
            fm = self.fontMetrics()
            minWidth = max(fm.width(str(v)) for v in range(self.minimum(), self.maximum() + 1))
            self.offset = max(minWidth, fm.height()) / 2
            margin = self.offset + self._inPadding + self._outPadding
            # self.layout().setContentsMargins(margin, margin, margin, margin)
            '''self.setGeometry(100, 100, width, height)  # Fixed size for current project
            parent = self.parent()
            pos_x = round(parent.width()/2)-round(self.width()/2)
            pos_y = round(parent.height()/2)-round(self.height()/2)
            print('parent', parent.width(), parent.height())
            print(pos_x, pos_y)
            self.move(pos_x, pos_y)'''
        except:
            raise Exception("daill size update error")

    def translateMouseEvent(self, event):
        # a helper function to translate mouse events to the dial
        return QtGui.QMouseEvent(event.type(),
            self.dial.mapFrom(self, event.pos()),
            event.button(), event.buttons(), event.modifiers())

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.FontChange:
            self.updateSize()

    def mousePressEvent(self, event):
        self.dial.mousePressEvent(self.translateMouseEvent(event))

    def mouseMoveEvent(self, event):
        self.dial.mouseMoveEvent(self.translateMouseEvent(event))

    def mouseReleaseEvent(self, event):
        self.dial.mouseReleaseEvent(self.translateMouseEvent(event))

    def paintEvent(self, event):
        try:
            radius = min(self.width(), self.height()) / 2
            radius -= (self.offset / 2 + self._outPadding)
            invert = -1 if self.invertedAppearance() else 1
            if self.wrapping():
                angleRange = 360
                startAngle = 270
                rangeOffset = 0
            else:
                angleRange = 300
                startAngle = 240 if invert > 0 else 300
                rangeOffset = 1
            fm = self.fontMetrics()

            # a reference line used for the target of the text rectangle
            reference = QtCore.QLineF.fromPolar(radius, 0).translated(self.rect().center())
            fullRange = self.maximum() - self.minimum()
            textRect = QtCore.QRect()

            qp = QtGui.QPainter(self)
            qp.setRenderHints(qp.Antialiasing)
            for p in range(0, fullRange + rangeOffset, 1):  # instead of '1' here was self.notchSize()
                if p % 5 == 0:  # and this line for five units at dial bar
                    value = self.minimum() + p
                    if invert < 0:
                        value -= 1
                        if value < self.minimum():
                            continue
                    angle = p / fullRange * angleRange * invert
                    reference.setAngle(startAngle - angle)
                    textRect.setSize(fm.size(QtCore.Qt.TextSingleLine, str(value)))
                    textRect.moveCenter(reference.p2().toPoint())
                    qp.drawText(textRect, QtCore.Qt.AlignCenter, str(value))
        except:
            raise Exception("Dial painting Error")


class TimerSetWindowClass(QDialog):
    """
    Диалоговое окно для установки времени
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedSize(400, 500)
        self.setModal(True)
        self.hour_label = QLabel(self)
        self.min_label = QLabel(self)
        self.sec_label = QLabel(self)
        self.dot_hour_label = QLabel(self)
        self.dot_min_label = QLabel(self)
        self.dot_sec_label = QLabel(self)
        self.dial_hours = ValueDial(parent=self, minimum=0, maximum=100)
        self.dial_mins = ValueDial(parent=self.dial_hours, minimum=0, maximum=60)
        self.dial_seconds = ValueDial(parent=self.dial_mins, minimum=0, maximum=60)
        self.dial_hours.setNotchesVisible(True)
        self.dial_mins.setNotchesVisible(True)
        self.dial_seconds.setNotchesVisible(True)
        self.okBtn = QPushButton(self)
        self.okBtn.setText('OK')
        self.okPressed = False
        self.minutes = 0
        self.seconds = 0
        self.hours = 0
        self.count = 0
        self.dial_hours.valueChanged.connect(self.hourSliderMoved)
        self.dial_mins.valueChanged.connect(self.minuteSliderMoved)
        self.dial_seconds.valueChanged.connect(self.secondSliderMoved)
        self.set_geometry()
        self.okBtn.clicked.connect(self.okBtnClick)
        self.setWindowTitle("Настройка времени")

    def hourSliderMoved(self):
        """ Движение слайдера для настройки часов. Изменение надписи"""
        hours = self.dial_hours.value()
        self.hour_label.setText(str(hours))
        self.hours = hours
        if (int(str(hours)[-1]) in [0,5,6,7,8,9]) or (hours in [11,12,13,14]):
            self.dot_hour_label.setText('часов')
            self.dot_hour_label.update()
        elif int(str(hours)[-1]) in [2,3,4]:
            self.dot_hour_label.setText('часа')
        elif str(hours)[-1] in ['1']:
            self.dot_hour_label.setText('час')

    def minuteSliderMoved(self):
        """ Движение слайдера для настройки минут. Изменение надписи"""
        self.min_label.setText(str(self.dial_mins.value()))
        self.minutes = self.dial_mins.value()
        mins = self.dial_mins.value()
        if (int(str(mins)[-1]) in [0, 5, 6, 7, 8, 9]) or (mins in [11, 12, 13, 14]):
            self.dot_min_label.setText('минут')
            self.dot_min_label.update()
        elif int(str(mins)[-1]) in [2, 3, 4]:
            self.dot_min_label.setText('минуты')
        elif str(mins)[-1] in ['1']:
            self.dot_min_label.setText('минута')

    def secondSliderMoved(self):
        """ Движение слайдера для настройки секунд. Изменение надписи"""
        self.sec_label.setText(str(self.dial_seconds.value()))
        self.seconds = self.dial_seconds.value()
        secs = self.dial_seconds.value()
        if (int(str(secs)[-1]) in [0, 5, 6, 7, 8, 9]) or (secs in [11, 12, 13, 14]):
            self.dot_sec_label.setText('секунд')
            self.dot_sec_label.update()
        elif int(str(secs)[-1]) in [2, 3, 4]:
            self.dot_sec_label.setText('секунды')
        elif str(secs)[-1] in ['1']:
            self.dot_sec_label.setText('секунда')

    def set_geometry(self):
        """ Настройка внешнего вида (интерфейса)"""
        try:
            center = round(self.width()/2)
            pos1, pos2, pos3 = round(center/2), center, round(center/2)+center
            self.setFont(QFont('Arial', 12))
            lbl_width = round(self.width()/3)-20
            self.hour_label.setGeometry(pos1-10, 10, 20, 16)
            self.min_label.setGeometry(pos2-10, 10, 20, 16)
            self.sec_label.setGeometry(pos3-10, 10, 20, 16)
            self.dot_hour_label.setGeometry(pos1-23, 30, 46, 20)
            self.dot_min_label.setGeometry(pos2-27, 30, 54, 20)
            self.dot_sec_label.setGeometry(pos3-30, 30, 60, 20)
            self.okBtn.setGeometry(center-50, self.height()-40, 100, 30)
            self.dial_hours.setGeometry(0, 60, 400, 400)
            self.dial_mins.setGeometry(65, 65, 270, 270)
            self.dial_seconds.setGeometry(63, 63, 143, 140)
        except:
            raise Exception("Timer Window Set Geometry Error")

    def okBtnClick(self):
        """ Нажатие кнопки подтверждения"""
        if self.seconds == 0 and self.minutes == 0 and self.hours == 0:
            pass
        else:
            self.okPressed = True
            self.count += 1
        self.close()


class TimerClass(QGroupBox):
    """
    Класс таймера. Панелька (groupBox) с кнопками, полосой прогресса и диалоговым окном
    """
    progressChanged = QtCore.pyqtSignal(int)

    def __init__(self, window, pos):
        super().__init__(window)
        self.time_set_win = TimerSetWindowClass(window)
        self.time_set_win.closeEvent = self.set_time
        self.timer = None
        self._is_time = False
        self.stop_timer = False
        self.pos = pos
        self.parent = window
        self.createButton = QPushButton(self)
        self.createButton.setText("Добавить")
        self.createButton.clicked.connect(self.add_timer)
        self.createButton.show()
        self.hours = QLabel(self)
        self.mins = QLabel(self)
        self.secs = QLabel(self)
        self.__time = 0
        self.start_time = 0
        self.startBtn = QPushButton(self)
        self.startBtn.close()
        self.delBtn = QPushButton(self)
        self.delBtn.close()
        self.delBtn.setObjectName('delBtn')
        self.progress_bar = QProgressBar(self)
        self.progress_bar.close()
        self.set_geometry()
        self.progressChanged.connect(self.progress_bar.setValue)

    def set_time_stat(self, stat):
        """ setter для поля Состояния Времени (is_time) - идет таймер или нет"""
        try:
            self._is_time = stat
            if not stat:
                self.startBtn.setText("Пуск")
                self._is_time = False
            else:
                if not self.timer:
                    self.timer = threading.Thread(target=self.loop, args=())
                    self.timer.start()
                self._is_time = True
                self.startBtn.setText("Пауза")
        except:
            raise Exception('Time Stat Error')

    def get_time_stat(self):
        """getter для поля Состояние Времени (is_time)"""
        return self._is_time

    is_time = property(get_time_stat, set_time_stat)

    def _set_time(self, _time):
        """ setter для поля Время (time)"""
        self.__time = _time
        hours = _time // 3600
        minutes = (_time - hours * 3600) // 60
        seconds = (_time - hours * 3600 - minutes * 60)
        self.hours.setText(str(hours) + ' ч')
        self.mins.setText(": " + str(minutes) + " м")
        self.secs.setText(": " + str(seconds) + " с")

    def _get_time(self):
        """getter поля Время (time)"""
        return self.__time

    time = property(_get_time, _set_time)

    def add_timer(self):
        """открытие диалогового окна для установки времени"""
        self.is_time = False
        self.time_set_win.show()

    def set_time(self, event):
        """ событие при закрытии диалогового окна. Установка времени, добавление кнопок"""
        if self.time_set_win.okPressed:
            self.move_create_btn()
            t = self.time_set_win.hours*3600+self.time_set_win.minutes*60+self.time_set_win.seconds
            self.start_time = t
            self.time = t
            self.time_set_win.close()
            self.time_setted()

    def move_create_btn(self):
        """ изменение надписи кнопки открытия окна после установки времени"""
        self.createButton.setText("Изменить время")

    def set_geometry(self):
        """ Настройка отображения панели, надписей и кнопки открытия окна"""
        try:
            self.setGeometry(10, (self.pos-1)*150+20, self.parent.width()-20, 150)
            self.hours.setGeometry(30, 10, 40, 40)
            self.mins.setGeometry(80, 10, 40, 40)
            self.secs.setGeometry(130, 10, 40, 41)
            if self.time_set_win.count == 0:
                self.createButton.setGeometry(50, 10, 100, 100)
        except:
            raise Exception('Set Geometry Error')

    def set_geometry2(self):
        """ настройка отображения кнопок и полосы прогресса"""
        try:
            center = round(self.width()/2)
            if self.time_set_win.count>0:
                self.createButton.setGeometry(round(center)+60, 10, (self.width()-60)-(round(center)+60)-20, 50)
            self.startBtn.setGeometry(round(self.width()/2)-50, 10, 100, 50)
            self.delBtn.setGeometry(self.width() - 60, 10, 50, 50)
            self.progress_bar.setGeometry(10, 80, self.width() - 20, 30)
        except:
            raise Exception('Set Geometry2 Error')

    def time_setted(self):
        """ Отображение кнопок после настройки времениб добавление нового таймера"""
        if self.time_set_win.count == 1:
            self.startBtn.setText('Пуск')
            self.startBtn.clicked.connect(self.timer_change)
            self.startBtn.show()
            self.delBtn.setText('Х')
            self.delBtn.clicked.connect(self.delete)
            self.delBtn.show()
            self.progress_bar.show()
            self.set_geometry2()
            add_next_timer(0)

    def timer_change(self):
        """ смена состояния времени (is_time) на противоположное"""
        try:
            self.is_time = not self.is_time
        except:
            raise Exception('Timer Change Error')

    def loop(self):
        """ процедура отсчета времени. Уменьшение на 1 сек., отображение полосы прогресса, выход при завершении"""
        try:
            while self.time > 0 and self.timer:
                if self.stop_timer:
                    break
                if self.is_time:
                    self.time -= 1
                    percent = round(((self.start_time-self.time)/self.start_time)*100)
                    self.progressChanged.emit(percent)
                    time.sleep(1)
            else:
                self.stop_timer = True
                self.timeout()
        except:
            raise Exception('Loop Error')

    def timeout(self):
        """Метод для завершения отсчета. Воспроизводит звук. сигнал"""
        try:
            self.createButton.close()
            self.startBtn.close()
            winsound.Beep(500, 1000)
        except:
            raise Exception('Timeout Error')

    def delete(self):
        """Для удаления панельки таймера"""
        add_next_timer(self.pos)
        self.stop_timer = True
        self.close()


def add_next_timer(pos):
    """Создание нового таймера (панели). Удаление указанного. Сдвиг всех следующих за ним при удалении"""
    global app, win
    if pos == 0:
        pos = len(app.timers) + 1
        timer = TimerClass(win, pos)
        app.timers.append(timer)
        timer.show()
    else:
        for t in app.timers:
            if t.pos == pos:
                app.timers.remove(t)
    for t in app.timers:
        if t.pos > pos:
            t.pos = t.pos - 1
            t.set_geometry()
            t.set_geometry2()


class MainWindow(QMainWindow):
    resized = pyqtSignal()

    def __init__(self, width, height):
        """Initiative method of window"""
        super(MainWindow, self).__init__()
        self.setGeometry(100, 100, width, height)
        self.setWindowTitle("Таймер")
        self.createUI()

    def resizeEvent(self, event):
        """Resizing window causes changing of widgets' sizes"""
        self.resized.emit()
        for timer in app.timers:
            timer.set_geometry()
            timer.set_geometry2()

    def createUI(self):
        """To set some window/app's options/settings/visual styles"""
        try:
            style_file = "style.css"

            with open(style_file, "r") as sf:
                self.setStyleSheet(sf.read())
        except:
            self.setStyleSheet("""
            MainWindow {
                background-color: #fff;
                min-width: 600px;
                max-width: 800px;
                min-height: 400px; } 
            TimerClass {
                border: 1px solid gray;
                border-radius: 5px;
                background-color: #fafafa; } 
            QLabel {
                font-size: 14px; }
            QPushButton {
                font-size: 16px;
                border: 3px solid gray;
                border-radius: 5px; }
            #delBtn {
                font-size: 24px; } """)


# Create application object and application window object
if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow(width=600, height=300)
    app.timers = [TimerClass(win, 1)]
    win.show()
    sys.exit(app.exec_())
