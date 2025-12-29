"""
Módulo de lógica de negocio para fondos de inversión.
Incluye obtención de datos en tiempo real de Yahoo Finance.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import streamlit as st

class FondoManager:
    """Gestor de operaciones relacionadas con fondos de inversión."""
    
    def __init__(self, db_manager):
        """Inicializa el gestor de fondos."""
        self.db = db_manager
        self.cache = {}
    
    @st.cache_data(ttl=300)  # Cache de 5 minutos
    def obtener_datos_mercado(_self, ticker: str) -> Optional[Dict]:
        """
        Obtiene datos en tiempo real de Yahoo Finance para un ticker.
        
        Args:
            ticker: Símbolo del fondo en Yahoo Finance
        
        Returns:
            Diccionario con datos de mercado o None si hay error
        """
        try:
            fondo = yf.Ticker(ticker)
            
            # Obtener información básica
            info = fondo.info
            
            # Obtener datos históricos para YTD
            hoy = datetime.now()
            inicio_ano = datetime(hoy.year, 1, 1)
            historico = fondo.history(start=inicio_ano.strftime('%Y-%m-%d'), 
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
                'valor_actual': round(precio_actual, 2),
                'cambio_diario_eur': round(cambio_diario_eur, 2),
                'cambio_diario_pct': round(cambio_diario_pct, 2),
                'cambio_ytd_pct': round(cambio_ytd_pct, 2)
            }
            
        except Exception as e:
            print(f"Error al obtener datos para {ticker}: {e}")
            return None
    
    def calcular_metricas_fondo(self, fondo_data: Dict) -> Dict:
        """
        Calcula todas las métricas para un fondo.
        
        Args:
            fondo_data: Datos del fondo desde la base de datos
        
        Returns:
            Diccionario con todas las métricas calculadas
        """
        try:
            datos_mercado = self.obtener_datos_mercado(fondo_data['ticker'])
            
            if not datos_mercado:
                # Usar valores por defecto si no se pueden obtener datos
                datos_mercado = {
                    'valor_actual': fondo_data.get('valor_actual', 0),
                    'cambio_diario_eur': 0,
                    'cambio_diario_pct': 0,
                    'cambio_ytd_pct': 0
                }
            
            valor_compra = fondo_data.get('valor_compra', 0)
            cantidad = fondo_data.get('cantidad', 0)
            valor_actual = datos_mercado['valor_actual']
            
            # Cálculos de ganancias/pérdidas
            ganancia_total_eur = (valor_actual - valor_compra) * cantidad
            ganancia_total_pct = ((valor_actual - valor_compra) / valor_compra * 100) if valor_compra > 0 else 0
            
            total_invertido = valor_compra * cantidad
            valor_actual_total = valor_actual * cantidad
            
            return {
                **fondo_data,
                **datos_mercado,
                'ganancia_total_eur': round(ganancia_total_eur, 2),
                'ganancia_total_pct': round(ganancia_total_pct, 2),
                'total_invertido': round(total_invertido, 2),
                'valor_actual_total': round(valor_actual_total, 2)
            }
            
        except Exception as e:
            print(f"Error al calcular métricas para fondo {fondo_data.get('nombre', '')}: {e}")
            return fondo_data
    
    def obtener_todos_fondos_con_metricas(self) -> Tuple[List[Dict], Dict]:
        """
        Obtiene todos los fondos con sus métricas calculadas.
        
        Returns:
            Tuple: (lista de fondos, diccionario de totales)
        """
        fondos_db = self.db.obtener_fondos()
        fondos_calculados = []
        
        total_invertido = 0
        valor_actual_total = 0
        ganancia_total_eur = 0
        
        for fondo in fondos_db:
            fondo_con_metricas = self.calcular_metricas_fondo(fondo)
            fondos_calculados.append(fondo_con_metricas)
            
            # Acumular totales
            total_invertido += fondo_con_metricas.get('total_invertido', 0)
            valor_actual_total += fondo_con_metricas.get('valor_actual_total', 0)
            ganancia_total_eur += fondo_con_metricas.get('ganancia_total_eur', 0)
        
        # Calcular porcentaje total de ganancia
        ganancia_total_pct = (ganancia_total_eur / total_invertido * 100) if total_invertido > 0 else 0
        
        totales = {
            'total_invertido': round(total_invertido, 2),
            'valor_actual_total': round(valor_actual_total, 2),
            'ganancia_total_eur': round(ganancia_total_eur, 2),
            'ganancia_total_pct': round(ganancia_total_pct, 2)
        }
        
        return fondos_calculados, totales
    
    def crear_dataframe_fondos(self, fondos: List[Dict], totales: Dict) -> pd.DataFrame:
        """
        Crea un DataFrame de pandas con formato para visualización.
        
        Args:
            fondos: Lista de diccionarios con datos de fondos
            totales: Diccionario con totales agregados
        
        Returns:
            DataFrame formateado
        """
        if not fondos:
            return pd.DataFrame()
        
        # Crear lista de filas para el DataFrame
        filas = []
        
        for fondo in fondos:
            fila = {
                'ID': fondo.get('id', ''),
                'Nombre del fondo': fondo.get('nombre', ''),
                'Ticker': fondo.get('ticker', ''),
                'Tipo de inversión': fondo.get('tipo_inversion', ''),
                'Valor de compra': fondo.get('valor_compra', 0),
                'Cantidad invertida': fondo.get('cantidad', 0),
                'Valor actual': fondo.get('valor_actual', 0),
                'Cambio diario (€)': fondo.get('cambio_diario_eur', 0),
                'Cambio diario (%)': fondo.get('cambio_diario_pct', 0),
                'Cambio YTD (%)': fondo.get('cambio_ytd_pct', 0),
                'Ganancias/pérdidas totales (€)': fondo.get('ganancia_total_eur', 0),
                'Ganancias/pérdidas totales (%)': fondo.get('ganancia_total_pct', 0),
                'Fecha de compra': fondo.get('fecha_compra', ''),
                'Total invertido': fondo.get('total_invertido', 0),
                'Valor actual total': fondo.get('valor_actual_total', 0)
            }
            filas.append(fila)
        
        # Crear DataFrame
        df = pd.DataFrame(filas)
        
        # Añadir fila de totales
        if not df.empty:
            fila_totales = {
                'Nombre del fondo': '**TOTALES**',
                'Ticker': '',
                'Tipo de inversión': '',
                'Valor de compra': '',
                'Cantidad invertida': '',
                'Valor actual': '',
                'Cambio diario (€)': '',
                'Cambio diario (%)': '',
                'Cambio YTD (%)': '',
                'Ganancias/pérdidas totales (€)': totales['ganancia_total_eur'],
                'Ganancias/pérdidas totales (%)': totales['ganancia_total_pct'],
                'Fecha de compra': '',
                'Total invertido': totales['total_invertido'],
                'Valor actual total': totales['valor_actual_total']
            }
            
            # Crear un DataFrame para la fila de totales y concatenar
            df_totales = pd.DataFrame([fila_totales])
            df = pd.concat([df, df_totales], ignore_index=True)
        
        return df
