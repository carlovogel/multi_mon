#!/usr/bin/env python3
# -*- coding: utf-8 -*

import sys
import subprocess
import configparser
from pathlib import Path
from PyQt5.QtGui import QIcon, QCursor
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QSize

# Xrandr flags:
PRIMARY = '--primary'
OFF = '--off'
LEFT_OF = '--left-of'
RIGHT_OF = '--right-of'
SAME_AS = '--same-as'


class MultiMon(QtWidgets.QDialog):
    """Tool to choose the multi monitor mode.
    """
    def __init__(self, parent=None):

        super().__init__(parent)
        self.config = configparser.ConfigParser()
        self.config.read(Path(__file__).parent / 'multi_mon_conf.conf')
        self.screen_count = int(self.config['Screens']['screen_count'])
        self.tv_count = int(self.config['Screens']['tv_count'])
        self.setWindowIcon(QIcon(str(Path(__file__).parent / 'icons' / 'tray_icon.svg')))
        with open(Path(__file__).parent / 'stylesheets' / 'multi_mon.stylesheet', 'r') as style_sheet_file:
            self.setStyleSheet(style_sheet_file.read())
        self.all_screens_tuple = self.load_screen_config()
        self.type_list = [screen_tuple[3] for screen_tuple in self.all_screens_tuple]
        self.screen_setup = ScreenSetup(*self.all_screens_tuple)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.push_button_transparent = QtWidgets.QPushButton()
        self.button_dict = self.make_buttons()
        current_mode = self.screen_setup.check_current_mode()
        if current_mode in self.button_dict:
            self.button_dict[current_mode].setDefault(True)
        self.connect_buttons()

    def load_screen_config(self):
        """Loads all the screen values from config parser to a tuple of tuples (port, resolution, rate, screen_type)
        for each screen ordered from left to right and returns it.
        """
        screen_tuple = ()
        for screen_nr in range(self.screen_count if self.screen_count > 2 else 3):
            if self.config['Screens'][f'port_screen_{screen_nr}']:
                screen_tuple += ((
                                     self.config['Screens'][f'port_screen_{screen_nr}'],
                                     self.config['Screens'][f'resolution_screen_{screen_nr}'],
                                     self.config['Screens'][f'rate_screen_{screen_nr}'],
                                     self.config['Screens'][f'type_screen_{screen_nr}']
                                 ),)
        return screen_tuple

    def make_buttons(self):
        """Creates and places the screen mode selection buttons and the transparent button.
        Returns dictionary {label: selection button} of all created buttons depending on
        the button settings made in 'CustomizeWindow' in settings_main.
        """
        horizontal_layout = QtWidgets.QHBoxLayout(self)
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.setSpacing(0)
        size_policy_transparent = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
                                                        )
        self.push_button_transparent.setSizePolicy(size_policy_transparent)
        self.push_button_transparent.setFocusPolicy(Qt.NoFocus)
        self.push_button_transparent.setStyleSheet("QPushButton {background-color: transparent; border: none}")

        vertical_frame = QtWidgets.QFrame()
        vertical_layout = QtWidgets.QVBoxLayout(vertical_frame)
        vertical_layout.setSpacing(8)

        button_tuple = ('main_only', 'secondary_extended', 'tv_extended', 'tv_only', 'all_extended',
                        'tv_mirror', 'secondary_mirror', 'secondary_only', 'secondary_2_only', 'secondary_2_extended',
                        'secondary_2_mirror', 'tv_2_only', 'tv_2_extended', 'tv_2_mirror'
                        )
        tool_tips_tuple = ('Main monitor only', 'Extended on secondary monitor', 'Extended on TV', 'TV only',
                           'Extended on all screens', 'Mirror on TV', 'Mirror on secondary monitor',
                           'Secondary monitor only', 'Secondary 2 monitor only', 'Extended on secondary 2 monitor',
                           'Mirror on secondary 2 monitor', 'TV 2 only', 'Extended on TV 2', 'Mirror on TV 2'
                           )
        icon_dir = self.get_icon_dir_name(self.screen_count, self.type_list)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        button_count = int(self.config['Customize']['button_count'])
        size_factor = -0.1*button_count + 1.6
        icon_width, icon_height = self.define_icon_size(self.screen_count, self.tv_count, self.type_list)
        button_dict = {}
        for index, label in enumerate(button_tuple):
            if self.config.getboolean('Customize', label):
                push_button = QtWidgets.QPushButton(vertical_frame)
                push_button.setSizePolicy(size_policy)
                push_button.setMinimumWidth(int(300*size_factor))
                push_button.setCursor(QCursor(Qt.PointingHandCursor))
                push_button.setIconSize(QSize(int(icon_width*size_factor), int(icon_height*size_factor)))
                vertical_layout.addWidget(push_button)
                push_button.setIcon(QIcon(str(icon_dir / f"{label}.svg")))
                push_button.setToolTip(tool_tips_tuple[index])
                button_dict[label] = push_button

        if self.config['Mode']['edge'] == 'right':
            vertical_layout.setContentsMargins(12, 0, 0, 0)
            horizontal_layout.addWidget(self.push_button_transparent)
            horizontal_layout.addWidget(vertical_frame)
        else:
            vertical_layout.setContentsMargins(0, 0, 12, 0)
            horizontal_layout.addWidget(vertical_frame)
            horizontal_layout.addWidget(self.push_button_transparent)

        return button_dict

    @staticmethod
    def define_icon_size(screen_count, tv_count, type_list):
        """Returns tuple of the icon width and height depending on the current monitor setup.
        """
        if screen_count >= 3:
            if tv_count == 1:
                if type_list[1] == 'tv':
                    icon_width = 242
                    icon_height = 70
                else:
                    icon_width = 231
                    icon_height = 70
            elif tv_count == 2:
                if type_list[1] == 'main':
                    icon_width = 273
                    icon_height = 70
                else:
                    icon_width = 263
                    icon_height = 70
            else:
                icon_width = 240
                icon_height = 60
        else:
            if tv_count:
                icon_width = 240
                icon_height = 100
            else:
                icon_width = 227
                icon_height = 85
        return icon_width, icon_height

    @staticmethod
    def get_icon_dir_name(screen_count, type_list):
        """Returns icon path depending on the current monitor setup.
        """
        dir_name = ''
        for screen_type in type_list:
            if screen_type:
                dir_name += screen_type.strip('_2') + '_'

        icon_dir = Path(__file__).parent / 'icons' / str(screen_count if screen_count < 4 else 3) / dir_name.strip('_')
        return icon_dir

    def connect_buttons(self):
        """Connects the buttons depending on the current monitor setup.
        """
        self.push_button_transparent.clicked.connect(self.close)
        for label in self.button_dict:
            self.button_dict[label].clicked.connect(getattr(self, f'switch_to_{label}'))

    def switch_to_main_only(self):
        """Changes current mode to main screen only.
        """
        self.screen_setup.change_to_given_mode(
            main_pos=PRIMARY, tv_pos=OFF, tv_2_pos=OFF, secondary_pos=OFF, secondary_2_pos=OFF
                                               )
        self.close()

    def switch_to_tv_only(self):
        """Changes current mode to tv only.
        """
        self.screen_setup.change_to_given_mode(
            main_pos=OFF, tv_pos=PRIMARY, tv_2_pos=OFF, secondary_pos=OFF, secondary_2_pos=OFF
                                               )
        self.close()

    def switch_to_tv_2_only(self):
        """Changes current mode to tv_2 only.
        """
        self.screen_setup.change_to_given_mode(
            main_pos=OFF, tv_pos=OFF, tv_2_pos=PRIMARY, secondary_pos=OFF, secondary_2_pos=OFF
                                               )
        self.close()

    def switch_to_secondary_only(self):
        """Changes current mode to secondary only.
        """
        self.screen_setup.change_to_given_mode(
            main_pos=OFF, tv_pos=OFF, tv_2_pos=OFF, secondary_pos=PRIMARY, secondary_2_pos=OFF
                                               )
        self.close()

    def switch_to_secondary_2_only(self):
        """Changes current mode to secondary_2 only.
        """
        self.screen_setup.change_to_given_mode(
            main_pos=OFF, tv_pos=OFF, tv_2_pos=OFF, secondary_pos=OFF, secondary_2_pos=PRIMARY
                                               )
        self.close()

    def switch_to_secondary_extended(self):
        """Changes current mode to main screen extended to secondary screen.
        """
        if self.type_list.index('main') < self.type_list.index('secondary'):
            self.screen_setup.change_to_given_mode(
                    main_pos=PRIMARY, tv_pos=OFF, tv_2_pos=OFF, secondary_pos=(RIGHT_OF, 'main'), secondary_2_pos=OFF
                                                   )
        else:
            self.screen_setup.change_to_given_mode(
                    main_pos=PRIMARY, tv_pos=OFF, tv_2_pos=OFF, secondary_pos=(LEFT_OF, 'main'), secondary_2_pos=OFF
                                                   )
        self.close()

    def switch_to_tv_extended(self):
        """Changes current mode to main screen extended to tv.
        """
        if self.type_list.index('main') < self.type_list.index('tv'):
            self.screen_setup.change_to_given_mode(
                    main_pos=PRIMARY, tv_pos=(RIGHT_OF, 'main'), tv_2_pos=OFF, secondary_pos=OFF, secondary_2_pos=OFF
                                                   )
        else:
            self.screen_setup.change_to_given_mode(
                    main_pos=PRIMARY, tv_pos=(LEFT_OF, 'main'), tv_2_pos=OFF, secondary_pos=OFF, secondary_2_pos=OFF
                                                   )
        self.close()

    def switch_to_secondary_2_extended(self):
        """Changes current mode to main screen extended to secondary_2 screen.
        """
        if self.type_list.index('main') < self.type_list.index('secondary_2'):
            self.screen_setup.change_to_given_mode(
                    main_pos=PRIMARY, tv_pos=OFF, tv_2_pos=OFF, secondary_pos=OFF, secondary_2_pos=(RIGHT_OF, 'main')
                                                   )
        else:
            self.screen_setup.change_to_given_mode(
                    main_pos=PRIMARY, tv_pos=OFF, tv_2_pos=OFF, secondary_pos=OFF, secondary_2_pos=(LEFT_OF, 'main')
                                                   )
        self.close()

    def switch_to_tv_2_extended(self):
        """Changes current mode to main screen extended to tv_2.
        """
        if self.type_list.index('main') < self.type_list.index('tv_2'):
            self.screen_setup.change_to_given_mode(
                    main_pos=PRIMARY, tv_pos=OFF, tv_2_pos=(RIGHT_OF, 'main'), secondary_pos=OFF, secondary_2_pos=OFF
                                                   )
        else:
            self.screen_setup.change_to_given_mode(
                    main_pos=PRIMARY, tv_pos=OFF, tv_2_pos=(LEFT_OF, 'main'), secondary_pos=OFF, secondary_2_pos=OFF
                                                   )
        self.close()

    def switch_to_tv_mirror(self):
        """Changes current mode to main screen mirrored to tv.
        """
        self.screen_setup.change_to_given_mode(
            main_pos=PRIMARY, tv_pos=(SAME_AS, 'main'), tv_2_pos=OFF, secondary_pos=OFF, secondary_2_pos=OFF
                                               )
        self.close()

    def switch_to_secondary_mirror(self):
        """Changes current mode to main screen mirrored to the secondary screen.
        """
        self.screen_setup.change_to_given_mode(
            main_pos=PRIMARY, tv_pos=OFF, tv_2_pos=OFF, secondary_pos=(SAME_AS, 'main'), secondary_2_pos=OFF
                                               )
        self.close()

    def switch_to_tv_2_mirror(self):
        """Changes current mode to main screen mirrored to tv_2.
        """
        self.screen_setup.change_to_given_mode(
            main_pos=PRIMARY, tv_pos=OFF, tv_2_pos=(SAME_AS, 'main'), secondary_pos=OFF, secondary_2_pos=OFF
                                               )
        self.close()

    def switch_to_secondary_2_mirror(self):
        """Changes current mode to main screen mirrored to the secondary_2 screen.
        """
        self.screen_setup.change_to_given_mode(
            main_pos=PRIMARY, tv_pos=OFF, tv_2_pos=OFF, secondary_pos=OFF, secondary_2_pos=(SAME_AS, 'main'),
                                               )
        self.close()

    def switch_to_all_extended(self):
        """Changes current mode to main screen extended to all screens.
        """
        if self.screen_count >= 3:
            if self.type_list[0] == 'main':
                self.screen_setup.change_to_given_mode(PRIMARY, (RIGHT_OF, 0), (RIGHT_OF, 1))
            if self.type_list[1] == 'main':
                self.screen_setup.change_to_given_mode((LEFT_OF, 1), PRIMARY, (RIGHT_OF, 1))
            if self.type_list[2] == 'main':
                self.screen_setup.change_to_given_mode((LEFT_OF, 1), (LEFT_OF, 2), PRIMARY)
        self.close()


class ScreenSetup(object):
    """The multi screen setup, with port, resolution, rate and type of each screen. Takes the tuples
    (port, resolution, rate, screen type) for every screen of the setup ordered from left to right.
    """
    def __init__(self, *tuples_all_screens):
        self.tuples_all_screens = tuples_all_screens

    def check_current_mode(self):
        """Returns a string containing the current monitor mode.
        """
        desktop_width = QtWidgets.QDesktopWidget().width()
        list_active_screens = QtWidgets.QApplication.screens()
        active_screen_count = len(list_active_screens)
        tuple_active_screens_ports = tuple(screen.name() for screen in list_active_screens)
        total_width_screens = 0
        for screen in list_active_screens:
            total_width_screens += screen.geometry().width()

        for screen_type in ('main', 'secondary', 'tv', 'secondary_2', 'tv_2'):
            if active_screen_count == 1:
                if tuple_active_screens_ports[0] == self.get_port_for_given_type(screen_type):
                    return f'{screen_type}_only'

            if active_screen_count == 2:
                if tuple_active_screens_ports[0] == self.get_port_for_given_type('main'):
                    if tuple_active_screens_ports[1] == self.get_port_for_given_type(screen_type):
                        if desktop_width == total_width_screens:
                            return f'{screen_type}_extended'
                        if desktop_width == QtWidgets.QDesktopWidget().screenGeometry().width():
                            return f'{screen_type}_mirror'

            if active_screen_count == 3 and desktop_width == total_width_screens:
                return 'all_extended'

    @staticmethod
    def get_part_of_command_for_given_monitor(mode, port, resolution, rate):
        """Returns the part of a xrandr command list for the given monitor with given parameters.
        """
        if type(mode) is str:
            mode = (mode,)
        screen_cmd_tuple = ('--output', port, *mode)

        if mode[0] is not OFF:
            screen_cmd_tuple += ('--mode', resolution, '--rate', rate)
        return screen_cmd_tuple

    def get_full_command_for_given_mode(self, *args_mode, **kwargs_mode_screen_type):
        """Returns the full Xrandr command list to change into the given mode. Takes the wished mode
        of each screen either as positional arguments ordered from the left screen to the right screen or as keyword
        arguments for the related screen type.
        kwargs: main_pos, secondary_pos, secondary_2_pos, tv_pos, tv_2_pos.
        Possible modes: '--off',
                        '--primary',
                        ('--left-of', relative_screen),
                        ('--right-of', relative_screen),
                        ('--same-as', relative_screen)
        The relative screen is given by a string containing the port.
        """
        command = ('xrandr',)
        # if called with the related screen types as keyword arguments:
        #
        if kwargs_mode_screen_type:
            for tuple_screen in self.tuples_all_screens:
                # check if one of the connected screens has the called screen type:
                #
                if (tuple_screen[3] + '_pos') in kwargs_mode_screen_type:
                    command += self.get_part_of_command_for_given_monitor(
                        kwargs_mode_screen_type[tuple_screen[3] + '_pos'], *tuple_screen[:3]
                                                                          )
        # if called with positional arguments ordered from left to right:
        #
        else:
            for mode, tuple_screen in zip(args_mode, self.tuples_all_screens):
                command += self.get_part_of_command_for_given_monitor(mode, *tuple_screen[:3])
        return command

    def change_to_given_mode(self, *args_mode, **kwargs_mode_screen_type):
        """Changes the current monitor setup to the new monitor setup with xrandr. Takes the wished mode
        of each screen either as positional arguments ordered from the left screen to the right screen or as keyword
        arguments for the related screen type.
        Returns True if successful. Returns False and prints Xrandr output, if errors appeared.
        kwargs: main_pos, secondary_pos, secondary_2_pos, tv_pos, tv_2_pos.
        Possible values: '--off',
                        '--primary',
                        ('--left-of', relative_screen),
                        (--right-of, relative_screen),
                        (--same-as, relative_screen)
        The relative screen is defined by the port or screen type (or screen nr if called with positional arguments).
        """
        if args_mode:
            args_mode = self.allow_call_by_type_or_nr_args(*args_mode)
        if kwargs_mode_screen_type:
            kwargs_mode_screen_type = self.allow_call_by_type_kwargs(**kwargs_mode_screen_type)

        command = self.get_full_command_for_given_mode(*args_mode, **kwargs_mode_screen_type)
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
            log_xrandr = proc.stdout.readlines()
        if log_xrandr:
            print(log_xrandr)
            return False
        return True

    def allow_call_by_type_or_nr_args(self, *args_mode):
        """Adds the possibility to define the relative screen of the modes (left_of, right_of, same_as) by the related
        screen type or the screen nr instead of the ports when the method change_to_given_mode is called with positional
        arguments. Takes a tuple of 'mode' commands with possible port, screen type or screen nr as relative screen.
        Returns tuple with the port as the relative screen. For example: ('--left-of', '1') --> ('--left-of', 'DP-0')
        """
        new_args_mode = ()
        for mode in args_mode:
            if type(mode) is tuple:
                if mode[1] in self.get_connected_screen_types():
                    new_args_mode += ((mode[0], self.get_port_for_given_type(mode[1])),)
                elif type(mode[1]) is int:
                    new_args_mode += ((mode[0], self.tuples_all_screens[mode[1]][0]),)
                else:
                    new_args_mode += (mode, )
            else:
                new_args_mode += (mode, )
        return new_args_mode

    def allow_call_by_type_kwargs(self, **kwargs_mode):
        """Adds the possibility to define the relative screen of the modes (left_of, right_of, same_as) by the related
        screen type instead of the port when the method change_to_given_mode is called with keyword arguments
        (by screen type). Takes a tuple of 'mode' commands with possible port or screen type as relative screen.
        Returns tuple with the port as the relative screen. For example: ('--left-of', 'main') --> ('--left-of', 'DP-0')
        """
        for mode_label, mode_arg in kwargs_mode.items():
            if (type(mode_arg) is tuple) and (mode_arg[1] in self.get_connected_screen_types()):
                kwargs_mode[mode_label] = (mode_arg[0], self.get_port_for_given_type(mode_arg[1]))
        return kwargs_mode

    def get_connected_screen_types(self):
        """Returns a tuple of the screen types of all connected screens loaded from the conf file.
        """
        return (screen_tuples[3] for screen_tuples in self.tuples_all_screens)

    def get_port_for_given_type(self, screen_type):
        """Returns the port for the screen with the given screen type loaded from the conf file.
        """
        for tuple_screen in self.tuples_all_screens:
            if screen_type in tuple_screen:
                return tuple_screen[0]
        return None


def main():
    app = QtWidgets.QApplication(sys.argv)
    tool = MultiMon()
    tool.showFullScreen()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
