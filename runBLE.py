import logging
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import subprocess
import serial
import Adafruit_BBIO.GPIO as GPIO
import os
import time
from configBLE import (
    Advertisement,
    Characteristic,
    Service,
    Application,
    find_adapter,
    Descriptor,
    Agent
)
import struct
import requests
import array
from enum import Enum
import sys
import time

MainLoop = None
"""try:
    from gi.repository import GLib

    MainLoop = GLib.MainLoop
except ImportError:
    import gobject as GObject

    MainLoop = GObject.MainLoop"""

try:
  from gi.repository import GObject
except ImportError:
  import gobject as GObject

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logHandler = logging.StreamHandler()
filelogHandler = logging.FileHandler("logs.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logHandler.setFormatter(formatter)
filelogHandler.setFormatter(formatter)
logger.addHandler(filelogHandler)
logger.addHandler(logHandler)

mainloop = None

BLUEZ_SERVICE_NAME = "org.bluez"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'

class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.freedesktop.DBus.Error.InvalidArgs"
class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotSupported"
class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.NotPermitted"
class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.InvalidValueLength"
class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = "org.bluez.Error.Failed"
def register_app_cb():
    logger.info("GATT application registered")
def register_app_error_cb(error):
    logger.critical("Failed to register application: " + str(error))
    mainloop.quit()

vetor = []
a = [0x3a, 0x12, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0xff, 0xff, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x3b]
GPIO.setup("P8_8", GPIO.OUT)
GPIO.output("P8_8", GPIO.HIGH)
ser=serial.Serial('/dev/ttyS1',115200,bytesize=serial.EIGHTBITS,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE, timeout=3)

class TestService(Service):
    TEST_SVC_UUID = '12345678-1234-5678-1234-56789abcdef0'

    def __init__(self, bus, index):
        Service.__init__(self, bus, index, self.TEST_SVC_UUID, True)
        self.add_characteristic(TestCharacteristic(bus, 0, self))

class TestCharacteristic(Characteristic):
    TEST_CHRC_UUID = '12345678-1234-5678-1234-56789abcdef1'

    def __init__(self, bus, index, service):
        Characteristic.__init__(
                self, bus, index,
                self.TEST_CHRC_UUID,
                ['read', 'write', 'notify'],
                service)
        self.value = []
        array_de_byte = []
        self.notifying = False
        #GObject.timeout_add(1000, self.notify(options=None))

    def notify_battery_level(self):
        if not self.notifying:
            return
        array_de_byte = dbus.Array(self.value, signature=dbus.Signature('y'))
        print(array_de_byte)
        packet_size = 512  # Tamanho máximo do pacote
        packets = [array_de_byte[i:i + packet_size] for i in range(0, len(array_de_byte), packet_size)]
        print(len(packets))
        for i, packet in enumerate(packets):
            self.value = []
            packet_data = bytes(packet)
            print(packet_data)
            self.value = packet_data
            a = dbus.Array(self.value, signature=dbus.Signature('y'))
            self.PropertiesChanged(
                    GATT_CHRC_IFACE,
                    { 'Value': a }, [])
            time.sleep(5)


    def ReadValue(self, options):

        return self.value

    def WriteValue(self, value, options):
        print(value)
        self.value = value

        bytes_value = bytes(self.value)
        string_value = bytes_value.decode('utf-8')
        if string_value == 'get':
            print(string_value)
            c=ser.write(bytearray(a))
            ser.flush()
            print("Enviado")
            GPIO.output("P8_8", GPIO.LOW)
            read=ser.readline()
            ser.flush()
            print("Recebido")
            GPIO.output("P8_8", GPIO.HIGH)
            print(read)
            self.value = read
            """array_de_byte = dbus.Array(read, signature=dbus.Signature('y'))
            packet_size = 512  # Tamanho máximo do pacote
            packets = [array_de_byte[i:i + packet_size] for i in range(0, len(array_de_byte), packet_size)]
            print(len(packets))
            for i, packet in enumerate(packets):
                self.value = []
                packet_data = bytes(packet)
                print(packet_data)
                self.value = packet_data"""

    def StartNotify(self):
        if self.notifying:
            print('Already notifying, nothing to do')
            return

        self.notifying = True
        self.notify_battery_level()

    def StopNotify(self):
        if not self.notifying:
            print('Not notifying, nothing to do')
            return

        self.notifying = False


class TestAdvertisement(Advertisement):
    def __init__(self, bus, index):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid('180D')
        self.add_service_uuid('180F')
        #self.add_service_uuid(TestService.TEST_SVC_UUID)
        #self.add_manufacturer_data(0xffff, [ 0x01, 0x02, 0x03])
        #self.add_service_data('9999', [0x00, 0x01, 0x02, 0x03, 0x04])
        self.include_tx_power = True
        #self.add_data(0x26, [0x01, 0x01, 0x00])


def register_ad_cb():
    print ('Advertisement registered')

def register_ad_error_cb(error):
    print ('Failed to register advertisement: ' + str(error))
    mainloop.quit()

def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if LE_ADVERTISING_MANAGER_IFACE in props:
            return o

    return None

AGENT_PATH = "/com/punchthrough/agent"

def main():
    global mainloop    
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = find_adapter(bus)

    if not adapter:
        logger.critical("GattManager1 interface not found")
        return

    adapter_obj = bus.get_object(BLUEZ_SERVICE_NAME, adapter)

    adapter_props = dbus.Interface(adapter_obj, "org.freedesktop.DBus.Properties")

    # powered property on the controller to on
    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

    # Get manager objs
    service_manager = dbus.Interface(adapter_obj, GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(adapter_obj, LE_ADVERTISING_MANAGER_IFACE)
    ler = dbus.Interface(adapter_obj, GATT_CHRC_IFACE)
    advertisement = TestAdvertisement(bus, 1)
    obj = bus.get_object(BLUEZ_SERVICE_NAME, "/org/bluez")
    
    device_interface = dbus.Interface(adapter_obj, 'org.bluez.GattManager1')
    agent = Agent(bus, AGENT_PATH)

    app = Application(bus)
    app.add_service(TestService(bus, 2))

    mainloop =GObject.MainLoop()
   
    agent_manager = dbus.Interface(obj, "org.bluez.AgentManager1")
    #agent_manager.RegisterAgent(AGENT_PATH, "DisplayYesNo")
    agent_manager.RegisterAgent(AGENT_PATH, "NoInputNoOutput")
    ad_manager.RegisterAdvertisement(
        advertisement.get_path(),
        {},
        reply_handler=register_ad_cb,
        error_handler=register_ad_error_cb,
    )

    logger.info("Registering GATT application...")

    service_manager.RegisterApplication(
        app.get_path(),
        {},
        reply_handler=register_app_cb,
        error_handler=[register_app_error_cb],
    )

    mainloop.run()
    
if __name__ == "__main__":
    os.system('sudo systemctl restart bluetooth')
    main()

