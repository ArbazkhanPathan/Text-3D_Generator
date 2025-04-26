import logging
import os
from typing import Dict
from datetime import datetime, timedelta
import base64
import json
from ontology_dc8f06af066e4a7880a5938933236037.config import ConfigClass
from ontology_dc8f06af066e4a7880a5938933236037.input import InputClass
from ontology_dc8f06af066e4a7880a5938933236037.output import OutputClass
from openfabric_pysdk.context import State, AppModel
from core.stub import Stub
from ollama import Client
import uuid
import sqlite3

configurations: Dict[str, ConfigClass] = dict()


def config(configuration: Dict[str, ConfigClass], state: State) -> None:
    for uid, conf in configuration.items():
        logging.info(f"Saving new config for user with id:'{uid}'")
        configurations[uid] = conf


def expand_prompt(prompt: str, model_name: str = "llama3") -> str:
    try:
        # Step 1: Fetch ALL memory (or last N entries)
        memory_context = fetch_full_memory()

        # Step 2: Prepare final prompt
        final_prompt = f"""
        You have access to past creations. 
        Use them if it helps to understand the user's request.

        --- MEMORY START ---
        {memory_context}
        --- MEMORY END ---

        Now, based on the user's request:
        {prompt}
        """

        # Step 3: Call LLM
        client = Client(host='http://host.docker.internal:11434')
        response = client.chat(model=model_name, messages=[
            {"role": "user", "content": final_prompt.strip()}
        ])
        return response['message']['content']

    except Exception as e:
        logging.error(f"Failed to call local LLM: {e}")
        return "Make me a glowing dragon standing on a cliff at sunset."

def fetch_full_memory() -> str:
    try:
        conn = sqlite3.connect('memory.db')  # or wherever your db is
        cursor = conn.cursor()

        cursor.execute("SELECT timestamp, prompt FROM memory ORDER BY timestamp DESC LIMIT 50")  # fetch last 50 memories
        rows = cursor.fetchall()

        # Format nicely
        formatted = ""
        for timestamp, prompt in rows:
            formatted += f"[{timestamp}] {prompt}\n"

        return formatted.strip()

    except Exception as e:
        logging.warning(f"Memory fetch failedd: {e}")
        return ""

    finally:
        conn.close()

def init_memory_db(db_path='memory.db'):
    try:
        conn = sqlite3.connect(db_path)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                prompt TEXT,
                image_path TEXT,
                model_path TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logging.warning(f"Could not initialize memory DB: {e}")

# Save to memory database
def remember(prompt: str, image_path: str, model_path: str, db_path='memory.db'):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO memory (timestamp, prompt, image_path, model_path)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), prompt, image_path, model_path))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.warning(f"Could not save memory: {e}")

def execute(model: AppModel) -> None:
    request: InputClass = model.request
    response: OutputClass = model.response

    user_config: ConfigClass = configurations.get('super-user', None)
    logging.info(f"User Configuration: {user_config}")

    app_ids = user_config.app_ids if user_config else []
    stub = Stub(app_ids)

    original_prompt = request.prompt
    chat_prompt = expand_prompt(original_prompt)
    logging.info(f"Chat Prompt: {chat_prompt}")
    expanded_prompt = chat_prompt
    logging.info(f"Expanded Prompt: {expanded_prompt}")

    image_obj = stub.call('c25dcd829d134ea98f5ae4dd311d13bc.node3.openfabric.network', {"prompt": expanded_prompt}, "super-user")
    image_data = image_obj.get("result")

    unique_id = str(uuid.uuid4())
    image_path = f"output_image_{unique_id}.png"
    with open(image_path, "wb") as f:
        f.write(image_data)
    logging.info(f"Saved image to {image_path}")

    with open(image_path, "rb") as f:
        image_bytes = f.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        logging.info(f"Encoded image size: {len(image_b64)}")

    model_obj = stub.call("f0b5f319156c4819b9827000b17e511a.node3.openfabric.network", {"input_image": image_b64}, "super-user")
    generated_object=model_obj.get("generated_object")
    video_object=model_obj.get("video_object")
    logging.info(f"generated_object: {generated_object[:10]}")
    logging.info(f"video_object: {video_object}")
    model_data_b64 = model_obj.get("generated_object") if model_obj else None
    if not model_data_b64:
        raise ValueError("No 3D model generated or 'result' is None")

    model_data = model_data_b64
    model_path = f"output_model_{unique_id}.glb"
    with open(model_path, "wb") as f:
        f.write(model_data)
    logging.info(f"Saved 3D model to {model_path}")
    init_memory_db()
    remember(chat_prompt, image_path, model_path)

    response.message = json.dumps({
    "status": "success",
    "message": "✅ Generated 3D model from your idea!",
    "image_path": image_path,
    "model_path": model_path
    })