import re
import random
from core_xml.generadores.generarMac import generar_mac, mac_a_ipv6_link_local
from core_xml.generadores.generarPartialDuuid import generar_partial_duid
from core_xml.generadores.generarRefId import generar_save_ref_id
from core_xml.generadores.generarUuid import generar_uuid
from core_xml.generadores.reemplazarMacSwitch import reemplazar_macs_switch

def safe(val):
    return "" if val is None else val

class GeneradorTopologia:

    def __init__(self, ruta, datos, links):
        self.datos = datos
        self.links = links
        self.ruta = ruta

        self.templates = self.cargar_templates()
        self.dispositivos = {}

        self.workspace = {
            "uuid1": generar_uuid(),
            "uuid2": generar_uuid(),
            "uuid3": generar_uuid(),
            "uuid4": generar_uuid(),
            "uuidRack": generar_uuid()
        }

    # =========================
    # TEMPLATES
    # =========================
    def cargar_templates(self):
        t = {}
        archivos = {
            "node_pc": "formatoNodoPc.xml",
            "node_sw": "formatoNodoSwitch.xml",
            "node_pd": "formatoNodoPd.xml",
            "node_router": "formatoNodoRouter.xml",
            "device_pc": "formatoDevicePc.xml",
            "device_sw": "formatoDeviceSwitch.xml",
            "device_pd": "formatoDevicePd.xml",
            "device_router": "formatoDeviceRouter.xml",
            "router_gigabit": "routerInterfaceGigabit.xml",
            "router_serial": "routerInterfaceSerial.xml",
            "config_router": "formatoConfigRouter.xml",
            "link_cobre": "formatoLinkCobre.xml",
            "link_serial": "formatoLinkSerial.xml",
            "main": "formatoMain.xml",
            "scenario": "formatoScenario.xml"
        }

        for k, v in archivos.items():
            with open(f"templates/{v}") as f:
                t[k] = f.read()

        return t

    # =====================================================
    # CREACIÓN DE DISPOSITIVOS
    # =====================================================

    def crear_pcs(self):
        for pc in self.datos.get("pcs", []):
            obj = {
                "tipo": "pc",
                "nombre": pc.get("nombre"),
                "posX": pc.get("x", 0),
                "posY": pc.get("y", 0),
                "ip": safe(pc.get("ip")),
                "mask": safe(pc.get("mask")),
                "gw": safe(pc.get("gw")),
                "uuid": generar_uuid(),
                "refId": pc.get("id"),
                "mac": generar_mac(),
                "mac_bt": generar_mac()
            }

            obj["node_xml"] = self.templates["node_pc"].format(
                nombre=obj["nombre"], uuidPC=obj["uuid"]
            )

            self.dispositivos[obj["nombre"]] = obj

    def crear_switches(self):
        for sw in self.datos.get("switches", []):
            obj = {
                "tipo": "sw",
                "nombre": sw.get("nombre"),
                "posX": sw.get("x", 0),
                "posY": sw.get("y", 0),
                "ip": safe(sw.get("ip")),
                "mask": safe(sw.get("mask")),
                "gw": safe(sw.get("gw")),
                "uuid": generar_uuid(),
                "refId": sw.get("id"),
                "macBuildInAddr": generar_mac(),
                "vlans": sw.get("vlans", []),
                "puertos": sw.get("puertos", {}),
                "cantVlans": len(sw.get("vlans", []))+5
            }

            obj["node_xml"] = self.templates["node_sw"].format(
                nombre=obj["nombre"], uuidSW=obj["uuid"]
            )

            self.dispositivos[obj["nombre"]] = obj

    def crear_routers(self):
        for r in self.datos.get("routers", []):
            obj = {
                "tipo": "router",
                "nombre": r["nombre"],
                "posX": r["x"],
                "posY": r["y"],
                "uuid": generar_uuid(),
                "refId": r["id"],
                "macBuildInAddr": generar_mac(),
                "interfaz": r["interfaz"],
                "enrutamiento": r.get("enrutamiento", {}),
                "rbp": r.get("rbp", False)
            }
            obj["node_xml"] = self.templates["node_router"].format(
                nombre=obj["nombre"], uuidR=obj["uuid"]
            )
            self.dispositivos[obj["nombre"]] = obj

    def crear_pds(self):
        for pd in self.datos.get("pds", []):
            obj = {
                "tipo": "pd",
                "nombre": pd["nombre"],
                "posX": pd["x"],
                "posY": pd["y"],
                "uuid": generar_uuid(),
                "refId": generar_save_ref_id()
            }
            obj["node_xml"] = self.templates["node_pd"].format(
                nombre=obj["nombre"], uuidPD=obj["uuid"]
            )
            self.dispositivos[obj["nombre"]] = obj

    # =====================================================
    # LINKS
    # =====================================================

    def procesar_links(self):
        lista = []

        for link in self.datos.get("links", []):
            d1 = self.dispositivos[link["from"]]
            d2 = self.dispositivos[link["to"]]

            if link["tipo"] in ["straight", "cross"]:
                tipoCable = "eStraightThrough" if link["tipo"] == "straight" else "eCrossOver"

                xml = self.templates["link_cobre"].format(
                    origenRefId=d1["refId"],
                    origenInterfaz=link["from_port"],
                    destinoRefId=d2["refId"],
                    destinoInterfaz=link["to_port"],
                    tipoCable=tipoCable
                )

            else:
                xml = self.templates["link_serial"].format(
                    origenRefId=d1["refId"],
                    origenInterfaz=link["from_port"],
                    destinoRefId=d2["refId"],
                    destinoInterfaz=link["to_port"]
                )

            lista.append(xml)

        return lista

    # =====================================================
    # CONFIGURACIÓN
    # =====================================================
    def config_pcs(self):
        for d in self.dispositivos.values():
            if d["tipo"] != "pc":
                continue

            mac = generar_mac()
            mac_bt = generar_mac()

            d["device_xml"] = self.templates["device_pc"].format(
                nombre=d["nombre"],
                ip=d.get("ip", ""),
                mask=d.get("mask", ""),
                gw=d.get("gw", ""),
                posX=d["posX"],
                posY=d["posY"],
                mac=mac,
                mac_ipv6=mac_a_ipv6_link_local(mac),
                macBluetooth=mac_bt,
                macBluetoothAipv6=mac_a_ipv6_link_local(mac_bt),
                uuidPC=d["uuid"],
                uuid1=self.workspace["uuid1"],
                uuid2=self.workspace["uuid2"],
                uuid3=self.workspace["uuid3"],
                refId=d["refId"],
                partialDuid=generar_partial_duid(),
                beaconUuid=generar_uuid()
            )
    def generar_vlans_xml(self, vlans, espacios):
        indent = " " * espacios
        texto = ""
        for v in vlans:
            texto += f'{indent}<VLAN name="VLAN{str(v).zfill(4)}" number="{v}" rspan="0"/>\n'
        return texto
    def generar_interfaces_switch(self, sw):
        puertos_config = sw.get("puertos", {})
        texto = ""
        # FastEthernet 1-24
        for i in range(1, 25):
            nombre = f"FastEthernet0/{i}"
            texto += f"      <LINE>interface {nombre}</LINE>\n"
            if nombre in puertos_config:
                cfg = puertos_config[nombre]
                if cfg["modo"] == "access":
                    texto += f"      <LINE> switchport mode access</LINE>\n"
                    texto += f"      <LINE> switchport access vlan {cfg['vlan']}</LINE>\n"
                elif cfg["modo"] == "trunk":
                    texto += f"      <LINE> switchport mode trunk</LINE>\n"
            texto += "      <LINE>!</LINE>\n"
        # Gigabit
        for i in range(1, 3):
            nombre = f"GigabitEthernet0/{i}"
            texto += f"      <LINE>interface {nombre}</LINE>\n"
            if nombre in puertos_config:
                cfg = puertos_config[nombre]
                if cfg["modo"] == "trunk":
                    texto += f"      <LINE> switchport mode trunk</LINE>\n"
            texto += "      <LINE>!</LINE>\n"
        return texto
    def config_switches(self):
        for d in self.dispositivos.values():
            if d["tipo"] != "sw":
                continue
            vlans = d.get("vlans", [])
            vlans_9 = self.generar_vlans_xml(vlans, 9)
            vlans_11 = self.generar_vlans_xml(vlans, 11)
            vlans_13 = self.generar_vlans_xml(vlans, 13)
            vlans_6 = self.generar_vlans_xml(vlans, 6)
            interfaces_xml = self.generar_interfaces_switch(d)
            device_xml = self.templates["device_sw"].format(
                nombre=d["nombre"],
                ip=d.get("ip", ""),
                mask=d.get("mask", ""),
                gw=d.get("gw", ""),
                posX=d["posX"],
                posY=d["posY"],
                macBuildInAddr=generar_mac(),
                uuidSW=d["uuid"],
                uuid1=self.workspace["uuid1"],
                uuid2=self.workspace["uuid2"],
                uuid3=self.workspace["uuid3"],
                uuid4=self.workspace["uuid4"],
                uuidRack=self.workspace["uuidRack"],
                refId=d["refId"],
                cantVlans=len(d.get("vlans", [])) + 5,
                vlans_9=vlans_9,
                vlans_11=vlans_11,
                vlans_13=vlans_13,
                vlans_6=vlans_6,
                interfaces=interfaces_xml
            )
            d["device_xml"] = reemplazar_macs_switch(device_xml)

    def generar_config_interfaces(self, router):
        texto = ""
        for port, data in (router.get("interfaz") or {}).items():
            # interfaz física
            texto += f"      <LINE>interface {port}</LINE>\n"
            texto += f"      <LINE> ip address {data['ip']} {data['mask']}</LINE>\n"
            if "GigabitEthernet" in port:
                texto += "      <LINE> duplex auto</LINE>\n"
                texto += "      <LINE> speed auto</LINE>\n"
            else:
                texto += f"      <LINE> clock rate {data.get('clock', 64000)}</LINE>\n"
            texto += "      <LINE>!</LINE>\n"
            # =========================
            # SUBINTERFACES VLAN
            # =========================
            for vlan in data.get("vlans", []):
                vid, gw, mask = vlan
                texto += f"      <LINE>interface {port}.{vid}</LINE>\n"
                texto += f"      <LINE> encapsulation dot1Q {vid}</LINE>\n"
                texto += f"      <LINE> ip address {gw} {mask}</LINE>\n"
                texto += "      <LINE>!</LINE>\n"
        return texto
    def generar_interfaces_router(self, router):
        slots = {}
        # inicializar
        for i in range(10):
            slots[f"slot{i}"] = ""
        for port, data in router["interfaz"].items():
            numero = int(re.findall(r'\d+', port)[0])
            if numero > 9:
                raise ValueError(f"Slot inválido: {port}")
            mac = generar_mac()
            macIPv6 = mac_a_ipv6_link_local(mac)
            # detectar tipo automáticamente
            if "GigabitEthernet" in port:
                slot = self.templates["router_gigabit"].format(
                    mac=mac,
                    ip=data["ip"],
                    mask=data["mask"],
                    macAIpv6=macIPv6
                )
            else:
                slot = self.templates["router_serial"].format(
                    mac=mac,
                    ip=data["ip"],
                    mask=data["mask"],
                    clock=data.get("clock", 64000),
                    macAIpv6=macIPv6
                )
            slots[f"slot{numero}"] = slot
        return slots
    def generar_routing(self, router):
        r = router.get("enrutamiento", {})
        rbp = router.get("rbp", False)
        if not r:
            return ""
        tipo = r.get("tipo", "").lower()
        redes = r.get("network", [])
        texto = ""
        # =====================
        # RIP
        # =====================
        if tipo in ["rip", "ripv2"]:
            texto += "      <LINE>router rip</LINE>\n"
            if tipo == "ripv2":
                texto += "      <LINE> version 2</LINE>\n"
            for net in redes:
                texto += f"      <LINE> network {net}</LINE>\n"
            if rbp:
                texto += "      <LINE> redistribute static</LINE>\n"
            texto += "      <LINE> no auto-summary</LINE>\n"
            texto += "      <LINE>!</LINE>\n"
        # =====================
        # EIGRP
        # =====================
        elif tipo == "eigrp":
            asn = r.get("as", 1)
            texto += f"      <LINE>router eigrp {asn}</LINE>\n"
            for net in redes:
                texto += f"      <LINE> network {net}</LINE>\n"
            if rbp:
                texto += "      <LINE> redistribute static</LINE>\n"
            texto += "      <LINE> no auto-summary</LINE>\n"
            texto += "      <LINE>!</LINE>\n"
        # =====================
        # OSPF
        # =====================
        elif tipo == "ospf":
            process_id = r.get("process_id", 1)
            texto += f"      <LINE>router ospf {process_id}</LINE>\n"
            for net in r.get("networks", []):
                texto += f"      <LINE> network {net['red']} {net['wildcard']} area 0</LINE>\n"
            if rbp:
                texto += "      <LINE> redistribute static</LINE>\n"
            texto += "      <LINE>!</LINE>\n"

        return texto
    def config_routers(self):
        for d in self.dispositivos.values():
            if d["tipo"] != "router":
                continue

            rbp_line = ""
            if d.get("rbp"):
                rbp_line = "      <LINE>ip route 0.0.0.0 0.0.0.0 Serial9/0</LINE>\n"
            config = self.templates["config_router"].format(
                nombre=d["nombre"],
                interfacesRouter=self.generar_config_interfaces(d),
                protocoloEnrutamiento=self.generar_routing(d),
                rbp=rbp_line
            )
            slots = self.generar_interfaces_router(d)
            d["device_xml"] = self.templates["device_router"].format(
                nombre=d["nombre"],
                posX=d["posX"],
                posY=d["posY"],
                macBuildInAddr=d["macBuildInAddr"],
                refId=d["refId"],
                uuidR=d["uuid"],
                uuid1=self.workspace["uuid1"],
                uuid2=self.workspace["uuid2"],
                uuid3=self.workspace["uuid3"],
                uuid4=self.workspace["uuid4"],
                uuidRack=self.workspace["uuidRack"],
                config=config,
                **slots
            )

    # =====================================================
    # SCENARIOS
    # =====================================================

    def procesar_scenarios(self):
        lista = []
        # =========================
        # PCs
        # =========================
        pcs = [d for d in self.dispositivos.values() if d["tipo"] == "pc"]
        if not pcs:
            return []
        origen = pcs[0]
        # destinos iniciales: PCs (menos el origen)
        destinos = pcs[1:]
        # =========================
        # SWITCHES
        # =========================
        switches = [d for d in self.dispositivos.values() if d["tipo"] == "sw"]
        destinos.extend(switches)
        # =========================
        # GENERAR PINGS
        # =========================
        for d in destinos:
            xml = self.templates["scenario"].format(
                origenRefId=origen["refId"],
                destinoRefId=d["refId"],
                destinoIp=d.get("ip", ""),  # importante: switches deben tener IP
                color=str(random.randint(-15000000, -100000))
            )
            lista.append(xml)

        return lista
    # =====================================================
    # FINAL
    # =====================================================
    def generar(self):
        # crear dispositivos
        self.crear_pcs()
        self.crear_switches()
        self.crear_routers()
        self.crear_pds()
        # configuración
        self.config_pcs()
        self.config_switches()
        self.config_routers()
        # links
        links = self.procesar_links()
        # escenarios
        scenarios = self.procesar_scenarios()
        xml_devices = "\n".join(d.get("device_xml", "") for d in self.dispositivos.values())
        xml_nodes_pc = "\n".join(d["node_xml"] for d in self.dispositivos.values() if d["tipo"] == "pc")
        xml_nodes_rack = "\n".join(d["node_xml"] for d in self.dispositivos.values() if d["tipo"] != "pc")
        return self.templates["main"].format(
            uuid1=self.workspace["uuid1"],
            uuid2=self.workspace["uuid2"],
            uuid3=self.workspace["uuid3"],
            uuid4=self.workspace["uuid4"],
            uuidRack=self.workspace["uuidRack"],
            devices=xml_devices,
            links="\n".join(links),
            nodes_pc=xml_nodes_pc,
            nodes_rack=xml_nodes_rack,
            scenarios="\n".join(scenarios)
        )

datos = {
    "pcs": [
        # --- SW1 ---
        {"nombre": "PC1", "x": 100, "y": 200, "ip": "192.168.2.10", "gw": "192.168.2.1", "mask": "255.255.255.0", "refId": generar_save_ref_id()},
        {"nombre": "PC2", "x": 300, "y": 200, "ip": "192.168.3.10", "gw": "192.168.3.1", "mask": "255.255.255.0", "refId": generar_save_ref_id()},
        # --- SW2 ---
        {"nombre": "PC3", "x": 400, "y": 200, "ip": "172.16.2.10", "gw": "172.16.2.1", "mask": "255.255.255.0", "refId": generar_save_ref_id()},
        {"nombre": "PC4", "x": 600, "y": 200, "ip": "172.16.3.10", "gw": "172.16.3.1", "mask": "255.255.255.0", "refId": generar_save_ref_id()}
    ],

    "switches": [
        {
            "nombre": "SW1",
            "x": 200,
            "y": 200,
            "ip": "192.168.1.10",
            "gw": "192.168.1.1",
            "mask": "255.255.255.0",
            "vlans": [2, 3],
            "refId": generar_save_ref_id(),
            "puertos": {
                "FastEthernet0/1": {"modo": "access", "vlan": 2},
                "FastEthernet0/2": {"modo": "access", "vlan": 3},
                "FastEthernet0/24": {"modo": "trunk"}
            }
        },
        {
            "nombre": "SW2",
            "x": 500,
            "y": 200,
            "ip": "172.16.1.10",
            "gw": "172.16.1.1",
            "mask": "255.255.255.0",
            "vlans": [2, 3],
            "refId": generar_save_ref_id(),
            "puertos": {
                "FastEthernet0/1": {"modo": "access", "vlan": 2},
                "FastEthernet0/2": {"modo": "access", "vlan": 3},
                "FastEthernet0/24": {"modo": "trunk"}
            }
        }
    ],

    "routers": [
        {
            "nombre": "R1",
            "x": 200,
            "y": 100,
            "refId": generar_save_ref_id(),
            "rbp": True,
            "interfaz": {
                "GigabitEthernet0/0": {"ip": "192.168.1.1", "mask": "255.255.255.0", "vlans": [(2, "192.168.2.1", "255.255.255.0"), (3, "192.168.3.1", "255.255.255.0")]},
                "Serial9/0": {"ip": "10.0.0.1", "mask": "255.255.255.252"}
            },
            "enrutamiento": {
                "tipo": "eigrp",
                "as": 100, #numero sistema autonomo
                "network": ["192.168.1.0", "10.0.0.0"]
            }
        },
        {
            "nombre": "R2",
            "x": 500,
            "y": 100,
            "refId": generar_save_ref_id(),
            "rbp": True,
            "interfaz": {
                "GigabitEthernet0/0": {"ip": "172.16.1.1", "mask": "255.255.255.0", "vlans": [(2, "172.16.2.1", "255.255.255.0"), (3, "172.16.3.1", "255.255.255.0")]},
                "Serial9/0": {"ip": "10.0.0.2", "mask": "255.255.255.252"}
            },
            # SOLO UN ENRUTAMIENTO POR ROUTER
            # ENRUTAMIENTO RIP V1
            # "enrutamiento": {
            #     "tipo": "rip",
            #     "network": ["172.16.1.0", "172.16.2.0", "172.16.3.0", "10.0.0.0"]
            # }
            # ENRUTAMIENTO RIP V2


            "enrutamiento": {
                "tipo": "ripv2",
                "network": ["172.16.1.0", "10.0.0.0"]
            }
            # ENRUTAMIENTO EIGRP
            # "enrutamiento": {
            #     "tipo": "eigrp",
            #     "as": 100, #numero sistema autonomo
            #     "network": ["192.168.1.0", "10.0.0.0"]
            # }
            # ENRUTAMIENTO OSPF
            # "enrutamiento": {
            #     "tipo": "ospf",
            #     "process_id": 1,
            #     "networks": [
            #         {"red": "192.168.1.0", "wildcard": "0.0.0.255"},
            #         {"red": "10.0.0.0", "wildcard": "0.0.0.3"}
            #     ]
            # }
        }
    ],

    "pds": [
        {"nombre": "PD1", "x": 0, "y": 0},
        {"nombre": "PD2", "x": 50, "y": 0}
    ],

    "links": [
        {"from": "PC1", "to": "SW1", "from_port": "FastEthernet0", "to_port": "FastEthernet0/1", "tipo": "straight"},
        {"from": "PC2", "to": "SW1", "from_port": "FastEthernet0", "to_port": "FastEthernet0/2", "tipo": "straight"},
        {"from": "PC3", "to": "SW2", "from_port": "FastEthernet0", "to_port": "FastEthernet0/1", "tipo": "straight"},
        {"from": "PC4", "to": "SW2", "from_port": "FastEthernet0", "to_port": "FastEthernet0/2", "tipo": "straight"},
        {"from": "R1", "to": "SW1", "from_port": "GigabitEthernet0/0", "to_port": "FastEthernet0/24", "tipo": "straight"},
        {"from": "R2", "to": "SW2", "from_port": "GigabitEthernet0/0", "to_port": "FastEthernet0/24", "tipo": "straight"},
        {"from": "R1", "to": "R2", "from_port": "Serial9/0", "to_port": "Serial9/0", "tipo": "serial"}
    ]
}

gen = GeneradorTopologia(datos)
xml = gen.generar()

with open("topologia.xml", "w") as f:
    f.write(xml)

print("XML generado correctamente")