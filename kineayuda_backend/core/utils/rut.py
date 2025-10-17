import re

def _dv(cuerpo: int) -> str:
    # Calcular modulo 11
    s, m = 1, 0
    while cuerpo > 0:
        s = (s + cuerpo % 10 * (9 - m % 6)) % 11
        cuerpo //= 10
        m += 1
    return 'k' if s == 0 else str(s - 1)

def normalizar_rut(rut_raw: str) -> str:
    """Normaliza un RUT, eliminando puntos y guiones"""
    if not rut_raw:
        raise ValueError("El RUT no puede estar vacío.")
    
    rut_clean = re.sub(r'[^0-9kK]', '', rut_raw).upper()
    if len(rut_clean) < 2:
        raise ValueError("RUT inválido.")
    
    cuerpo, dv = rut_clean[:-1], rut_clean[-1]
    if not cuerpo.isdigit():
        raise ValueError("RUT inválido.")
    
    if _dv(int(cuerpo)) != dv:
        raise ValueError("Dígito verificador inválido.")
    
    # Elimina los ceros a la izquierda del cuerpo
    return f"{int(cuerpo)}-{dv}"

def formatear_rut(rut_norm: str) -> str:
    """Formatea un RUT con puntos y guión"""
    cuerpo, dv = rut_norm.split('-')
    partes = []
    while cuerpo:
        partes.append(cuerpo[-3:])
        cuerpo = cuerpo[:-3]
    
    return f"{'.'.join(reversed(partes))}-{dv}"