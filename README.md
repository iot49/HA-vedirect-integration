# Victron VE.Direct Integration

Many Victron devices (e.g. SmartShunt and MPPT solar chargers) output status information over a VE.Direct bus (really just a TTL UART operating at 19200 baud).

This integration makes this information available to Home Assistant. The VE.Direct device can be connected either wired or wireless via an HM-18 Bluetooth module.