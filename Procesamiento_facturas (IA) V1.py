import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Importamos nuestros módulos locales
import config
from extractor_ia import procesar_y_guardar_factura_vision

class ManejadorArchivos(FileSystemEventHandler):
    def __init__(self, edificio): 
        self.edificio = edificio
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.pdf'):
            time.sleep(3) 
            procesar_y_guardar_factura_vision(event.src_path, os.path.basename(event.src_path), self.edificio)
            
    def on_moved(self, event):
        if not event.is_directory and event.dest_path.lower().endswith('.pdf'):
            time.sleep(3) 
            procesar_y_guardar_factura_vision(event.dest_path, os.path.basename(event.dest_path), self.edificio)

if __name__ == "__main__":
    print("🛡️ GUARDIÁN V6 (MODULARIZADO) ACTIVO")
    observador = Observer()
    
    for ed, ruta in config.carpetas_edificios.items():
        if os.path.exists(ruta):
            observador.schedule(ManejadorArchivos(ed), ruta, recursive=False)
            print(f"✓ Vigilando: {ed}")
            
    observador.start()
    try:
        while True: 
            time.sleep(1)
    except KeyboardInterrupt:
        observador.stop()
    observador.join()