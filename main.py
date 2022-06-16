import uos
import utime
from machine import Pin, UART, SPI
import sdcard
from ili9341 import Display, color565
from micropyGPS import MicropyGPS
from xglcd_font import XglcdFont

ErrorCount = 0
TIMEZONE = -8
my_gps = MicropyGPS(TIMEZONE)
wendy = XglcdFont('fonts/Wendy7x8.c', 7, 8)
IBM = XglcdFont('fonts/IBMPlexMono12x24.c', 12, 24, letter_count=216)
LCDspi = SPI(0,
             baudrate=30000000,
             polarity=1,
             phase=1,
             bits=8,
             firstbit=SPI.MSB,
             sck=Pin(18),
             mosi=Pin(19),
             miso=Pin(16))
display = Display(LCDspi, dc=Pin(15), cs=Pin(17), rst=Pin(14))
display.clear()
# noinspection PyArgumentList
gps_module = UART(1,
                  baudrate=9600,
                  tx=Pin(4),
                  rx=Pin(5))
SDspi = SPI(1,
           baudrate=30000000,
           polarity=0,
           phase=0,
           bits=8,
           firstbit=SPI.MSB,
           sck=Pin(10),
           mosi=Pin(11),
           miso=Pin(8))
sd = sdcard.SDCard(SDspi, cs=Pin(9, Pin.OUT))
vfs = uos.VfsFat(sd)
uos.mount(vfs, "/sd")


def convert(parts):
    if parts[0] == 0:
        return None
    data = parts[0] + (parts[1] / 60.0)
    if parts[2] == 'S':
        data = -data
    if parts[2] == 'W':
        data = -data
    data = '{0:.6f}'.format(data)  # to 6 decimal places
    return str(data)


def main_loop():
    while True:
        length = gps_module.any()
        if length > 0:
            b = gps_module.read(length)
            for y in b:
                my_gps.update(chr(y))
        # _________________________________________________
        latitude = convert(my_gps.latitude)
        longitude = convert(my_gps.longitude)
        # _________________________________________________
        if latitude is None and latitude is None:
            # print('No Data')
            display.draw_text(108, 210, 'No Data...', IBM, color565(255, 0, 0),
                              landscape=True, background=color565(0, 0, 0))
            utime.sleep(4)
            display.clear()
            for y in range(5, -1, -1):
                display.draw_text(108, 240, f'Retrying in {y}...', IBM, color565(255, 0, 0),
                                  landscape=True, background=color565(0, 0, 0))
                utime.sleep(1)
                display.clear()
            continue
        # _________________________________________________
        t = my_gps.timestamp
        gpsTime = ' Time:' + '{:02d}:{:02d}:{:02}'.format(t[0], t[1], t[2])
        gpsdate = ' Date:' + my_gps.date_string('')
        speed = ' Speed:' + my_gps.speed_string('mph')
        gpshorizontal = 'Lat:' + latitude + ' Lon:' + longitude + speed + gpsTime + gpsdate
        NLat = 48.10795
        SLat = 48.10264
        WLon = -123.37720
        ELon = -123.36491
        LatP = (float(NLat) - float(latitude)) / (float(NLat) - float(SLat)) * 232
        LonP = (float(ELon) - float(longitude)) / (float(ELon) - float(WLon)) * 320
        LatR = int(float(LatP))
        LonR = int(float(LonP))
        display.fill_vrect(232, 0, 8, 320, color565(0, 0, 0))
        display.draw_text(232, 320, gpshorizontal, wendy, color565(255, 255, 255),
                          landscape=True, background=color565(0, 0, 0))
        if float(SLat) < float(latitude) < float(NLat) and float(WLon) < float(longitude) < float(ELon):
            display.draw_image('images/home.raw', 0, 0, 232, 320)
            display.fill_circle(LatR, LonR, 5, color565(255, 0, 255))
        else:
            display.draw_image('images/PA232x320.raw', 0, 0, 232, 320)
        utime.sleep(5)


while True:
    try:
        main_loop()
    except IndexError:
        TotalCount = ErrorCount + 1
        ErrorCount = TotalCount
        with open("/sd/ErrorCount.txt", "w") as file:
           file.write(f"An error has occurred {ErrorCount} times. \r\n")
        with open("/sd/ErrorCount.txt", "r") as file:
           CountReport = file.read()
           print(CountReport)
        for x in range(5, -1, -1):
            display.draw_text(108, 320, f'An Error Occurred, Retrying in {x}', IBM, color565(255, 0, 0),
                              landscape=True)
            utime.sleep(1)
            continue
