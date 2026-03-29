
# =============================================================================
# MÓDULO 3: BÚSQUEDA HEURÍSTICA 
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

