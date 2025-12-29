"""
Aplicación principal del Dashboard Financiero.
Implementa la navegación entre las 4 páginas requeridas.
"""

import streamlit as st
from config import configurar_pagina, aplicar_estilo_tabla, COLORES_GRAFICOS
from database import obtener_db_manager
from fondo_module import FondoManager
from accion_module import AccionManager
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

# Configurar página
configurar_pagina()

# Inicializar managers
try:
    db_manager = obtener_db_manager()
    fondo_manager = FondoManager(db_manager)
    accion_manager = AccionManager(db_manager)
except Exception as e:
    st.error(f"Error al inicializar la aplicación: {e}")
    st.stop()

def render_navegacion():
    """Renderiza el menú de navegación superior fijo."""
    st.markdown("""
        <div class="nav-bar">
            <center>
                <button class="nav-button" onclick="window.location.href='?page=fondos'">📊 Fondos de Inversión</button>
                <button class="nav-button" onclick="window.location.href='?page=acciones'">📈 Acciones</button>
                <button class="nav-button" onclick="window.location.href='?page=graficas_fondos'">📉 Gráficas de Fondos</button>
                <button class="nav-button" onclick="window.location.href='?page=graficas_acciones'">📊 Gráficas de Acciones</button>
            </center>
        </div>
        <script>
            // Resaltar la página activa
            const params = new URLSearchParams(window.location.search);
            const page = params.get('page') || 'fondos';
            const buttons = document.querySelectorAll('.nav-button');
            buttons.forEach(button => {
                if (button.textContent.includes(page.charAt(0).toUpperCase() + page.slice(1))) {
                    button.classList.add('active');
                }
            });
        </script>
    """, unsafe_allow_html=True)

def pagina_fondos():
    """Renderiza la página de Fondos de Inversión."""
    st.title("📊 Gestión de Fondos de Inversión")
    
    # Controles superiores
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Actualizar Datos", key="actualizar_fondos"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("➕ Añadir Fondo", key="añadir_fondo"):
            st.session_state.mostrar_formulario_fondo = True
    
    with col3:
        if st.button("📊 Ver Resumen", key="ver_resumen_fondos"):
            st.session_state.mostrar_resumen_fondos = not st.session_state.get('mostrar_resumen_fondos', False)
    
    # Formulario para añadir/editar fondo
    if st.session_state.get('mostrar_formulario_fondo', False):
        with st.form("formulario_fondo", clear_on_submit=True):
            st.subheader("➕ Añadir/Editar Fondo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre del Fondo", key="nombre_fondo")
                ticker = st.text_input("Ticker (Yahoo Finance)", key="ticker_fondo").upper()
                tipo_inversion = st.selectbox("Tipo de Inversión", ["RF", "RV"], key="tipo_fondo")
            
            with col2:
                valor_compra = st.number_input("Valor de Compra (€)", min_value=0.0, step=0.01, key="valor_fondo")
                cantidad = st.number_input("Cantidad", min_value=0.0, step=0.01, key="cantidad_fondo")
                fecha_compra = st.date_input("Fecha de Compra", key="fecha_fondo")
            
            col_submit1, col_submit2 = st.columns(2)
            with col_submit1:
                if st.form_submit_button("💾 Guardar Fondo"):
                    if nombre and ticker and valor_compra > 0:
                        fondo_data = {
                            'nombre': nombre,
                            'ticker': ticker,
                            'tipo_inversion': tipo_inversion,
                            'valor_compra': valor_compra,
                            'cantidad': cantidad,
                            'fecha_compra': fecha_compra.strftime('%Y-%m-%d')
                        }
                        
                        try:
                            db_manager.guardar_fondo(fondo_data)
                            st.success("✅ Fondo guardado correctamente")
                            st.session_state.mostrar_formulario_fondo = False
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al guardar: {e}")
                    else:
                        st.warning("⚠️ Por favor, completa todos los campos obligatorios")
            
            with col_submit2:
                if st.form_submit_button("❌ Cancelar"):
                    st.session_state.mostrar_formulario_fondo = False
                    st.rerun()
    
    # Obtener y mostrar datos
    fondos, totales = fondo_manager.obtener_todos_fondos_con_metricas()
    df_fondos = fondo_manager.crear_dataframe_fondos(fondos, totales)
    
    # Mostrar resumen si está activado
    if st.session_state.get('mostrar_resumen_fondos', False) and not df_fondos.empty:
        with st.expander("📊 Resumen de Fondos", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Total Invertido",
                    value=f"€{totales['total_invertido']:,.2f}"
                )
            
            with col2:
                st.metric(
                    label="Valor Actual Total",
                    value=f"€{totales['valor_actual_total']:,.2f}"
                )
            
            with col3:
                ganancia_color = "inverse" if totales['ganancia_total_eur'] < 0 else "normal"
                st.metric(
                    label="Ganancia/Pérdida Total",
                    value=f"€{totales['ganancia_total_eur']:,.2f}",
                    delta=f"{totales['ganancia_total_pct']:+.2f}%",
                    delta_color=ganancia_color
                )
    
    # Mostrar tabla de fondos
    if not df_fondos.empty:
        st.subheader("📋 Tabla de Fondos de Inversión")
        
        # Aplicar estilos a la tabla
        df_estilizado = aplicar_estilo_tabla(df_fondos, tipo="fondos")
        
        # Mostrar tabla con opciones de edición/eliminación
        st.dataframe(
            df_estilizado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Nombre del fondo": st.column_config.TextColumn("Fondo", width="large"),
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Tipo de inversión": st.column_config.TextColumn("Tipo", width="small"),
                "Valor de compra": st.column_config.NumberColumn("Compra", format="€%.2f"),
                "Cantidad invertida": st.column_config.NumberColumn("Cantidad", format="%.2f"),
                "Valor actual": st.column_config.NumberColumn("Actual", format="€%.2f"),
                "Cambio diario (%)": st.column_config.TextColumn("Diario %"),
                "Cambio YTD (%)": st.column_config.TextColumn("YTD %"),
                "Ganancias/pérdidas totales (%)": st.column_config.TextColumn("G/P %"),
                "Ganancias/pérdidas totales (€)": st.column_config.NumberColumn("G/P €", format="€%.2f"),
                "Fecha de compra": st.column_config.DateColumn("Fecha"),
                "Total invertido": st.column_config.NumberColumn("Total Inv.", format="€%.2f"),
                "Valor actual total": st.column_config.NumberColumn("Total Act.", format="€%.2f")
            }
        )
        
        # Controles para editar/eliminar
        st.subheader("⚙️ Gestión de Fondos")
        col_id, col_edit, col_delete = st.columns([2, 1, 1])
        
        with col_id:
            fondos_disponibles = [f"{f['id']}: {f['nombre']}" for f in fondos]
            if fondos_disponibles:
                fondo_seleccionado = st.selectbox(
                    "Seleccionar Fondo",
                    fondos_disponibles,
                    key="select_fondo"
                )
                
                if fondo_seleccionado:
                    fondo_id = int(fondo_seleccionado.split(":")[0])
                    
                    with col_edit:
                        if st.button("✏️ Editar", key="editar_fondo"):
                            st.session_state.fondo_a_editar = fondo_id
                            st.session_state.mostrar_formulario_fondo = True
                            st.rerun()
                    
                    with col_delete:
                        if st.button("🗑️ Eliminar", key="eliminar_fondo"):
                            if db_manager.eliminar_fondo(fondo_id):
                                st.success("✅ Fondo eliminado correctamente")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ Error al eliminar el fondo")
    else:
        st.info("ℹ️ No hay fondos registrados. Usa el botón 'Añadir Fondo' para comenzar.")

def pagina_acciones():
    """Renderiza la página de Acciones."""
    st.title("📈 Gestión de Acciones")
    
    # Controles superiores
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Actualizar Datos", key="actualizar_acciones"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("➕ Añadir Acción", key="añadir_accion"):
            st.session_state.mostrar_formulario_accion = True
    
    with col3:
        if st.button("📊 Ver Resumen", key="ver_resumen_acciones"):
            st.session_state.mostrar_resumen_acciones = not st.session_state.get('mostrar_resumen_acciones', False)
    
    # Formulario para añadir/editar acción
    if st.session_state.get('mostrar_formulario_accion', False):
        with st.form("formulario_accion", clear_on_submit=True):
            st.subheader("➕ Añadir/Editar Acción")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre de la Empresa", key="nombre_accion")
                ticker = st.text_input("Ticker (Yahoo Finance)", key="ticker_accion").upper()
                sector = st.text_input("Sector (opcional)", key="sector_accion")
            
            with col2:
                precio_compra = st.number_input("Precio de Compra (€)", min_value=0.0, step=0.01, key="precio_accion")
                num_acciones = st.number_input("Número de Acciones", min_value=0, step=1, key="num_acciones")
                fecha_compra = st.date_input("Fecha de Compra", key="fecha_accion")
            
            col_submit1, col_submit2 = st.columns(2)
            with col_submit1:
                if st.form_submit_button("💾 Guardar Acción"):
                    if nombre and ticker and precio_compra > 0:
                        accion_data = {
                            'nombre': nombre,
                            'ticker': ticker,
                            'sector': sector,
                            'precio_compra': precio_compra,
                            'num_acciones': num_acciones,
                            'fecha_compra': fecha_compra.strftime('%Y-%m-%d')
                        }
                        
                        try:
                            db_manager.guardar_accion(accion_data)
                            st.success("✅ Acción guardada correctamente")
                            st.session_state.mostrar_formulario_accion = False
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al guardar: {e}")
                    else:
                        st.warning("⚠️ Por favor, completa todos los campos obligatorios")
            
            with col_submit2:
                if st.form_submit_button("❌ Cancelar"):
                    st.session_state.mostrar_formulario_accion = False
                    st.rerun()
    
    # Obtener y mostrar datos
    acciones, totales = accion_manager.obtener_todas_acciones_con_metricas()
    df_acciones = accion_manager.crear_dataframe_acciones(acciones, totales)
    
    # Mostrar resumen si está activado
    if st.session_state.get('mostrar_resumen_acciones', False) and not df_acciones.empty:
        with st.expander("📊 Resumen de Acciones", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Total Invertido",
                    value=f"€{totales['total_invertido']:,.2f}"
                )
            
            with col2:
                st.metric(
                    label="Valor Actual Total",
                    value=f"€{totales['valor_actual_total']:,.2f}"
                )
            
            with col3:
                ganancia_color = "inverse" if totales['ganancia_total_eur'] < 0 else "normal"
                st.metric(
                    label="Ganancia/Pérdida Total",
                    value=f"€{totales['ganancia_total_eur']:,.2f}",
                    delta=f"{totales['ganancia_total_pct']:+.2f}%",
                    delta_color=ganancia_color
                )
    
    # Mostrar tabla de acciones
    if not df_acciones.empty:
        st.subheader("📋 Tabla de Acciones")
        
        # Aplicar estilos a la tabla
        df_estilizado = aplicar_estilo_tabla(df_acciones, tipo="acciones")
        
        # Mostrar tabla
        st.dataframe(
            df_estilizado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Nombre": st.column_config.TextColumn("Empresa", width="large"),
                "Ticker": st.column_config.TextColumn("Ticker", width="small"),
                "Sector": st.column_config.TextColumn("Sector", width="medium"),
                "Precio de compra": st.column_config.NumberColumn("Compra", format="€%.2f"),
                "Número de acciones": st.column_config.NumberColumn("Cantidad", format="%d"),
                "Valor actual": st.column_config.NumberColumn("Actual", format="€%.2f"),
                "Cambio diario (%)": st.column_config.TextColumn("Diario %"),
                "Cambio YTD (%)": st.column_config.TextColumn("YTD %"),
                "Ganancias/pérdidas (%)": st.column_config.TextColumn("G/P %"),
                "Ganancias/pérdidas (€)": st.column_config.NumberColumn("G/P €", format="€%.2f"),
                "Fecha de compra": st.column_config.DateColumn("Fecha"),
                "Total invertido": st.column_config.NumberColumn("Total Inv.", format="€%.2f"),
                "Valor actual total": st.column_config.NumberColumn("Total Act.", format="€%.2f")
            }
        )
        
        # Controles para editar/eliminar
        st.subheader("⚙️ Gestión de Acciones")
        col_id, col_edit, col_delete = st.columns([2, 1, 1])
        
        with col_id:
            acciones_disponibles = [f"{a['id']}: {a['nombre']}" for a in acciones]
            if acciones_disponibles:
                accion_seleccionada = st.selectbox(
                    "Seleccionar Acción",
                    acciones_disponibles,
                    key="select_accion"
                )
                
                if accion_seleccionada:
                    accion_id = int(accion_seleccionada.split(":")[0])
                    
                    with col_edit:
                        if st.button("✏️ Editar", key="editar_accion"):
                            st.session_state.accion_a_editar = accion_id
                            st.session_state.mostrar_formulario_accion = True
                            st.rerun()
                    
                    with col_delete:
                        if st.button("🗑️ Eliminar", key="eliminar_accion"):
                            if db_manager.eliminar_accion(accion_id):
                                st.success("✅ Acción eliminada correctamente")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("❌ Error al eliminar la acción")
    else:
        st.info("ℹ️ No hay acciones registradas. Usa el botón 'Añadir Acción' para comenzar.")

def pagina_graficas_fondos():
    """Renderiza la página de gráficas de fondos."""
    st.title("📉 Análisis Visual de Fondos")
    
    # Obtener datos
    fondos, totales = fondo_manager.obtener_todos_fondos_con_metricas()
    
    if not fondos:
        st.info("ℹ️ No hay fondos registrados para mostrar gráficas.")
        return
    
    # Preparar datos para gráficas
    df_fondos = pd.DataFrame(fondos)
    
    # Colores personalizados
    colores_fondos = COLORES_GRAFICOS["fondos"]
    colores_tipos = {
        "RF": COLORES_GRAFICOS["RF"],
        "RV": COLORES_GRAFICOS["RV"]
    }
    
    # Gráfica 1: Distribución por fondo
    st.subheader("📊 Distribución por Fondo")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Crear gráfico de donut
        fig1 = go.Figure(data=[go.Pie(
            labels=df_fondos['nombre'],
            values=df_fondos['total_invertido'],
            hole=0.5,
            marker=dict(colors=colores_fondos[:len(df_fondos)]),
            textinfo='percent+label',
            textposition='inside',
            hovertemplate="<b>%{label}</b><br>" +
                         "Invertido: €%{value:,.2f}<br>" +
                         "Porcentaje: %{percent}<extra></extra>"
        )])
        
        fig1.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f8fafc',
            showlegend=False,
            height=500,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Mostrar tabla de resumen
        st.markdown("### Detalles por Fondo")
        resumen_df = df_fondos[['nombre', 'total_invertido', 'valor_actual_total', 'ganancia_total_pct']].copy()
        resumen_df['total_invertido'] = resumen_df['total_invertido'].apply(lambda x: f"€{x:,.2f}")
        resumen_df['valor_actual_total'] = resumen_df['valor_actual_total'].apply(lambda x: f"€{x:,.2f}")
        resumen_df['ganancia_total_pct'] = resumen_df['ganancia_total_pct'].apply(lambda x: f"{x:+.2f}%")
        
        st.dataframe(
            resumen_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "nombre": st.column_config.TextColumn("Fondo"),
                "total_invertido": st.column_config.TextColumn("Invertido"),
                "valor_actual_total": st.column_config.TextColumn("Valor Actual"),
                "ganancia_total_pct": st.column_config.TextColumn("G/P %")
            }
        )
    
    # Gráfica 2: Distribución por tipo de inversión
    st.subheader("📈 Distribución por Tipo de Inversión")
    
    if 'tipo_inversion' in df_fondos.columns:
        df_tipos = df_fondos.groupby('tipo_inversion').agg({
            'total_invertido': 'sum',
            'valor_actual_total': 'sum'
        }).reset_index()
        
        col3, col4 = st.columns([3, 2])
        
        with col3:
            # Crear gráfico de barras apiladas
            fig2 = go.Figure()
            
            for i, tipo in enumerate(df_tipos['tipo_inversion']):
                color = colores_tipos.get(tipo, colores_fondos[i % len(colores_fondos)])
                
                fig2.add_trace(go.Bar(
                    x=[tipo],
                    y=[df_tipos.loc[df_tipos['tipo_inversion'] == tipo, 'total_invertido'].values[0]],
                    name=tipo,
                    marker_color=color,
                    text=[f"€{df_tipos.loc[df_tipos['tipo_inversion'] == tipo, 'total_invertido'].values[0]:,.0f}"],
                    textposition='auto',
                    hovertemplate="<b>Tipo: %{x}</b><br>" +
                                 "Total Invertido: €%{y:,.2f}<br>" +
                                 "<extra></extra>"
                ))
            
            fig2.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#f8fafc',
                barmode='group',
                height=400,
                margin=dict(t=50, b=50, l=50, r=50),
                xaxis_title="Tipo de Inversión",
                yaxis_title="Total Invertido (€)",
                showlegend=False
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        with col4:
            # Mostrar estadísticas por tipo
            st.markdown("### Estadísticas por Tipo")
            
            for _, row in df_tipos.iterrows():
                tipo = row['tipo_inversion']
                total_inv = row['total_invertido']
                valor_actual = row['valor_actual_total']
                porcentaje_total = (total_inv / df_tipos['total_invertido'].sum()) * 100
                
                st.metric(
                    label=f"{tipo} - Renta {'Fija' if tipo == 'RF' else 'Variable'}",
                    value=f"€{total_inv:,.0f}",
                    delta=f"{porcentaje_total:.1f}% del total"
                )
    else:
        st.warning("⚠️ No hay datos de tipo de inversión disponibles.")

def pagina_graficas_acciones():
    """Renderiza la página de gráficas de acciones."""
    st.title("📊 Análisis Visual de Acciones")
    
    # Obtener datos
    acciones, totales = accion_manager.obtener_todas_acciones_con_metricas()
    
    if not acciones:
        st.info("ℹ️ No hay acciones registradas para mostrar gráficas.")
        return
    
    # Preparar datos para gráficas
    df_acciones = pd.DataFrame(acciones)
    
    # Colores personalizados
    colores_acciones = COLORES_GRAFICOS["acciones"]
    
    # Gráfica 1: Distribución por acción
    st.subheader("📈 Distribución por Acción")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Crear gráfico de donut
        fig1 = go.Figure(data=[go.Pie(
            labels=df_acciones['nombre'],
            values=df_acciones['total_invertido'],
            hole=0.5,
            marker=dict(colors=colores_acciones[:len(df_acciones)]),
            textinfo='percent+label',
            textposition='inside',
            hovertemplate="<b>%{label}</b><br>" +
                         "Invertido: €%{value:,.2f}<br>" +
                         "Porcentaje: %{percent}<extra></extra>"
        )])
        
        fig1.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='#f8fafc',
            showlegend=False,
            height=500,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Mostrar tabla de resumen
        st.markdown("### Detalles por Acción")
        resumen_df = df_acciones[['nombre', 'ticker', 'total_invertido', 'ganancia_total_pct']].copy()
        resumen_df['total_invertido'] = resumen_df['total_invertido'].apply(lambda x: f"€{x:,.2f}")
        resumen_df['ganancia_total_pct'] = resumen_df['ganancia_total_pct'].apply(lambda x: f"{x:+.2f}%")
        
        st.dataframe(
            resumen_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "nombre": st.column_config.TextColumn("Empresa"),
                "ticker": st.column_config.TextColumn("Ticker"),
                "total_invertido": st.column_config.TextColumn("Invertido"),
                "ganancia_total_pct": st.column_config.TextColumn("G/P %")
            }
        )
    
    # Gráfica 2: Distribución por sector
    st.subheader("🏢 Distribución por Sector")
    
    if 'sector' in df_acciones.columns and df_acciones['sector'].notna().any():
        df_sectores = df_acciones.groupby('sector').agg({
            'total_invertido': 'sum',
            'valor_actual_total': 'sum',
            'nombre': 'count'
        }).reset_index()
        df_sectores = df_sectores.rename(columns={'nombre': 'num_acciones'})
        
        # Filtrar sectores no disponibles
        df_sectores = df_sectores[df_sectores['sector'] != 'No disponible']
        
        if not df_sectores.empty:
            col3, col4 = st.columns([3, 2])
            
            with col3:
                # Crear gráfico de barras horizontales
                fig2 = go.Figure(data=[go.Bar(
                    y=df_sectores['sector'],
                    x=df_sectores['total_invertido'],
                    orientation='h',
                    marker_color=colores_acciones[:len(df_sectores)],
                    text=[f"€{x:,.0f}" for x in df_sectores['total_invertido']],
                    textposition='auto',
                    hovertemplate="<b>Sector: %{y}</b><br>" +
                                 "Total Invertido: €%{x:,.2f}<br>" +
                                 "Número de acciones: %{customdata[0]}<br>" +
                                 "<extra></extra>",
                    customdata=df_sectores[['num_acciones']].values
                )])
                
                fig2.update_layout(
                    template="plotly_dark",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#f8fafc',
                    height=400,
                    margin=dict(t=50, b=50, l=50, r=50),
                    xaxis_title="Total Invertido (€)",
                    yaxis_title="Sector",
                    showlegend=False
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
            with col4:
                # Mostrar estadísticas por sector
                st.markdown("### Estadísticas por Sector")
                
                for _, row in df_sectores.iterrows():
                    sector = row['sector']
                    total_inv = row['total_invertido']
                    num_acc = row['num_acciones']
                    porcentaje_total = (total_inv / df_sectores['total_invertido'].sum()) * 100
                    
                    st.metric(
                        label=f"{sector}",
                        value=f"€{total_inv:,.0f}",
                        delta=f"{num_acc} acciones"
                    )
        else:
            st.info("ℹ️ No hay datos de sector disponibles para las acciones registradas.")
    else:
        st.warning("⚠️ No hay datos de sector disponibles.")

def main():
    """Función principal de la aplicación."""
    # Inicializar estado de la sesión
    if 'pagina_actual' not in st.session_state:
        st.session_state.pagina_actual = 'fondos'
    
    # Renderizar navegación
    render_navegacion()
    
    # Determinar página actual desde parámetros de URL
    query_params = st.query_params
    pagina = query_params.get("page", ["fondos"])[0]
    
    # Renderizar página correspondiente
    if pagina == "fondos":
        pagina_fondos()
    elif pagina == "acciones":
        pagina_acciones()
    elif pagina == "graficas_fondos":
        pagina_graficas_fondos()
    elif pagina == "graficas_acciones":
        pagina_graficas_acciones()
    else:
        pagina_fondos()

if __name__ == "__main__":
    main()
