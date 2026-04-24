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
        ## Datos de entrada
        self.datos = datos
        self.links = links
        self.ruta = ruta

        ##
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

        t = {}
        for k, v in archivos.items():
            with open(f"{self.ruta}/core_xml/templates/{v}") as f:
                t[k] = f.read()
        return t

    # =========================
    # PCS
    # =========================
    def procesar_pcs(self):
        lista = []

        for pc in self.datos.get("pcs", []):
            obj = {
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

            obj["device_xml"] = self.templates["device_pc"].format(
                nombre=obj["nombre"],
                ip=obj["ip"],
                mask=obj["mask"],
                gw=obj["gw"],
                posX=obj["posX"],
                posY=obj["posY"],
                mac=obj["mac"],
                mac_ipv6=mac_a_ipv6_link_local(obj["mac"]),
                macBluetooth=obj["mac_bt"],
                macBluetoothAipv6=mac_a_ipv6_link_local(obj["mac_bt"]),
                uuidPC=obj["uuid"],
                uuid1=self.workspace["uuid1"],
                uuid2=self.workspace["uuid2"],
                uuid3=self.workspace["uuid3"],
                refId=obj["refId"],
                partialDuid=generar_partial_duid(),
                beaconUuid=generar_uuid()
            )

            self.dispositivos[obj["nombre"]] = obj
            lista.append(obj)

        return lista

    # =========================
    # SWITCHES
    # =========================
    def procesar_switches(self):
        lista = []

        for sw in self.datos.get("switches", []):
            obj = {
                "nombre": sw.get("nombre"),
                "posX": sw.get("x", 0),
                "posY": sw.get("y", 0),
                "ip": safe(sw.get("ip")),
                "mask": safe(sw.get("mask")),
                "gw": safe(sw.get("gw")),
                "uuid": generar_uuid(),
                "refId": sw.get("id"),
                "macBuildInAddr": generar_mac(),
            }

            obj["node_xml"] = self.templates["node_sw"].format(
                nombre=obj["nombre"], uuidSW=obj["uuid"]
            )

            device_xml = self.templates["device_sw"].format(
                nombre=obj["nombre"],
                ip=obj["ip"],
                mask=obj["mask"],
                gw=obj["gw"],
                posX=obj["posX"],
                posY=obj["posY"],
                macBuildInAddr=obj["macBuildInAddr"],
                uuidSW=obj["uuid"],
                uuid1=self.workspace["uuid1"],
                uuid2=self.workspace["uuid2"],
                uuid3=self.workspace["uuid3"],
                uuid4=self.workspace["uuid4"],
                uuidRack=self.workspace["uuidRack"],
                refId=obj["refId"],
                cantVlans=1,
                vlans_9="",
                vlans_11="",
                vlans_13="",
                vlans_6="",
                interfaces=""
            )

            obj["device_xml"] = reemplazar_macs_switch(device_xml)

            self.dispositivos[obj["nombre"]] = obj
            lista.append(obj)

        return lista

    # =========================
    # ROUTERS
    # =========================
    def generar_routing(self, router):
        r = router.get("enrutamiento") or {}   # 🔥 clave aquí
        rbp = router.get("rbp", False)

        if not r:
            return ""

        tipo = (r.get("tipo") or "").lower()
        redes = r.get("network", []) or []

        texto = ""

        # =====================
        # RIP
        # =====================
        if tipo in ["rip", "ripv2"]:
            texto += "      <LINE>router rip</LINE>\n"

            if tipo == "ripv2":
                texto += "      <LINE> version 2</LINE>\n"

            for net in redes:
                if net:
                    texto += f"      <LINE> network {net}</LINE>\n"

            if rbp:
                texto += "      <LINE> redistribute static</LINE>\n"

            texto += "      <LINE> no auto-summary</LINE>\n"
            texto += "      <LINE>!</LINE>\n"

        # =====================
        # EIGRP
        # =====================
        elif tipo == "eigrp":
            asn = r.get("as") or 1

            texto += f"      <LINE>router eigrp {asn}</LINE>\n"

            for net in redes:
                if net:
                    texto += f"      <LINE> network {net}</LINE>\n"

            if rbp:
                texto += "      <LINE> redistribute static</LINE>\n"

            texto += "      <LINE> no auto-summary</LINE>\n"
            texto += "      <LINE>!</LINE>\n"

        # =====================
        # OSPF
        # =====================
        elif tipo == "ospf":
            process_id = r.get("process_id") or 1
            texto += f"      <LINE>router ospf {process_id}</LINE>\n"
            for net in r.get("networks", []) or []:
                red = net.get("red")
                wc = net.get("wildcard")
                if red and wc:
                    texto += f"      <LINE> network {red} {wc} area 0</LINE>\n"
            if rbp:
                texto += "      <LINE> redistribute static</LINE>\n"
            texto += "      <LINE>!</LINE>\n"
        return texto

    def procesar_routers(self):
        lista = []
        for r in self.datos.get("routers", []):
            rbp_line = ""
            if r.get("rbp"):
                rbp_line = "      <LINE>ip route 0.0.0.0 0.0.0.0 Serial9/0</LINE>\n"
            config = self.templates["config_router"].format(
                nombre=r.get("nombre"),
                interfacesRouter="",
                protocoloEnrutamiento=self.generar_routing(r),
                rbp=rbp_line
            )
            obj = {
                "nombre": r.get("nombre"),
                "posX": r.get("x", 0),
                "posY": r.get("y", 0),
                "uuid": generar_uuid(),
                "refId": r.get(id),
                "macBuildInAddr": generar_mac(),
            }
            obj["node_xml"] = self.templates["node_router"].format(
                nombre=obj["nombre"], uuidR=obj["uuid"]
            )
            obj["device_xml"] = self.templates["device_router"].format(
                nombre=obj["nombre"],
                posX=obj["posX"],
                posY=obj["posY"],
                macBuildInAddr=obj["macBuildInAddr"],
                refId=obj["refId"],
                uuidR=obj["uuid"],
                uuid1=self.workspace["uuid1"],
                uuid2=self.workspace["uuid2"],
                uuid3=self.workspace["uuid3"],
                uuid4=self.workspace["uuid4"],
                uuidRack=self.workspace["uuidRack"],
                config=config,
                slot0="", slot1="", slot2="", slot3="",
                slot4="", slot5="", slot6="", slot7="",
                slot8="", slot9=""
            )
            self.dispositivos[obj["nombre"]] = obj
            lista.append(obj)

        return lista

    # =========================
    # LINKS
    # =========================
    def procesar_links(self):
        lista = []

        for link in self.datos.get("links", []):
            d1 = self.dispositivos.get(link.get("from"))
            d2 = self.dispositivos.get(link.get("to"))

            if not d1 or not d2:
                continue

            xml = self.templates["link_cobre"].format(
                origenRefId=d1["refId"],
                origenInterfaz=link.get("from_port"),
                destinoRefId=d2["refId"],
                destinoInterfaz=link.get("to_port"),
                tipoCable="eStraightThrough"
            )

            lista.append(xml)

        return lista

    # =========================
    # SCENARIOS
    # =========================
    def procesar_scenarios(self):
        pcs = [d for d in self.dispositivos.values() if d["nombre"].startswith("PC")]

        if len(pcs) < 2:
            return []

        pcs.sort(key=lambda x: int(x["nombre"].replace("PC", "")))
        origen = pcs[0]

        lista = []
        for d in pcs[1:]:
            xml = self.templates["scenario"].format(
                origenRefId=origen["refId"],
                destinoRefId=d["refId"],
                destinoIp=d.get("ip", ""),
                color=str(random.randint(-15000000, -100000))
            )
            lista.append(xml)

        return lista

    # =========================
    # GENERAR FINAL
    # =========================

    def generar_devices(self):
        pcs = self.procesar_pcs()
        sws = self.procesar_switches()
        routers = self.procesar_routers()

        return pcs + sws + routers

    def generar(self):

        pcs = self.procesar_pcs()
        sws = self.procesar_switches()
        routers = self.procesar_routers()
        links = self.procesar_links()
        scenarios = self.procesar_scenarios()

        return self.templates["main"].format(
            uuid1=self.workspace["uuid1"],
            uuid2=self.workspace["uuid2"],
            uuid3=self.workspace["uuid3"],
            uuid4=self.workspace["uuid4"],
            uuidRack=self.workspace["uuidRack"],
            devices="\n".join(d["device_xml"] for d in pcs+sws+routers),
            links="\n".join(links),
            nodes_pc="\n".join(d["node_xml"] for d in pcs),
            nodes_rack="\n".join(d["node_xml"] for d in sws+routers),
            scenarios="\n".join(scenarios)
        )

# =========================
# EJECUCIÓN
# =========================
if __name__ == "__main__":
    datos = {
    }
    gen = GeneradorTopologia(datos)
    xml = gen.generar()

    with open("topologia.xml", "w") as f:
        f.write(xml)

    print("XML generado correctamente")