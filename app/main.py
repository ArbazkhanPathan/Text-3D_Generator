import logging
import os
from typing import Dict
from datetime import datetime
import base64
import json
from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass
from ontology_dc8f06af066e4a7880a5938933236037.input import InputClass
from ontology_dc8f06af066e4a7880a5938933236037.output import OutputClass
from openfabric_pysdk.context import State, AppModel
from core.stub import Stub
from ollama import Client

# App IDs from Openfabric Challenge
TEXT_TO_IMAGE_APP = 'f0997a01-d6d3-a5fe-53d8-561300318557'
IMAGE_TO_3D_APP = '69543f29-4d41-4afc-7f29-3d51591f11eb'

configurations: Dict[str, ConfigClass] = dict()


def config(configuration: Dict[str, ConfigClass], state: State) -> None:
    for uid, conf in configuration.items():
        logging.info(f"Saving new config for user with id:'{uid}'")
        configurations[uid] = conf


def expand_prompt(prompt: str, model_name: str = "llama3") -> str:
    try:
        client = Client(host='http://localhost:11434')
        response = client.chat(model=model_name, messages=[
            {"role": "user", "content": prompt}
        ])
        return response['message']['content']
    except Exception as e:
        logging.error(f"Failed to call local LLM: {e}")
        return "Make me a glowing dragon standing on a cliff at sunset."


def remember(prompt: str, image_path: str, model_path: str):
    try:
        with open("memory.txt", "a") as f:
            f.write(f"{datetime.now()}\nPrompt: {prompt}\nImage: {image_path}\nModel: {model_path}\n\n")
    except Exception as e:
        logging.warning(f"Could not save memory: {e}")


def execute(model: AppModel) -> None:
    request: InputClass = model.request
    response: OutputClass = model.response

    user_config: ConfigClass = configurations.get('super-user', None)
    logging.info(f"User Configuration: {user_config}")

    # Initialize Openfabric app stub
    app_ids = user_config.app_ids if user_config else []
    stub = Stub(app_ids)

    # Step 1: Expand prompt with local LLM
    original_prompt = request.prompt
    expanded_prompt = expand_prompt(original_prompt)
    logging.info(f"Expanded Prompt: {expanded_prompt}")

    # Step 2: Call Text-to-Image app
    image_obj = stub.call('c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network', {"prompt": expanded_prompt}, "super-user")
    image_data = image_obj.get("result")

    # Save image to file
    image_path = "output_image.png"
    with open(image_path, "wb") as f:
        f.write(image_data)
    logging.info("Saved image to output_image.png")

    # Step 3: Call Image-to-3D app
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        logging.info(f"Encoded image size: {len(image_b64)}")

    logging.info(f"Image-path: {image_path}")
    model_obj = stub.call("f0b5f319156c4819b9827000b17e511a.node3.openfabric.network", {"input_image": image_b64}, "super-user")

    generated_object=model_obj.get("generated_object")
    video_object=model_obj.get("video_object")
    logging.info(f"generated_object: {generated_object[:10]}")
    logging.info(f"video_object: {video_object}")
    model_data_b64 = model_obj.get("generated_object") if model_obj else None
    if not model_data_b64:
        raise ValueError("No 3D model generated or 'result' is None")

    model_data = model_data_b64
    model_path = "output_model.glb"
    with open(model_path, "wb") as f:
        f.write(model_data)

    logging.info("Saved 3D model to output_model.glb")


    # Step 4: Memory
    remember(original_prompt, image_path, model_path)

    # Step 5: Prepare API Response
    response.message = f"✅ Generated 3D model from your idea!\n\n🖼️ Image: {image_path}\n🧱 3D path: {model_path}"
