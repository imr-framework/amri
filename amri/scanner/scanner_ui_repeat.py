if __name__ == '__main__':
    import sys
    from pathlib import Path

    SEARCH_PATH = Path(__file__).parent.parent.parent
    sys.path.insert(0, SEARCH_PATH)

import os
import subprocess
import time

import pyautogui

from amri.utils.log_utils import log

PROTOCOL_PYAUTOGUI_PATH = os.path.join(os.path.dirname(__file__), 'pyautogui_assets', 'protocol')
TWIX_PYAUTOGUI_PATH = os.path.join(os.path.dirname(__file__), 'pyautogui_assets', 'twix')


def __repeat_protocol(pulseq_left, pulseq_top):
    log('Initiating next automated scan...')
    pyautogui.rightClick(pulseq_left, pulseq_top)
    pyautogui.click(125, 260)


def __copy_file_via_twix():
    """Copy acquired raw data to C:/TEMP via Twix."""
    log('Copying relevant acquired file to local via Twix...')
    # Launch Twix from command line and wait for it to open
    subprocess.Popen(['twix'])
    time.sleep(1.5)

    # Select first (most recent) file to copy
    left, top = pyautogui.locateCenterOnScreen(TWIX_PYAUTOGUI_PATH + '/twix_pulseq.PNG')
    pyautogui.rightClick(left, top + 20)
    pyautogui.click(left + 20, top + 30)

    # Confirm 'TEMP' folder as destination
    time.sleep(0.5)
    left, top = pyautogui.locateCenterOnScreen(TWIX_PYAUTOGUI_PATH + '/twix_confirm_copy.PNG')
    pyautogui.click(left, top)
    time.sleep(5)


def __close_twix():
    pyautogui.press('alt')
    pyautogui.press('f')
    pyautogui.press('x')


def main(seq_scan_time, pulseq_left, pulseq_top):
    pyautogui.PAUSE = 0.5

    # Repeat protocol and wait for it to complete execution
    __repeat_protocol(pulseq_left, pulseq_top)
    time.sleep(seq_scan_time)

    # Copy raw data via Twix to local and cloud, and close Twix
    __copy_file_via_twix()
    __close_twix()
