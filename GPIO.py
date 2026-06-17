from gpiozero import *
import board
import busio
import threading
import time
from digitalio import Direction, Pull
from adafruit_mcp230xx.mcp23017 import MCP23017


# === INITIALISATION DU MODULE I2C ===
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    
    # Premier module (adresse par défaut 0x20)
    mcp1 = MCP23017(i2c, address=0x20) 
    
    # Deuxième module (adresse 0x21 grâce au A0 sur VCC)
    mcp2 = MCP23017(i2c, address=0x21) 
    
    print("[INFO] Modules I2C détectés avec succès.")
except Exception as e:
    print(f"[ERREUR CRITIQUE] Impossible de se connecter aux modules I2C : {e}")
    mcp1 = None
    mcp2 = None


# === CLASSES ADAPTATEURS POUR LE MODULE ===
# Ces classes imitent le comportement de gpiozero pour ne pas casser ton code

class MCP_LED:
    def __init__(self, mcp_device, pin_number):
        self.pin = mcp_device.get_pin(pin_number)
        self.pin.direction = Direction.OUTPUT
        self.pin.value = False

    def on(self):
        self.pin.value = True

    def off(self):
        self.pin.value = False

    @property
    def is_lit(self):
        return self.pin.value

    def close(self):
        self.off()


class MCP_Button:
    def __init__(self, mcp_device, pin_number):
        self.pin = mcp_device.get_pin(pin_number)
        self.pin.direction = Direction.INPUT
        self.pin.pull = Pull.UP 
        
        # Variables pour gérer l'événement when_pressed
        self._when_pressed_callback = None
        self._last_state = self.is_pressed
        
        # Thread de surveillance (tourne en arrière-plan)
        self._stop_event = threading.Event()
        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._monitor_thread.start()

    @property
    def is_pressed(self):
        # Inversé car Pull-Up (0V quand pressé)
        return not self.pin.value 

    @property
    def when_pressed(self):
        return self._when_pressed_callback

    @when_pressed.setter
    def when_pressed(self, callback):
        # C'est ici que ton code Flask vient attacher sa fonction lambda !
        self._when_pressed_callback = callback

    def _monitor(self):
        """Boucle de surveillance invisible qui tourne en tâche de fond"""
        while not self._stop_event.is_set():
            current_state = self.is_pressed
            
            # Si le bouton vient juste d'être pressé (passage de Relâché à Pressé)
            if current_state == True and self._last_state == False:
                if self._when_pressed_callback is not None:
                    # On déclenche ta fonction (ex: on_bouton_b1_pressed)
                    self._when_pressed_callback()
                    
            self._last_state = current_state
            # Petite pause de 50ms (sert aussi d'anti-rebond basique)
            time.sleep(0.05) 

    def close(self):
        # Arrête le thread proprement quand on nettoie les GPIO
        self._stop_event.set()

# === CONFIGURATION DES GPIO ===
GPIO_CONFIG = {
    # === LIGNE 1 ===
    'led_start_L1': ('LED', 14, 'LED Démarrage Niveau 1'),
    'bouton_start_L1': ('Button', 15, 'Bouton Démarrage Niveau 1'),

    'led_b4_L1': ('LED', 4, 'LED Boîte 4 Niveau 1'),
    'bouton_b4_L1': ('Button', 17, 'Bouton Boîte 4 Niveau 1'),

    'led_b3_L1': ('LED', 27, 'LED Boite 3 Ligne 1'),
    'bouton_b3_L1': ('Button', 22, 'Bouton boite 3 Ligne 1'),

    'led_b2_L1': ('LED_MCP1', 0, 'LED Boite 2 Ligne 1'),
    'bouton_b2_L1': ('Button_MCP1', 2, 'Bouton boite 2 Ligne 1'),

    'led_b1_L1': ('LED_MCP2', 0, 'LED Boite 1 Ligne 1'),
    'bouton_b1_L1': ('Button_MCP2', 2, 'Bouton boite 1 Ligne 1'),

    'bouton_maboul_start_L1': ('Button_MCP2', 4, 'Maboul START Ligne 1'),
    'bouton_maboul_touch_L1': ('Button_MCP2', 7, 'Maboul FIL CUIVRE Ligne 1'),
    'bouton_maboul_end_L1':   ('Button_MCP2', 6, 'Maboul FIN Ligne 1'),

    # === LIGNE 2 ===
    'led_start_L2': ('LED', 24, 'LED Démarrage Niveau 1'),
    'bouton_start_L2': ('Button', 25, 'Bouton Démarrage Niveau 2'),

    'led_b4_L2': ('LED', 9, 'LED Boîte 4 Niveau 1'),
    'bouton_b4_L2': ('Button', 10, 'Bouton Boîte 4 Niveau 1'),

    'led_b3_L2': ('LED', 11, 'LED Boîte 3 Niveau 1'),
    'bouton_b3_L2': ('Button', 5, 'Bouton Boîte 3 Niveau 1'),
    
    'led_b2_L2': ('LED_MCP1', 8, 'LED Boite 2 Ligne 2'),
    'bouton_b2_L2': ('Button_MCP1', 10, 'Bouton boite 2 Ligne 2'),

    'led_b1_L2': ('LED_MCP2', 8, 'LED Boite 1 Ligne 2'),
    'bouton_b1_L2': ('Button_MCP2', 10, 'Bouton boite 13 Ligne 2'),

    'bouton_maboul_start_L2': ('Button_MCP2', 12, 'Maboul START Ligne 2'),
    'bouton_maboul_touch_L2': ('Button_MCP2', 15, 'Maboul FIL CUIVRE Ligne 2'),
    'bouton_maboul_end_L2':   ('Button_MCP2', 14, 'Maboul FIN Ligne 2')
}


# === VARIABLES GLOBALES ===
Dict_GPIO = {}
gpio_initialises = False


def init_gpio():
    """
    Initialise tous les GPIO basés sur GPIO_CONFIG
    """
    global Dict_GPIO, gpio_initialises
    
    if gpio_initialises:
        print("[INFO] GPIO déjà initialisés")
        return True
    
    try:
        count_success = 0
        count_error = 0
        
        print("\n[INIT] Démarrage de l'initialisation des GPIO...")
        
        for nom_gpio, (type_gpio, numero, description) in GPIO_CONFIG.items():
            try:
                # --- Composants Raspberry Pi classiques (gpiozero) ---
                if type_gpio == 'LED':
                    obj = LED(numero)
                    Dict_GPIO[nom_gpio] = obj
                    print(f"✓ {description} (Pi GPIO {numero})")
                    count_success += 1
                        
                elif type_gpio == 'Button':
                    obj = Button(numero)
                    Dict_GPIO[nom_gpio] = obj
                    print(f"✓ {description} (Pi GPIO {numero})")
                    count_success += 1

                elif type_gpio == 'OutputDevice':
                    obj = OutputDevice(numero)
                    Dict_GPIO[nom_gpio] = obj
                    print(f"✓ {description} (Pi GPIO {numero})")
                    count_success += 1

                # --- Composants sur le MODULE I2C N°1 ---
                elif type_gpio == 'LED_MCP1':
                    if mcp1 is None: raise Exception("Module I2C 1 non disponible")
                    obj = MCP_LED(mcp1, numero)
                    Dict_GPIO[nom_gpio] = obj
                    print(f"✓ {description} (Module 1 Pin {numero})")
                    count_success += 1

                elif type_gpio == 'Button_MCP1':
                    if mcp1 is None: raise Exception("Module I2C 1 non disponible")
                    obj = MCP_Button(mcp1, numero)
                    Dict_GPIO[nom_gpio] = obj
                    print(f"✓ {description} (Module 1 Pin {numero})")
                    count_success += 1

                # --- Composants sur le MODULE I2C N°2 ---
                elif type_gpio == 'LED_MCP2':
                    if mcp2 is None: raise Exception("Module I2C 2 non disponible")
                    obj = MCP_LED(mcp2, numero)
                    Dict_GPIO[nom_gpio] = obj
                    print(f"✓ {description} (Module 2 Pin {numero})")
                    count_success += 1

                elif type_gpio == 'Button_MCP2':
                    if mcp2 is None: raise Exception("Module I2C 2 non disponible")
                    obj = MCP_Button(mcp2, numero)
                    Dict_GPIO[nom_gpio] = obj
                    print(f"✓ {description} (Module 2 Pin {numero})")
                    count_success += 1
                        
            except Exception as e:
                print(f"✗ ERREUR {description} (Pin {numero}): {e}")
                count_error += 1
        
        # Rapport final
        print(f"\n[RAPPORT] ✓ Succès: {count_success} | ✗ Erreurs: {count_error}")
        print(f"[DEBUG] Total dans Dict_GPIO: {len(Dict_GPIO)} composants")
        
        if count_success > 0:
            gpio_initialises = True
            print(f"[SUCCESS] Initialisation complétée\n")
            return True
        else:
            print(f"[ERREUR] Aucun GPIO n'a pu être initialisé\n")
            return False
        
    except Exception as e:
        print(f"[ERREUR CRITIQUE] {e}\n")
        return False

# ... (Le reste de tes fonctions demandeGPIO, eteindre_tous_leds, etc. reste STRICTEMENT identique !)

def demandeGPIO(nom_gpio):
    """
    Retourne l'objet GPIO correspondant au nom
    
    Args:
        nom_gpio (str): Nom logique du GPIO (ex: 'led_start_L1')
    
    Returns:
        LED or Button or None: Objet GPIO ou None si non trouvé
    """
    if nom_gpio not in Dict_GPIO:
        print(f"[ERREUR] GPIO '{nom_gpio}' non trouvé dans Dict_GPIO")
        print(f"[DEBUG] Disponibles: {list(Dict_GPIO.keys())}")
        return None
    
    obj = Dict_GPIO.get(nom_gpio)
    if obj is None:
        print(f"[ERREUR] GPIO '{nom_gpio}' retourne None")
    return obj


def eteindre_tous_leds():
    """Éteint toutes les LEDs"""
    count = 0
    for nom, obj in Dict_GPIO.items():
        if 'led' in nom.lower() and obj is not None and hasattr(obj, 'off'):
            try:
                obj.off()
                count += 1
            except Exception as e:
                print(f"[ERREUR] Extinction LED {nom}: {e}")
    print(f"[INFO] {count} LEDs éteintes")


def allumer_tous_leds():
    """Allume toutes les LEDs"""
    count = 0
    for nom, obj in Dict_GPIO.items():
        if 'led' in nom.lower() and obj is not None and hasattr(obj, 'on'):
            try:
                obj.on()
                count += 1
            except Exception as e:
                print(f"[ERREUR] Allumage LED {nom}: {e}")
    print(f"[INFO] {count} LEDs allumées")


def get_gpio_status():
    """
    Retourne l'état de tous les GPIO
    
    Returns:
        dict: État de chaque GPIO
    """
    status = {}
    for nom, obj in Dict_GPIO.items():
        if obj is None:
            status[nom] = {'type': 'Unknown', 'state': 'NULL'}
        elif hasattr(obj, 'is_lit'):
            status[nom] = {'type': 'LED', 'state': 'ON' if obj.is_lit else 'OFF'}
        elif hasattr(obj, 'is_pressed'):
            status[nom] = {'type': 'Button', 'state': 'PRESSED' if obj.is_pressed else 'RELEASED'}
    return status


def cleanup_gpio():
    """Nettoie et ferme tous les GPIO"""
    try:
        for nom, obj in Dict_GPIO.items():
            if obj is not None and hasattr(obj, 'close'):
                obj.close()
        print("[INFO] Tous les GPIO fermés")
        global gpio_initialises
        gpio_initialises = False
    except Exception as e:
        print(f"[ERREUR] Lors du nettoyage des GPIO: {e}")


# === HELPERS POUR ACCÈS RAPIDE ===
def get_led(niveau, boite):
    """
    Récupère une LED spécifique
    
    Args:
        niveau (int): 1 ou 2
        boite (str): 'start', 'b1', 'b2', 'b3', 'b4'
    
    Returns:
        LED or None
    """
    nom = f"led_{boite}_L{niveau}"
    led = demandeGPIO(nom)
    
    if led is None:
        print(f"[ERREUR] LED introuvable: {nom}")
        print(f"[DEBUG] Vérifiez votre GPIO_CONFIG et le niveau {niveau}")
    
    return led


def get_bouton(niveau, boite):
    """
    Récupère un bouton spécifique
    
    Args:
        niveau (int): 1 ou 2
        boite (str): 'start', 'b1', 'b2', 'b3', 'b4'
    
    Returns:
        Button or None
    """
    nom = f"bouton_{boite}_L{niveau}"
    bouton = demandeGPIO(nom)
    
    if bouton is None:
        print(f"[ERREUR] Bouton introuvable: {nom}")
        print(f"[DEBUG] Vérifiez votre GPIO_CONFIG et le niveau {niveau}")
    
    return bouton

def get_maboul_input(niveau, action):
    """
    Récupère un pin du docteur maboul spécifique
    action peut être: 'start', 'touch', 'end'
    """
    nom = f"bouton_maboul_{action}_L{niveau}"
    return demandeGPIO(nom)