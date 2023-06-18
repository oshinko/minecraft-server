# mcops

Minecraft server maintenance package.

install:

```sh
pip install "mcops @ git+https://github.com/oshinko/minecraft-server.git#subdirectory=ops"
```

if you use OpenAI LLM:

```sh
pip install "mcops[openai] @ git+https://github.com/oshinko/minecraft-server.git#subdirectory=ops"
read -sp "OpenAI API Key: " openai_api_key; echo
```

test:

```sh
webhook=your-discord-webhook
WEBHOOK=$webhook OPENAI_API_KEY=$openai_api_key python -m tests
```
