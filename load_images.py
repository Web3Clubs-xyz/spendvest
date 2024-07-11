import os
import requests

MEDIA_DIR = 'static/bot_media'
PHONE_NUMBER_ID = '365548836635602'
ACCESS_TOKEN = 'EAAUCpth1wAIBO65uhRqBqKGnTMZAYnUEknmL9SwqgjXvp9ixJQ16phlRLAlct2VNKapiwa9MCHYobqmQinCO4HkZBtbZBB9w8lIfzsXBVAR9gPVLMCvBegyupjkJrGGtchq4DY6V3oGutZBZC165PaYxPF7ry62ImsHx6LdlYyBa0ZBJAtB4F17FKrGmtLAT59kjDs4zyHE6rvehv9T4UR47yAK5wZD'
FB_GRAPH_URL = f'https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/media'

def get_mime_type(file_name):
    extension = file_name.lower().split('.')[-1]
    print(f"Extension is: {extension}")

    if extension in ['jpeg', 'jpg']:
        return 'image/jpeg'
    elif extension == 'png':
        return 'image/png'
    elif extension == 'webp':
        return 'image/webp'
    elif extension == 'mp4':
        return 'video/mp4'
    else:
        return None

def upload_media(file_path, mime_type):
    print(f"Uploading file, file_path: {file_path}, mime_type: {mime_type}")

    with open(file_path, 'rb') as media_file:
        files = {
            'file': (os.path.basename(file_path), media_file, mime_type),
            'type': (None, mime_type),
            'messaging_product': (None, 'whatsapp')
        }
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}'
        }
        response = requests.post(FB_GRAPH_URL, headers=headers, files=files)
        return response.json()

def main():
    media_ids = {}
    for file_name in os.listdir(MEDIA_DIR):
        if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.mp4')):
            file_path = os.path.join(MEDIA_DIR, file_name)
            mime_type = get_mime_type(file_name)
            if mime_type:
                response = upload_media(file_path, mime_type)
                if 'id' in response:
                    media_ids[file_name] = response['id']
                else:
                    print(f"Failed to upload {file_name}: {response}")
            else:
                print(f"Unsupported file type: {file_name}")
        else:
            print(f"Skipping non-media file: {file_name}")

    print(media_ids)

if __name__ == '__main__':
    main()
