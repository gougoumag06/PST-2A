import time
import sys
import signal
import board
import busio
from gpiozero import OutputDevice
from digitalio import Direction
from adafruit_mcp230xx.mcp23017 import MCP23017

# ==============================================================================
# CONFIGURATION DES PINS NATIVES (Raspberry Pi)
# ==============================================================================
# On exclut les pins 2 et 3 dédiées au bus I2C
PI_PINS = [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]

pi_devices = []

def cleanup():
    """Libère proprement toutes les ressources du Raspberry Pi"""
    print("\n[CLEANUP] Libération des GPIO natifs...")
    for dev in pi_devices:
        try:
            dev.close()
        except Exception:
            pass
    print("[INFO] Nettoyage terminé. Script arrêté.")
    sys.exit(0)

# Attraper les signaux de fermeture pour quitter proprement
signal.signal(signal.SIGINT, lambda s, f: cleanup())
signal.signal(signal.SIGTERM, lambda s, f: cleanup())


print("=======================================================")
print("          DÉMARRAGE DU RESET GÉNÉRAL GPIO              ")
print("=======================================================")

# --- ÉTAPE 1 : RESET DES GPIO NATIFS DU PI ---
print("\n[1/2] Reset des GPIO physiques du Raspberry Pi...")
for pin in PI_PINS:
    try:
        # On passe la pin en sortie et on force à LOW (0V) pour éteindre les LEDs
        dev = OutputDevice(pin, initial_value=False)
        pi_devices.append(dev)
    except Exception as e:
        print(f"  ✗ Impossible de reset la Pi pin {pin} : {e}")

print(f"  ✓ {len(pi_devices)} pins natives du Pi configurées à LOW.")


# --- ÉTAPE 2 : RESET DES EXTENSION MCP23017 VIA I2C ---
print("\n[2/2] Reset des modules MCP23017 (I2C)...")
try:
    # Initialisation temporaire du bus I2C
    i2c = busio.I2C(board.SCL, board.SDA)
    
    # Adresses de tes deux modules d'après ton code principal
    mcp_addresses = [0x20, 0x21]
    
    for addr in mcp_addresses:
        try:
            mcp = MCP23017(i2c, address=addr)
            print(f"  ✓ Module MCP23017 détecté à l'adresse {hex(addr)}. Reset des 16 pins à LOW...")
            
            # On force les 16 pins de chaque module en sortie et à False (Éteint)
            for pin_num in range(16):
                p = mcp.get_pin(pin_num)
                p.direction = Direction.OUTPUT
                p.value = False
                
        except Exception as e:
            print(f"  ⚠ Module au format {hex(addr)} non détecté ou inaccessible ({e}). Pass.")

except Exception as e:
    print(f"  ✗ Erreur critique : Impossible d'ouvrir le bus I2C général : {e}")


# --- ÉTAPE 3 : MAINTIEN DU RESET ---
print("\n=======================================================")
print("[SUCCÈS] Tout le système a été remis à zéro (Éteint).")
print("Laisse ce script tourner pour maintenir l'état éteint.")
print("👉 Appuie sur Ctrl+C pour quitter et libérer les pins.")
print("=======================================================")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    cleanup()