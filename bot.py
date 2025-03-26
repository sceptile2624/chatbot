import time
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

# =========================================================
# 1. TOKENS DE SLACK
#    Reemplaza estos valores con tus tokens reales.
#    (No recomendado exponerlos directamente en producción)
# =========================================================
SLACK_BOT_TOKEN = ""
SLACK_APP_TOKEN = ""

# =========================================================
# 2. DICCIONARIO DE CASOS (ÁRBOL DE SOLUCIONES)
#    Cada clave agrupa palabras clave y una respuesta específica.
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
    "drivers": {
        "keywords": ["driver", "controlador", "controladores"],
        "response": (
            "• **Problema con los drivers**\n"
            "  - Asegúrate de tener los controladores actualizados para tus dispositivos.\n"
            "  - Revisa la web del fabricante o utiliza la herramienta de actualización de drivers.\n"
            "  - Si el problema persiste, contacta a IT."
        )
    },
    "software": {
        "keywords": ["software", "aplicación", "programa", "instalación", "error de instalación"],
        "response": (
            "• **Problema con el software**\n"
            "  - Verifica que la aplicación esté instalada y actualizada correctamente.\n"
            "  - Revisa los requisitos del sistema y, si es necesario, reinstala el programa.\n"
            "  - Si el problema continúa, contacta a IT."
        )
    },
    # Categoría genérica para mensajes muy generales
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
# 3. MENÚ DE OPCIONES PARA CASOS GENERALES
#    Se muestran opciones numeradas para que el usuario seleccione.
# =========================================================
menu_options = {
    "1": "mouse",
    "2": "power",
    "3": "camera",
    "4": "vpn",
    "5": "internet",
    "6": "office",
    "7": "printer",
    "8": "audio",
    "9": "drivers",
    "10": "software",
    "11": "other"  # Para otro problema no listado
}

def get_menu_text():
    return (
        "Por favor, elige la categoría que mejor describe tu problema:\n"
        "1. Problema con el mouse\n"
        "2. El equipo no enciende\n"
        "3. Problema con la cámara\n"
        "4. Problema con la VPN\n"
        "5. Problema de conexión a Internet\n"
        "6. Problema con Microsoft Office\n"
        "7. Problema con la impresora\n"
        "8. Problema de audio\n"
        "9. Problema con los drivers\n"
        "10. Problema con el software\n"
        "11. Otro problema (contactar IT)"
    )

# =========================================================
# 4. GESTIÓN DE CONTEXTO
#    Se usa para recordar si un usuario ya recibió el menú.
# =========================================================
user_context = {}  # Clave: user_id, valor: diccionario de estado

# =========================================================
# 5. FUNCIÓN PARA BUSCAR SOLUCIONES EN EL MENSAJE
#    Devuelve una lista de respuestas y una lista de claves (categorías)
# =========================================================
def find_solutions_in_message(text):
    text_lower = text.lower()
    matched_responses = []
    matched_keys = []
    for issue_key, issue_data in ISSUES.items():
        if any(keyword in text_lower for keyword in issue_data["keywords"]):
            matched_responses.append(issue_data["response"])
            matched_keys.append(issue_key)
    return matched_responses, matched_keys

# =========================================================
# 6. FUNCIÓN PRINCIPAL QUE PROCESA LOS EVENTOS
#    - Si el usuario ya tiene un menú pendiente, se interpreta su respuesta.
#    - Si no, se analiza el mensaje para detectar problemas específicos.
#    - Si el mensaje es muy general o solo coincide con "generic", se muestra el menú.
#    - Si el usuario responde "gracias" o "me sirvió", se envía un mensaje de agradecimiento.
# =========================================================
def process(client: SocketModeClient, req: SocketModeRequest):
    if req.type == "events_api":
        event = req.payload.get("event", {})
        if event.get("type") == "message" and "subtype" not in event:
            text = event.get("text", "")
            channel_id = event.get("channel", "")
            user_id = event.get("user", "")
            text_lower = text.strip().lower()

            # Si el usuario agradece, enviar mensaje de agradecimiento
            if text_lower in ["gracias", "me sirvio", "me sirvió", "ok, gracias", "muchas gracias", "muchisimas gracias"]:
                web_client.chat_postEphemeral(
                    channel=channel_id,
                    text="¡De nada! Me alegra saber que te sirvió. Si tienes más preguntas, aquí estoy para ayudarte.",
                    user=user_id
                )
                # Limpiar contexto, si existiera
                if user_id in user_context:
                    user_context.pop(user_id)
                response = SocketModeResponse(envelope_id=req.envelope_id)
                client.send_socket_mode_response(response)
                return

            # Si el usuario ya tiene un menú pendiente, interpreta su selección
            if user_id in user_context and user_context[user_id].get("awaiting_selection", False):
                selection = text.strip()
                if selection in menu_options:
                    chosen = menu_options[selection]
                    if chosen == "other":
                        response_text = (
                            "Hemos recibido tu solicitud. Un miembro de IT se pondrá en contacto contigo para brindarte soporte adicional."
                        )
                    else:
                        response_text = ISSUES[chosen]["response"]
                    web_client.chat_postEphemeral(
                        channel=channel_id,
                        text=response_text,
                        user=user_id
                    )
                    # Limpiar el contexto del usuario
                    user_context.pop(user_id, None)
                else:
                    # Selección inválida: se reenvía el menú
                    web_client.chat_postEphemeral(
                        channel=channel_id,
                        text="Opción no válida. " + get_menu_text(),
                        user=user_id
                    )
                response = SocketModeResponse(envelope_id=req.envelope_id)
                client.send_socket_mode_response(response)
                return

            # Si no hay menú pendiente, buscar soluciones en el mensaje
            matched_responses, matched_keys = find_solutions_in_message(text)

            # Si no se detecta ningún problema específico o solo se detecta "generic", se muestra el menú
            if not matched_responses or (len(matched_responses) == 1 and "generic" in matched_keys):
                user_context[user_id] = {"awaiting_selection": True, "channel": channel_id}
                menu_text = "No se identificó un problema específico. " + get_menu_text()
                web_client.chat_postEphemeral(
                    channel=channel_id,
                    text=menu_text,
                    user=user_id
                )
            else:
                # Si se detectaron problemas específicos, se combinan y se envían las respuestas
                combined_response = "He encontrado algunas sugerencias:\n\n" + "\n\n".join(matched_responses)
                web_client.chat_postEphemeral(
                    channel=channel_id,
                    text=combined_response,
                    user=user_id
                )
        # Enviar respuesta de acuse (ack) a Slack
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

# =========================================================
# 7. BLOQUE PRINCIPAL: INICIALIZA CLIENTES Y EJECUTA
# =========================================================
if __name__ == "__main__":
    # Inicializa el cliente web de Slack
    web_client = WebClient(token=SLACK_BOT_TOKEN)

    # Inicializa el cliente de Socket Mode
    socket_client = SocketModeClient(
        app_token=SLACK_APP_TOKEN,
        web_client=web_client
    )

    # Registra el listener para procesar los eventos
    socket_client.socket_mode_request_listeners.append(process)

    # Conecta vía Socket Mode
    socket_client.connect()
    print("Bot iniciado y escuchando mensajes ...")

    # Mantiene el script en ejecución
    while True:
        time.sleep(1)
