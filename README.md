# python_timer

###### python, pyqt5, python css, threading, gui, signals

Таймер на Python с использованием библиотеки PyQt5. 
Код круглого слайдера (QDial) взят по адресу _https://stackoverflow.com/questions/63698714/how-to-show-markings-on-qdial-in-pyqt5-python_

Ошибки при создании:
1. _QBackingStore::endPaint() called with active painter; did you forget to destroy it or call QPainter::end() on it?_
2. _QObject::setParent: Cannot set parent, new parent is in a different thread_

1.1 ~~Причина:~~ Обращение к progressBar напрямую (self.progressBar.setValue(x))
1.2 **Надо** обращаться через сигнал
class TimerClass(QGroupBox):
progressChanged = QtCore.pyqtSignal(int)
...
  def __init__(self):
...
  self.progressChanged.connect(self.progress_bar.setValue)
...
  self.progressChanged.emit(percent)

3. _При попытке настроить границы/ скругление границ через стили границы пропадают совсем_
3.1. ~~Причина:~~ неправильный порядок параметров
3.2. **Надо** задавать настройки в определенном порядке:
Stylesheet {
...
border: px type color;
... }
Использование в другом порядке = ошибка
