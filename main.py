import os
import requests

# Si ya tienes tu token en una variable de entorno, lo lees así:
# SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

# O lo asignas directamente para pruebas (no recomendado en producción):
SLACK_BOT_TOKEN = "xoxb-..."  # Reemplaza con tu token chido
CHANNEL_ID = "C07AJPVC0P8"    # ID del canal #itsupport

def get_all_messages():
    """
    Obtiene todos los mensajes del canal indicado, sin filtrar por fecha.
    Retorna una lista con todos los mensajes.
    """
    url = "https://slack.com/api/conversations.history"
    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}"
    }
    params = {
        "channel": CHANNEL_ID,
        "limit": 1000
    }

    all_messages = []
    while True:
        response = requests.get(url, headers=headers, params=params).json()

        if not response.get("ok"):
            print("Error en la API de Slack:", response.get("error"))
            break

        messages = response.get("messages", [])
        all_messages.extend(messages)

        # Verificar si hay más páginas de resultados
        if response.get("has_more"):
            # Actualizamos el cursor para la siguiente llamada
            next_cursor = response.get("response_metadata", {}).get("next_cursor")
            if next_cursor:
                params["cursor"] = next_cursor
            else:
                break
        else:
            # No hay más páginas
            break

    return all_messages

def main():
    all_messages = get_all_messages()
    print(f"Se obtuvieron {len(all_messages)} mensajes en total.")

    # Filtramos mensajes que contengan la palabra "ticket"
    tickets = []
    for msg in all_messages:
        text = msg.get("text", "").lower()
        if "ticket" in text:
            tickets.append(msg)

    print(f"Se encontraron {len(tickets)} mensajes con la palabra 'ticket'.")
    print("=== Mensajes con 'ticket' ===")
    for t in tickets:
        print(f"- {t.get('text', '')}")

if __name__ == "__main__":
    main()