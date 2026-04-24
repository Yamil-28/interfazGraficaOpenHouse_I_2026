import random


# =========================
# GENERAR MAC ADDRESS
# =========================

import random

def generar_mac():
    # Primer byte: 02 → local + unicast
    mac = [0x02, random.randint(0x00, 0x7f)]

    # Otros 4 bytes aleatorios
    mac += [random.randint(0x00, 0xff) for _ in range(4)]

    # Convertir a string continuo
    mac_str = ''.join(f"{b:02X}" for b in mac)

    # Formato Cisco: XXXX.XXXX.XXXX
    return f"{mac_str[0:4]}.{mac_str[4:8]}.{mac_str[8:12]}"


# =========================
# MAC → EUI-64 → IPv6 LINK-LOCAL
# =========================

def mac_a_ipv6_link_local(mac):
    # 1. Quitar los puntos y convertir a lista de bytes
    mac = mac.replace(".", "")  # 0ADADA1EBDDB
    mac_bytes = [mac[i:i+2] for i in range(0, 12, 2)]

    # 2. Insertar FF:FE en medio (EUI-64)
    eui64 = mac_bytes[:3] + ["FF", "FE"] + mac_bytes[3:]

    # 3. Flip del bit U/L
    first_byte = int(eui64[0], 16)
    first_byte ^= 0x02
    eui64[0] = f"{first_byte:02X}"

    # 4. Agrupar en bloques de 4 hex (2 bytes)
    ipv6_parts = []
    for i in range(0, len(eui64), 2):
        ipv6_parts.append(eui64[i] + eui64[i+1])

    # 5. Construir IPv6 link-local
    ipv6 = "FE80::" + ":".join(ipv6_parts)

    return ipv6.upper()