import base64
from PIL import Image
import io
import json
from .aws_clients import rekognition, s3, dynamodb, SAGEMAKER_ENDPOINT

def pil_to_base64(img: Image.Image) -> str:
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

def check_face(image_bytes):
    """Call Rekognition to check if face is known."""
    resp = rekognition.search_faces_by_image(
        CollectionId=os.getenv("REKOGNITION_COLLECTION"),
        Image={'Bytes': image_bytes},
        MaxFaces=1,
        FaceMatchThreshold=85
    )
    if resp['FaceMatches']:
        user_id = resp['FaceMatches'][0]['Face']['ExternalImageId']
        return True, user_id
    return False, None

def log_access(user_id, event, s3_key=None):
    table = dynamodb.Table(os.getenv("DYNAMODB_TABLE"))
    table.put_item(Item={
        'userId': user_id,
        'event': event
    })
