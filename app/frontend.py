import streamlit as st
import requests
import os
import json
import re
import ast
import streamlit.components.v1 as components
import base64

API_URL = "http://localhost:8888"

st.title("3D Model Generator")

# --- Session state to store results ---
if "result" not in st.session_state:
    st.session_state.result = None
if "error" not in st.session_state:
    st.session_state.error = None

# --- FORM ---
with st.form(key="prompt_form"):
    prompt = st.text_area("Enter your prompt for 3D model generation", "A glowing dragon on a cliff at sunset")
    submit = st.form_submit_button("Generate")

    if submit:
        if prompt:
            payload = {"prompt": prompt}
            try:
                with st.spinner("Generating 3D model..."):
                    response = requests.post(f"{API_URL}/execution", json=payload)
                    response.raise_for_status()

                    try:
                        fixed_data = ast.literal_eval(response.text)
                        result = json.loads(fixed_data['message'])
                        st.session_state.result = result
                        st.session_state.error = None
                    except ValueError as e:
                        st.session_state.result = None
                        st.session_state.error = f"JSON parsing error: {e}\nRaw response: {response.text}"
            except requests.exceptions.RequestException as e:
                st.session_state.result = None
                st.session_state.error = f"API request error: {e}\nRaw response: {response.text if 'response' in locals() else 'No response'}"
        else:
            st.warning("Please enter a prompt.")

# --- SHOW RESULTS AFTER FORM SUBMISSION ---
if st.session_state.error:
    st.error(st.session_state.error)

if st.session_state.result:
    result = st.session_state.result

    image_path = result.get('image_path')
    model_path = result.get('model_path')

    if image_path:
        st.write(f"Image path: {image_path}, exists: {os.path.exists(image_path)}")
        if os.path.exists(image_path):
            st.image(image_path, caption="Generated Image", use_column_width=True)
            with open(image_path, "rb") as f:
                st.download_button(
                    label="Download Image",
                    data=f,
                    file_name=os.path.basename(image_path),
                    mime="image/png"
                )
        else:
            st.warning(f"Image file not found: {image_path}")
    else:
        st.warning("Image path not found in response.")

    if model_path:
        st.write(f"Model path: {model_path}, exists: {os.path.exists(model_path)}")
        if os.path.exists(model_path):
            with open(model_path, "rb") as f:
                st.download_button(
                    label="Download 3D Model",
                    data=f,
                    file_name=os.path.basename(model_path),
                    mime="model/gltf-binary"
                )
                if model_path and os.path.exists(model_path):
                    with open(model_path, "rb") as f:
                        glb_data = f.read()
                        glb_base64 = base64.b64encode(glb_data).decode()

                    # Embed model using <model-viewer> (Google's Web Component)
                    model_html = f"""
                    <html>
                    <head>
                    <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
                    </head>
                    <body style="margin: 0; padding: 0;">
                    <model-viewer 
                        src="data:model/gltf-binary;base64,{glb_base64}"
                        alt="3D model"
                        auto-rotate
                        camera-controls
                        style="width: 100%; height: 500px;">
                    </model-viewer>
                    </body>
                    </html>
                    """
                    
                    components.html(model_html, height=520)
        else:
            st.warning(f"3D model file not found: {model_path}")
    else:
        st.warning("3D model path not found in response.")
