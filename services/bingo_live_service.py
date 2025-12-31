"""
Servicio de Bingo en Vivo
=========================
Maneja el estado de una jugada interactiva en tiempo real.
"""

import os
import glob
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple, Any


@dataclass
class Carton:
    """Representa un cartón individual."""
    bingo_id: str
    carton_tipo: str  # A, B, C, D, E, F
    numeros: Set[int]
    aciertos: Set[int] = field(default_factory=set)
    
    @property
    def cantidad_aciertos(self) -> int:
        return len(self.aciertos)
    
    @property
    def es_ganador(self) -> bool:
        return self.cantidad_aciertos >= 10
    
    @property
    def id_completo(self) -> str:
        return f"{self.bingo_id}-{self.carton_tipo}"
    
    def marcar_numero(self, numero: int) -> bool:
        """Marca un número si está en el cartón. Retorna True si hubo acierto."""
        if numero in self.numeros:
            self.aciertos.add(numero)
            return True
        return False
    
    def desmarcar_numero(self, numero: int) -> bool:
        """Desmarca un número. Retorna True si estaba marcado."""
        if numero in self.aciertos:
            self.aciertos.discard(numero)
            return True
        return False
    
    def to_dict(self) -> Dict:
        return {
            'bingo_id': self.bingo_id,
            'carton_tipo': self.carton_tipo,
            'id_completo': self.id_completo,
            'numeros': sorted(list(self.numeros)),
            'aciertos': sorted(list(self.aciertos)),
            'cantidad_aciertos': self.cantidad_aciertos,
            'es_ganador': self.es_ganador
        }


class EstadoJugada:
    """Mantiene el estado de una jugada en vivo."""
    
    def __init__(self, archivo_corel: str):
        self.archivo_corel = archivo_corel
        self.cartones: List[Carton] = []
        self.bolillas_cantadas: List[int] = []
        self.bolillas_disponibles: Set[int] = set(range(1, 61))
        self.ganadores: List[Carton] = []
        self.jugada_terminada: bool = False
        
        # Cargar cartones
        self._cargar_cartones()
    
    def _cargar_cartones(self):
        """Carga cartones desde archivo Corel."""
        df = pd.read_csv(self.archivo_corel, sep=';')
        
        tipos_carton = {
            'A': (1, 11),
            'B': (11, 21),
            'C': (21, 31),
            'D': (32, 42),
            'E': (42, 52),
            'F': (52, 62),
        }
        
        for _, fila in df.iterrows():
            bingo_id_1 = str(fila.iloc[0]).zfill(4)
            bingo_id_2 = str(fila.iloc[31]).zfill(4)
            
            for tipo in ['A', 'B', 'C']:
                inicio, fin = tipos_carton[tipo]
                numeros = set(int(x) for x in fila.iloc[inicio:fin])
                self.cartones.append(Carton(
                    bingo_id=bingo_id_1,
                    carton_tipo=tipo,
                    numeros=numeros
                ))
            
            for tipo in ['D', 'E', 'F']:
                inicio, fin = tipos_carton[tipo]
                numeros = set(int(x) for x in fila.iloc[inicio:fin])
                self.cartones.append(Carton(
                    bingo_id=bingo_id_2,
                    carton_tipo=tipo,
                    numeros=numeros
                ))
    
    def cantar_bolilla(self, numero: int) -> Dict[str, Any]:
        """
        Canta una bolilla y actualiza el estado.
        Retorna información sobre los aciertos y posibles ganadores.
        """
        if self.jugada_terminada:
            return {
                'exito': False,
                'mensaje': 'La jugada ya terminó',
                'hay_ganador': True
            }
        
        if numero not in self.bolillas_disponibles:
            return {
                'exito': False,
                'mensaje': f'Bolilla {numero} ya fue cantada',
                'hay_ganador': False
            }
        
        # Marcar bolilla como cantada
        self.bolillas_cantadas.append(numero)
        self.bolillas_disponibles.discard(numero)
        
        # Verificar aciertos en todos los cartones
        aciertos_nuevos = []
        for carton in self.cartones:
            if carton.marcar_numero(numero):
                aciertos_nuevos.append({
                    'carton': carton.id_completo,
                    'aciertos': carton.cantidad_aciertos
                })
                
                # Verificar si es ganador
                if carton.es_ganador and carton not in self.ganadores:
                    self.ganadores.append(carton)
        
        # Si hay ganadores, la jugada termina
        if self.ganadores:
            self.jugada_terminada = True
        
        return {
            'exito': True,
            'bolilla': numero,
            'total_cantadas': len(self.bolillas_cantadas),
            'aciertos_nuevos': aciertos_nuevos,
            'ranking_top20': self.obtener_ranking(20),
            'hay_ganador': len(self.ganadores) > 0,
            'ganadores': [g.to_dict() for g in self.ganadores]
        }
    
    def deshacer_bolilla(self) -> Dict[str, Any]:
        """Deshace la última bolilla cantada."""
        if not self.bolillas_cantadas:
            return {
                'exito': False,
                'mensaje': 'No hay bolillas para deshacer'
            }
        
        # Recuperar última bolilla
        ultima_bolilla = self.bolillas_cantadas.pop()
        self.bolillas_disponibles.add(ultima_bolilla)
        
        # Desmarcar en todos los cartones
        for carton in self.cartones:
            carton.desmarcar_numero(ultima_bolilla)
        
        # Limpiar ganadores si los había
        self.ganadores = [c for c in self.cartones if c.es_ganador]
        self.jugada_terminada = len(self.ganadores) > 0
        
        return {
            'exito': True,
            'bolilla_deshecha': ultima_bolilla,
            'total_cantadas': len(self.bolillas_cantadas),
            'ranking_top20': self.obtener_ranking(20),
            'hay_ganador': len(self.ganadores) > 0,
            'ganadores': [g.to_dict() for g in self.ganadores]
        }
    
    def obtener_ranking(self, top_n: int = 20) -> List[Dict]:
        """Obtiene los N cartones con más aciertos."""
        ordenados = sorted(
            self.cartones,
            key=lambda c: c.cantidad_aciertos,
            reverse=True
        )[:top_n]
        
        return [{
            'carton': c.id_completo,
            'bingo_id': c.bingo_id,
            'carton_tipo': c.carton_tipo,
            'aciertos': c.cantidad_aciertos,
            'es_ganador': c.es_ganador
        } for c in ordenados]
    
    def obtener_carton_detalle(self, bingo_id: str) -> List[Dict]:
        """Obtiene el detalle de los 3 cartones de un bingo específico."""
        cartones_bingo = [c for c in self.cartones if c.bingo_id == bingo_id]
        return [c.to_dict() for c in cartones_bingo]
    
    def obtener_estado(self) -> Dict[str, Any]:
        """Retorna el estado completo de la jugada."""
        return {
            'archivo': os.path.basename(self.archivo_corel),
            'total_cartones': len(self.cartones),
            'bolillas_cantadas': self.bolillas_cantadas,
            'bolillas_disponibles': sorted(list(self.bolillas_disponibles)),
            'total_cantadas': len(self.bolillas_cantadas),
            'ranking_top20': self.obtener_ranking(20),
            'jugada_terminada': self.jugada_terminada,
            'hay_ganador': len(self.ganadores) > 0,
            'ganadores': [g.to_dict() for g in self.ganadores]
        }
    
    def reiniciar(self):
        """Reinicia la jugada manteniendo los mismos cartones."""
        self.bolillas_cantadas = []
        self.bolillas_disponibles = set(range(1, 61))
        self.ganadores = []
        self.jugada_terminada = False
        
        # Limpiar aciertos de todos los cartones
        for carton in self.cartones:
            carton.aciertos = set()


# Almacén global de jugadas activas (en producción usar Redis o similar)
_jugadas_activas: Dict[str, EstadoJugada] = {}


def iniciar_jugada(archivo_corel: str, jugada_id: str = None) -> Tuple[str, Dict]:
    """Inicia una nueva jugada y retorna su ID."""
    if jugada_id is None:
        from datetime import datetime
        jugada_id = datetime.now().strftime('%Y%m%d%H%M%S')
    
    estado = EstadoJugada(archivo_corel)
    _jugadas_activas[jugada_id] = estado
    
    return jugada_id, estado.obtener_estado()


def obtener_jugada(jugada_id: str) -> Optional[EstadoJugada]:
    """Obtiene una jugada activa por su ID."""
    return _jugadas_activas.get(jugada_id)


def eliminar_jugada(jugada_id: str):
    """Elimina una jugada activa."""
    if jugada_id in _jugadas_activas:
        del _jugadas_activas[jugada_id]


def buscar_archivo_corel(carpeta_bingos: str = 'bingos') -> Optional[str]:
    """Busca el archivo Corel más reciente."""
    archivos_corel = []
    
    patron_bingos = os.path.join(carpeta_bingos, '*', '*_corel.csv')
    archivos_corel.extend(glob.glob(patron_bingos))
    archivos_corel.extend(glob.glob('*_corel.csv'))
    
    if not archivos_corel:
        return None
    
    archivos_corel.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return archivos_corel[0]
