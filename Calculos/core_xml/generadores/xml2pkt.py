import zlib
import struct
import os


def xor_data(data: bytes, key: int) -> bytes:
    result = bytearray(len(data))
    for i, byte in enumerate(data):
        result[i] = byte ^ ((key - i) & 0xFF)
    return bytes(result)


def xml_a_pkt(input_path: str, output_path: str) -> bool:
    try:
        with open(input_path, "rb") as f:
            xml_data = f.read()
        # Comprimir XML
        compressed = zlib.compress(xml_data, level=zlib.Z_BEST_COMPRESSION)
        #Añadir tamaño original (4 bytes little-endian)
        payload = struct.pack("<I", len(xml_data)) + compressed
        # Cifrado XOR
        file_size = len(payload)
        encrypted = xor_data(payload, file_size)
        # Guardar PKT
        with open(output_path, "wb") as f:
            f.write(encrypted)
        print(f"[✓] PKT generado: {output_path}")
        return True
    except Exception as e:
        print(f"[✗] Error al convertir a PKT: {e}")
        return False