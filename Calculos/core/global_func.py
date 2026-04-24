import time
import random

def generar_save_ref_id():
    # Base con tiempo en microsegundos
    base = str(int(time.time() * 1_000_000))
    if len(base) > 16:
        numero = base[:16]
    else:
        faltan = 16 - len(base)
        extra = ''.join(str(random.randint(0, 9)) for _ in range(faltan))
        numero = base + extra
    return f"save-ref-id:{numero}"