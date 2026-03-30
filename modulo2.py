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