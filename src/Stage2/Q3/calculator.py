import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QPushButton, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QPalette

class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Calculator')
        self.setFixedSize(320, 480)

        # 전체 레이아웃
        vbox = QVBoxLayout()

        # 결과창
        self.result = QLineEdit('0')
        self.result.setAlignment(Qt.AlignRight)
        self.result.setReadOnly(True)
        self.result.setFixedHeight(80)
        self.result.setFont(QFont('Arial', 24))
        vbox.addWidget(self.result)

        # 버튼 레이아웃
        grid = QGridLayout()
        buttons = [
            ('AC', 0, 0), ('+/-', 0, 1), ('%', 0, 2), ('/', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('*', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('-', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3),
            ('0', 4, 0, 1, 2), ('.', 4, 2), ('=', 4, 3)
        ]

        for button in buttons:
            if len(button) == 3:
                text, row, col = button
                btn = QPushButton(text)
                grid.addWidget(btn, row, col)
            else:
                text, row, col, rowspan, colspan = button
                btn = QPushButton(text)
                grid.addWidget(btn, row, col, rowspan, colspan)

            btn.setFixedSize(70, 70)
            btn.setFont(QFont('Arial', 18))

            # 스타일 설정
            if text in ['+', '-', '*', '/', '=']:
                btn.setStyleSheet('background-color: orange; color: white; border-radius: 35px;')
            elif text in ['AC', '+/-', '%']:
                btn.setStyleSheet('background-color: lightgray; color: black; border-radius: 35px;')
            else:
                btn.setStyleSheet('background-color: darkgray; color: white; border-radius: 35px;')

            btn.clicked.connect(self.buttonClicked)

        vbox.addLayout(grid)
        self.setLayout(vbox)

        self.current_expression = ''

        # 배경색 설정
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        self.setPalette(palette)

    def buttonClicked(self):
        sender = self.sender()
        text = sender.text()

        if text == 'AC':
            self.current_expression = ''
            self.result.setText('0')
        elif text == '+/-':
            if self.current_expression:
                if self.current_expression.startswith('-'):
                    self.current_expression = self.current_expression[1:]
                else:
                    self.current_expression = '-' + self.current_expression
                self.result.setText(self.current_expression)
        elif text == '%':
            try:
                value = float(self.current_expression)
                value = value / 100
                self.current_expression = str(value)
                self.result.setText(self.current_expression)
            except:
                pass
        elif text == '=':
            try:
                result = str(eval(self.current_expression))
                self.result.setText(result)
                self.current_expression = result
            except:
                self.result.setText('Error')
                self.current_expression = ''
        else:
            if self.result.text() == '0' and text not in ['+', '-', '*', '/', '.']:
                self.current_expression = text
            else:
                self.current_expression += text
            self.result.setText(self.current_expression)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    calc = Calculator()
    calc.show()
    sys.exit(app.exec_())