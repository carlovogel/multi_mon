# MultiMon
Tool with QT5-GUI to quickly and conveniently switch between all possible multi monitor modes on Linux using Xrandr.

## Installation:

Used packages : pyqt5

### Clone
Clone this repo to your local machine using 
    `https://github.com/carlovogel/multi_mon/`
### Setup
To quickly access MultiMon connect the following command with a preferred keyboard shortcut.
 
`python /”your_saving_directory”/multi_mon.py`

## Configuration:

Run main_settings.py to open the window shown below to configure your screen setup.
![Main setting window](/screenshots_for_readme/main_settings.png)

Select the screen type of your screens ordered from left to right in the drop down menu of the related tool button:
![Screentype menu](/screenshots_for_readme/main_settings_menu.png)

Select the port, the resolution and the refresh rate for each screen and the side of your screen where you want to show up MultiMon.
![Port menu](/screenshots_for_readme/main_settings_port.png)

Click on “Customize MultiMon” to open the window shown below to choose which buttons you want to show up in MultiMon:
![Customize window](/screenshots_for_readme/customize_window.png)

## Usage:

Open the tool by pressing a preferred shortcut or by running:

`python /”your_saving_directory”/multi_mon.py`

to show up on the left or the right edge of your current screen to select the wished mode with the mouse or the keyboard. 
![MultiMon 1](/screenshots_for_readme/multi_mon_right_1.png)

Button icons are matching the selected screen setup:
![MultiMon 2](/screenshots_for_readme/multi_mon_right_2.png)

Customizable button choice:
![MultiMon left](/screenshots_for_readme/multi_mon_left.png)

Works for two screens too:
![MultiMon two screens](/screenshots_for_readme/multi_mon_right_two_screens.png)
