import serial


class serialApp():
    def __init__(self):
        self.tty = serial.Serial()
        self.tty.port = '/dev/ttyS1'
        self.tty.baudrate = 9600
        self.tty.timeout = 1

    def connectSerial(self):
        try:
            self.tty.open()
            print('certo')
        except:
            print('erro')

    def readSerial(self):
        read=self.tty.read(10)
        print(read.decode('utf-8'))


    def writeSerial(self, value):
        #i=0
        a = self.tty.write(value)
        print(a)
        #while(i<=10):
        #self.tty.write(b'cermob')
        self.tty.flushOutput()
        #if a != 0:
            #print("Recebido")
            #i+1"""
