import time
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

# Tokens
SLACK_BOT_TOKEN = ""

# Token de nivel de aplicación para Socket Mode (xapp-...)
SLACK_APP_TOKEN = ""

# lista de oalabras clave que disparan la respuesta
KEYWORDS = ["ayuda", "it", "no sirve", "no funciona", "no conecta", "no abre"]

# Cliente web de Slack (para enviar mensajes)
web_client = WebClient(token=SLACK_BOT_TOKEN)

# Cliente de Socket Mode
socket_client = SocketModeClient(
    app_token=SLACK_APP_TOKEN,
    web_client=web_client
)

def process(client: SocketModeClient, req: SocketModeRequest):
    if req.type == "events_api":
        event = req.payload.get("event", {})
        if event.get("type") == "message" and "subtype" not in event:
            text = event.get("text", "").lower()
            channel_id = event.get("channel", "")
            user_id = event.get("user", "")

            # Verificamos si alguna de las palabras clave está en el mensaje
            if any(keyword in text for keyword in KEYWORDS):
                # Enviamos un mensaje ephemeral (solo el usuario lo ve)
                web_client.chat_postEphemeral(
                    channel=channel_id,
                    text="¡Hola! Vemos que necesitas ayuda. En breve revisaremos tu caso.",
                    user=user_id
                )

        # Enviamos la respuesta (ack) a Slack para confirmar
        response = SocketModeResponse(envelope_id=req.envelope_id)
        client.send_socket_mode_response(response)

if __name__ == "__main__":
    # Agregamos la función que maneja los eventos
    socket_client.socket_mode_request_listeners.append(process)
    # Conectamos con Socket Mode
    socket_client.connect()
    print("Bot iniciado y escuchando mensajes (Socket Mode)...")
    # Mantén el script en ejecución
    while True:
        time.sleep(1)