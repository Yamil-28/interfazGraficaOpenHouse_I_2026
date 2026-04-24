import secrets

def generar_partial_duid():
    # 8 bytes = 64 bits
    return '-'.join(f"{b:02X}" for b in secrets.token_bytes(8)) + '-'