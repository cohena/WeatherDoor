from sys import argv
import threading
import time
import arrow
import forecastio
from lcd_manager import display_on_lcd
import lcd_manager

HOME = (argv[1], argv[2])
API_KEY = "35c0c2e65b10c0ab13eb9f28eab70e81"

START_HOUR = 7
END_HOUR = 22


latest_forecast = None


def update_screen():
    global latest_forecast

    if not START_HOUR <= arrow.now('US/Pacific').hour < END_HOUR:
        lcd_manager.off()
        time.sleep(60)
        return

    currently = latest_forecast.currently().d
    feels_like = int(round(currently['apparentTemperature']))
    wind_speed = int(round(currently['windSpeed']))
    top_line = "Feels %s - %s mph" % (feels_like, wind_speed)

    minutely = latest_forecast.minutely()
    bottom_line = "%s" % minutely.summary

    display_on_lcd([top_line, bottom_line])
    time.sleep(15)


def update_forecast():
    global latest_forecast

    if not START_HOUR <= arrow.now('US/Pacific').hour < END_HOUR:
        return

    print "Updating forecast..."
    latest_forecast = forecastio.load_forecast(API_KEY, *HOME)


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


class APIThread(StoppableThread):
    def run(self):
        while not self._stop.is_set():
            try:
                update_forecast()
            except Exception as e:
                display_on_lcd([str(e)[0:lcd_manager.LCD_WIDTH], str(e)[lcd_manager.LCD_WIDTH:lcd_manager.LCD_WIDTH*2]])
                raise e
            time.sleep(120)


class ScreenThread(StoppableThread):
    def run(self):
        while not self._stop.is_set():
            try:
                update_screen()
            except Exception as e:
                display_on_lcd([str(e)[0:lcd_manager.LCD_WIDTH], str(e)[lcd_manager.LCD_WIDTH:lcd_manager.LCD_WIDTH*2]])
                raise e

if __name__ == "__main__":
    update_forecast()

    api_thread = APIThread()
    api_thread.daemon = True

    screen_thread = ScreenThread()
    screen_thread.daemon = True

    api_thread.start()
    screen_thread.start()

    api_thread.join()
    screen_thread.join()
