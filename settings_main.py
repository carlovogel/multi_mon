#!/usr/bin/env python3
# -*- coding: utf-8 -*

import sys
import subprocess
import configparser
from pathlib import Path
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QCursor, QFont

CONF_FILE = Path(__file__).parent / 'multi_mon_conf.conf'
ICONS_DIR = Path(__file__).parent / 'icons'
STYLE_SHEET_DIR = Path(__file__).parent / 'stylesheets'
FONT = QFont('Noto Sans', 18)
TYPE_DICT = {
    'main': (QIcon(str(ICONS_DIR / 'screen_main.svg')), 'Main monitor'),
    'tv': (QIcon(str(ICONS_DIR / 'tv.svg')), 'TV or projector'),
    'secondary': (QIcon(str(ICONS_DIR / 'screen_secondary.svg')), 'Secondary monitor')
             }
BUTTON_LABEL_TUPLE = ('main_only', 'secondary_extended', 'tv_extended', 'tv_only', 'all_extended',
                      'tv_mirror', 'secondary_mirror', 'secondary_only', 'secondary_2_only',
                      'secondary_2_extended', 'secondary_2_mirror', 'tv_2_only', 'tv_2_extended', 'tv_2_mirror'
                      )


class ProxyStyleBiggerMenuIcons(QtWidgets.QProxyStyle):
    """Changes the icon size for the screen type menu entries in the tool button menu.
    """
    def pixelMetric(self, pixel_metric, option=None, widget=QtWidgets.QMenu):
        if pixel_metric == QtWidgets.QStyle.PM_SmallIconSize:
            return 90
        else:
            return QtWidgets.QProxyStyle.pixelMetric(self, pixel_metric, option, widget)


class SettingsMainWindow(QtWidgets.QDialog):
    """Main settings window. Options to select the screen types, ports, resolutions and refresh rates of each screen.
    Option to select the side on which MultiMon is going to show up.
    Option to open the customize window and to start MultiMon.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('MultiMon Settings')
        self.setWindowIcon(QIcon(str(ICONS_DIR / 'icon_settings.svg')))
        self.config = self.read_config()
        self.connected_ports_dict = self.get_connected_screen_infos()
        self.screen_count = len(self.connected_ports_dict)
        try:
            self.tv_count = int(self.config['Screens']['tv_count'] or 0)
        except KeyError:
            self.tv_count = 0
        self.vertical_layout_main = QtWidgets.QVBoxLayout(self)
        self.vertical_layout_main.setContentsMargins(10, 10, 10, 10)
        self.vertical_layout_main.setSpacing(10)
        self.make_reload_layout()
        self.widget_dict_tuple = self.make_screen_settings_layout()
        self.mode_radio_button_tuple = self.make_mode_selection_layout()
        self.make_button_box()
        self.action_tuple = self.make_screen_type_menu()
        self.load_values_from_config_to_gui()
        self.disable_middle_screen_if_two_screens()
        with open(STYLE_SHEET_DIR / 'main_settings.stylesheet', 'r') as style_sheet:
            self.setStyleSheet(style_sheet.read().replace(
                    'unchecked_icon_file', str(ICONS_DIR / 'radio_unchecked.svg')
                                                          ).replace(
                'checked_icon_file', str(ICONS_DIR / 'radio_checked.svg')
                                                                    )
                               )

    @staticmethod
    def read_config():
        """Initializes the config parser and reads the conf file into it, if the conf file exists.
        Adds all sections to the config parser, if not.
        """
        config = configparser.ConfigParser()
        if not config.read(CONF_FILE):
            for section in ('Screens', 'Mode', 'Customize'):
                config.add_section(section)
        return config

    @staticmethod
    def get_connected_screen_infos():
        """Returns a dict with all connected ports as keys and dictionaries as values,
        where the resolutions of the connected screens are the keys and all possible refresh rates the values:
        {port: {resolution: rate}}
        Uses the tool Xrandr to get the information.
        """
        with subprocess.Popen(('xrandr', '-q'), stdout=subprocess.PIPE) as proc:
            all_port_list = proc.stdout.readlines()
        port_dict = {}
        resolution_dict = {}
        port = ''
        for line in all_port_list[1:]:
            if b'disconnected' in line:
                pass
            elif b'connected' in line:
                resolution_dict = {}
                port = line.split(sep=b' ')[0].decode('utf-8')
            else:
                line = line.replace(b'*', b'').replace(b'+', b'').strip().split(sep=b' ')
                resolution = line[0].decode('utf-8')
                rate_list = [line[index].decode('utf-8') for index in range(1, len(line)) if line[index]]
                rate_list.sort(key=float, reverse=True)
                resolution_dict[resolution] = rate_list
                port_dict[port] = resolution_dict
        return port_dict

    def make_reload_layout(self):
        """Creates and places the 'Reload Window' button and the label next to it.
        Returns the reload button widget.
        """
        horizontal_layout_reload = QtWidgets.QHBoxLayout()
        horizontal_layout_reload.setContentsMargins(10, 10, 10, 10)

        label_reload = QtWidgets.QLabel(self)
        label_reload.setFont(FONT)
        spacer_item = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        push_button_reload = QtWidgets.QPushButton(self)
        push_button_reload.setMinimumSize(QSize(0, 60))
        push_button_reload.setFont(FONT)
        push_button_reload.setCursor(QCursor(Qt.PointingHandCursor))
        push_button_reload.clicked.connect(self.reload_window)

        horizontal_layout_reload.addWidget(label_reload)
        horizontal_layout_reload.addItem(spacer_item)
        horizontal_layout_reload.addWidget(push_button_reload)

        plural_string = ['are', 's'] if self.screen_count > 1 else ['is', '']
        label_reload.setText(
            f'There {plural_string[0]} {self.screen_count} connected screen{plural_string[1]} detected. Not correct?\n'
            f'Check your connection and click reload connections:'
                             )
        push_button_reload.setToolTip('Reload the window with a new connection check.')
        push_button_reload.setText('   Reload window   ')
        self.vertical_layout_main.addLayout(horizontal_layout_reload)
        return push_button_reload

    def make_screen_settings_layout(self):
        """Creates and places the screen settings widgets.
        Return a tuple of dictionaries with the frame and the widgets related to the port, resolution, rate and
        screen type as values and their names as keys:
            'port': combo_box_port,
            'resolution': combo_box_resolution,
            'rate': combo_box_rate,
            'type_label': label_type,
            'type_button': tool_button_type,
            'type_menu': QtWidgets.QMenu(),
            'frame': frame
        """
        horizontal_layout_screen_settings = QtWidgets.QHBoxLayout()
        horizontal_layout_screen_settings.setContentsMargins(0, 0, 0, 0)
        horizontal_layout_screen_settings.setSpacing(0)

        widget_dict_tuple = ()
        for position in ('left', 'middle', 'right'):
            frame = QtWidgets.QFrame(self)
            font_big = QFont('Noto Sans', 22)
            font_small = QFont('Noto Sans', 11)
            vertical_layout = QtWidgets.QVBoxLayout(frame)
            vertical_layout.setContentsMargins(10, 10, 10, 10)
            vertical_layout.setSpacing(2)

            label_type = (QtWidgets.QLabel(frame))
            label_type.setContentsMargins(0, 0, 0, 10)
            label_type.setFont(font_big)
            label_type.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
            label_type.setText(f'{position.capitalize()} screen')
            tool_button_type = QtWidgets.QToolButton(frame)
            tool_button_type.setMinimumSize(QSize(380, 300))
            tool_button_type.setCursor(QCursor(Qt.PointingHandCursor))
            tool_button_type.setIcon(QIcon(str(ICONS_DIR / 'screen.svg')))
            tool_button_type.setIconSize(QSize(270, 200))
            tool_button_type.setPopupMode(QtWidgets.QToolButton.InstantPopup)
            tool_button_type.setToolButtonStyle(Qt.ToolButtonIconOnly)

            label_port = QtWidgets.QLabel(frame)
            label_port.setContentsMargins(0, 10, 0, 0)
            label_port.setFont(font_small)
            combo_box_port = QtWidgets.QComboBox(frame)
            combo_box_port.setCursor(QCursor(Qt.PointingHandCursor))
            combo_box_port.activated.connect(self.change_resolution_and_rate_entries)
            combo_box_port.setFont(font_small)

            label_resolution = QtWidgets.QLabel(frame)
            label_resolution.setFont(font_small)
            combo_box_resolution = QtWidgets.QComboBox(frame)
            combo_box_resolution.setMinimumSize(QSize(110, 0))
            combo_box_resolution.setCursor(QCursor(Qt.PointingHandCursor))
            combo_box_resolution.activated.connect(self.change_resolution_and_rate_entries)
            combo_box_resolution.setFont(font_small)
            spacer_item = QtWidgets.QSpacerItem(0, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

            label_rate = QtWidgets.QLabel(frame)
            label_rate.setFont(font_small)
            combo_box_rate = QtWidgets.QComboBox(frame)
            combo_box_rate.setCursor(QCursor(Qt.PointingHandCursor))
            combo_box_rate.setFont(font_small)
            label_hz = QtWidgets.QLabel(frame)

            label_port.setText('Port:')
            label_rate.setText('Refresh rate:')
            label_resolution.setText('Resolution:')
            label_hz.setText('Hz')
            combo_box_port.setToolTip(f'Select the port of the {position} screen.')
            combo_box_resolution.setToolTip(f'Select the resolution of the {position} screen.')
            combo_box_rate.setToolTip(f'Select the refresh rate of the {position} screen.')
            tool_button_type.setToolTip(f'Select the type of the {position} screen.')

            grid_layout_combo = QtWidgets.QGridLayout()
            grid_layout_combo.setContentsMargins(0, 10, 0, 0)
            grid_layout_combo.setHorizontalSpacing(4)
            grid_layout_combo.setVerticalSpacing(2)

            grid_layout_combo.addWidget(label_resolution, 0, 0, 1, 1)
            grid_layout_combo.addWidget(label_rate, 0, 2, 1, 1)
            grid_layout_combo.addWidget(combo_box_resolution, 1, 0, 1, 1)
            grid_layout_combo.addItem(spacer_item, 1, 1, 1, 1)
            grid_layout_combo.addWidget(combo_box_rate, 1, 2, 1, 1)
            grid_layout_combo.addWidget(label_hz, 1, 3, 1, 1)

            vertical_layout.addWidget(label_type)
            vertical_layout.addWidget(tool_button_type)
            vertical_layout.addWidget(label_port)
            vertical_layout.addWidget(combo_box_port)
            vertical_layout.addLayout(grid_layout_combo)

            horizontal_layout_screen_settings.addWidget(frame)
            widget_dict = {
                'port': combo_box_port,
                'resolution': combo_box_resolution,
                'rate': combo_box_rate,
                'type_label': label_type,
                'type_button': tool_button_type,
                'type_menu': QtWidgets.QMenu(),
                'frame': frame
                           }
            widget_dict_tuple += (widget_dict,)
        self.vertical_layout_main.addLayout(horizontal_layout_screen_settings)
        return widget_dict_tuple

    def make_mode_selection_layout(self):
        """Creates and places the radio buttons for the mode selection and the label next to it.
        Returns a tuple of the left and the right radio button widget.
        """
        horizontal_layout_mode = QtWidgets.QHBoxLayout()
        horizontal_layout_mode.setContentsMargins(10, 10, 10, 10)
        horizontal_layout_mode.setSpacing(40)

        label_mode = QtWidgets.QLabel(self)
        label_mode.setFont(FONT)
        label_mode.setMinimumHeight(60)
        spacer_item = QtWidgets.QSpacerItem(20, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        radio_button_left_mode = QtWidgets.QRadioButton(self)
        radio_button_left_mode.setFont(FONT)
        radio_button_left_mode.setCursor(QCursor(Qt.PointingHandCursor))
        radio_button_right_mode = QtWidgets.QRadioButton(self)
        radio_button_right_mode.setFont(FONT)
        radio_button_right_mode.setCursor(QCursor(Qt.PointingHandCursor))

        horizontal_layout_mode.addWidget(label_mode)
        horizontal_layout_mode.addItem(spacer_item)
        horizontal_layout_mode.addWidget(radio_button_left_mode)
        horizontal_layout_mode.addWidget(radio_button_right_mode)

        label_mode.setText('Where on your screen do you want to show MultiMon?')
        radio_button_left_mode.setText('Left edge')
        radio_button_left_mode.setToolTip('MultiMon shows up on the left edge of the screen.')
        radio_button_right_mode.setText('Right edge')
        radio_button_right_mode.setToolTip('MultiMon shows up on the right edge of the screen.')

        self.vertical_layout_main.addLayout(horizontal_layout_mode)

        return radio_button_left_mode, radio_button_right_mode

    def make_button_box(self):
        """Creates and places the buttons 'Start MultiMon', 'Customize MultiMon', 'Exit' and 'Apply' and connects them
        to their related methods.
        """
        horizontal_layout_button_box = QtWidgets.QHBoxLayout()
        horizontal_layout_button_box.setSpacing(20)
        horizontal_layout_button_box.setContentsMargins(10, 0, 10, 10)
        push_button_start = QtWidgets.QPushButton(self)
        push_button_start.setMinimumSize(QSize(0, 60))
        push_button_start.setFont(FONT)
        push_button_start.setCursor(QCursor(Qt.PointingHandCursor))
        push_button_customize = QtWidgets.QPushButton(self)
        push_button_customize.setMinimumSize(QSize(0, 60))
        push_button_customize.setFont(FONT)
        push_button_customize.setCursor(QCursor(Qt.PointingHandCursor))

        spacer_item = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        push_button_exit = QtWidgets.QPushButton(self)
        push_button_exit.setMinimumSize(QSize(60, 60))
        push_button_exit.setCursor(QCursor(Qt.PointingHandCursor))
        push_button_exit.setIcon(QIcon(str(ICONS_DIR / 'exit.svg')))
        push_button_exit.setIconSize(QSize(40, 40))
        push_button_apply = QtWidgets.QPushButton(self)
        push_button_apply.setMinimumSize(QSize(66, 60))
        push_button_apply.setCursor(QCursor(Qt.PointingHandCursor))
        push_button_apply.setIcon(QIcon(str(ICONS_DIR / 'finish.svg')))
        push_button_apply.setIconSize(QSize(46, 43))

        horizontal_layout_button_box.addWidget(push_button_start)
        horizontal_layout_button_box.addWidget(push_button_customize)
        horizontal_layout_button_box.addItem(spacer_item)
        horizontal_layout_button_box.addWidget(push_button_exit)
        horizontal_layout_button_box.addWidget(push_button_apply)
        self.vertical_layout_main.addLayout(horizontal_layout_button_box)
        push_button_start.setText('   Start MultiMon   ')
        push_button_customize.setText('   Customize MultiMon   ')
        push_button_start.setToolTip('Save settings and start MultiMon')
        push_button_customize.setToolTip('Save settings and customize the buttons showing up in MultiMon')
        push_button_exit.setToolTip('Exit')
        push_button_apply.setToolTip('Save and exit')
        push_button_exit.clicked.connect(self.close)
        if self.screen_count > 1:
            push_button_start.clicked.connect(self.start_multi_mon)
            push_button_customize.clicked.connect(self.open_customize_window)
            push_button_apply.clicked.connect(self.apply_changes_and_exit)
        else:
            for button in (push_button_start, push_button_customize, push_button_apply):
                button.clicked.connect(self.one_screen_warning)

    def make_screen_type_menu(self):
        """Returns a tuple of dictionaries {screen_type: action} for each screen, where the actions
        are associated to the screen type entries of the tool button menus.
        """
        menu_entries_tuple = ()
        with open(STYLE_SHEET_DIR / 'tool_button_menu.stylesheet', 'r') as style_sheet_file:
            menu_style_sheet = style_sheet_file.read()
        for widget_dict in self.widget_dict_tuple:
            action_type_dict = {}
            for screen_type, icon_label_tuple in TYPE_DICT.items():
                menu_entries = QtWidgets.QAction(*icon_label_tuple)
                menu_entries.triggered.connect(self.change_screen_type_by_action)
                widget_dict['type_menu'].addAction(menu_entries)
                widget_dict['type_button'].setMenu(widget_dict['type_menu'])
                widget_dict['type_menu'].setStyleSheet(menu_style_sheet)
                action_type_dict[screen_type] = menu_entries
            menu_entries_tuple += (action_type_dict,)
        return menu_entries_tuple

    def load_values_from_config_to_gui(self):
        """Loads all the values from the config parser to the related default values of the GUI.
        """
        tuple_ports = tuple(self.connected_ports_dict)
        tuple_port_labels = self.get_more_detailed_port_tuple(tuple(self.connected_ports_dict))
        for screen_nr, widget_dict in enumerate(self.widget_dict_tuple):
            self.load_port_entries(screen_nr, tuple_port_labels)
            try:
                widget_dict['port'].setCurrentIndex(
                    tuple_ports.index(self.config['Screens'][f'port_screen_{screen_nr}'])
                                                    )
            except ValueError:
                pass
            except KeyError:
                pass
            self.load_resolution_and_rate_entries(screen_nr)
            try:
                self.set_screen_type(screen_nr, self.config['Screens'][f'type_screen_{screen_nr}'].strip('_2'))
            except KeyError:
                pass
        try:
            mode_edge = self.config['Mode']['edge']
        except KeyError:
            mode_edge = ''
        if mode_edge == 'left':
            self.mode_radio_button_tuple[0].setChecked(True)
        else:
            self.mode_radio_button_tuple[1].setChecked(True)

    @staticmethod
    def get_more_detailed_port_tuple(port_tuple):
        """Adds the model and the manufacturer to the tuple of ports for the active screens using QT5 methods.
        Returns more detailed tuple for given port tuple.
        """
        list_active_screens = QtWidgets.QApplication.screens()
        tuple_port_label = ()
        for port in port_tuple:
            for screen in list_active_screens:
                if port == screen.name():
                    port = f'{screen.name()}: {screen.model().strip("-")} by {screen.manufacturer()}'

            tuple_port_label += (port,)
        return tuple_port_label

    def disable_middle_screen_if_two_screens(self):
        """Disables middle screen GUI elements if there are less then three screens.
        """
        if self.screen_count < 3:
            self.widget_dict_tuple[1]['frame'].setDisabled(True)
            self.widget_dict_tuple[1]['type_label'].setText('disconnected')
            self.widget_dict_tuple[1]['type_button'].setIcon(QIcon(str(ICONS_DIR / 'screen_disabled.svg')))
            self.widget_dict_tuple[1]['type_menu'].setDefaultAction(QtWidgets.QAction())
            self.widget_dict_tuple[1]['port'].clear()
            self.widget_dict_tuple[1]['resolution'].clear()
            self.widget_dict_tuple[1]['rate'].clear()

    def load_port_entries(self, screen_nr, tuple_port_labels):
        """Loads the given tuple of labels of all connected ports to the port combo box of the screen with the given
        screen nr.
        """
        for mon in tuple_port_labels:
            self.widget_dict_tuple[screen_nr]['port'].addItem(mon)

    def load_resolution_and_rate_entries(self, screen_nr):
        """Loads all possible resolutions and refresh rates for the selected port to the associated combo boxes.
        Loads the values for port, resolution and rate from the config parser to the related widgets as default values.
        """
        port_combo_box = self.widget_dict_tuple[screen_nr]['port']
        resolution_combo_box = self.widget_dict_tuple[screen_nr]['resolution']
        resolution_combo_box.clear()
        for resolution in self.connected_ports_dict[port_combo_box.currentText().split(sep=' ')[0].strip(':')]:
            resolution_combo_box.addItem(resolution)
        try:
            resolution_combo_box.setCurrentText(self.config['Screens'][f'resolution_screen_{screen_nr}'])
        except KeyError:
            pass
        self.load_rate_entries(screen_nr)

    def load_rate_entries(self, screen_nr):
        """Loads all possible refresh rates for the selected port and resolution to the associated combo box.
        """
        port_combo_box = self.widget_dict_tuple[screen_nr]['port']
        resolution_combo_box = self.widget_dict_tuple[screen_nr]['resolution']
        rate_combo_box = self.widget_dict_tuple[screen_nr]['rate']
        rate_combo_box.clear()
        resolution_dict = self.connected_ports_dict[port_combo_box.currentText().split(sep=' ')[0].strip(':')]
        for rate in resolution_dict[resolution_combo_box.currentText()]:
            rate_combo_box.addItem(rate)
        try:
            rate_combo_box.setCurrentText(self.config['Screens'][f'rate_screen_{screen_nr}'])
        except KeyError:
            pass

    def set_screen_type(self, screen_nr, screen_type):
        """Changes label, icon and menu default value for the given screen_nr to the given screen type.
        """
        try:
            self.widget_dict_tuple[screen_nr]['type_menu'].setDefaultAction(self.action_tuple[screen_nr][screen_type])
            self.widget_dict_tuple[screen_nr]['type_button'].setIcon(TYPE_DICT[screen_type][0])
            self.widget_dict_tuple[screen_nr]['type_label'].setText(TYPE_DICT[screen_type][1])
        except KeyError:
            pass

    def change_resolution_and_rate_entries(self):
        """Updates the shown resolution and refresh rates if the port or the resolution combo boxes were activated.
        """
        for screen_nr, widget_dict in enumerate(self.widget_dict_tuple):
            if widget_dict['port'] is self.sender():
                self.load_resolution_and_rate_entries(screen_nr)
            elif widget_dict['resolution'] is self.sender():
                self.load_rate_entries(screen_nr)

    def change_screen_type_by_action(self):
        """Changes label, icon and default_action of the screen associated to the action calling this method.
        """
        for screen_nr, type_dict in enumerate(self.action_tuple):
            for screen_type, action in type_dict.items():
                if action is self.sender():
                    self.set_screen_type(screen_nr, screen_type)

    def reload_window(self):
        """Reloads the window with a new scan of all connected ports.
        """
        self.close()
        settings_main_new = SettingsMainWindow(self)
        settings_main_new.show()

    def start_multi_mon(self):
        """Saves the settings and opens MultiMon.
        """
        if not self.apply_changes_and_exit():
            return False
        from multi_mon import MultiMon
        start_multi_mon = MultiMon(self)
        start_multi_mon.showFullScreen()

    def open_customize_window(self):
        """Saves the settings and opens the Customize Window.
        Returns False, if settings the settings are incorrect.
        """
        if not self.save_all_values_in_config():
            return False
        customize_window = CustomizeWindow(self, self.config)
        customize_window.show()

    def save_mode_in_config(self):
        """Saves the side selection ('left' / 'right') of the mode radio buttons in the config parser.
        """
        if self.mode_radio_button_tuple[0].isChecked():
            self.config['Mode']['edge'] = 'left'
        else:
            self.config['Mode']['edge'] = 'right'

    def save_all_values_in_config(self):
        """Saves all the values in the config parser.
        Returns True, if successful - Returns False and opens warning window, if not.
        """
        selected_values_dict = self.get_all_values_from_widgets()
        if not self.check_if_all_settings_correct(selected_values_dict['type'], selected_values_dict['port']):
            return False
        new_tv_count = selected_values_dict['type'].count('tv')
        if self.check_if_setup_changed(self.screen_count, new_tv_count):
            self.tv_count = new_tv_count
            self.set_default_button_selection()
        self.config['Screens']['tv_count'] = str(new_tv_count)
        self.config['Screens']['screen_count'] = str(self.screen_count)
        selected_values_dict['type'] = self.rename_double_screen_types(selected_values_dict['type'])
        for screen_nr in range(self.screen_count if self.screen_count > 2 else 3):
            for key, value in selected_values_dict.items():
                self.config['Screens'][f'{key}_screen_{screen_nr}'] = value[screen_nr]
        self.save_mode_in_config()
        return True

    def get_all_values_from_widgets(self):
        """Reads all the selected values from the GUI widgets. Returns a dictionary with the value names as keys and
        tuples of the values indexed by the screen_nr as values. Possible keys: 'port, 'resolution', 'rate, 'type
        """
        selected_values_dict = {'port': (), 'resolution': (), 'rate': (), 'type': ()}

        for screen_nr, type_dict in enumerate(self.action_tuple):
            selected_values_dict['port'] += (self.widget_dict_tuple[screen_nr]['port'].currentText().split(sep=':')[0],)
            selected_values_dict['resolution'] += (self.widget_dict_tuple[screen_nr]['resolution'].currentText(),)
            selected_values_dict['rate'] += (self.widget_dict_tuple[screen_nr]['rate'].currentText(),)
            screen_type_to_add = ''
            for screen_type, action in type_dict.items():
                if self.widget_dict_tuple[screen_nr]['type_menu'].defaultAction() is action:
                    screen_type_to_add = screen_type
            selected_values_dict['type'] += (screen_type_to_add,)
        return selected_values_dict

    def check_if_all_settings_correct(self, selected_screen_type_tuple, selected_port_tuple):
        """Opens warning window and Returns False, if incorrect settings detected.
        Returns True, if all settings are correct.
        """
        if 'main' not in selected_screen_type_tuple:
            self.open_warning_window('You need to select at least one main screen.')
            return False

        elif selected_screen_type_tuple.count('main') > 1:
            self.open_warning_window('Only one main screen.')
            return False

        elif len(tuple(filter(bool, selected_screen_type_tuple))) != self.screen_count:
            self.open_warning_window('You need to select the screen type for each screen.')
            return False

        elif len(selected_port_tuple) != len(set(selected_port_tuple)):
            self.open_warning_window('Incorrect port selection. You need to select a different port each screen.')
            return False
        return True

    def check_if_setup_changed(self, new_screen_count, new_tv_count):
        """Returns True if either the screen count or the tv count is different then the value loaded from the config 
        parser. Returns False if they haven't changed.
        """
        try:
            old_screen_count = int(self.config['Screens']['screen_count'])
        except KeyError:
            old_screen_count = 0
        if (old_screen_count != new_screen_count) or (self.tv_count != new_tv_count):
            return True
        else:
            return False

    def set_default_button_selection(self):
        """Sets the button selection to the default selection:
        Three-screens-mode: First 6 buttons
        Two-screens-mode: All buttons
        """
        button_dict = CustomizeWindow.make_button_dict(self.screen_count, self.tv_count)
        button_count = 0
        button_list = list(BUTTON_LABEL_TUPLE)
        for label in button_dict:
            if button_count < 6:
                self.config['Customize'][label] = 'True'
                button_list.remove(label)
                button_count += 1
        for label in button_list:
            self.config['Customize'][label] = 'False'
        self.config['Customize']['button_count'] = str(button_count)

    def apply_changes_and_exit(self):
        """Saves all the settings in the config parser, writes the config parser to the conf file and closes the main 
        window. Returns True if successful, False if not.
        """
        if not self.save_all_values_in_config():
            return False
        with CONF_FILE.open('w') as conf_file:
            self.config.write(conf_file)
        self.close()
        return True

    def open_warning_window(self, warning_string):
        """Opens warning window with the given warning string.
        """
        warning_window = WarningWindow(self)
        warning_window.label_warning.setText(warning_string)
        warning_window.show()

    @staticmethod
    def rename_double_screen_types(screen_types_tuple):
        """If there are more then one tv or secondary screens, adds '_2','_3',...,_n to the related screen type names.
        Takes tuple of screen_types. Returns tuple of renamed screen types.
        """
        new_screen_types_tuple = ()
        for index, screen_type in enumerate(screen_types_tuple):
            total_count = screen_types_tuple.count(screen_type)
            counter = screen_types_tuple[:index].count(screen_type)
            new_screen_types_tuple += (
                (screen_type + '_' + str(counter + 1),) if total_count > 1 and counter > 0 else (screen_type,)
                                       )
        return new_screen_types_tuple

    def one_screen_warning(self):
        """Opens warning window, if only one screen is connected.
        """
        self.open_warning_window('You need at least two connected screens to use MultiMon.')


class CustomizeWindow(QtWidgets.QDialog):
    """Window to select the buttons to show up in MultiMon.
    """
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.setWindowTitle('Customize MultiMon')
        with open(STYLE_SHEET_DIR / 'customize.stylesheet', 'r') as style_sheet:
            self.setStyleSheet(style_sheet.read())
        self.config = config
        self.label_title = QtWidgets.QLabel()
        self.label_title.setText('Select the buttons to show up in MultiMon')
        self.label_title.setFont(FONT)
        self.vertical_layout = QtWidgets.QVBoxLayout(self)
        self.vertical_layout.setContentsMargins(10, 10, 10, 10)
        self.vertical_layout.setSpacing(20)
        self.vertical_layout.addWidget(self.label_title)
        self.button_dict = self.make_check_buttons()
        self.make_bottom_button_box()

    def make_check_buttons(self):
        """Initializes and places the selection buttons. Returns a dict with all available buttons depending on the
        setup chosen in the main settings window as values and their labels as keys.
        """
        from multi_mon import MultiMon
        grid_layout_selection = QtWidgets.QGridLayout()
        grid_layout_selection.setSpacing(20)
        screen_count = int(self.config['Screens']['screen_count'])
        tv_count = int(self.config['Screens']['tv_count'])
        type_list = [self.config['Screens'][f'type_screen_{screen_nr}']
                     for screen_nr in range(screen_count if screen_count > 2 else 3)]
        icon_width, icon_height = MultiMon.define_icon_size(screen_count, tv_count, type_list)
        name_tooltip_dict = self.make_button_dict(screen_count, tv_count)
        button_dict = {}
        icon_dir = MultiMon.get_icon_dir_name(screen_count, type_list)
        row = 0
        column = 0
        for name, tooltip in name_tooltip_dict.items():
            button = QtWidgets.QPushButton(self)
            button.setMinimumSize(QSize(300, 180))
            button.setCursor(QCursor(Qt.PointingHandCursor))
            button.setIconSize(QSize(icon_width, icon_height))
            button.setCheckable(True)
            grid_layout_selection.addWidget(button, row, column,  1, 1)
            button.setIcon(QIcon(str(icon_dir / f'{name}.svg')))
            button.setToolTip(tooltip)
            button.setChecked(self.config.getboolean('Customize', name))
            button_dict[name] = button
            column += 1
            if column == 2:
                column = 0
                row += 1
        self.vertical_layout.addLayout(grid_layout_selection)
        return button_dict

    @staticmethod
    def make_button_dict(screen_count, tv_count):
        """Returns a dictionary with the names of all possible buttons for the selected setup as keys
        and the related tooltips as values. Takes the screen count and the tv count as arguments.
        """
        tool_tips_tuple = (
            'Main monitor only', 'Extended on secondary monitor', 'Extended on TV', 'TV only',
            'Extended on all screens', 'Mirror on TV', 'Mirror on secondary monitor',
            'Secondary monitor only', 'Secondary 2 monitor only', 'Extended on secondary 2 monitor',
            'Mirror on secondary 2 monitor', 'TV 2 only', 'Extended on TV 2', 'Mirror on TV 2'
                           )
        name_tooltip_dict = {}
        if screen_count >= 3:
            exclude_tuple = ('tv', '2', 'secondary')
            for label, tooltip in zip(BUTTON_LABEL_TUPLE, tool_tips_tuple):
                if exclude_tuple[tv_count] not in label:
                    name_tooltip_dict[label] = tooltip
        else:
            include_tuple = ('secondary', 'tv')
            for label, tooltip in zip(BUTTON_LABEL_TUPLE, tool_tips_tuple):
                if 'main' in label or (include_tuple[tv_count] in label and '2' not in label):
                    name_tooltip_dict[label] = tooltip
        return name_tooltip_dict

    def make_bottom_button_box(self):
        """Creates and places the ok and cancel buttons on the bottom.
        """
        horizontal_layout = QtWidgets.QHBoxLayout()
        horizontal_layout.setSpacing(20)
        spacer_item = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        horizontal_layout.addItem(spacer_item)
        push_button_cancel = QtWidgets.QPushButton()
        push_button_cancel.setMinimumSize(QSize(60, 60))
        push_button_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        push_button_cancel.setIcon(QIcon(str(ICONS_DIR / 'exit.svg')))
        push_button_cancel.setToolTip('Cancel')
        push_button_cancel.setIconSize(QSize(40, 40))
        push_button_cancel.setProperty('bottom', True)
        horizontal_layout.addWidget(push_button_cancel)
        push_button_ok = QtWidgets.QPushButton(self)
        push_button_ok.setMinimumSize(QSize(66, 60))
        push_button_ok.setCursor(QCursor(Qt.PointingHandCursor))
        push_button_ok.setIcon(QIcon(str(ICONS_DIR / 'finish.svg')))
        push_button_ok.setToolTip('Save and exit')
        push_button_ok.setIconSize(QSize(46, 43))
        push_button_ok.setProperty('bottom', True)
        horizontal_layout.addWidget(push_button_ok)
        self.vertical_layout.addLayout(horizontal_layout)
        push_button_ok.clicked.connect(self.save_selection_and_exit)
        push_button_cancel.clicked.connect(self.close)

    def save_selection_and_exit(self):
        """Saves the button states in the config parser and closes the window.
        """
        button_count = 0
        for label in BUTTON_LABEL_TUPLE:
            if label in self.button_dict:
                self.config['Customize'][label] = str(self.button_dict[label].isChecked())
                if self.button_dict[label].isChecked():
                    button_count += 1
            else:
                self.config['Customize'][label] = 'False'
        self.config['Customize']['button_count'] = str(button_count)
        self.close()


class WarningWindow(QtWidgets.QDialog):
    """Shows up, if user tried to save the config with invalid settings.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon.fromTheme('documentinfo'))
        self.setWindowTitle('Attention')
        self.verticalLayout = QtWidgets.QVBoxLayout(self)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)
        self.verticalLayout.setSpacing(20)
        self.push_button_ok = QtWidgets.QPushButton(self)
        self.push_button_ok.setMinimumSize(QSize(110, 45))
        self.push_button_ok.setText('Ok')
        self.push_button_ok.setFont(FONT)
        self.push_button_ok.setCursor(QCursor(Qt.PointingHandCursor))
        self.label_warning = QtWidgets.QLabel(self)
        self.label_warning.setFont(FONT)
        self.verticalLayout.addWidget(self.label_warning)
        self.verticalLayout.addWidget(self.push_button_ok, 0, Qt.AlignCenter)
        self.push_button_ok.clicked.connect(self.close)
        self.setFocus()


def main():
    app = QtWidgets.QApplication(sys.argv)
    action_icon_style = ProxyStyleBiggerMenuIcons()
    app.setStyle(action_icon_style)
    settings_main = SettingsMainWindow()
    settings_main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
