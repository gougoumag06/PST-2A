from gpiozero import OutputDevice
import signal
import sys

# Liste des pins GPIO BCM standards (exclut 14/15 UART, etc.)
pins = [2,3,4,5,6,7,8,9,10,11,12,13,16,17,18,19,20,21,22,23,24,25,26,27]

devices = []

def cleanup():
    for dev in devices:
        dev.close()
    sys.exit(0)

signal.signal(signal.SIGINT, lambda s, f: cleanup())
signal.signal(signal.SIGTERM, lambda s, f: cleanup())

# Configurer comme sorties et mettre à LOW
for pin in pins:
    dev = OutputDevice(pin, initial_value=False)
    devices.append(dev)

print("Tous les GPIO clear (LOW). Appuie Ctrl+C pour nettoyer.")
input("Attends...")

cleanup()