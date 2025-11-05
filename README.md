[![Español](https://img.shields.io/badge/Espa%C3%B1ol-red?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA3NTAgNTAwIj48cGF0aCBmaWxsPSIjY2YxNDJiIiBkPSJNMCAwaDc1MHY1MDBIMHoiLz48cGF0aCBmaWxsPSIjZmNkZDA3IiBkPSJNMCAxMjVoNzUwdjI1MEgwVjEyNXoiLz48cGF0aCBmaWxsPSIjMDA0MzQ2IiBkPSJNMCAwYzI3LjYxNCAwIDU1LjIyOCAxMS4wNDUgNzUuNzU3IDMwLjU4N0wxMjUgNzUuNzU3VjBIMHoiLz48cGF0aCBmaWxsPSIjMDA0MzQ2IiBkPSJNMCA1MDBjMjcuNjE0IDAgNTUuMjI4LTExLjA0NSA3NS43NTctMzAuNTg3TDEyNSA0MjQuMjQzVjUwMEgwWiIvPjxwYXRoIGZpbGw9IiMwMDQzNDYiIGQ9Ik03NTAgMGMtMjcuNjE0IDAtNTUuMjI4IDExLjA0NS03NS43NTcgMzAuNTg3TDYyNSA3NS43NTdWMDBINzUwWiIvPjxwYXRoIGZpbGw9IiMwMDQzNDYiIGQ9Ik03NTAgNTAwYy0yNy42MTQgMC01NS4yMjgtMTEuMDQ1LTc1Ljc1Ny0zMC41ODdMNjI1IDQyNC4yNDNWNTAwSDc1MFoiLz48Y2lyY2xlIGN4PSIzNzUiIGN5PSIyNTAiIHI9IjgwIiBmaWxsPSIjZmNkZDA3Ii8+PHBhdGggZmlsbD0iI2JkM2Q0YyIgZD0iTTM3NSAxNzBjLTQ0LjE4MyAwLTgwIDM1LjgyLTgwIDgwczM1LjgyIDgwIDgwIDgwIDgwLTM1LjgyIDgwLTgwLTM1LjgyLTgwLTgwLTgweiIvPjxwYXRoIGZpbGw9IiNmZmYiIGQ9Ik0zNzUgMTkwYzMzLjEzNyAwIDYwIDI2Ljg2MyA2MCA2MHMtMjYuODYzIDYwLTYwIDYwLTYwLTI2Ljg2My02MC02MCAyNi44NjMtNjAgNjAtNjB6Ii8+PHBhdGggZmlsbD0iI2JkM2Q0YyIgZD0iTTM3NSAyMDBjMjcuNjE0IDAgNTAtMjIuMzg2IDUwLTUwcy0yMi4zODYtNTAtNTAtNTAtNTAtMjIuMzg2LTUwLTUwIDIyLjM4Ni01MCA1MC01MHoiLz48cGF0aCBmaWxsPSIjZmNkZDA3IiBkPSJNMzU1IDI1MGgyMHYyMGgtMjB6TTM2NSAyMzBoMjB2MjBoLTIwem0xMC0yMGgyMHYyMGgtMjB6TTM3NSAyMjBoMjB2MjBoLTIwem0xMC0yMGgyMHYyMGgtMjB6Ii8+PC9zdmc+)](#BPSR Auto Modules — Optimizador de módulos-version-española)

# BPSR Auto Modules — Module Optimizer

A graphical interface tool to capture and analyze in-game modules, facilitating the automatic discovery of optimal equipment combinations.

![Application Screenshot](https://github.com/mrsnakke/gachaIMG/blob/main/img1.png?raw=true)

## Key Features

- Intuitive graphical interface — all functionality is accessible via buttons and menus.
- Automatic data capture — start monitoring from the application, and the program detects game data.
- Advanced filtering:
    - Filter by module type: Attack, Guard, Support, or All.
    - Filter by specific attributes to search for concrete combinations.
    - Pre-configured attribute presets for popular classes.
- Instant re-filtering — change filters and use "Rescreen" to update results without re-capturing.
- Detailed results visualization:
    - Combinations ordered by a "fitness" score.
    - Visualization of each module (image, rarity, and attributes).
    - Summary of total attribute distribution and estimated combat power calculation.
- Integrated console — process logs visible in a panel that you can show or hide.

## Prerequisites

To run this project, you will need the following:

1.  **Python 3.8 or higher**: If you don't have Python installed, download it from the official website: [python.org](https://www.python.org/downloads/). Make sure to check the "Add Python to PATH" option during installation.
2.  **Npcap**: Npcap must be installed for the application to capture game network traffic.
    - Download the Npcap installer (version npcap-1.83 or higher is recommended) from [npcap.com](https://npcap.com/#download).
    - During installation, check the "Install Npcap in WinPcap API-compatible Mode" option if available.

Npcap allows the application to read the network packets necessary to extract module data.

## Installation

Follow these steps to set up and run the project:

1.  **Clone the repository**:
    Open a terminal (CMD, PowerShell, or Git Bash) and run the following command to clone the repository:
    ```bash
    git clone https://github.com/mrsnakke/BPSR-AutoModules.git
    cd BPSR-AutoModules
    ```

2.  **Create and activate a virtual environment (recommended)**:
    It is good practice to use a virtual environment to manage project dependencies.
    ```bash
    python -m venv venv
    ```
    -   **On Windows**:
        ```bash
        .\venv\Scripts\activate
        ```
    -   **On macOS/Linux**:
        ```bash
        source venv/bin/activate
        ```

3.  **Install dependencies**:
    With the virtual environment activated, install the necessary Python libraries:
    ```bash
    pip install customtkinter Pillow scapy zstandard protobuf
    ```
    *Note: `scapy` may require administrator permissions on some systems for installation or execution.*

## Usage

1.  **Run the application**:
    Once all dependencies are installed, you can start the application by running the main script:
    ```bash
    python gui_app.py
    ```

2.  **Initial configuration in the application**:
    -   Open the configuration panel ("Config" button).
    -   Select the network interface you use (Ethernet or Wi-Fi).
    -   Choose the module type (Attack / Guard / Support / All).
    -   Define attributes manually or select a preset.

3.  **Start monitoring**:
    -   Click "Start Monitoring" to begin capturing.
    -   In the game, trigger data transmission (e.g., changing channels or returning to the character selection screen).
    -   The application will detect the data and display the best results in the main panel.

4.  **Adjust and re-filter**:
    -   Adjust filters and use "Rescreen" to recalculate without re-capturing.
    -   When finished, click "Stop Monitoring".

## Contributions

We appreciate your contributions! If you find a bug, have a suggestion for improvement, or want to add new features, feel free to open an "issue" or submit a "pull request".

**Known issues:**
-   The user interface may appear unresponsive for a few seconds while intensive background tasks are performed (e.g., module optimization). This is due to the nature of parallel operations and GUI updates. We are working on improving fluidity.

## Credits

- This project is a fork that integrates and adapts previous work by other authors.
- Main credits:
    - Fork based on: StarResonanceAutoMod — author: fudiyangjin
        https://github.com/fudiyangjin/StarResonanceAutoMod
    - We also appreciate the complementary work of StarResonanceDamageCounter (dmlgzs):
        https://github.com/dmlgzs/StarResonanceDamageCounter

If you use this project, please respect the original licenses and attributions.

---

**Disclaimer**: This tool is for learning and data analysis purposes only. It should not be used for activities that violate the game's terms of service. The user assumes the associated risks. The project author is not responsible for misuse by third parties. Make sure to comply with game and community rules and policies before using it.

<a name="BPSR Auto Modules — Module Optimizer-english-version"></a>
<br>

# BPSR Auto Modules — Optimizador de módulos

Herramienta con interfaz gráfica para capturar y analizar los módulos del juego, que facilita encontrar combinaciones óptimas de equipamiento de forma automática.

[![English](https://img.shields.io/badge/English-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA4NDAgNjMwIj48cGF0aCBmaWxsPSIjYjIyMjM0IiBkPSJNMCAwaDk4MHY2ODNIMHoiLz48cGF0aCBmaWxsPSIjZmZmIiBkPSJNMCA3Nmg5ODB2NTJIMHptMCAxNTJoOTgwdi01Mkgwem0wIDE1Mmg5ODB2LTUySDB6bTAgMTUyaDk4MHYtNTJIMHptMCAxNTJoOTgwdi01MkgweiIvPjxwYXRoIGZpbGw9IiMwMDMyOTYiIGQ9Ik0wIDBoNDIwVjM2OEgwem0zMCAyNGwzMyAxMDIgMTAtMzEtMzItODcgNzIgMzcgOTctMzcgMTIgMzItNzIgODYgMTIgMzEgOTYtMzcgNzIgMzYtMzItODcgMTAtMzIgMzMgMTAyLTEwMy02Mi0xMDMgNjIgMzMgMTAyIDEwLTMxLTMyLTg3IDcyIDM3IDk3LTM3IDEyIDMyLTcyIDg2IDEyIDMxIDk2LTM3IDcyIDM2LTMyLTg3IDEwLTMyIDMzIDEwMi0xMDMtNjItMTAzIDYyem0wIDEyMGwzMyAxMDIgMTAtMzEtMzItODcgNzIgMzcgOTctMzcgMTIgMzItNzIgODYgMTIgMzEgOTYtMzcgNzIgMzYtMzItODcgMTAtMzIgMzMgMTAyLTEwMy02Mi0xMTAgNjIgMzMgMTAyIDEwLTMxLTMyLTg3IDcyIDM3IDk3LTM3IDEyIDMyLTcyIDg2IDEyIDMxIDk2LTM3IDcyIDM2LTMyLTg3IDEwLTMyIDMzIDEwMi0xMDMtNjItMTAzIDYyem0xNjggMTIwbDMzIDEwMiAxMC0zMS0zMi04NyA3MiAzNyA5Ny0zNyAxMiAzMi03MiA4NiAxMiAzMSA5Ni0zNyA3MiAzNi0zMi04NyAxMC0zMiAzMyAxMDItMTAzLTYyLTEwMyA2MnoiLz48L3N2Zz4=)](#BPSR Auto Modules — Module Optimizer)

[![English](https://img.shields.io/badge/English-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA4NDAgNjMwIj48cGF0aCBmaWxsPSIjYjIyMjM0IiBkPSJNMCAwaDk4MHY2ODNIMHoiLz48cGF0aCBmaWxsPSIjZmZmIiBkPSJNMCA3Nmg5ODB2NTJIMHptMCAxNTJoOTgwdi01Mkgwem0wIDE1Mmg5ODB2LTUySDB6bTAgMTUyaDk4MHYtNTJIMHptMCAxNTJoOTgwdi01MkgweiIvPjxwYXRoIGZpbGw9IiMwMDMyOTYiIGQ9Ik0wIDBoNDIwVjM2OEgwem0zMCAyNGwzMyAxMDIgMTAtMzEtMzItODcgNzIgMzcgOTctMzcgMTIgMzItNzIgODYgMTIgMzEgOTYtMzcgNzIgMzYtMzItODcgMTAtMzIgMzMgMTAyLTEwMy02Mi0xMDMgNjIgMzMgMTAyIDEwLTMxLTMyLTg3IDcyIDM3IDk3LTM3IDEyIDMyLTcyIDg2IDEyIDMxIDk2LTM3IDcyIDM2LTMyLTg3IDEwLTMyIDMzIDEwMi0xMDMtNjItMTAzIDYyem0wIDEyMGwzMyAxMDIgMTAtMzEtMzItODcgNzIgMzcgOTctMzcgMTIgMzItNzIgODYgMTIgMzEgOTYtMzcgNzIgMzYtMzItODcgMTAtMzIgMzMgMTAyLTEwMy02Mi0xMTAgNjIgMzMgMTAyIDEwLTMxLTMyLTg3IDcyIDM3IDk3LTM3IDEyIDMyLTcyIDg2IDEyIDMxIDk2LTM3IDcyIDM2LTMyLTg3IDEwLTMyIDMzIDEwMi0xMDMtNjItMTAzIDYyem0xNjggMTIwbDMzIDEwMiAxMC0zMS0zMi04NyA3MiAzNyA5Ny0zNyAxMiAzMi03MiA4NiAxMiAzMSA5Ni0zNyA3MiAzNi0zMi04NyAxMC0zMiAzMyAxMDItMTAzLTYyLTEwMyA2MnoiLz48L3N2Zz4=)](#-BPSR Auto Modules — Module Optimizer)

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

Para ejecutar este proyecto, necesitarás lo siguiente:

1.  **Python 3.8 o superior**: Si no tienes Python instalado, descárgalo desde el sitio web oficial: [python.org](https://www.python.org/downloads/). Asegúrate de marcar la opción "Add Python to PATH" durante la instalación.
2.  **Npcap**: Es necesario instalar Npcap para que la aplicación pueda capturar tráfico de red del juego.
    - Descarga el instalador de Npcap (se recomienda la versión npcap-1.83 o superior) desde [npcap.com](https://npcap.com/#download).
    - Durante la instalación, marca la opción "Install Npcap in WinPcap API-compatible Mode" si está disponible.

Npcap permite que la aplicación lea los paquetes de red necesarios para extraer los datos de los módulos.

## Instalación

Sigue estos pasos para configurar y ejecutar el proyecto:

1.  **Clonar el repositorio**:
    Abre una terminal (CMD, PowerShell o Git Bash) y ejecuta el siguiente comando para clonar el repositorio:
    ```bash
    git clone https://github.com/mrsnakke/BPSR-AutoModules.git
    cd BPSR-AutoModules
    ```

2.  **Crear y activar un entorno virtual (recomendado)**:
    Es una buena práctica usar un entorno virtual para gestionar las dependencias del proyecto.
    ```bash
    python -m venv venv
    ```
    -   **En Windows**:
        ```bash
        .\venv\Scripts\activate
        ```
    -   **En macOS/Linux**:
        ```bash
        source venv/bin/activate
        ```

3.  **Instalar dependencias**:
    Con el entorno virtual activado, instala las librerías de Python necesarias:
    ```bash
    pip install customtkinter Pillow scapy zstandard protobuf
    ```
    *Nota: `scapy` puede requerir permisos de administrador en algunos sistemas para su instalación o ejecución.*

## Uso

1.  **Ejecutar la aplicación**:
    Una vez que todas las dependencias estén instaladas, puedes iniciar la aplicación ejecutando el script principal:
    ```bash
    python gui_app.py
    ```

2.  **Configuración inicial en la aplicación**:
    -   Abre el panel de configuración (botón "Config").
    -   Selecciona la interfaz de red que usas (Ethernet o Wi‑Fi).
    -   Elige el tipo de módulo (Attack / Guard / Support / All).
    -   Define atributos manualmente o selecciona un preset.

3.  **Iniciar monitoreo**:
    -   Haz clic en "Start Monitoring" para comenzar la captura.
    -   En el juego, provoca el envío de datos (por ejemplo, cambiando de canal o volviendo a la pantalla de selección de personaje).
    -   La aplicación detectará los datos y mostrará los mejores resultados en el panel principal.

4.  **Ajustar y re-filtrar**:
    -   Ajusta los filtros y usa "Rescreen" para recalcular sin volver a capturar.
    -   Cuando termines, haz clic en "Stop Monitoring".

## Contribuciones

¡Agradecemos tus contribuciones! Si encuentras un error, tienes una sugerencia de mejora o quieres añadir nuevas funcionalidades, no dudes en abrir un "issue" o enviar un "pull request".

**Problemas conocidos:**
-   La interfaz de usuario puede parecer que no responde por unos segundos mientras se realizan tareas intensivas en segundo plano (por ejemplo, la optimización de módulos). Esto se debe a la naturaleza de las operaciones paralelas y la actualización de la GUI. Estamos trabajando en mejorar la fluidez.

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
