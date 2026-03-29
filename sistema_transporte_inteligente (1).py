"""
=============================================================================
SISTEMA INTELIGENTE DE RUTAS - TRANSMILENIO BOGOTÁ
=============================================================================
Basado en:
  - Capítulo 2: Lógica y Representación del Conocimiento
  - Capítulo 3: Sistemas Basados en Reglas
  - Capítulo 9: Técnicas Basadas en Búsquedas Heurísticas
  Benítez, R. (2014). Inteligencia artificial avanzada. Barcelona: Editorial UOC.

=============================================================================
"""

import heapq
import math
from typing import Optional


# =============================================================================
# MÓDULO 1: BASE DE CONOCIMIENTO (Cap. 2 - Lógica y Representación)
# =============================================================================
# Representación del mundo mediante:
#   - Hechos (facts): afirmaciones sobre el estado del mundo
#   - Reglas (rules): si <condición> entonces <conclusión>
#   - Ontología: estructura de conceptos del dominio
# =============================================================================

class BaseConocimiento:
    """
    Representa el conocimiento del dominio usando:
    - Lógica proposicional para hechos simples
    - Lógica de predicados para relaciones entre estaciones
    - Reglas de producción del tipo IF-THEN
    """

    def __init__(self):
        # ----- HECHOS (Proposiciones sobre el mundo) -----
        # Formato: estación -> (latitud, longitud, troncal, características)
        self.estaciones = {
            # Troncal NQS (Norte-Quito-Sur)
            "Portal Sur":          (-4.68, -74.15, "NQS", {"portal": True,  "intercambiador": False}),
            "Autopista Sur 80":    (-4.61, -74.13, "NQS", {"portal": False, "intercambiador": False}),
            "Américas":            (-4.59, -74.11, "NQS", {"portal": False, "intercambiador": True}),
            "Bosa":                (-4.62, -74.18, "NQS", {"portal": False, "intercambiador": False}),

            # Troncal Caracas
            "Portal Usme":         (-4.72, -74.12, "Caracas", {"portal": True,  "intercambiador": False}),
            "Molinos":             (-4.66, -74.10, "Caracas", {"portal": False, "intercambiador": False}),
            "Ricaurte":            (-4.61, -74.09, "Caracas", {"portal": False, "intercambiador": True}),
            "La Sabana":           (-4.60, -74.08, "Caracas", {"portal": False, "intercambiador": True}),
            "Las Aguas":           (-4.59, -74.07, "Caracas", {"portal": False, "intercambiador": False}),
            "Calle 45":            (-4.56, -74.07, "Caracas", {"portal": False, "intercambiador": False}),
            "Héroes":              (-4.54, -74.07, "Caracas", {"portal": False, "intercambiador": True}),
            "Calle 100":           (-4.50, -74.07, "Caracas", {"portal": False, "intercambiador": True}),
            "Portal Norte":        (-4.43, -74.07, "Caracas", {"portal": True,  "intercambiador": False}),

            # Troncal Calle 80
            "Portal 80":           (-4.57, -74.17, "Calle80", {"portal": True,  "intercambiador": False}),
            "Granja Carrera 77":   (-4.57, -74.12, "Calle80", {"portal": False, "intercambiador": False}),
            "Minuto de Dios":      (-4.57, -74.10, "Calle80", {"portal": False, "intercambiador": False}),
            "Ferias":              (-4.57, -74.08, "Calle80", {"portal": False, "intercambiador": True}),

            # Estaciones centrales / intercambio
            "Av. Jiménez":         (-4.59, -74.07, "Multiple", {"portal": False, "intercambiador": True}),
            "Tercer Milenio":      (-4.60, -74.08, "Multiple", {"portal": False, "intercambiador": True}),
            "Universidades":       (-4.58, -74.07, "Multiple", {"portal": False, "intercambiador": True}),

            # Troncal Autonorte
            "Toberin":             (-4.46, -74.06, "Autonorte", {"portal": False, "intercambiador": False}),
            "Mazurén":             (-4.48, -74.06, "Autonorte", {"portal": False, "intercambiador": False}),
            "Cardio Infantil":     (-4.50, -74.06, "Autonorte", {"portal": False, "intercambiador": False}),
        }

        # ----- CONEXIONES (Grafo de conocimiento) -----
        # Formato: (estación_A, estación_B, tiempo_minutos, tipo_conexion)
        # El tiempo incluye: tiempo de viaje + tiempo promedio de espera
        self.conexiones_raw = [
            # Troncal Caracas (línea principal)
            ("Portal Usme",    "Molinos",      8,  "troncal"),
            ("Molinos",        "Ricaurte",     10, "troncal"),
            ("Ricaurte",       "La Sabana",    3,  "troncal"),
            ("La Sabana",      "Tercer Milenio", 2, "troncal"),
            ("Tercer Milenio", "Av. Jiménez",  2,  "troncal"),
            ("Av. Jiménez",    "Las Aguas",    2,  "troncal"),
            ("Las Aguas",      "Universidades",2,  "troncal"),
            ("Universidades",  "Calle 45",     5,  "troncal"),
            ("Calle 45",       "Héroes",       5,  "troncal"),
            ("Héroes",         "Calle 100",    8,  "troncal"),
            ("Calle 100",      "Portal Norte", 15, "troncal"),

            # Troncal NQS
            ("Portal Sur",     "Autopista Sur 80", 10, "troncal"),
            ("Autopista Sur 80","Américas",    8,  "troncal"),
            ("Américas",       "Ricaurte",     5,  "troncal"),
            ("Bosa",           "Américas",     12, "troncal"),

            # Troncal Calle 80
            ("Portal 80",      "Granja Carrera 77", 8, "troncal"),
            ("Granja Carrera 77","Minuto de Dios",   5, "troncal"),
            ("Minuto de Dios", "Ferias",       4,  "troncal"),
            ("Ferias",         "Héroes",       5,  "troncal"),

            # Troncal Autonorte
            ("Calle 100",      "Cardio Infantil", 4, "troncal"),
            ("Cardio Infantil","Mazurén",      4,  "troncal"),
            ("Mazurén",        "Toberin",      4,  "troncal"),

            # Transbordos (conexiones entre troncales en estaciones intercambiadoras)
            ("Ricaurte",       "La Sabana",    2,  "transbordo"),
            ("Héroes",         "Ferias",       3,  "transbordo"),
            ("Calle 100",      "Cardio Infantil", 3, "transbordo"),
            ("Av. Jiménez",    "Tercer Milenio", 2, "transbordo"),
            ("Américas",       "Bosa",         5,  "transbordo"),
        ]

        # Construir grafo bidireccional
        self.grafo = {}
        for est in self.estaciones:
            self.grafo[est] = []

        for a, b, t, tipo in self.conexiones_raw:
            self.grafo[a].append((b, t, tipo))
            self.grafo[b].append((a, t, tipo))  # bidireccional

        # ----- HECHOS DINÁMICOS (estado actual del sistema) -----
        self.hechos = {
            "hora_pico": False,
            "estaciones_cerradas": [],
            "congestiones": {},  # estación -> nivel (1-3)
            "clima_adverso": False,
        }

    def agregar_hecho(self, clave: str, valor):
        """Agrega un hecho dinámico a la base de conocimiento."""
        self.hechos[clave] = valor
        print(f"  [BC] Hecho registrado: {clave} = {valor}")

    def consultar_hecho(self, clave: str):
        """Consulta un hecho de la base de conocimiento."""
        return self.hechos.get(clave)

    def obtener_vecinos(self, estacion: str):
        """Retorna las estaciones conectadas (vecinos en el grafo)."""
        return self.grafo.get(estacion, [])

    def es_intercambiador(self, estacion: str) -> bool:
        """Predicado lógico: ¿la estación es intercambiadora?"""
        if estacion in self.estaciones:
            return self.estaciones[estacion][3].get("intercambiador", False)
        return False

    def es_portal(self, estacion: str) -> bool:
        """Predicado lógico: ¿la estación es un portal?"""
        if estacion in self.estaciones:
            return self.estaciones[estacion][3].get("portal", False)
        return False

    def coordenadas(self, estacion: str) -> tuple:
        """Retorna (lat, lon) de una estación."""
        if estacion in self.estaciones:
            lat, lon = self.estaciones[estacion][0], self.estaciones[estacion][1]
            return (lat, lon)
        return (0, 0)


# =============================================================================
# MÓDULO 2: MOTOR DE REGLAS (Cap. 3 - Sistemas Basados en Reglas)
# =============================================================================
# Sistema de producción con:
#   - Reglas IF-THEN en lenguaje natural + implementación
#   - Encadenamiento hacia adelante (forward chaining)
#   - Ciclo: Reconocimiento → Resolución de conflictos → Actuación
# =============================================================================

class Regla:
    """Representa una regla de producción IF <condicion> THEN <accion>."""

    def __init__(self, nombre: str, condicion, accion, prioridad: int = 1):
        self.nombre = nombre
        self.condicion = condicion   # función que evalúa la condición
        self.accion = accion         # función que ejecuta la acción
        self.prioridad = prioridad   # para resolución de conflictos

    def __repr__(self):
        return f"Regla('{self.nombre}', prioridad={self.prioridad})"


class MotorReglas:
    """
    Motor de inferencia con encadenamiento hacia adelante.

    Ciclo de razonamiento (según Benítez Cap. 3):
    1. RECONOCIMIENTO: evalúa qué reglas aplican sobre los hechos actuales
    2. RESOLUCIÓN DE CONFLICTOS: selecciona la regla de mayor prioridad
    3. ACTUACIÓN: ejecuta la regla seleccionada y actualiza hechos
    """

    def __init__(self, base_conocimiento: BaseConocimiento):
        self.bc = base_conocimiento
        self.memoria_trabajo = {}   # hechos + conclusiones derivadas
        self.reglas = []
        self._registrar_reglas()
        self.ajuste_tiempo = 1.0    # factor multiplicador de tiempo
        self.recomendaciones = []

    def _registrar_reglas(self):
        """
        Define las reglas de producción del dominio.
        Notación formal: REGLA_i: Si <P1 ∧ P2 ∧ ...> ENTONCES <Q>
        """

        # REGLA 1: Hora pico → penalizar tiempo de viaje
        self.reglas.append(Regla(
            nombre="R1_HoraPico",
            condicion=lambda bc: bc.consultar_hecho("hora_pico") is True,
            accion=self._accion_hora_pico,
            prioridad=3
        ))

        # REGLA 2: Estación cerrada → bloquear nodo en grafo
        self.reglas.append(Regla(
            nombre="R2_EstacionCerrada",
            condicion=lambda bc: len(bc.consultar_hecho("estaciones_cerradas") or []) > 0,
            accion=self._accion_estacion_cerrada,
            prioridad=5   # máxima prioridad (seguridad)
        ))

        # REGLA 3: Congestión → penalizar estaciones congestionadas
        self.reglas.append(Regla(
            nombre="R3_Congestion",
            condicion=lambda bc: len(bc.consultar_hecho("congestiones") or {}) > 0,
            accion=self._accion_congestion,
            prioridad=2
        ))

        # REGLA 4: Clima adverso → recomendar portal más cercano
        self.reglas.append(Regla(
            nombre="R4_ClimaAdverso",
            condicion=lambda bc: bc.consultar_hecho("clima_adverso") is True,
            accion=self._accion_clima,
            prioridad=2
        ))

        # REGLA 5: Ruta con transbordo → alertar al usuario
        self.reglas.append(Regla(
            nombre="R5_Transbordo",
            condicion=lambda bc: self.memoria_trabajo.get("requiere_transbordo", False),
            accion=self._accion_transbordo,
            prioridad=1
        ))

    def _accion_hora_pico(self):
        self.ajuste_tiempo = 1.4
        self.recomendaciones.append("⚠️  Hora pico detectada: tiempos incrementados 40%.")
        self.memoria_trabajo["hora_pico_aplicada"] = True

    def _accion_estacion_cerrada(self):
        cerradas = self.bc.consultar_hecho("estaciones_cerradas")
        for est in cerradas:
            # Eliminar del grafo temporalmente
            self.memoria_trabajo[f"bloqueada_{est}"] = True
        self.recomendaciones.append(
            f"🚫 Estaciones cerradas: {', '.join(cerradas)}. Ruta alternativa calculada."
        )

    def _accion_congestion(self):
        congest = self.bc.consultar_hecho("congestiones")
        for est, nivel in congest.items():
            penalizacion = nivel * 3   # +3 min por nivel de congestión
            self.memoria_trabajo[f"penalizacion_{est}"] = penalizacion
        self.recomendaciones.append(
            f"🚌 Congestión en {len(congest)} estación(es). Tiempos ajustados."
        )

    def _accion_clima(self):
        self.recomendaciones.append(
            "🌧️  Clima adverso: se recomienda usar portales con cubierta."
        )

    def _accion_transbordo(self):
        self.recomendaciones.append(
            "🔄 La ruta requiere transbordo. Tiempo adicional incluido."
        )

    def ejecutar(self) -> dict:
        """
        Ciclo de encadenamiento hacia adelante.
        Retorna el contexto derivado para el módulo de búsqueda.
        """
        print("\n" + "="*60)
        print("  MOTOR DE REGLAS — Encadenamiento Hacia Adelante")
        print("="*60)

        reglas_aplicables = []

        # FASE 1: RECONOCIMIENTO — ¿Qué reglas se disparan?
        for regla in self.reglas:
            try:
                if regla.condicion(self.bc):
                    reglas_aplicables.append(regla)
                    print(f"  ✓ Regla disparada: {regla.nombre}")
            except Exception:
                pass

        if not reglas_aplicables:
            print("  → No se disparó ninguna regla. Condiciones normales.")

        # FASE 2: RESOLUCIÓN DE CONFLICTOS — ordenar por prioridad (mayor = primero)
        reglas_aplicables.sort(key=lambda r: r.prioridad, reverse=True)

        # FASE 3: ACTUACIÓN — ejecutar cada regla seleccionada
        for regla in reglas_aplicables:
            regla.accion()

        return {
            "ajuste_tiempo": self.ajuste_tiempo,
            "memoria_trabajo": self.memoria_trabajo,
            "recomendaciones": self.recomendaciones,
        }

    def estacion_bloqueada(self, estacion: str) -> bool:
        """Verifica si una estación fue bloqueada por alguna regla."""
        return self.memoria_trabajo.get(f"bloqueada_{estacion}", False)

    def penalizacion(self, estacion: str) -> float:
        """Retorna la penalización en minutos para una estación."""
        return self.memoria_trabajo.get(f"penalizacion_{estacion}", 0)


# =============================================================================
# MÓDULO 3: BÚSQUEDA HEURÍSTICA A* (Cap. 9 - Técnicas Heurísticas)
# =============================================================================
# Algoritmo A* con función de evaluación: f(n) = g(n) + h(n)
#   - g(n): costo real acumulado desde el origen
#   - h(n): heurística admisible (distancia geográfica al destino)
#   - f(n): estimación del costo total de la ruta pasando por n
#
# Propiedades (Benítez Cap. 9):
#   - Completo: siempre encuentra solución si existe
#   - Óptimo: si h(n) es admisible (nunca sobreestima)
#   - La heurística de distancia euclidiana es admisible porque
#     el tiempo de viaje real siempre es ≥ distancia / velocidad_max
# =============================================================================

class BuscadorHeuristico:
    """
    Implementa el algoritmo A* para encontrar la ruta óptima
    en la red de TransMilenio, combinando:
      - Costo real g(n): tiempo acumulado de viaje
      - Heurística h(n): distancia geográfica al destino
      - Ajustes del motor de reglas
    """

    VELOCIDAD_PROMEDIO_KMH = 25  # velocidad promedio TransMilenio

    def __init__(self, bc: BaseConocimiento, motor: MotorReglas):
        self.bc = bc
        self.motor = motor
        self.contexto = motor.memoria_trabajo

    def heuristica(self, estacion: str, destino: str) -> float:
        """
        h(n): Distancia geográfica euclidiana convertida a tiempo.
        Es ADMISIBLE porque nunca sobreestima el tiempo real.

        Fórmula: h = distancia_km / velocidad_max * 60  [minutos]
        """
        lat1, lon1 = self.bc.coordenadas(estacion)
        lat2, lon2 = self.bc.coordenadas(destino)

        # Distancia euclidiana en grados (~111 km por grado)
        d = math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111
        tiempo_heuristico = (d / self.VELOCIDAD_PROMEDIO_KMH) * 60
        return tiempo_heuristico

    def buscar(self, origen: str, destino: str) -> Optional[dict]:
        """
        Algoritmo A* — Búsqueda heurística óptima.

        Estructura de datos:
        - OPEN:   montículo mínimo con (f, g, estacion, camino)
        - CLOSED: conjunto de estaciones ya expandidas

        Condición de parada: estación expandida == destino
        """
        print("\n" + "="*60)
        print("  BÚSQUEDA HEURÍSTICA A*")
        print(f"  Origen:  {origen}")
        print(f"  Destino: {destino}")
        print("="*60)

        if origen not in self.bc.estaciones:
            print(f"  ERROR: '{origen}' no existe en la red.")
            return None
        if destino not in self.bc.estaciones:
            print(f"  ERROR: '{destino}' no existe en la red.")
            return None
        if origen == destino:
            return {"ruta": [origen], "tiempo": 0, "transbordos": 0}

        # Inicialización
        h_inicial = self.heuristica(origen, destino)
        # Formato nodo: (f, g, estacion_actual, camino, tipos_conexion, transbordos)
        open_list = [(h_inicial, 0, origen, [origen], [], 0)]
        closed_set = set()
        iteracion = 0

        while open_list:
            f, g, actual, camino, tipos, transbordos = heapq.heappop(open_list)
            iteracion += 1

            # Nodo ya expandido → saltar
            if actual in closed_set:
                continue

            closed_set.add(actual)
            print(f"  [{iteracion:02d}] Expandiendo: {actual:25s} | g={g:.1f}min | h={f-g:.1f}min | f={f:.1f}min")

            # ¿Llegamos al destino?
            if actual == destino:
                print(f"\n  ✅ Ruta encontrada en {iteracion} iteraciones.")
                return {
                    "ruta": camino,
                    "tiempo_total": round(g, 1),
                    "transbordos": transbordos,
                    "tipos_conexion": tipos,
                    "nodos_explorados": iteracion,
                }

            # Expandir vecinos
            for vecino, tiempo_base, tipo_conex in self.bc.obtener_vecinos(actual):

                # Verificar bloqueo por motor de reglas
                if self.motor.estacion_bloqueada(vecino):
                    continue
                if vecino in closed_set:
                    continue

                # Costo real: tiempo base + ajustes del motor de reglas
                t = tiempo_base * self.motor.ajuste_tiempo
                t += self.motor.penalizacion(vecino)

                # Penalización adicional si hay transbordo
                nuevo_transbordos = transbordos
                if tipo_conex == "transbordo":
                    t += 5  # +5 min por transbordo
                    nuevo_transbordos += 1

                g_nuevo = g + t
                h_nuevo = self.heuristica(vecino, destino)
                f_nuevo = g_nuevo + h_nuevo

                heapq.heappush(open_list, (
                    f_nuevo, g_nuevo, vecino,
                    camino + [vecino],
                    tipos + [tipo_conex],
                    nuevo_transbordos
                ))

        print("  ❌ No existe ruta entre las estaciones.")
        return None


# =============================================================================
# MÓDULO 4: INTERFAZ DEL SISTEMA EXPERTO
# =============================================================================

class SistemaTransporteInteligente:
    """
    Integra los tres módulos en un sistema experto completo:
    1. Base de Conocimiento (Cap. 2)
    2. Motor de Reglas      (Cap. 3)
    3. Búsqueda Heurística  (Cap. 9)
    """

    def __init__(self):
        print("╔══════════════════════════════════════════════════════════╗")
        print("║   SISTEMA INTELIGENTE DE RUTAS — TRANSMILENIO BOGOTÁ    ║")
        print("║   Basado en Benítez (2014) — IA Avanzada                ║")
        print("╚══════════════════════════════════════════════════════════╝\n")

        self.bc = BaseConocimiento()
        self.motor = MotorReglas(self.bc)
        self.buscador = None

    def configurar_contexto(self, hora_pico=False, cerradas=None,
                             congestiones=None, clima=False):
        """Carga hechos dinámicos en la base de conocimiento."""
        print("📋 Configurando contexto del sistema...\n")
        self.bc.agregar_hecho("hora_pico", hora_pico)
        self.bc.agregar_hecho("estaciones_cerradas", cerradas or [])
        self.bc.agregar_hecho("congestiones", congestiones or {})
        self.bc.agregar_hecho("clima_adverso", clima)

    def encontrar_ruta(self, origen: str, destino: str) -> dict:
        """
        Pipeline completo:
        1. Motor de reglas evalúa el contexto
        2. A* busca la ruta óptima con ajustes aplicados
        3. Se presenta el resultado al usuario
        """
        # Paso 1: Motor de reglas
        self.motor.ejecutar()

        # Paso 2: Marcar transbordo si aplica
        if len(self.motor.recomendaciones) > 0:
            self.motor.memoria_trabajo["requiere_transbordo"] = True

        # Paso 3: Búsqueda A*
        self.buscador = BuscadorHeuristico(self.bc, self.motor)
        resultado = self.buscador.buscar(origen, destino)

        if resultado:
            self._presentar_resultado(origen, destino, resultado)

        return resultado

    def _presentar_resultado(self, origen: str, destino: str, r: dict):
        """Presenta la ruta de forma legible."""
        print("\n" + "╔" + "═"*58 + "╗")
        print("║" + "  RESULTADO DE LA BÚSQUEDA".center(58) + "║")
        print("╚" + "═"*58 + "╝")

        print(f"\n  📍 Origen:  {origen}")
        print(f"  🏁 Destino: {destino}")
        print(f"  ⏱️  Tiempo estimado: {r['tiempo_total']} minutos")
        print(f"  🔄 Transbordos: {r['transbordos']}")
        print(f"  🔍 Nodos explorados por A*: {r['nodos_explorados']}")

        print(f"\n  {'RUTA ÓPTIMA':─^50}")
        ruta = r["ruta"]
        for i, est in enumerate(ruta):
            if i == 0:
                print(f"  🚏 [{i+1:02d}] {est}  ← INICIO")
            elif i == len(ruta) - 1:
                print(f"  🏁 [{i+1:02d}] {est}  ← DESTINO")
            else:
                tipo = r["tipos_conexion"][i-1] if i-1 < len(r["tipos_conexion"]) else ""
                icono = "🔄" if tipo == "transbordo" else "➡️ "
                print(f"  {icono} [{i+1:02d}] {est}")

        if self.motor.recomendaciones:
            print(f"\n  {'RECOMENDACIONES DEL SISTEMA':─^50}")
            for rec in self.motor.recomendaciones:
                print(f"  {rec}")

        print()


# =============================================================================
# MENÚ INTERACTIVO
# =============================================================================

def menu_interactivo():
    """Menú para elegir origen, destino y condiciones desde la terminal."""

    sistema = SistemaTransporteInteligente()
    estaciones = list(sistema.bc.estaciones.keys())

    while True:
        print("\n" + "═"*62)
        print("  MENÚ PRINCIPAL")
        print("═"*62)
        print("  Estaciones disponibles:\n")
        for i, est in enumerate(estaciones):
            portal = " [PORTAL]" if sistema.bc.es_portal(est) else ""
            inter  = " [intercambiador]" if sistema.bc.es_intercambiador(est) else ""
            print(f"  {i+1:2d}. {est}{portal}{inter}")

        print("\n" + "─"*62)

        # Seleccionar origen
        while True:
            try:
                op = input("\n  Escribe el NÚMERO de la estación ORIGEN (0 para salir): ")
                if op.strip() == "0":
                    print("\n  ¡Hasta luego!\n")
                    return
                idx = int(op) - 1
                if 0 <= idx < len(estaciones):
                    origen = estaciones[idx]
                    break
                else:
                    print("  ⚠  Número fuera de rango, intenta de nuevo.")
            except ValueError:
                print("  ⚠  Ingresa solo el número.")

        # Seleccionar destino
        while True:
            try:
                op = input(f"  Escribe el NÚMERO de la estación DESTINO (origen: {origen}): ")
                idx = int(op) - 1
                if 0 <= idx < len(estaciones):
                    destino = estaciones[idx]
                    if destino == origen:
                        print("  ⚠  El destino debe ser diferente al origen.")
                    else:
                        break
                else:
                    print("  ⚠  Número fuera de rango, intenta de nuevo.")
            except ValueError:
                print("  ⚠  Ingresa solo el número.")

        # Condiciones del contexto
        print("\n  ─── Condiciones del sistema (s = sí / Enter = no) ───")
        hora_pico = input("  ¿Es hora pico? (s/Enter): ").strip().lower() == "s"
        clima     = input("  ¿Clima adverso? (s/Enter): ").strip().lower() == "s"

        cerradas = []
        resp = input("  ¿Hay estaciones cerradas? (s/Enter): ").strip().lower()
        if resp == "s":
            print("  Estaciones disponibles para cerrar:")
            for i, est in enumerate(estaciones):
                print(f"    {i+1:2d}. {est}")
            nums = input("  Escribe los números separados por coma (ej: 3,7): ")
            for n in nums.split(","):
                try:
                    idx = int(n.strip()) - 1
                    if 0 <= idx < len(estaciones):
                        cerradas.append(estaciones[idx])
                except ValueError:
                    pass

        congestiones = {}
        resp = input("  ¿Hay congestión en alguna estación? (s/Enter): ").strip().lower()
        if resp == "s":
            print("  Estaciones disponibles:")
            for i, est in enumerate(estaciones):
                print(f"    {i+1:2d}. {est}")
            nums = input("  Escribe los números separados por coma: ")
            for n in nums.split(","):
                try:
                    idx = int(n.strip()) - 1
                    if 0 <= idx < len(estaciones):
                        congestiones[estaciones[idx]] = 2
                except ValueError:
                    pass

        # Ejecutar sistema
        sistema2 = SistemaTransporteInteligente()
        sistema2.configurar_contexto(
            hora_pico=hora_pico,
            cerradas=cerradas,
            congestiones=congestiones,
            clima=clima
        )
        sistema2.encontrar_ruta(origen, destino)

        continuar = input("\n  ¿Calcular otra ruta? (s/Enter para salir): ").strip().lower()
        if continuar != "s":
            print("\n  ¡Hasta luego!\n")
            break


if __name__ == "__main__":
    menu_interactivo()
