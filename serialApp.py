import serial
import Adafruit_BBIO.GPIO as GPIO

class serialApp():
    def __init__(self):
        self.tty=serial.Serial('/dev/ttyS1', 115200, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=3)
        GPIO.setup("P8_8", GPIO.OUT)

    def connectSerial(self):
        try:
            self.tty.open()
            print('certo')
        except:
            print('erro')


    def readSerial(self):
        GPIO.output("P8_8", GPIO.LOW)
        read=self.tty.readline()
        self.tty.flush()
        print(read)


    def writeSerial(self):
        GPIO.output("P8_8", GPIO.HIGH) 
        hash_read = [0x3a, 0x12, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0xff, 0xff, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x3b]
        a = self.tty.write(bytearray(hash_read))
        self.tty.flush()
        print("Enviado!")

    def close(self):
        self.tty.close()
