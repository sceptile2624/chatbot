import time
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

# =========================================================
# 1. TOKENS DE SLACK
#    Reemplaza estos valores con tus tokens reales
#    (No recomendado exponerlos directamente en producción)
# =========================================================
SLACK_BOT_TOKEN = ""
SLACK_APP_TOKEN = ""

# =========================================================
# 2. DICCIONARIO DE CASOS (ÁRBOL DE SOLUCIONES)
#    Cada clave (p.e. "mouse") agrupa palabras clave y una
#    respuesta específica.
# =========================================================
ISSUES = {
    "mouse": {
        "keywords": ["mouse", "ratón"],
        "response": (
            "• **Problema con el mouse**\n"
            "  - Verifica que esté correctamente conectado (USB o Bluetooth).\n"
            "  - Si es inalámbrico, revisa que las baterías estén cargadas.\n"
            "  - Si el problema persiste, contacta a IT."
        )
    },
    "power": {
        "keywords": ["no prende", "no enciende", "no arranca"],
        "response": (
            "• **El equipo no enciende**\n"
            "  - Asegúrate de que esté conectado a la corriente y déjalo cargar por al menos 30 minutos.\n"
            "  - Si después de ese tiempo sigue sin encender, contacta a IT."
        )
    },
    "camera": {
        "keywords": ["cámara", "camara", "webcam"],
        "response": (
            "• **Problema con la cámara**\n"
            "  - Verifica que no esté tapada físicamente.\n"
            "  - Asegúrate de que la aplicación tenga los permisos de cámara.\n"
            "  - Si el problema continúa, contacta a IT."
        )
    },
    "vpn": {
        "keywords": ["vpn", "conectar vpn"],
        "response": (
            "• **Problema con la VPN**\n"
            "  - Revisa que esté instalada correctamente y que tus credenciales sean válidas.\n"
            "  - Si necesitas asistencia adicional, contacta a IT."
        )
    },
    "internet": {
        "keywords": ["no hay internet", "no funciona internet", "sin internet", "no tengo red", "no hay red", "desconectado"],
        "response": (
            "• **Problema de conexión a Internet**\n"
            "  - Revisa tu conexión WiFi o cable Ethernet.\n"
            "  - Verifica que el router esté encendido y funcionando.\n"
            "  - Si persiste, contacta a IT."
        )
    },
    "office": {
        "keywords": ["office", "word", "excel", "powerpoint", "outlook"],
        "response": (
            "• **Problema con Microsoft Office**\n"
            "  - Asegúrate de que tu licencia esté activa y tu cuenta sea la correcta.\n"
            "  - Si sigue fallando, contacta a IT."
        )
    },
    "printer": {
        "keywords": ["impresora", "printer"],
        "response": (
            "• **Problema con la impresora**\n"
            "  - Revisa que esté encendida y conectada a la red.\n"
            "  - Verifica que haya papel y que el tóner o tinta no se haya agotado.\n"
            "  - Si el inconveniente continúa, contacta a IT."
        )
    },
    "audio": {
        "keywords": ["no suena", "no hay audio", "no se escucha", "micrófono", "microfono"],
        "response": (
            "• **Problema de audio**\n"
            "  - Revisa el volumen y la configuración de entrada/salida.\n"
            "  - Comprueba que el micrófono y los altavoces estén conectados correctamente.\n"
            "  - Si no se soluciona, contacta a IT."
        )
    },
    # Caso genérico (ayuda, no funciona, etc.)
    "generic": {
        "keywords": ["ayuda", "it", "no funciona", "no sirve", "no conecta", "no abre"],
        "response": (
            "• **Solicitud de ayuda general**\n"
            "  - Describe con más detalle tu problema.\n"
            "  - Si persiste la falla, contacta a IT."
        )
    },
}

# =========================================================
# 3. FUNCIÓN PARA BUSCAR SOLUCIONES EN EL MENSAJE
#    Devuelve una lista con todas las respuestas que coincidan
#    con las palabras clave encontradas.
# =========================================================
def find_solutions_in_message(text):
    text_lower = text.lower()
    matched_responses = []

    # Verifica cada categoría en ISSUES
    for issue_key, issue_data in ISSUES.items():
        # Si alguna palabra clave de esa categoría está en el texto, se añade la respuesta
        if any(keyword in text_lower for keyword in issue_data["keywords"]):
            matched_responses.append(issue_data["response"])

    return matched_responses

# =========================================================
# 4. FUNCIÓN PRINCIPAL QUE PROCESA LOS EVENTOS
#    Escucha los mensajes y, si detecta palabras clave, responde
#    con sugerencias específicas.
# =========================================================
def process(client: SocketModeClient, req: SocketModeRequest):
    if req.type == "events_api":
        event = req.payload.get("event", {})
        # Filtramos mensajes simples (sin subtype) para evitar duplicados
        if event.get("type") == "message" and "subtype" not in event:
            text = event.get("text", "")
            channel_id = event.get("channel", "")
            user_id = event.get("user", "")

            # Busca posibles soluciones
            solutions = find_solutions_in_message(text)

            if solutions:
                # Combina todas las respuestas encontradas en un solo mensaje
                combined_response = "He encontrado algunas sugerencias:\n\n" + "\n\n".join(solutions)
            else:
                # Respuesta genérica si no se reconoció ningún problema
                combined_response = (
                    "Hemos recibido tu solicitud, pero no reconocemos el problema específico.\n"
                    "Un miembro de IT se pondrá en contacto contigo para brindarte soporte adicional."
                )

            # Enviar mensaje efímero (sólo visible para el usuario)
            web_client.chat_postEphemeral(
                channel=channel_id,
                text=combined_response,
                user=user_id
            )

        # Respuesta de acuse (ack) a Slack
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

# =========================================================
# 5. BLOQUE PRINCIPAL: INICIALIZA CLIENTES Y EJECUTA
# =========================================================
if __name__ == "__main__":
    # Crea el cliente web de Slack (para enviar mensajes)
    web_client = WebClient(token=SLACK_BOT_TOKEN)

    # Crea el cliente de Socket Mode (para recibir eventos en tiempo real)
    socket_client = SocketModeClient(
        app_token=SLACK_APP_TOKEN,
        web_client=web_client
    )

    # Registra la función 'process' como listener de eventos
    socket_client.socket_mode_request_listeners.append(process)

    # Conecta vía Socket Mode
    socket_client.connect()
    print("Bot iniciado y escuchando mensajes (Socket Mode)...")

    # Mantiene el script en ejecución para recibir eventos continuamente
    while True:
        time.sleep(1)
