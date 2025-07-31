To extend the Ollama model lifetime to 20 minutes before unloading on a Linux system, you can configure the `OLLAMA_KEEP_ALIVE` environment variable or use the `keep_alive` parameter in API requests. Below are the steps specific to Linux:

### Option 1: Set `OLLAMA_KEEP_ALIVE` for the Ollama Service
Most Linux distributions use systemd to manage the Ollama service. You can set the environment variable globally to keep models loaded for 20 minutes (1200 seconds).

1. **Edit the systemd service file**:
   ```bash
   sudo systemctl edit ollama.service
   ```
2. Add or modify the `[Service]` section to include:
   ```ini
   [Service]
   Environment="OLLAMA_KEEP_ALIVE=20m"
   ```
   Alternatively, you can use seconds:
   ```ini
   [Service]
   Environment="OLLAMA_KEEP_ALIVE=1200"
   ```
3. Save and exit the editor.
4. **Reload and restart the service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart ollama.service
   ```
5. **Verify the service is running**:
   ```bash
   systemctl status ollama.service
   ```

### Option 2: Set `OLLAMA_KEEP_ALIVE` for a User Session
If you’re running Ollama manually in a terminal (not as a service), set the environment variable before starting Ollama:
```bash
export OLLAMA_KEEP_ALIVE=20m
ollama serve
```
To make this persistent across sessions, add the export command to your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`):
```bash
echo 'export OLLAMA_KEEP_ALIVE=20m' >> ~/.bashrc
source ~/.bashrc
```

### Option 3: Set `keep_alive` via API Request
If you’re interacting with Ollama via its API, include the `keep_alive` parameter in your requests to keep the model loaded for 20 minutes:
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Hello, world!",
  "keep_alive": "20m"
}'
```
or
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Hello, world!",
  "keep_alive": 1200
}'
```

### Option 4: Running Ollama in Docker
If you’re using Docker on Linux:
```bash
docker run -d -e OLLAMA_KEEP_ALIVE=20m -p 11434:11434 ollama/ollama
```

### Verify the Configuration
Check which models are loaded and their remaining time:
```bash
ollama ps
```
This shows the model name, size, processor (CPU/GPU), and unload timer.

### Troubleshooting
- **Model unloads too soon**: Ensure no API calls override `keep_alive` with a shorter duration. Check the systemd service file for typos.
- **Service not picking up changes**: Run `sudo systemctl daemon-reload` and restart the service. Verify the environment variable with:
  ```bash
  sudo systemctl show ollama.service | grep OLLAMA_KEEP_ALIVE
  ```
- **System sleep issues**: If the system sleeps, Ollama may hang. Stop the service before sleep:
  ```bash
  sudo systemctl stop ollama.service
  ```

Setting `OLLAMA_KEEP_ALIVE=20m` via the systemd service is the most robust solution for persistent configuration on Linux.