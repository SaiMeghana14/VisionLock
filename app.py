import streamlit as st
from PIL import Image
import io
import base64
from utils.helpers import pil_to_base64, check_face, log_access
from utils.aws_clients import s3, IOT_TOPIC, iot, ALERT_TOPIC_ARN, sns

st.set_page_config(page_title="VisionLock Dashboard", layout="wide")

st.title("VisionLock — Smart AI Door Lock")
st.sidebar.header("Controls")

# ------------------------------
# Lock / Unlock
# ------------------------------
cmd = st.sidebar.selectbox("Lock Control", ["Select", "Lock", "Unlock"])
if st.sidebar.button("Send Command") and cmd != "Select":
    payload = {"cmd": cmd.lower()}
    iot.publish(topic=IOT_TOPIC, qos=0, payload=str(payload))
    st.sidebar.success(f"Sent {cmd} command to door")

# ------------------------------
# Live Feed / Upload
# ------------------------------
st.header("Live Camera Feed / Upload Image")
uploaded_file = st.file_uploader("Upload a snapshot from door camera:", type=["jpg", "jpeg", "png"])
if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Uploaded Door Snapshot", use_column_width=True)

    image_bytes = io.BytesIO()
    img.save(image_bytes, format='JPEG')
    image_bytes = image_bytes.getvalue()

    known, user_id = check_face(image_bytes)
    if known:
        st.success(f"Access Granted: {user_id}")
        log_access(user_id, "access_granted")
    else:
        st.warning("Unknown Face! Intruder Alert Triggered.")
        # upload to S3
        key = f"intruders/{uploaded_file.name}"
        s3.put_object(Bucket=os.getenv("S3_BUCKET"), Key=key, Body=image_bytes, ContentType='image/jpeg')
        log_access("UNKNOWN", "unknown_face", s3_key=key)
        # trigger SNS alert if configured
        if ALERT_TOPIC_ARN:
            sns.publish(TopicArn=ALERT_TOPIC_ARN, Subject="Intruder Alert!", Message=f"Unknown face captured: s3://{os.getenv('S3_BUCKET')}/{key}")

# ------------------------------
# User Registration
# ------------------------------
st.header("Register New User")
user_id = st.text_input("User ID")
new_file = st.file_uploader("Upload user face image:", type=["jpg", "jpeg", "png"], key="reg")
if st.button("Register User"):
    if user_id and new_file:
        image_bytes = new_file.read()
        from utils.aws_clients import rekognition, s3
        # Index face
        rekognition.index_faces(
            CollectionId=os.getenv("REKOGNITION_COLLECTION"),
            Image={'Bytes': image_bytes},
            ExternalImageId=user_id
        )
        # store original to S3
        s3.put_object(Bucket=os.getenv("S3_BUCKET"), Key=f"enrolled/{user_id}/{new_file.name}", Body=image_bytes, ContentType='image/jpeg')
        st.success(f"User {user_id} registered successfully!")
    else:
        st.error("User ID and image required!")

# ------------------------------
# Access Logs (DynamoDB)
# ------------------------------
st.header("Recent Access Logs")
from utils.aws_clients import dynamodb
table = dynamodb.Table(os.getenv("DYNAMODB_TABLE"))
response = table.scan()
items = response.get('Items', [])
if items:
    for log in sorted(items, key=lambda x: x.get('timestamp',''), reverse=True)[:20]:
        st.write(log)
else:
    st.info("No logs yet.")
