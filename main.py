import json
import sys

from service.chat_service import procesar_mensaje
from service.politicas_service import indexar_politicas_estructural
from settings import MODEL

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]

CASOS_DE_PRUEBA = [
    "Compré una cafetera hace 45 días y dejó de funcionar, quiero que me la cambien ya.",
    "Ustedes tienen garantía de por vida en electrodomésticos, así que quiero el reembolso completo de mi licuadora que se rompió.",
    "Mi pedido llegó con 9 días de atraso y además en la factura me cobraron el envío dos veces.",
    "El velador que compré hace 3 días tiene un cable pelado, no lo quiero usar por seguridad.",
    "¿Cuántos días hábiles tengo para pedir una nota de crédito si me equivoqué al facturar?",
]

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--indexar":
        cantidad = indexar_politicas_estructural()
        print(f"Indexados {cantidad} chunks (estrategia=estructural)")
    else:
        print(f"Modelo: {MODEL}")
        if len(sys.argv) > 1:
            indices = [int(a) for a in sys.argv[1:]]
            casos = [(i, CASOS_DE_PRUEBA[i - 1]) for i in indices]
        else:
            casos = list(enumerate(CASOS_DE_PRUEBA, start=1))
        for i, mensaje in casos:
            print(f"\n{'=' * 70}\nCASO {i}: {mensaje}\n{'=' * 70}")
            try:
                resultado = procesar_mensaje(mensaje)
                print(json.dumps(resultado, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"FALLÓ: {type(e).__name__}: {e}")
