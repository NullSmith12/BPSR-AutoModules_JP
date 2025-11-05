# BPSR Auto Modules — Optimizador de módulos

Herramienta con interfaz gráfica para capturar y analizar los módulos del juego, que facilita encontrar combinaciones óptimas de equipamiento de forma automática.

![Captura de pantalla de la aplicación](https://github.com/mrsnakke/gachaIMG/blob/main/img1.png?raw=true)

## Características principales

- Interfaz gráfica intuitiva — toda la funcionalidad está accesible mediante botones y menús.
- Captura de datos automática — inicia el monitoreo desde la aplicación y el programa detecta los datos del juego.
- Filtrado avanzado:
    - Filtra por tipo de módulo: Ataque, Guardia, Soporte o Todos.
    - Filtra por atributos específicos para buscar combinaciones concretas.
    - Presets de atributos preconfigurados para clases populares.
- Re-filtrado instantáneo — cambia los filtros y usa "Rescreen" para actualizar resultados sin volver a capturar.
- Visualización detallada de resultados:
    - Combinaciones ordenadas por una puntuación de "fitness".
    - Visualización de cada módulo (imagen, rareza y atributos).
    - Resumen de la distribución total de atributos y cálculo del poder de combate estimado.
- Consola integrada — registros de proceso visibles en un panel que puedes mostrar u ocultar.

## Requisitos previos

Es necesario instalar Npcap para que la aplicación pueda capturar tráfico de red del juego.

1. Descarga el instalador de Npcap (se recomienda la versión 1.79 o superior).
2. Durante la instalación, marca la opción "Install Npcap in WinPcap API-compatible Mode" si está disponible.

Npcap permite que la aplicación lea los paquetes de red necesarios para extraer los datos de los módulos.

## Uso básico

1. Ejecuta la aplicación (archivo `.exe`).
2. Abre el panel de configuración (botón "Modules").
     - Selecciona la interfaz de red que usas (Ethernet o Wi‑Fi).
     - Elige el tipo de módulo (Attack / Guard / Support / All).
     - Define atributos manualmente o selecciona un preset.
3. Haz clic en "Start Monitoring" para comenzar la captura.
4. En el juego, provoca el envío de datos (por ejemplo, cambiando de canal o volviendo a la pantalla de selección de personaje).
5. La aplicación detectará los datos y mostrará los mejores resultados en el panel principal.
6. Ajusta filtros y usa "Rescreen" para recalcular sin volver a capturar.
7. Cuando termines, haz clic en "Stop Monitoring".

## Créditos

- Este proyecto es un fork que integra y adapta trabajo previo de otros autores.
- Crédits principales:
    - Fork basado en: StarResonanceAutoMod — autor: fudiyangjin
        https://github.com/fudiyangjin/StarResonanceAutoMod
    - Además agradecemos el trabajo complementario de StarResonanceDamageCounter (dmlgzs):
        https://github.com/dmlgzs/StarResonanceDamageCounter

Si utilizas este proyecto, por favor respeta las licencias y atribuciones originales.

---

**Descargo de responsabilidad**: Esta herramienta es únicamente para fines de aprendizaje y análisis de datos. No debe usarse para actividades que infrinjan los términos de servicio del juego. El usuario asume los riesgos asociados. El autor del proyecto no se hace responsable del uso indebido por parte de terceros. Asegúrate de cumplir las normas y políticas del juego y la comunidad antes de usarla.
