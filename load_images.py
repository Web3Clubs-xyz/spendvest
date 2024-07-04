import os
import requests

MEDIA_DIR = 'static/bot_media'
PHONE_NUMBER_ID = '365548836635602'
ACCESS_TOKEN = 'EAAUCpth1wAIBO7b7yK8TeHBGQLb2Jox5mKIHZCGFZBUEjDrEiQZCzUNSa5W8JBebGZATZAHVNEyXikeSMvZCXzPlw4g4PSn14ru5ZCZCc8OfIuYYuCSHM0sbpziGGzmFD73b71IhQBkrIthFPeRBo1bhUMIOSEf5Ro5ZCMZAdL9XmUuaR6rZA3ymjBVihnvNLDaieM8d0tQVtNhBiKAHkbGOFfdJ3OQRZC8ZD'
FB_GRAPH_URL = f'https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/media'

def get_mime_type(image_name):
    extension = image_name.lower().split('.')[-1]
    print(f"Extension is: {extension}")

    if extension in ['jpeg', 'jpg']:
        return 'image/jpeg'
    elif extension == 'png':
        return 'image/png'
    elif extension == 'webp':
        return 'image/webp'
    else:
        return None

def upload_image(image_path, mime_type):
    print(f"Uploading file, file_path: {image_path}, mime_type: {mime_type}")

    with open(image_path, 'rb') as image_file:
        files = {
            'file': (os.path.basename(image_path), image_file, mime_type),
            'type': (None, mime_type),
            'messaging_product': (None, 'whatsapp')
        }
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}'
        }
        response = requests.post(FB_GRAPH_URL, headers=headers, files=files)
        return response.json()

def main():
    image_ids = {}
    for image_name in os.listdir(MEDIA_DIR):
        if image_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            image_path = os.path.join(MEDIA_DIR, image_name)
            mime_type = get_mime_type(image_name)
            if mime_type:
                response = upload_image(image_path, mime_type)
                if 'id' in response:
                    image_ids[image_name] = response['id']
                else:
                    print(f"Failed to upload {image_name}: {response}")
            else:
                print(f"Unsupported file type: {image_name}")
        else:
            print(f"Skipping non-image file: {image_name}")

    print(image_ids)

if __name__ == '__main__':
    main()
