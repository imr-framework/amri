if __name__ == '__main__':
    import sys
    from pathlib import Path

    SEARCH_PATH = Path(__file__).parent.parent.parent
    sys.path.insert(0, SEARCH_PATH)

import os
import time

import pyautogui

SELFADMIN_PYAUTOGUI_PATH = os.path.join(os.path.dirname(__file__), 'pyautogui_assets', 'selfadmin')


def enter():
    # Open patient table console
    left, top = pyautogui.locateCenterOnScreen(SELFADMIN_PYAUTOGUI_PATH + '/selfadmin_console.PNG')
    pyautogui.click(left, top)

    # Take in the patient table
    left, top = pyautogui.locateCenterOnScreen(SELFADMIN_PYAUTOGUI_PATH + '/selfadmin_center.PNG')
    pyautogui.click(left, top)

    time.sleep(4)

    # Close patient table console
    pyautogui.hotkey('alt', 'f4')


def quit():
    # Open patient table console
    left, top = pyautogui.locateCenterOnScreen(SELFADMIN_PYAUTOGUI_PATH + '/selfadmin_console.PNG')
    pyautogui.click(left, top)

    # Bring out the patient table
    left, top = pyautogui.locateCenterOnScreen(SELFADMIN_PYAUTOGUI_PATH + '/selfadmin_home.PNG')
    pyautogui.click(left, top)

    time.sleep(4)

    # Close patient table console
    pyautogui.hotkey('alt', 'f4')
