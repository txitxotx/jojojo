"""
Módulo de conexión y operaciones con Supabase para persistencia de datos.
"""

import os
from typing import List, Dict, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# Cargar variables de entorno
load_dotenv()

class DatabaseManager:
    """Gestor de operaciones de base de datos con Supabase."""
    
    def __init__(self):
        """Inicializa la conexión con Supabase."""
        self.url = os.environ.get("SUPABASE_URL")
        self.key = os.environ.get("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY deben estar definidos en las variables de entorno")
        
        self.client: Client = create_client(self.url, self.key)
    
    def obtener_fondos(self) -> List[Dict]:
        """Obtiene todos los fondos de inversión de la base de datos."""
        try:
            response = self.client.table("fondos").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error al obtener fondos: {e}")
            return []
    
    def guardar_fondo(self, fondo_data: Dict) -> Dict:
        """Guarda un nuevo fondo o actualiza uno existente."""
        try:
            if "id" in fondo_data and fondo_data["id"]:
                # Actualizar fondo existente
                response = self.client.table("fondos")\
                    .update(fondo_data)\
                    .eq("id", fondo_data["id"])\
                    .execute()
            else:
                # Crear nuevo fondo
                response = self.client.table("fondos")\
                    .insert(fondo_data)\
                    .execute()
            
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error al guardar fondo: {e}")
            return {}
    
    def eliminar_fondo(self, fondo_id: int) -> bool:
        """Elimina un fondo por su ID."""
        try:
            response = self.client.table("fondos")\
                .delete()\
                .eq("id", fondo_id)\
                .execute()
            return True
        except Exception as e:
            print(f"Error al eliminar fondo: {e}")
            return False
    
    def obtener_acciones(self) -> List[Dict]:
        """Obtiene todas las acciones de la base de datos."""
        try:
            response = self.client.table("acciones").select("*").execute()
            return response.data
        except Exception as e:
            print(f"Error al obtener acciones: {e}")
            return []
    
    def guardar_accion(self, accion_data: Dict) -> Dict:
        """Guarda una nueva acción o actualiza una existente."""
        try:
            if "id" in accion_data and accion_data["id"]:
                # Actualizar acción existente
                response = self.client.table("acciones")\
                    .update(accion_data)\
                    .eq("id", accion_data["id"])\
                    .execute()
            else:
                # Crear nueva acción
                response = self.client.table("acciones")\
                    .insert(accion_data)\
                    .execute()
            
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error al guardar acción: {e}")
            return {}
    
    def eliminar_accion(self, accion_id: int) -> bool:
        """Elimina una acción por su ID."""
        try:
            response = self.client.table("acciones")\
                .delete()\
                .eq("id", accion_id)\
                .execute()
            return True
        except Exception as e:
            print(f"Error al eliminar acción: {e}")
            return False
    
    def crear_tablas_iniciales(self) -> None:
        """Crea las tablas iniciales si no existen."""
        # Esta función asume que las tablas ya están creadas en Supabase
        # En un entorno real, se ejecutarían migraciones SQL
        pass

# Instancia global de DatabaseManager
db_manager = None

def obtener_db_manager() -> DatabaseManager:
    """Obtiene la instancia global de DatabaseManager."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager
