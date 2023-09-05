import sys
from functools import partial
from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

LABELS = [
    "O",
    "B-PRO",
    "B-MAR",
    "B-ESP",
    "B-TAM",
    "B-QUA",
    "I-PRO",
    "I-MAR",
    "I-ESP",
    "I-TAM",
    "I-QUA",
]

# TODO: move to a better file further
def generate_tokens(name: str) -> List:
    return name.strip().split(" ")


class NERLabelingApp(QMainWindow):
    def __init__(self, file_data: str):
        super().__init__()
        self.file_data = file_data
        self.data_list = self.read_data(file_data)
        self.selected_tags = []
        self.current_text_index = 0
        self.current_label_index = 0
        self.current_word_index = 0
        self.current_button_index = 0
        self.current_words = None

        # Widgtes
        self.text_view = None
        self.word_view = None
        self.tags_view = None
        self.save_button = None
        self.clear_button = None
        self.next_text_button = None
        self.previous_text_button = None
        self.next_word_button = None
        self.previous_word_button = None
        self.current_index_label = None
        self.label_buttons = []

        self.print_shortkeys()
        self.create_actions()
        self._load_widgets()
        self._load_layout()
        self.update_all()

    def update_all(self):
        self._update_text()
        self._update_word()
        self._update_labels()
        self._update_index()

    def reset_all(self):
        self.selected_tags = []
        self.update_all()

    def _update_text(self):
        text = self.data_list[self.current_text_index].get("product")
        self.current_word_index = 0
        self.text_view.setPlainText(text)
        self.current_words = generate_tokens(text)

    def _update_word(self):
        self.word_view.setPlainText(self.current_words[self.current_word_index])

    def _update_labels(self):
        text = ""
        for tag in self.data_list[self.current_text_index]["tags"] + self.selected_tags:
            tag_name = tag[0]
            name = self.text_view.toPlainText()[tag[1] : tag[2]]
            text += f"{tag_name} : {name}\n"
        self.tags_view.setText(text)

    def _update_index(self):
        self.current_index_label.setText(str(self.current_text_index))

    def save_data_action(self):
        self.data_list[self.current_text_index]["tags"] += self.selected_tags
        self.selected_tags = []
        self.save_to_file(self.file_data)

    def save_to_file(self, file_data):
        with open(file_data, "w+") as f:
            f.write("[")
            for product in self.data_list:
                f.write(f"{repr(product)},\n")
            f.write("]\n")

    def clear_action(self):
        self.data_list[self.current_text_index]["tags"] = []
        self.reset_all()

    def previous_text_action(self):
        self.current_text_index -= 1
        self.current_text_index = max(self.current_text_index, 0)
        self.reset_all()

    def next_text_action(self):
        self.current_text_index += 1
        self.current_text_index = min(self.current_text_index, len(self.data_list) - 1)
        self.reset_all()

    def previous_word_action(self):
        self.current_word_index -= 1
        self.current_word_index = max(self.current_word_index, 0)
        self._update_word()

    def next_word_action(self):
        self.current_word_index += 1
        self.current_word_index = min(self.current_word_index, len(self.current_words) - 1)
        self._update_word()

    def label_button_clicked(self, id):
        text = self.data_list[self.current_text_index].get("product")
        start = 0
        for idx in range(self.current_word_index):
            word = self.current_words[idx]
            start += len(word) + 1
        word = self.current_words[self.current_word_index]
        end = start + len(word)
        updated = False
        for selected_tag in self.selected_tags:
            if selected_tag[1] == start and selected_tag[2] == end:
                selected_tag[0] = LABELS[id]
                updated = True
        tag = [LABELS[id], start, end]
        if not updated and not tag in self.selected_tags:
            self.selected_tags.append(tag)
        self.next_word_action()
        self._update_labels()

    def read_data(self, file_data):
        with open(file_data, "r+") as f:
            data_list = eval(f.read())
        return data_list

    def _load_widgets(self):
        self.text_view = QTextEdit(self)
        self.text_view.setFixedHeight(self.text_view.fontMetrics().height() + 10)
        self.text_view.setReadOnly(True)

        self.word_view = QTextEdit(self)
        self.word_view.setFixedHeight(self.word_view.fontMetrics().height() + 10)
        self.word_view.setReadOnly(True)

        self.tags_view = QLabel(self)
        self.tags_view.setStyleSheet("background-color: lightblue;")

        # Buttons
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_data_action)

        self.clear_button = QPushButton("Clear", self)
        self.clear_button.clicked.connect(self.clear_action)

        self.next_text_button = QPushButton(">>", self)
        self.next_text_button.clicked.connect(self.next_text_action)

        self.previous_text_button = QPushButton("<<", self)
        self.previous_text_button.clicked.connect(self.previous_text_action)

        self.next_word_button = QPushButton(">", self)
        self.next_word_button.clicked.connect(self.next_word_action)

        self.previous_word_button = QPushButton("<", self)
        self.previous_word_button.clicked.connect(self.previous_word_action)

        self.current_index_label = QLabel(self)
        self.current_index_label.setText("0")
        self.current_index_label.setAlignment(Qt.AlignCenter)
        for id, label in enumerate(LABELS):
            button = QPushButton(label, self)
            button.clicked.connect(partial(self.label_button_clicked, id))
            self.label_buttons.append(button)
        self.label_buttons[self.current_button_index].setFocus()

    def _load_layout(self):
        self.setWindowTitle("NER Labeling Interface")
        self.resize(500, 300)

        # The labels handler (Save, Clear)
        labels_handler_layout = QHBoxLayout()
        labels_handler_layout.addWidget(self.save_button)
        labels_handler_layout.addWidget(self.clear_button)

        labels_tools_widget = QWidget()
        labels_tools_widget.setLayout(labels_handler_layout)

        # Tags Buttons
        tag_buttons_intermediate_layout = QHBoxLayout()
        tag_buttons_layout = QHBoxLayout()
        intermediate_buttons = [x for x in self.label_buttons if x.text().startswith("I-")]
        for button in self.label_buttons:
            if button in intermediate_buttons:
                tag_buttons_intermediate_layout.addWidget(button)
            else:
                tag_buttons_layout.addWidget(button)

        tags_widget = QWidget()
        tags_widget.setLayout(tag_buttons_layout)
        tags_intermediate_widget = QWidget()
        tags_intermediate_widget.setLayout(tag_buttons_intermediate_layout)
        # The text handler (<<, <, index, >, >>)
        text_handler_layout = QHBoxLayout()
        text_handler_layout.addWidget(self.previous_text_button)
        text_handler_layout.addWidget(self.previous_word_button)
        text_handler_layout.addWidget(self.current_index_label)
        text_handler_layout.addWidget(self.next_word_button)
        text_handler_layout.addWidget(self.next_text_button)

        text_tools_widget = QWidget()
        text_tools_widget.setLayout(text_handler_layout)

        # Main Layoutw
        layout = QVBoxLayout()
        layout.addWidget(self.text_view)
        layout.addWidget(self.word_view)
        layout.addWidget(tags_widget)
        layout.addWidget(tags_intermediate_widget)
        layout.addWidget(self.tags_view)
        layout.addWidget(labels_tools_widget)
        layout.addWidget(text_tools_widget)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def create_actions(self):
        # Actions
        go_to_next_text = QAction("Next Text", self)
        go_to_previous_text = QAction("Previous Text", self)
        save_action = QAction("Save", self)
        clear_action = QAction("Clear", self)
        next_button = QAction("Button next", self)
        previous_button = QAction("Button previous", self)
        click_button = QAction("Click Button", self)

        go_to_next_text.setShortcut(QKeySequence(Qt.Key_Right))
        go_to_previous_text.setShortcut(QKeySequence(Qt.Key_Left))
        save_action.setShortcut(QKeySequence(Qt.Key_S))
        clear_action.setShortcut(QKeySequence(Qt.Key_C))
        next_button.setShortcut(QKeySequence(Qt.Key_D))
        previous_button.setShortcut(QKeySequence(Qt.Key_A))
        click_button.setShortcut(QKeySequence(Qt.Key_W))

        # Connect the action to a slot (function)
        go_to_next_text.triggered.connect(self.next_text_action)
        go_to_previous_text.triggered.connect(self.previous_text_action)
        save_action.triggered.connect(self.save_data_action)
        clear_action.triggered.connect(self.clear_action)
        next_button.triggered.connect(self.next_button_action)
        previous_button.triggered.connect(self.previous_button_action)
        click_button.triggered.connect(self.click_button_action)

        # Add the action to the main window
        self.addAction(go_to_next_text)
        self.addAction(go_to_previous_text)
        self.addAction(save_action)
        self.addAction(clear_action)
        self.addAction(next_button)
        self.addAction(previous_button)
        self.addAction(click_button)

    def next_button_action(self):
        self.current_button_index = (self.current_button_index + 1) % len(self.label_buttons)
        self.update_selected_button_color()

    def previous_button_action(self):
        self.current_button_index = (self.current_button_index - 1) % len(self.label_buttons)
        self.update_selected_button_color()

    def update_selected_button_color(self):
        self.label_buttons[self.current_button_index].setFocus()
        for button in self.label_buttons:
            button.setStyleSheet("")  # Reset style for all buttons
        self.label_buttons[self.current_button_index].setStyleSheet("background-color: yellow;")

    def click_button_action(self):
        self.label_buttons[self.current_button_index].click()

    def print_shortkeys(self):
        text = f"""Shortkeys:
        a: previous tag
        d: next tag
        w: click selected button
        s: save
        c: clear
        left arrow: previous word
        right arrow: next word
        """
        print(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    for flag in sys.argv:
        if flag.startswith("--data="):
            file_data = flag.split("=")[-1]
    window = NERLabelingApp(file_data)
    window.show()
    sys.exit(app.exec_())
