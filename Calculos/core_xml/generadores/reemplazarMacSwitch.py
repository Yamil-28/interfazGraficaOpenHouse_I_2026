import re
from core_xml.generadores.generarMac import generar_mac

def reemplazar_macs_switch(template):
    macs = {}

    def reemplazo(match):
        interfaz = match.group(1)  # f0/1, g0/1, etc

        if interfaz not in macs:
            macs[interfaz] = generar_mac()

        return macs[interfaz]

    # Busca {macf0/1}, {macg0/1}, etc
    return re.sub(r"\{mac(f0/\d+|g0/\d+)\}", reemplazo, template)