"""VE.Direct message decoder"""

import logging

_LOGGER = logging.getLogger(__name__)


class Decoder:

    @classmethod
    def init(cls):
        cls._init_fields()

    @classmethod
    def decode(cls, label, value):
        if label in cls._FIELDS:
            return cls._FIELDS[label]._decode(label, value)
        return None

    def __init__(self, name, icon, unit, scaler):
        self._name = name
        self._icon = icon
        self._unit = unit
        self._scaler = scaler
        self._last_value = None

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def unit(self):
        return self._unit

    @property
    def scaler(self):
        return self._scaler

    def __repr__(self):
        return f"{self.name} [{self.unit}]"

    def _decode(self, label, value):
        if self.scaler != None:
            # scale value and convert to number
            value = float(value) * self.scaler
        if value == self._last_value:
            return
        # don't spam with spurious data
        if label in ('V', 'I') and self._last_value and abs(value-self._last_value) < 0.005:
            return
        if label in ('P', ) and self._last_value and abs(value-self._last_value) < 2:
            return
        if label in ('TTG', ) and value < 0:
            return
        self._last_value = value
        if label == 'AR': value = self._ar(value)
        if label == 'CS': value = self._cs(value)
        if label == 'ERR': value = self._err(value)
        return (value, self)

    def _ar(self, value):
        AR = {}
        AR[0b00000000000001] = 'Low Voltage'
        AR[0b00000000000010] = 'High Voltage'
        AR[0b00000000000100] = 'Low SOC'
        AR[0b00000000001000] = 'Low Starter Voltage'
        AR[0b00000000010000] = 'High Starter Voltage'
        AR[0b00000000100000] = 'Low Temperature'
        AR[0b00000001000000] = 'High Temperature'
        AR[0b00000010000000] = 'Mid Voltage'
        AR[0b00000100000000] = 'Overload'
        AR[0b00001000000000] = 'DC-ripple'
        AR[0b00010000000000] = 'Low V AC out'
        AR[0b00100000000000] = 'High V AC out'
        AR[0b01000000000000] = 'High V AC out'
        AR[0b10000000000000] = 'BMS Lockout'
        value = int(value)
        msgs = []
        for bit, msg in AR.items():
            if bit & value != 0:
                msgs.append(msg)
        value = ', '.join(msgs)
        if not value: value = "no alarm"
        return value

    def _cs(self, value):
        CS = {}
        CS[  0] = 'Off'
        CS[  1] = 'Low Power'
        CS[  2] = 'Fault'
        CS[  3] = 'Bulk'
        CS[  4] = 'Absorption'
        CS[  5] = 'Float'
        CS[  7] = 'Equalize (manual)'
        CS[  9] = 'Inverting'
        CS[245] = 'Starting-up'
        CS[247] = 'Auto equalize'
        CS[252] = 'External Control'
        return CS.get(int(value), value)

    def _err(self, value):
        ERR = {}
        ERR[  0] = 'No error'
        ERR[  2] = 'Battery voltage too high'
        ERR[ 17] = 'Charger temperature too high'
        ERR[ 18] = 'Charger over current'
        ERR[ 19] = 'Charger current reversed'
        ERR[ 20] = 'Bulk time limit exceeded'
        ERR[ 21] = 'Current sensor issue'
        ERR[ 26] = 'Terminals overheated'
        ERR[ 28] = 'Converter issue'
        ERR[ 33] = 'Input voltage too high'
        ERR[ 34] = 'Input current too high'
        ERR[ 38] = 'Input shutdown (excessive battery voltage'
        ERR[ 39] = 'Input shutdown (off mode)'
        ERR[ 65] = 'Lost communication with one of devices'
        ERR[ 66] = 'Synchronised charging device configuration issue'
        ERR[ 67] = 'BMS connection lost'
        ERR[ 68] = 'Network misconfigured'
        ERR[116] = 'Factory calibration data lost'
        ERR[117] = 'Invalid/incompatible firmware'
        ERR[119] = 'User settings invalid'
        return ERR.get(int(value), value)

    @classmethod
    def _init_fields(cls):
        cls._add('V', 'Voltage', 'mdi:current-dc', 'V', 0.001)
        cls._add('VPV', 'Panel Voltage', 'mdi:solar-panel', 'V', 0.001)
        cls._add('PPV', 'Panel Power', 'mdi:solar-power-variant', 'W')
        cls._add('I', 'Current', 'mdi:current-dc', 'A', 0.001)
        cls._add('IL', 'Load Current', 'mdi:current-dc', 'A', 0.001)
        cls._add('T', 'Temperature', 'mdi:thermometer-low', '°C')
        cls._add('P', 'Power', 'mdi:current-dc', 'W')
        cls._add('SOC', 'SOC', 'mdi:gauge', '%', 0.1)
        cls._add('TTG', 'Time to go', 'mdi:clock-outline', 'min')
        cls._add('Alarm', 'Alarm', 'mdi:alarm-light-outline')
        cls._add('AR', 'Alarm Reason', 'mdi:alarm-light-outline')
        cls._add('H2', 'Last Discharge', 'mdi:home-battery-outline', 'Ah', 0.001)
        cls._add('H3', 'Average Discharge', 'mdi:home-battery-outline', 'Ah', 0.001)
        cls._add('H19', 'Yield Total', 'mdi:home-battery', 'Wh', 0.1)
        cls._add('H20', 'Yield Today', 'mdi:home-battery', 'Wh', 0.1)
        cls._add('H22', 'Yield Yesterday', 'mdi:home-battery', 'Wh', 0.1)
        cls._add('ERR', 'Error Code', 'mdi:alarm-light-outline')
        cls._add('CS', 'State of Operation', 'mdi:state-machine')
        cls._add('PID', 'Time to go', 'mdi:identifier')
        # cls._add('H7', 'Min Battery Voltage', 'mdi:current-dc', 'V', 0.001)
        # cls._add('H8', 'Max Battery Voltage', 'mdi:current-dc', 'V', 0.001)

    @classmethod
    def _add(cls, label, name, icon, unit='', scaler=None):
        cls._FIELDS[label] = Decoder(name, icon, unit, scaler)

    # dict of all known messages
    _FIELDS = {}


