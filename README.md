# 🌐 Screen Translator

Traductor de pantalla en tiempo real. Selecciona cualquier región de tu pantalla y obtén la traducción al español al instante, impulsado por **Groq** (Llama 4 Scout).

https://github.com/user-attachments/assets/d73a51e6-9a29-49b9-8293-4b109b59d1df

## ✨ Características

- **Hotkey global** — `Ctrl+Shift+Space` activa la captura en cualquier momento.
- **Selección visual** — Arrastra sobre la pantalla congelada para elegir la región a traducir.
- **Traducción con IA** — Usa el modelo `meta-llama/llama-4-scout-17b-16e-instruct` vía la API de Groq.
- **Ventana flotante** — El resultado aparece en una ventana siempre visible con tema oscuro.

## 📋 Requisitos previos

- **Python 3.10+**
- **API Key de Groq** — Obtén una en [console.groq.com](https://console.groq.com/)
- **Windows** — La captura de pantalla y el hotkey global están optimizados para Windows.

## 🚀 Instalación

### 1. Clonar o descargar el proyecto

```bash
git clone <url-del-repositorio>
cd translator
```

### 2. Crear un entorno virtual

```bash
python -m venv venv
```

### 3. Activar el entorno virtual

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**CMD:**
```cmd
.\venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

> Una vez activado, verás `(venv)` al inicio de tu línea de comandos.

### 4. Instalar las dependencias

```bash
pip install -r requirements.txt
```

## ⚙️ Configuración

Antes de ejecutar, debes definir tu API Key de Groq como variable de entorno:

**PowerShell:**
```powershell
$env:GROQ_API_KEY="tu_api_key_aquí"
```

**CMD:**
```cmd
set GROQ_API_KEY=tu_api_key_aquí
```

**Linux / macOS:**
```bash
export GROQ_API_KEY="tu_api_key_aquí"
```

## ▶️ Uso

```bash
python screen_translator.py
```

1. Presiona `Ctrl+Shift+Space` para activar la captura.
2. Arrastra el cursor para seleccionar la región que deseas traducir.
3. Espera unos segundos mientras la IA procesa la imagen.
4. La traducción aparecerá en una ventana flotante.
5. Presiona `ESC` durante la selección para cancelar.

## 📦 Dependencias

| Paquete    | Descripción                              |
|------------|------------------------------------------|
| `Pillow`   | Manipulación de imágenes                 |
| `mss`      | Captura de pantalla rápida y multiplataforma |
| `keyboard` | Detección de hotkeys globales            |
| `groq`     | Cliente oficial de la API de Groq        |
