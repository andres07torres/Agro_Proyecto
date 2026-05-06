# 🌱 Pro Agro - Sistema de Gestión e Inteligencia Agrícola

![Desarrollo](https://img.shields.io/badge/Desarrollo-Completado-success?style=for-the-badge&logo=github)
![Version](https://img.shields.io/badge/Versión-1.0.0-blue?style=for-the-badge)

**Pro Agro** es una plataforma web avanzada diseñada para la gestión, análisis y visualización de datos agrícolas. Utilizando tecnologías de vanguardia y procesamiento de datos científicos, permite a los agricultores y técnicos tomar decisiones informadas basadas en datos reales y mapas interactivos.

---

## 🚀 Tecnologías Utilizadas

### Backend & Core
<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white" alt="SQLAlchemy" />
</p>

### Frontend & UI
<p align="left">
  <img src="https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5" />
  <img src="https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white" alt="CSS3" />
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" alt="JavaScript" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="TailwindCSS" />
  <img src="https://img.shields.io/badge/Jinja2-B41717?style=for-the-badge&logo=jinja&logoColor=white" alt="Jinja2" />
</p>

### Análisis de Datos & Ciencia
<p align="left">
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas" />
  <img src="https://img.shields.io/badge/NumPy-013243?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy" />
  <img src="https://img.shields.io/badge/SciPy-8CAAE6?style=for-the-badge&logo=scipy&logoColor=white" alt="SciPy" />
  <img src="https://img.shields.io/badge/Xarray-00A2E8?style=for-the-badge&logo=xarray&logoColor=white" alt="Xarray" />
</p>

---

## ✨ Características Principales

- 🔐 **Autenticación Segura**: Sistema completo de inicio de sesión y gestión de usuarios.
- 📊 **Panel de Control (Dashboard)**: Visualización dinámica de métricas agrícolas esenciales.
- 📈 **Análisis de Tendencias**: Herramientas para visualizar la evolución de datos a lo largo del tiempo.
- 📥 **Gestión de Datos**: Sistema de carga de archivos científicos y visualización de historial.
- 🗺️ **Mapas Interactivos**: Integración con servicios de cartografía para visualización espacial.
- 📱 **Diseño Responsivo**: Interfaz moderna optimizada para todos los dispositivos.
- 🛡️ **Seguridad Avanzada**: Implementación de CSP, protección XSS y limitador de peticiones.

---

## 🛠️ Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/usuario/Pro_Agro.git
   cd Pro_Agro
   ```

2. **Crear un entorno virtual:**
   ```bash
   python -m venv env
   source env/bin/activate  # En Windows: env\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno:**
   Crea un archivo `.env` basado en el `.env.example` (si existe) o añade:
   ```env
   SECRET_KEY=tu_clave_secreta
   DATABASE_URL=postgresql://usuario:password@localhost/pro_agro
   FLASK_DEBUG=True
   ```

5. **Ejecutar la aplicación:**
   ```bash
   python main.py
   ```

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Para más detalles, consulta el archivo `LICENSE`.

---

<p align="center">
  Hecho con ❤️ para el sector agrícola.
</p>
