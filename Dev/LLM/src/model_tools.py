from transformers import AutoModelForCausalLM, AutoTokenizer
import os
import torch


def get_model_and_tokenizer(configDict):
    """Load model/tokenizer with proper settings"""
    model_name = configDict["model_name"]
    TORCH_DTYPE = configDict["torch_dtype"]
    DEVICE_CONFIG = configDict["device_config"]
    model_dir = configDict["model_dir"]+"/"+model_name.split("/")[1]
    print("Model directory:", model_dir)
    if not os.path.exists(model_dir):
        print("Downloading and saving model locally...")
        os.makedirs(model_dir, exist_ok=True)

        # Load with trust_remote_code for custom components
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=TORCH_DTYPE,
            device_map=DEVICE_CONFIG,
            trust_remote_code=True
        )
        model.save_pretrained(model_dir)

        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        tokenizer.save_pretrained(model_dir)
    else:
        print("Loading local model from", model_dir)
        model = AutoModelForCausalLM.from_pretrained(
            model_dir,
            torch_dtype=TORCH_DTYPE if TORCH_DTYPE != "auto" else None,
            device_map=DEVICE_CONFIG,
            trust_remote_code=True
        )

        if DEVICE_CONFIG == "mps":
            model = model.to(torch.device("mps"))

        # Load tokenizer with trust_remote_code
        tokenizer = AutoTokenizer.from_pretrained(
            model_dir,
            trust_remote_code=True
        )

    return model, tokenizer


def generate_response(prompt, tokenizer, model, max_new_tokens=1024):
    print("\n\n")
    print("*"*80)
    print("\n\nPrompt:\n\n")
    print(prompt)
    messages = [
        {"role": "system", "content": "You are a good teacher. you ansewer requests concisely without using filler words or sentences like 'sure ..', 'certainly ..', or 'of course'"},
        {"role": "user", "content": prompt}  # The user's input prompt
    ]
   #messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    input_length = inputs.input_ids.shape[1]
    outputs = model.generate(**inputs, max_new_tokens=max_new_tokens)
    output_ids = outputs[0][input_length:]
    response = tokenizer.decode(output_ids, skip_special_tokens=True)
    print("Generated response:\n\n")
    print(response)
    print("\n\n")
    return response
