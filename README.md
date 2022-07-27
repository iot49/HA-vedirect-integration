# Victron VE.Direct Integration

Many Victron devices (e.g. SmartShunt and MPPT solar chargers) output status information over a VE.Direct bus (really just a TTL UART operating at 19200 baud).

This integration makes this information available to Home Assistant. The VE.Direct device can be connected either wired or wireless via an HM-18 Bluetooth module. I am using an HM-19 from DSD TECH purchased from Amazon. Other modules may work also.

## Configuration

Add the following to your `configuration.yaml` file:

```
# Example configuration.yaml entry
sensor vedirect:
  - platform: vedirect
    port: /dev/ttyUSB0
    name: Solar
```

## Configuration Variables

**port** string <br />
Serial port (e.g. `/dev/ttyUSB0`) or BLE MAC address (e.g. `A0:2C:65:CA:13:9B`). If you do not know the port leave it empty and check the Home Assistant log. It attempts to list possible values that may help you figure out the correct setting. Update the configuration and restart Home Assitant. 

**name** string <br />
Name of the device, e.g. `Solar` or `Battery`. Multiple sensors (e.g. for a battery monitor and solar charger) with different names can be set up.

## Entities

Creates appropriate entities, e.g.

    * `sensor.battery_soc`, 
    * `sensor.solar_power`,
    * etc.

## Hardware

Connection can be either hardwired (e.g. with a Victron Energy VE.Direct to USB Interface) or wireless with an HM-18 module. I am using a `DSD TECH HM-18 CC2640R2F Bluetooth 5.0 BLE Module Compatible with HM-10 for Arduino`.

The HM-18 comes configured for 9600 baud and must be set to 19200 baud to be compatible with VE.Direct.

Connect the device to a serial port (e.g. using a `DSD TECH SH-U09C2 USB to TTL Adapter Built-in FTDI FT232RL IC for Debugging and Programming` TTL to USB interface).

Then run the following Python code. E.g. from a Home Assistant Terminal (`python3`). You may need to install pyserial first (`pip3 pyserial`).

Verify that the module is working:

```python
with serial.Serial(port=port, baudrate=9600) as dev:
    dev.write(b'AT+BAUD?')
    time.sleep(0.1)
    while dev.in_waiting > 0:
        print(dev.read(dev.in_waiting))

# should return b'OK+Get:3'
```

Now change the baudrate:

```python
with serial.Serial(port=port, baudrate=9600) as dev:
    dev.write(b'AT+BAUD4')
    time.sleep(0.1)
    while dev.in_waiting > 0:
        print(dev.read(dev.in_waiting))

# should return b'OK+Set:4'
```

Reconnect at the new baudrate and verify that communication is working:

```python
with serial.Serial(port=port, baudrate=19200) as dev:
    dev.write(b'AT+BAUD?')
    time.sleep(0.1)
    while dev.in_waiting > 0:
        print(dev.read(dev.in_waiting))

# should return b'OK+Get:4'
```
