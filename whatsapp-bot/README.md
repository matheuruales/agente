# Bot de WhatsApp para calificar leads inmobiliarios

Adaptación del bot de ejemplo usando Baileys. Envía los mensajes al agente FastAPI (`/api/lead/analyze`) y responde con el score y resumen.

## Configuración
1. Copia `.env.example` a `.env` y ajusta:
   - `AGENT_API_URL`: URL del endpoint del agente (ej: http://localhost:8000/api/lead/analyze).
   - `AGENT_API_TOKEN`: token si tu agente requiere auth (opcional).
   - `SESSION_DIR`: carpeta donde se guardará la sesión de WhatsApp.
2. Instala dependencias:
   ```bash
   cd whatsapp-bot
   npm install
   ```

## Ejecución
```bash
npm start
```
Se mostrará un QR en consola. Escanéalo con WhatsApp para iniciar sesión.

## Uso
- Envía cualquier mensaje: el bot lo enviará al agente y responderá con el tipo de lead, presupuesto, zona, urgencia y razonamiento.
- Comandos:
  - `!help` muestra ayuda.
  - `!ping` prueba disponibilidad.
