"""
Módulo de lógica de negocio para acciones.
Incluye obtención de datos en tiempo real de Yahoo Finance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import streamlit as st

class AccionManager:
    """Gestor de operaciones relacionadas con acciones."""
    
    def __init__(self, db_manager):
        """Inicializa el gestor de acciones."""
        self.db = db_manager
        self.cache = {}
    
    @st.cache_data(ttl=300)  # Cache de 5 minutos
    def obtener_datos_mercado(_self, ticker: str) -> Optional[Dict]:
        """
        Obtiene datos en tiempo real de Yahoo Finance para una acción.
        
        Args:
            ticker: Símbolo de la acción en Yahoo Finance
        
        Returns:
            Diccionario con datos de mercado o None si hay error
        """
        try:
            accion = yf.Ticker(ticker)
            
            # Obtener información básica
            info = accion.info
            
            # Obtener datos históricos para YTD
            hoy = datetime.now()
            inicio_ano = datetime(hoy.year, 1, 1)
            historico = accion.history(start=inicio_ano.strftime('%Y-%m-%d'), 
                                      end=hoy.strftime('%Y-%m-%d'))
            
            if historico.empty:
                return None
            
            # Calcular cambios
            precio_actual = info.get('regularMarketPrice', 
                                   info.get('currentPrice', 
                                          historico['Close'].iloc[-1] if not historico.empty else 0))
            
            precio_cierre_anterior = info.get('regularMarketPreviousClose', 
                                            historico['Close'].iloc[-2] if len(historico) > 1 else precio_actual)
            
            precio_inicio_ano = historico['Close'].iloc[0] if not historico.empty else precio_actual
            
            cambio_diario_pct = ((precio_actual - precio_cierre_anterior) / precio_cierre_anterior * 100) 
            cambio_diario_eur = precio_actual - precio_cierre_anterior
            
            cambio_ytd_pct = ((precio_actual - precio_inicio_ano) / precio_inicio_ano * 100) 
            
            return {
                'nombre': info.get('longName', ticker),
                'ticker': ticker,
                'sector': info.get('sector', 'No disponible'),
                'valor_actual': round(precio_actual, 2),
                'cambio_diario_eur': round(cambio_diario_eur, 2),
                'cambio_diario_pct': round(cambio_diario_pct, 2),
                'cambio_ytd_pct': round(cambio_ytd_pct, 2)
            }
            
        except Exception as e:
            print(f"Error al obtener datos para {ticker}: {e}")
            return None
    
    def calcular_metricas_accion(self, accion_data: Dict) -> Dict:
        """
        Calcula todas las métricas para una acción.
        
        Args:
            accion_data: Datos de la acción desde la base de datos
        
        Returns:
            Diccionario con todas las métricas calculadas
        """
        try:
            datos_mercado = self.obtener_datos_mercado(accion_data['ticker'])
            
            if not datos_mercado:
                # Usar valores por defecto si no se pueden obtener datos
                datos_mercado = {
                    'valor_actual': accion_data.get('valor_actual', 0),
                    'cambio_diario_eur': 0,
                    'cambio_diario_pct': 0,
                    'cambio_ytd_pct': 0,
                    'sector': 'No disponible'
                }
            
            precio_compra = accion_data.get('precio_compra', 0)
            num_acciones = accion_data.get('num_acciones', 0)
            valor_actual = datos_mercado['valor_actual']
            
            # Cálculos de ganancias/pérdidas
            ganancia_total_eur = (valor_actual - precio_compra) * num_acciones
            ganancia_total_pct = ((valor_actual - precio_compra) / precio_compra * 100) if precio_compra > 0 else 0
            
            total_invertido = precio_compra * num_acciones
            valor_actual_total = valor_actual * num_acciones
            
            return {
                **accion_data,
                **datos_mercado,
                'ganancia_total_eur': round(ganancia_total_eur, 2),
                'ganancia_total_pct': round(ganancia_total_pct, 2),
                'total_invertido': round(total_invertido, 2),
                'valor_actual_total': round(valor_actual_total, 2)
            }
            
        except Exception as e:
            print(f"Error al calcular métricas para acción {accion_data.get('ticker', '')}: {e}")
            return accion_data
    
    def obtener_todas_acciones_con_metricas(self) -> Tuple[List[Dict], Dict]:
        """
        Obtiene todas las acciones con sus métricas calculadas.
        
        Returns:
            Tuple: (lista de acciones, diccionario de totales)
        """
        acciones_db = self.db.obtener_acciones()
        acciones_calculadas = []
        
        total_invertido = 0
        valor_actual_total = 0
        ganancia_total_eur = 0
        
        for accion in acciones_db:
            accion_con_metricas = self.calcular_metricas_accion(accion)
            acciones_calculadas.append(accion_con_metricas)
            
            # Acumular totales
            total_invertido += accion_con_metricas.get('total_invertido', 0)
            valor_actual_total += accion_con_metricas.get('valor_actual_total', 0)
            ganancia_total_eur += accion_con_metricas.get('ganancia_total_eur', 0)
        
        # Calcular porcentaje total de ganancia
        ganancia_total_pct = (ganancia_total_eur / total_invertido * 100) if total_invertido > 0 else 0
        
        totales = {
            'total_invertido': round(total_invertido, 2),
            'valor_actual_total': round(valor_actual_total, 2),
            'ganancia_total_eur': round(ganancia_total_eur, 2),
            'ganancia_total_pct': round(ganancia_total_pct, 2)
        }
        
        return acciones_calculadas, totales
    
    def crear_dataframe_acciones(self, acciones: List[Dict], totales: Dict) -> pd.DataFrame:
        """
        Crea un DataFrame de pandas con formato para visualización.
        
        Args:
            acciones: Lista de diccionarios con datos de acciones
            totales: Diccionario con totales agregados
        
        Returns:
            DataFrame formateado
        """
        if not acciones:
            return pd.DataFrame()
        
        # Crear lista de filas para el DataFrame
        filas = []
        
        for accion in acciones:
            fila = {
                'ID': accion.get('id', ''),
                'Nombre': accion.get('nombre', ''),
                'Ticker': accion.get('ticker', ''),
                'Sector': accion.get('sector', 'No disponible'),
                'Precio de compra': accion.get('precio_compra', 0),
                'Número de acciones': accion.get('num_acciones', 0),
                'Valor actual': accion.get('valor_actual', 0),
                'Cambio diario (€)': accion.get('cambio_diario_eur', 0),
                'Cambio diario (%)': accion.get('cambio_diario_pct', 0),
                'Cambio YTD (%)': accion.get('cambio_ytd_pct', 0),
                'Ganancias/pérdidas (€)': accion.get('ganancia_total_eur', 0),
                'Ganancias/pérdidas (%)': accion.get('ganancia_total_pct', 0),
                'Fecha de compra': accion.get('fecha_compra', ''),
                'Total invertido': accion.get('total_invertido', 0),
                'Valor actual total': accion.get('valor_actual_total', 0)
            }
            filas.append(fila)
        
        # Crear DataFrame
        df = pd.DataFrame(filas)
        
        # Añadir fila de totales
        if not df.empty:
            fila_totales = {
                'Nombre': '**TOTALES**',
                'Ticker': '',
                'Sector': '',
                'Precio de compra': '',
                'Número de acciones': '',
                'Valor actual': '',
                'Cambio diario (€)': '',
                'Cambio diario (%)': '',
                'Cambio YTD (%)': '',
                'Ganancias/pérdidas (€)': totales['ganancia_total_eur'],
                'Ganancias/pérdidas (%)': totales['ganancia_total_pct'],
                'Fecha de compra': '',
                'Total invertido': totales['total_invertido'],
                'Valor actual total': totales['valor_actual_total']
            }
            
            # Crear un DataFrame para la fila de totales y concatenar
            df_totales = pd.DataFrame([fila_totales])
            df = pd.concat([df, df_totales], ignore_index=True)
        
        return df
