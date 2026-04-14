# Hugging Face Token Syntax

This note explains how to use Hugging Face models with a token stored in `.env`.

## Official behavior

According to the Hugging Face docs:

- `HF_TOKEN` is the standard environment variable for Hub authentication.
- `huggingface_hub` reads environment variables at import time, so the token must be set before importing Hugging Face libraries.
- Libraries such as `transformers` and `huggingface_hub` also support an explicit `token=` parameter.

Primary docs:

- https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables
- https://huggingface.co/docs/huggingface_hub/quick-start#authentication
- https://huggingface.co/docs/transformers/main_classes/model
- https://huggingface.co/docs/transformers/main_classes/pipelines

## `.env` format

Put your token in `.env` like this:

```env
HF_TOKEN=hf_your_token_here
```

Use a `read` token unless you actually need write access.

## Important repo-specific caveat

In this repo, [backend/app/config.py](backend/app/config.py) uses `pydantic-settings` with the prefix `INTELMEDIA_`, and it does not currently declare an `env_file`. That means a bare `HF_TOKEN` in the repo root `.env` is not automatically loaded into Python just because the file exists.

In practice, one of these must be true before importing `transformers` or `huggingface_hub`:

- the shell already exported `HF_TOKEN`
- Docker Compose passed `HF_TOKEN` into the container
- your Python code loaded `.env` explicitly

## Recommended Python pattern

If you want Python to read the local `.env` file directly, use `python-dotenv`:

```python
import os

from dotenv import load_dotenv

load_dotenv()

hf_token = os.getenv("HF_TOKEN")
if not hf_token:
    raise RuntimeError("HF_TOKEN is missing")
```

Then load models with either implicit env auth or explicit `token=`.

## `transformers` examples

### 1. Implicit auth from `HF_TOKEN`

If `HF_TOKEN` is already in the environment before import, this is enough:

```python
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

model_id = "openai/whisper-large-v3"

processor = AutoProcessor.from_pretrained(model_id)
model = AutoModelForSpeechSeq2Seq.from_pretrained(model_id)
```

This is the cleanest approach when the process environment is already correct.

### 2. Explicit `token=` parameter

This is safer when you want to be explicit:

```python
import os

from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer

load_dotenv()
hf_token = os.getenv("HF_TOKEN")

model_id = "meta-llama/Llama-3.1-8B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_id, token=hf_token)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    token=hf_token,
    device_map="auto",
)
```

Use the same pattern for other classes:

```python
from transformers import AutoModelForSeq2SeqLM, AutoProcessor, AutoTokenizer

AutoTokenizer.from_pretrained(model_id, token=hf_token)
AutoProcessor.from_pretrained(model_id, token=hf_token)
AutoModelForSeq2SeqLM.from_pretrained(model_id, token=hf_token)
```

### 3. `pipeline(...)`

`pipeline` also accepts `token=`:

```python
import os

from dotenv import load_dotenv
from transformers import pipeline

load_dotenv()
hf_token = os.getenv("HF_TOKEN")

translator = pipeline(
    task="translation",
    model="facebook/nllb-200-distilled-600M",
    token=hf_token,
    device_map="auto",
)
```

For ASR:

```python
asr = pipeline(
    task="automatic-speech-recognition",
    model="openai/whisper-large-v3",
    token=hf_token,
    device_map="auto",
)
```

## `huggingface_hub` examples

Download files directly from the Hub:

```python
import os

from dotenv import load_dotenv
from huggingface_hub import hf_hub_download

load_dotenv()
hf_token = os.getenv("HF_TOKEN")

path = hf_hub_download(
    repo_id="openai/whisper-large-v3",
    filename="config.json",
    token=hf_token,
)
```

Check auth:

```python
import os

from dotenv import load_dotenv
from huggingface_hub import whoami

load_dotenv()
hf_token = os.getenv("HF_TOKEN")

print(whoami(token=hf_token))
```

## Docker Compose pattern

If the backend will run in Docker, pass `HF_TOKEN` into the container explicitly. Example:

```yaml
services:
  backend:
    env_file:
      - .env
    environment:
      - HF_TOKEN=${HF_TOKEN}
```

Without that, the token in the repo root `.env` will not automatically appear inside the backend container.

## Practical advice for IntelMedIA

For this repo, the lowest-friction approach is:

1. Keep `HF_TOKEN` in `.env`.
2. Pass it into Docker Compose or load it with `load_dotenv()` in Python before importing HF libraries.
3. Use explicit `token=hf_token` in `from_pretrained(...)`, `pipeline(...)`, and `hf_hub_download(...)`.
4. Avoid hardcoding tokens in source files.

That gives you predictable behavior for gated or private models and avoids relying on machine-local `hf auth login` state.
