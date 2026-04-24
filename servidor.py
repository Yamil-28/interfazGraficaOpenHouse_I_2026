from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Esta es la clase que te pasará tu equipo
class GeneralCore:
    def __init__(self):
 # Esta lista persistirá en memoria
        self.rutaDeConexiones = None # Inicializamos en None para evitar errores de referencia
        self.lista = ["R1","R2","R3","R4","R5"] # Simulamos una lista de routers en RAM
        self.grafo = []# Inicializamos en None
        # Crea el archivo de prueba al iniciar el servidor
        print(">>> Objeto GeneralCore instanciado y listo.")

    def crear_txt_prueba(self,saludo1,saludo2):
        try:
            with open("SERVIDOR_VIVO.txt", "w", encoding="utf-8") as archivo:
                archivo.write("--- REPORTE DE SISTEMA AUTOPKT ---\n")
                archivo.write(f"Último encendido: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                archivo.write("¡Felicidades.\n")
                archivo.write(f"Estado inicial de ruta: {self.rutaDeConexiones}\n")
                archivo.write(f"Ruta recibida para prueba mmm: {saludo1,saludo2}\n")
            print(">>> Archivo SERVIDOR_VIVO.txt generado como prueba de vida.")
        except Exception as e:
            print(f"Error al crear archivo de prueba: {e}")


    def mostrar_routers(self,lista_routers):
        self.grafo = lista_routers
        return lista_routers
    
    def aplicar_enrutamiento(self,protocolo, routers):
        with open("enrutamiento_log.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"--- Enrutamiento aplicado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            log_file.write(f"Protocolo seleccionado: {protocolo}\n")
            log_file.write(f"Routers seleccionados para enrutamiento: {routers}\n\n")
        # Aquí iría la lógica de enrutamiento basada en el protocolo seleccionado
        return "Enrutamiento aplicado con éxito."

    
    def cargarIPs(self, IPs):
        print(f"Ruta de IPs recibida: {IPs}")
        return f"Ruta de IPs: {IPs}"
    def cargar_datos(self, ruta):
        if not ruta:
            return "Error: No se proporcionó una ruta válida."
           
        #  AQUÍ OCURRE LA MAGIA: Guardamos la ruta en el atributo del objeto
        self.rutaDeConexiones = ruta
       
       
        return f"Dirección {self.rutaDeConexiones} guardada en RAM."
    
    def aplicarEnrutamiento(self, dic):
        print("Simulación:", dic)

# CREACIÓN DEL OBJETO ÚNICO (Singleton)
nucleo = GeneralCore()


# --- RUTAS DE LA API REST ---
@app.route('/api/cargar', methods=['POST'])
def ruta_cargar():
    datos = request.json
    mensaje = nucleo.cargar_datos(datos.get('ruta'))
    return jsonify({
        "mensaje": mensaje,
        "ruta_almacenada": nucleo.rutaDeConexiones
    })

@app.route('/api/obtener-routers', methods=['GET'])
def listaDeRouters():
    routers = nucleo.mostrar_routers(nucleo.lista)
    return jsonify({
        "routers": routers

    })

@app.route('/api/cargarIPs', methods=['POST'])
def ruta_IPs():
    datos = request.json
    mensaje = nucleo.cargarIPs(datos.get('rutaIPs'))
    return jsonify({"mensaje": "Ruta guardada."})


@app.route('/api/guardar', methods=['POST'])
def ruta_guardar():
    datos = request.json
    mensaje = nucleo.crear_txt_prueba(datos.get('saludo1'), datos.get('saludo2'))
    return jsonify({"Hola": mensaje})

@app.route('/api/mostrarlistaRouters', methods=['GET'])
def obtenerLista():
    return jsonify({
        "routers": nucleo.lista
    })


# RESTAURADO: Esta ruta es necesaria para que funcione la pestaña de Protocolos
@app.route('/api/protocolo', methods=['POST'])
def ruta_protocolo():
    datos = request.json

    protocolo = datos.get('protocolo')   # "OSPF"
    routers = datos.get('routers')       # ["R1", "R2"]

    dic = {protocolo: routers}           # 👈 ESTO ES TU TRABAJO
    print("Dic: ", dic)
    nucleo.aplicarEnrutamiento(dic)   # 👈 se lo pasas

    return jsonify({"mensaje": "ok"})

# CORREGIDO: Una sola ruta de estado que devuelve la info correcta
@app.route('/api/estado', methods=['GET'])
def ruta_estado():
    return jsonify({
        "archivo_guardado": nucleo.rutaDeConexiones, # Usa el nombre que configuraste en React
        "routers_en_ram": nucleo.grafo
    })

if __name__ == '__main__':
    app.run(port=5000)