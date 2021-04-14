import time

# Registers definitions
FREQ_STEPS = 10
RADIO_REG_CHIPID = 0x00

RADIO_REG_CTRL = 0x02
RADIO_REG_CTRL_OUTPUT = 0x8000
RADIO_REG_CTRL_UNMUTE = 0x4000
RADIO_REG_CTRL_MONO = 0x2000
RADIO_REG_CTRL_BASS = 0x1000
RADIO_REG_CTRL_SEEKUP = 0x0200
RADIO_REG_CTRL_SEEK = 0x0100
RADIO_REG_CTRL_RDS = 0x0008
RADIO_REG_CTRL_NEW = 0x0004
RADIO_REG_CTRL_RESET = 0x0002
RADIO_REG_CTRL_ENABLE = 0x0001

RADIO_REG_CHAN = 0x03
RADIO_REG_CHAN_SPACE = 0x0003
RADIO_REG_CHAN_SPACE_100 = 0x0000
RADIO_REG_CHAN_BAND = 0x000C
RADIO_REG_CHAN_BAND_FM = 0x0000
RADIO_REG_CHAN_BAND_FMWORLD = 0x0008
RADIO_REG_CHAN_TUNE = 0x0010
RADIO_REG_CHAN_NR = 0x7FC0

RADIO_REG_R4 = 0x04
RADIO_REG_R4_EM50 = 0x0800
RADIO_REG_R4_SOFTMUTE = 0x0200
RADIO_REG_R4_AFC = 0x0100

RADIO_REG_VOL = 0x05
RADIO_REG_VOL_VOL = 0x000F

RADIO_REG_RA = 0x0A
RADIO_REG_RA_RDS = 0x8000
RADIO_REG_RA_RDSBLOCK = 0x0800
RADIO_REG_RA_STEREO = 0x0400
RADIO_REG_RA_NR = 0x03FF
RADIO_REG_RA_STC = 0x4000
RADIO_REG_RA_SF = 0x2000

RADIO_REG_RB = 0x0B
RADIO_REG_RB_FMTRUE = 0x0100
RADIO_REG_RB_FMREADY = 0x0080

# Radio class definition
class Radio:
    """
    A class for communicating with the rda5807m chip

    ...

    Attributes
    ----------
    registers : list
        virtual registers
    address : int
        chip's address
    maxvolume : int
        maximum volume
    freqLow, freqHigh, freqSteps : int
        min and max frequency for FM band, and frequency steps
    board : busio.i2c object
        used for i2c communication
    frequency : int
        current chip frequency
    volume : int
        current chip volume
    bassBoost : boolean
        toggle bass boost on the chip
    mute : boolean
        toggle mute/unmute
    softMute : boolean
        toggle soft mute (mute if signal strength too low)
    mono : boolean
        toggle stereo mode
    rds : boolean
        toggle rds
    tuned : boolean
        is chip tuned
    band : string
        selected band (FM or FMWORLD)
    """

    # Initialize virtual registers
    registers = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    # Chip constants
    I2C_SEQ = 0x10
    I2C_REG = 0x11
    maxvolume = 15

    # FMWORLD Band
    freqLow = 8700
    freqHigh = 10800
    freqSteps = 10

    # Set default frequency and volume
    def __init__(self, i2c, frequency=10000, volume=1):
        self.i2c = i2c
        self.frequency = frequency

        # Basic audio info
        self.volume = volume
        self.bassBoost = False
        self.mute = False
        self.softMute = False

        # Radio features from the chip
        self.mono = False
        self.rds = False
        self.tuned = False

        # Band - Default FMWORLD
        # 1. FM
        # 2. FMWORLD
        self.band = "FMWORLD"

        # Functions saves register values to virtual registers, sets the basic frequency and volume
        self.setup()
        print("Got to point 1!")
        self.tune()  # Apply volume and frequency

    def setup(self):
        # Initialize registers
        self.registers[RADIO_REG_CHIPID] = 0x58
        self.registers[RADIO_REG_CTRL] = (RADIO_REG_CTRL_RESET | RADIO_REG_CTRL_ENABLE) | (
                RADIO_REG_CTRL_UNMUTE | RADIO_REG_CTRL_OUTPUT)
        # self.registers[RADIO_REG_R4] = RADIO_REG_R4_EM50
        # Initialized to volume - 6 by default
        self.registers[RADIO_REG_VOL] = 0x84D1
        # Other registers are already set to zero
        # Update registers
        self.saveRegister(RADIO_REG_CTRL)
        self.saveRegister(RADIO_REG_VOL)

        self.registers[
            RADIO_REG_CTRL] = RADIO_REG_CTRL_ENABLE | RADIO_REG_CTRL_NEW | RADIO_REG_CTRL_RDS | RADIO_REG_CTRL_UNMUTE | RADIO_REG_CTRL_OUTPUT
        self.saveRegister(RADIO_REG_CTRL)

        # Turn on bass boost and rds
        self.setBassBoost(True)

        self.rds = True
        self.mute = False

    def tune(self):
        # Tunes radio to current frequency and volume
        self.setFreq(self.frequency)
        self.setVolume(self.volume)
        self.tuned = True

    def setFreq(self, freq):
        # Sets frequency to freq
        if freq < self.freqLow:
            freq = self.freqLow
        elif freq > self.freqHigh:
            freq = self.freqHigh
        self.frequency = freq
        newChannel = (freq - self.freqLow) // 10

        regChannel = RADIO_REG_CHAN_TUNE  # Enable tuning
        regChannel = regChannel | (newChannel << 6)

        # Enable output, unmute
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | (
                RADIO_REG_CTRL_OUTPUT | RADIO_REG_CTRL_UNMUTE | RADIO_REG_CTRL_RDS | RADIO_REG_CTRL_ENABLE)
        self.saveRegister(RADIO_REG_CTRL)

        # Save frequency to register
        self.registers[RADIO_REG_CHAN] = regChannel
        self.saveRegister(RADIO_REG_CHAN)
        time.sleep(0.2)

        # Adjust volume
        self.saveRegister(RADIO_REG_VOL)
        time.sleep(0.3)

        # Get frequnecy
        self.getFreq()


    def getFreq(self):
        # Read register RA
        #self.writeBytes(bytes([RADIO_REG_RA]))
        self.registers[RADIO_REG_RA] = self.read16()

        ch = self.registers[RADIO_REG_RA] & RADIO_REG_RA_NR

        self.frequency = self.freqLow + ch * 10
        return self.frequency

    def formatFreq(self):
        # Formats the current frequency for better readabilitiy
        freq = self.frequency

        s = str(freq)
        s = list(s)
        last_two = s[-2:]
        s[-2] = "."
        s[-1] = last_two[0]
        s.append(last_two[1])
        return ("".join(s)) + " Mhz"

    def setBand(self, band):
        # Changes bands to FM or FMWORLD
        self.band = band
        if band == "FM":
            r = RADIO_REG_CHAN_BAND_FM
        else:
            r = RADIO_REG_CHAN_BAND_FMWORLD
        self.registers[RADIO_REG_CHAN] = (r | RADIO_REG_CHAN_SPACE_100)
        self.saveRegister(RADIO_REG_CHAN)

    def term(self):
        # Terminates all receiver functions
        self.setVolume(0)
        self.registers[RADIO_REG_CTRL] = 0x0000
        self.saveRegisters

    def setBassBoost(self, switchOn):
        # Switches bass boost to true or false
        self.bassBoost = switchOn
        regCtrl = self.registers[RADIO_REG_CTRL]
        if switchOn:
            regCtrl = regCtrl | RADIO_REG_CTRL_BASS
        else:
            regCtrl = regCtrl & (~RADIO_REG_CTRL_BASS)
        self.registers[RADIO_REG_CTRL] = regCtrl
        self.saveRegister(RADIO_REG_CTRL)

    def setMono(self, switchOn):
        # Switches mono to 0 or 1
        self.mono = switchOn
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_SEEK)
        if switchOn:
            self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_MONO
        else:
            self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_MONO)
        self.saveRegister(RADIO_REG_CTRL)

    def setMute(self, switchOn):
        # Switches mute off or on
        self.mute = switchOn
        if (switchOn):
            self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_UNMUTE)
        else:
            self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_UNMUTE
        self.saveRegister(RADIO_REG_CTRL)

    def setSoftMute(self, switchOn):
        # Switches soft mute off or on
        self.softMute = switchOn
        if switchOn:
            self.registers[RADIO_REG_R4] = self.registers[RADIO_REG_R4] | RADIO_REG_R4_SOFTMUTE
        else:
            self.registers[RADIO_REG_R4] = self.registers[RADIO_REG_R4] & (~RADIO_REG_R4_SOFTMUTE)
        self.saveRegister(RADIO_REG_R4)

    def softReset(self):
        # Soft reset chip
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_RESET
        self.saveRegister(RADIO_REG_CTRL)
        time.sleep(2)
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_RESET)
        self.saveRegister(RADIO_REG_CTRL)

    def seekUp(self):
        # Start seek mode upwards
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_SEEKUP
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_SEEK
        self.saveRegister(RADIO_REG_CTRL)

        # Wait until scan is over
        time.sleep(1)
        self.getFreq()
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_SEEK)
        self.saveRegister(RADIO_REG_CTRL)

    def seekDown(self):
        # Start seek mode downwards
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_SEEKUP)
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] | RADIO_REG_CTRL_SEEK
        self.saveRegister(RADIO_REG_CTRL)

        # Wait until scan is over
        time.sleep(1)
        self.getFreq()
        self.registers[RADIO_REG_CTRL] = self.registers[RADIO_REG_CTRL] & (~RADIO_REG_CTRL_SEEK)
        self.saveRegister(RADIO_REG_CTRL)

    def setVolume(self, volume):
        # Sets the volume
        if (volume > self.maxvolume):
            volume = self.maxvolume
        self.volume = volume
        self.registers[RADIO_REG_VOL] = self.registers[RADIO_REG_VOL] & (~RADIO_REG_VOL_VOL)
        self.registers[RADIO_REG_VOL] = self.registers[RADIO_REG_VOL] | volume
        self.saveRegister(RADIO_REG_VOL)


    def getRssi(self):
        # Get the current signal strength
        #self.writeBytes(bytes([RADIO_REG_RB]))
        self.registers[RADIO_REG_RB]=self.readRegisters(0xb)
        self.rssi = self.registers[RADIO_REG_RB] >> 10
        return self.rssi

    def getRadioInfo(self):
        # Reads info from chip and saves it into virtual memory
        self.readRegisters()
        if self.registers[RADIO_REG_RA] & RADIO_REG_RA_RDS:
            self.rds = True
        self.rssi = self.registers[RADIO_REG_RB] >> 10
        if self.registers[RADIO_REG_RB] & RADIO_REG_RB_FMTRUE:
            self.tuned = True
        if self.registers[RADIO_REG_CTRL] & RADIO_REG_CTRL_MONO:
            self.mono = True

    def saveRegister(self, regN):
        # Write register from memory to receiver
        regVal=bytearray(2)
        regVal1 = self.registers[regN]  # 16 bit value in list
        regVal[0] = regVal1 >> 8
        regVal[1] = regVal1 & 255
        #write to i2c address with particular register and value 
        self.i2c.writeto_mem(self.I2C_REG, regN,regVal)


    def saveRegisters(self):
        #save data into register 2 to 7
        for i in range(2, 7):
            self.saveRegister(i)
        

    def read16(self):
        # Reads two bytes, returns as one 16 bit integer
        result = bytearray(4)
        self.i2c.readfrom_into(self.I2C_SEQ, result)
        return result[0] * 256 + result[1]

    def readRegisters(self,reg):
        #redfrom_mem_into  reg,memadd,buffer
        result = bytearray(2)
        self.i2c.readfrom_mem_into(self.I2C_REG , reg,result)
        return result[0] * 256 + result[1]
