from core.global_func import generar_save_ref_id as gen_id
from core_xml.main import GeneradorTopologia as Gen_xml
import time
import os
import pprint
## OPERADORES CLASES
from core.operadores import (
    Operator_reader as O_reader,
    Operator_links as O_links,
    Operador_nets as O_nets
)
## GRAFO CLASES
from core.grafo import Grafo_red
# Para el servidor
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

#------
class General_Core:
    def __init__(self):
        ruta_script = os.path.dirname(os.path.abspath(__file__)).replace('\\','/')
        self.ruta = ruta_script
        ## General Corej
        self.dic_device_type = {}
        self.dic_conexiones = {}
        self.dic_device_objeto = {}
        self.dic_edges = {}
        self.lista_routers = []
        ## Special Core
        self.dic_general = {}
        self.dic_objeto_net = {}
        ## clases especales (constantes)
        self.grafo_general = Grafo_red()
        self.cal_redes = O_nets(self.ruta, self.dic_device_objeto, self.dic_objeto_net)
        self.generador_topologia: Gen_xml|None = None
        ## PARA XML - protocolo
        self.dic_router_protocolo = {}

        # banderas
        self.ips_cargadas = False
        self.conexiones_cargadas = False

    def read_devices(self,ruta):
        operator = O_reader(ruta)
        dic_device_type, dic_device_objeto, dic_conexiones = operator.get_core()

        self.dic_device_type.clear()
        self.dic_device_type.update(dic_device_type)

        self.dic_device_objeto.clear()
        self.dic_device_objeto.update(dic_device_objeto)

        self.dic_conexiones.clear()
        self.dic_conexiones.update(dic_conexiones)

        self.lista_routers = operator.lista_routers  

        self.conexiones_cargadas = True
        return "True"

    def write_links_graph(self):
        operator = O_links(self.dic_device_objeto, self.dic_conexiones)
        self.dic_edges = operator.get_links()

    def send_devices_graph(self):
        if self.dic_device_objeto:
            devices = self.dic_device_objeto.items()
            self.grafo_general.add_all_nodes(devices)
    def send_links_graph(self):
        if self.dic_edges:
            edges = self.dic_edges.items()
            self.grafo_general.add_all_edges(edges)
    def put_ips_devices(self,ruta):
        self.cal_redes.read_ips(ruta)
        self.ips_cargadas = True
    def asignar_posiciones(self):
        self.grafo_general.asignar_posiciones()

    def send_devices_attributes_xml(self):
        
        dic_all_atributes = {
            "pds": [
                {"nombre": "PD1", "x": 0, "y": 0},
                {"nombre": "PD2", "x": 50, "y": 0}
            ]
        }

        lista_links = []
        for objeto in self.dic_device_objeto.values():
            device_type = objeto.get_type()
            match (device_type):
                case 'pc': device_type = "pcs"
                case 'sw': device_type = "switches"
                case 'r': device_type = "routers"

            if not device_type in dic_all_atributes:    
                dic_all_atributes[device_type] = []
            dic_all_atributes[device_type].append(objeto.get_atributes())
        for devices, info in self.dic_edges.items():
            d1,d2 = devices
            i1,cable, i2 = info
            lista_links.append({"from": d1, "to": d2, "from_port": i1, "to_port": i2, "tipo": cable})
        dic_all_atributes["links"] = lista_links
        if self.generador_topologia == None:
            self.generador_topologia = Gen_xml(dic_all_atributes,self.dic_router_protocolo,self.ruta)
        self.generador_topologia.generar()
        return dic_all_atributes

    def calcular_ramas(self):
        if self.lista_routers:
            return self.cal_redes.calcular_router_ramas(self.lista_routers, self.grafo_general.grafo)
        else: 
            print("No se pudo realizar inter-vlans; no existe ROUTERS en la topologia")
            return None

# agrege self
    def aplicar_protocolos(self,dic_router_protocolo):

        dic = {
            'router1': "RIPv1"
        }
    # agregado de servidor.py
    def aplicarEnrutamiento(self, dic):
        print("Simulación:", dic)
        self.dic_router_protocolo 
        protocolo, routers = list(dic.items())[0]
        if self.dic_router_protocolo.get(protocolo) is None:
            self.dic_router_protocolo[protocolo] = []
        self.dic_router_protocolo[protocolo].extend(routers)
    
    def crear_topologia_xml(self):
        self.write_links_graph()
        self.send_devices_graph()
        self.send_links_graph()
        self.asignar_posiciones()
        self.calcular_ramas()
        self.send_devices_attributes_xml()
        if self.generador_topologia is not None:
            if not self.conexiones_cargadas and not self.ips_cargadas:
                return False
            
            self.generador_topologia.generar()
            return True
        return False    
    
#-----
# CREACIÓN DEL OBJETO ÚNICO (Singleton)
nucleo = General_Core()


# --- RUTAS DE LA API REST ---
# para cargar liks
@app.route('/api/cargar', methods=['POST'])
def read_devices():
    datos = request.json
    mensaje = nucleo.read_devices(datos.get('ruta').replace('\\','/'))
    return jsonify({
        "mensaje": mensaje
    })

@app.route('/api/obtener-routers', methods=['GET'])
def listaDeRouters():
    return jsonify({
        "routers": nucleo.lista_routers
    })

@app.route('/api/cargarIPs', methods=['POST'])
def put_ips_devices():
    datos = request.json
    mensaje = nucleo.put_ips_devices(datos.get('rutaIPs'))
    return jsonify({"mensaje": "Ruta guardada."})


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


@app.route('/api/generar_pkt', methods=['POST'])
def crear_topologia_xml():
    successful = nucleo.crear_topologia_xml()
    return jsonify({
        "bandera": successful
    })
# CORREGIDO: Una sola ruta de estado que devuelve la info correcta

if __name__ == '__main__':
    app.run(port=5000)
# ----