import { useState, useRef, useEffect } from 'react'
import './assets/main.css'
import logoImg from './assets/logoCp.png'

function App() {
  const [activeTab, setActiveTab] = useState('inicio')
  
  // Estados de datos base
  const [rutaCSV, setRutaCSV] = useState("")
  const [dispositivosConfirmados, setDispositivosConfirmados] = useState(false)
  const [consola, setConsola] = useState(["> AutoPKT Iniciado. Listo para operar."])
  const consolaRef = useRef(null)

  // Estados interactivos para la pestaña de Protocolos
  const [routersDisponibles, setRoutersDisponibles] = useState([])
  const [routersSeleccionados, setRoutersSeleccionados] = useState([])
  const [configuraciones, setConfiguraciones] = useState([]) 

  const log = (mensaje) => setConsola((prev) => [...prev, `> ${mensaje}`])

  useEffect(() => {
    if (consolaRef.current) consolaRef.current.scrollTop = consolaRef.current.scrollHeight
  }, [consola])

  // --- LOGICA DE BOTONES GLOBALES ---
  const handleCargarCSV = async () => {
    const archivo = await window.electron.ipcRenderer.invoke('abrir-archivo')
    if (archivo) {
      setRutaCSV(archivo)
      setDispositivosConfirmados(false)
      log(`CSV Cargado: ${archivo.split('\\').pop()}`)
    }
  }

 const handleConfirmarDispositivos = async () => {
    log("Enviando ruta real de topología al núcleo de Python...")
    try {
      // Usamos 127.0.0.1 que es 100% seguro contra bloqueos de Windows
      const res = await fetch('http://127.0.0.1:5000/api/cargar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ruta: rutaCSV }) 
      })
      const data = await res.json()
      
      setDispositivosConfirmados(true)
      setRoutersDisponibles(data.routers) 
      log(`Éxito: ${data.mensaje}`)
      
    } catch (error) {
      console.error(error) // Para ver el error real con F12 si falla
      log("Error Fatal: No se pudo contactar al servidor Python en 127.0.0.1.")
    }
  }

  const handleGenerarXML = async () => {
    log("Solicitando compilación final al servidor Python...")
    try {
      // En el futuro, Python tendrá esta ruta para exportar todo lo que tiene en memoria
      const res = await fetch('http://127.0.0.1:5000/api/exportar', {
        method: 'POST'
      })
      const data = await res.json()
      log(`Exportación: ${data.mensaje}`)
    } catch (error) {
      log("Error al intentar generar el archivo PKT.")
    }
  }

  // --- LÓGICA DE LA PESTAÑA DE PROTOCOLOS ---
  const toggleRouter = (router) => {
    if (routersSeleccionados.includes(router)) {
      setRoutersSeleccionados(routersSeleccionados.filter(r => r !== router))
    } else {
      setRoutersSeleccionados([...routersSeleccionados, router])
    }
  }

const aplicarProtocolo = async (protocolo) => {
    if (routersSeleccionados.length === 0) return log("Error: Selecciona al menos un router primero.")
    
    log(`Enviando configuración ${protocolo} al servidor...`)
    try {
      const res = await fetch('http://127.0.0.1:5000/api/protocolo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ protocolo: protocolo, routers: routersSeleccionados })
      })
      const data = await res.json()
      
      // Si Python responde OK, actualizamos la interfaz
      setConfiguraciones([...configuraciones, { protocolo, routers: routersSeleccionados }])
      setRoutersDisponibles(routersDisponibles.filter(r => !routersSeleccionados.includes(r)))
      setRoutersSeleccionados([]) 
      log(`Respuesta del servidor: ${data.mensaje}`)
    } catch (error) {
      log("Error: Falló la configuración de protocolos. ¿Python sigue vivo?")
    }
  }

  // --- RENDERIZADO DE LAS PESTAÑAS ---
  const renderTabContent = () => {
    switch (activeTab) {
      case 'inicio':
        return (
          <div className="tab-panel" style={{ borderTop: '4px solid var(--primary)' }}>
            <h2>Bienvenido a AutoPKT</h2>
            <p style={{color: 'var(--text-muted)'}}>Plataforma avanzada para la automatización y modelado de topologías de red en Packet Tracer. Sigue el flujo de trabajo en las pestañas superiores.</p>
            
            <div className="dashboard-grid">
              <div className="dash-card">
                <h3>1. Ingresa de Datos</h3>
                <p>Carga de archivos CSV generados por IA con dispositivos y conexiones físicas.</p>
              </div>
              <div className="dash-card">
                <h3>2. Lógica de Red</h3>
                <p>Cálculo de segmentos IP y aplicación dinámica de protocolos (OSPF, RIP, EIGRP).</p>
              </div>
              <div className="dash-card">
                <h3>3. Exportación</h3>
                <p>Compilación del árbol de datos en formato XML / .pkt nativo de Cisco.</p>
              </div>
            </div>
          </div>
        )
      case 'conexiones':
        return (
          <div className="tab-panel">
            <h2>Gestor de Topología Base</h2>
            <p style={{color: 'var(--text-muted)'}}>Selecciona el archivo que contiene la estructura física de la red.</p>
            <div className="controles-flex">
              <button className="btn btn-primary" onClick={handleCargarCSV}>📁 Buscar Archivo CSV</button>
              <div className="ruta-box">{rutaCSV || "Esperando archivo de topología..."}</div>
            </div>
            <button 
              className="btn btn-success" 
              disabled={!rutaCSV || dispositivosConfirmados} 
              onClick={handleConfirmarDispositivos}
            >
              ✅ Iniciar Análisis de Grafo
            </button>
          </div>
        )
      case 'ips':
        return (
          <div className="tab-panel">
            <h2>Asignación de Direccionamiento IP</h2>
            <p style={{color: 'var(--text-muted)'}}>El sistema calculará las subredes necesarias para los enlaces identificados.</p>
            <div style={{ background: 'var(--bg-app)', padding: '30px', borderRadius: '8px', border: '1px dashed var(--border)', textAlign: 'center' }}>
              <button className="btn btn-primary" style={{margin: '0 auto'}} disabled={!dispositivosConfirmados} onClick={() => log("Calculando subredes y asignando IPs a las interfaces...")}>
                Ejecutar Autoconfiguración de IPs
              </button>
            </div>
          </div>
        )
      case 'protocolos':
        return (
          <div className="tab-panel">
            <h2>Enrutamiento Dinámico por Zonas</h2>
            <p style={{color: 'var(--text-muted)'}}>Selecciona los routers que pertenecerán a una misma zona y aplica su protocolo correspondiente.</p>
            
            <h4 style={{marginBottom: '10px', color: 'var(--text-main)'}}>1. Selecciona Routers Disponibles:</h4>
            <div className="router-list">
              {routersDisponibles.length === 0 ? <span style={{color: 'var(--text-muted)', fontStyle: 'italic'}}>No hay routers disponibles para configurar. (Sube un CSV en 'Conexiones' y confírmalo).</span> : null}
              {routersDisponibles.map(router => (
                <div 
                  key={router} 
                  className={`router-item ${routersSeleccionados.includes(router) ? 'selected' : ''}`}
                  onClick={() => toggleRouter(router)}
                >
                  {router}
                </div>
              ))}
            </div>

            <h4 style={{marginBottom: '10px', color: 'var(--text-main)'}}>2. Aplicar Protocolo a la selección:</h4>
            <div style={{display: 'flex', gap: '10px', marginBottom: '25px'}}>
              <button className="btn btn-primary" disabled={routersSeleccionados.length === 0} onClick={() => aplicarProtocolo('OSPF')}>+ Asignar OSPF</button>
              <button className="btn btn-primary" disabled={routersSeleccionados.length === 0} onClick={() => aplicarProtocolo('RIP')}>+ Asignar RIP</button>
              <button className="btn btn-primary" disabled={routersSeleccionados.length === 0} onClick={() => aplicarProtocolo('EIGRP')}>+ Asignar EIGRP</button>
            </div>

            <h4 style={{marginBottom: '10px', color: 'var(--text-main)'}}>Zonas Configuradas:</h4>
            <div>
              {configuraciones.length === 0 ? <p style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>Aún no se han configurado protocolos.</p> : null}
              {configuraciones.map((conf, index) => (
                <div key={index} className="config-badge">
                  <strong>[Zona {conf.protocolo}]</strong>
                  <span>{conf.routers.join(', ')}</span>
                </div>
              ))}
            </div>
          </div>
        )
      case 'grafo':
        return (
          <div className="tab-panel">
            <h2>Renderizado y Exportación</h2>
            <div style={{width: '100%', height: '220px', background: 'var(--console-bg)', border: '1px solid var(--border)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', marginBottom: '15px'}}>
              [Lienzo Reservado para Renderizado de Grafo de Red]
            </div>
            <button className="btn btn-success" disabled={!dispositivosConfirmados} onClick={handleGenerarXML}>
              🚀 CONSTRUIR ARCHIVO PKT FINAL
            </button>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <>
      <nav className="topbar">
        <img src={logoImg} alt="LogoPkt.jpeg" style={{ height: '35px', width: 'auto' }} />
        <h1>AutoPKT</h1>
        <div className="tabs-container">
          <button className={`tab-btn ${activeTab === 'inicio' ? 'active' : ''}`} onClick={() => setActiveTab('inicio')}>Inicio</button>
          <button className={`tab-btn ${activeTab === 'conexiones' ? 'active' : ''}`} onClick={() => setActiveTab('conexiones')}>Conexiones</button>
          <button className={`tab-btn ${activeTab === 'ips' ? 'active' : ''}`} onClick={() => setActiveTab('ips')}>Asignar IPs</button>
          <button className={`tab-btn ${activeTab === 'protocolos' ? 'active' : ''}`} onClick={() => setActiveTab('protocolos')}>Protocolos</button>
          <button className={`tab-btn ${activeTab === 'grafo' ? 'active' : ''}`} onClick={() => setActiveTab('grafo')}>Ver Red</button>
        </div>
      </nav>

      <main className="main-content">
        <div style={{width: '100%', maxWidth: '850px', display: 'flex', flexDirection: 'column'}}>
          {renderTabContent()}
          <div className="consola-container" ref={consolaRef}>
            {consola.map((linea, index) => <div key={index}>{linea}</div>)}
          </div>
        </div>
      </main>
    </>
  )
}

export default App