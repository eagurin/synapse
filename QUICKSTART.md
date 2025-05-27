# 🚀 Synapse Quick Start Guide

## Prerequisites

- Docker & Docker Compose
- At least one LLM API key (OpenAI, Anthropic, etc.)
- 5 minutes ⏱️

## Step 1: Clone & Setup

```bash
# Clone the repository
git clone https://github.com/eagurin/synapse.git
cd synapse

# Initial setup
make setup
```

## Step 2: Configure API Keys

Edit `.env` file with your API keys:

```bash
# Required: At least one LLM provider
OPENAI_API_KEY=sk-...        # If you have OpenAI
ANTHROPIC_API_KEY=sk-ant-... # If you have Anthropic

# Optional: Add more providers
GOOGLE_API_KEY=...
MISTRAL_API_KEY=...
```

## Step 3: Start Synapse

```bash
# Start all services
make docker-up

# Check logs
make docker-logs
```

Synapse is now running at `http://localhost:8000` 🎉

## Step 4: Configure Your IDE

### For Cursor

1. Open Cursor Settings (⌘+,)
2. Go to **Models** → **Add Model**
3. Configure:
   - Model ID: `synapse`
   - API Base: `http://localhost:8000/v1`
   - API Key: `your-api-key` (from .env)

### For Cline (VSCode)

Add to settings.json:
```json
{
  "cline.apiProvider": "openai",
  "cline.apiUrl": "http://localhost:8000/v1",
  "cline.apiKey": "your-api-key",
  "cline.model": "synapse"
}
```

### For Continue

Edit `~/.continue/config.json`:
```json
{
  "models": [{
    "title": "Synapse",
    "provider": "openai",
    "model": "synapse",
    "apiKey": "your-api-key",
    "apiBase": "http://localhost:8000/v1"
  }]
}
```

## Step 5: Test It Out

```bash
# Test the API
curl http://localhost:8000/health

# Test chat completion
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "synapse",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## 📚 Next Steps

1. **Index Your Documentation**
   ```bash
   # Upload your docs
   curl -X POST http://localhost:8000/api/documents/upload \
     -H "Authorization: Bearer your-api-key" \
     -F "files=@docs/README.md"
   ```

2. **Enable Memory**
   - Synapse automatically remembers conversations
   - Use `X-User-ID` header for user-specific memory

3. **Add Custom Tools**
   - Check `examples/mcp_tools.py` for MCP examples

## 🛟 Troubleshooting

### "Connection refused"
- Check if services are running: `docker ps`
- Check logs: `make docker-logs`

### "Invalid API key"
- Make sure your .env file has valid API keys
- Restart services: `make docker-down && make docker-up`

### "Out of memory"
- Synapse needs ~2GB RAM minimum
- Reduce vector dimensions in config if needed

## 🤝 Need Help?

- 📖 [Full Documentation](https://github.com/eagurin/synapse/wiki)
- 💬 [Discord Community](https://discord.gg/synapse)
- 🐛 [Report Issues](https://github.com/eagurin/synapse/issues)