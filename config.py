"""
Configuración centralizada de estilos y constantes de la aplicación.
Diseño profesional oscuro para dashboard financiero.
"""

import streamlit as st

def configurar_pagina():
    """Configura el diseño general de la página Streamlit."""
    st.set_page_config(
        page_title="Dashboard Financiero Pro",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Inyectar CSS personalizado para diseño oscuro y profesional
    st.markdown("""
        <style>
        /* Fondo principal oscuro */
        .stApp {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f1f5f9;
        }
        
        /* Encabezados */
        h1, h2, h3, h4, h5, h6 {
            color: #f8fafc !important;
            font-weight: 600 !important;
        }
        
        /* Contenedores de tarjetas */
        .card {
            background: rgba(30, 41, 59, 0.9);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #334155;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
        }
        
        /* Tablas estilizadas */
        .dataframe {
            background-color: #1e293b !important;
            color: #cbd5e1 !important;
        }
        
        .dataframe th {
            background-color: #0f172a !important;
            color: #e2e8f0 !important;
            font-weight: 600 !important;
            padding: 12px !important;
        }
        
        .dataframe td {
            padding: 10px !important;
            border-bottom: 1px solid #334155 !important;
        }
        
        .dataframe tr:hover {
            background-color: #2d3748 !important;
        }
        
        /* Botones modernos */
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
        }
        
        /* Menú de navegación superior fijo */
        .nav-bar {
            position: sticky;
            top: 0;
            z-index: 1000;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid #334155;
            padding: 12px 0;
            margin-bottom: 30px;
        }
        
        .nav-button {
            display: inline-block;
            margin: 0 10px;
            padding: 10px 24px;
            border-radius: 8px;
            background: transparent;
            color: #cbd5e1;
            border: 1px solid #475569;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
        }
        
        .nav-button:hover {
            background: rgba(59, 130, 246, 0.1);
            color: #60a5fa;
            border-color: #3b82f6;
        }
        
        .nav-button.active {
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            color: white;
            border-color: #3b82f6;
        }
        
        /* Campos de formulario */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input {
            background-color: #1e293b !important;
            color: #f1f5f9 !important;
            border: 1px solid #475569 !important;
            border-radius: 8px !important;
        }
        
        /* Selectores y dropdowns */
        .stSelectbox > div > div {
            background-color: #1e293b !important;
            color: #f1f5f9 !important;
            border: 1px solid #475569 !important;
            border-radius: 8px !important;
        }
        
        /* Spinners y animaciones */
        .stSpinner > div {
            border-color: #3b82f6 transparent transparent transparent !important;
        }
        
        /* Alertas y mensajes */
        .stAlert {
            border-radius: 10px;
            border: none !important;
        }
        
        /* Scrollbar personalizada */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1e293b;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }
        </style>
    """, unsafe_allow_html=True)

def aplicar_estilo_tabla(df, tipo="default"):
    """
    Aplica estilos profesionales a DataFrames de pandas.
    
    Args:
        df: DataFrame de pandas
        tipo: "fondos", "acciones", o "default"
    
    Returns:
        DataFrame estilizado
    """
    def formatear_moneda(val):
        if isinstance(val, (int, float)):
            return f"€{val:,.2f}"
        return val
    
    def formatear_porcentaje(val):
        if isinstance(val, (int, float)):
            color = "red" if val < 0 else "green"
            return f'<span style="color: {color}">{val:+.2f}%</span>'
        return val
    
    def formatear_cambio(val):
        if isinstance(val, (int, float)):
            color = "red" if val < 0 else "green"
            simbolo = "▼" if val < 0 else "▲"
            return f'<span style="color: {color}">{simbolo} {abs(val):.2f}%</span>'
        return val
    
    # Copiar el DataFrame para no modificar el original
    df_estilizado = df.copy()
    
    # Aplicar formatos según el tipo de tabla
    if tipo == "fondos":
        columnas_moneda = ["Valor de compra", "Valor actual", "Ganancias/pérdidas totales (€)", "Total invertido", "Valor actual total"]
        columnas_porcentaje = ["Cambio diario (%)", "Cambio YTD (%)", "Ganancias/pérdidas totales (%)"]
        
    elif tipo == "acciones":
        columnas_moneda = ["Precio de compra", "Valor actual", "Ganancias/pérdidas (€)", "Total invertido", "Valor actual total"]
        columnas_porcentaje = ["Cambio diario (%)", "Cambio YTD (%)", "Ganancias/pérdidas (%)"]
    
    else:
        columnas_moneda = []
        columnas_porcentaje = []
    
    # Aplicar formatos
    for col in columnas_moneda:
        if col in df_estilizado.columns:
            df_estilizado[col] = df_estilizado[col].apply(formatear_moneda)
    
    for col in columnas_porcentaje:
        if col in df_estilizado.columns:
            if "Cambio diario" in col:
                df_estilizado[col] = df_estilizado[col].apply(formatear_cambio)
            else:
                df_estilizado[col] = df_estilizado[col].apply(formatear_porcentaje)
    
    return df_estilizado

COLORES_GRAFICOS = {
    "fondos": ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ef4444", "#06b6d4"],
    "acciones": ["#6366f1", "#ec4899", "#14b8a6", "#f97316", "#84cc16", "#a855f7"],
    "RF": "#10b981",  # Renta Fija - Verde
    "RV": "#ef4444",  # Renta Variable - Rojo/Naranja
}
