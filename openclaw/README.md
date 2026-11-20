# OpenClaw

Capa de orquestacion del agente. Contiene la identidad, las reglas y la skill
`finanzas` con las que el agente interpreta los mensajes. No contiene reglas
de negocio ni accede a PostgreSQL.

## Como se conecta con el resto del sistema

```text
Interfaz web --(JWT)--> POST /chat (FastAPI) --> OpenClaw /v1/chat/completions --> LLM
                              ^                         |
                              |   tool elegida + datos  |
                              +-------------------------+
                 FastAPI ejecuta la tool con el usuario del JWT y valida todo
```

- El backend envia el mensaje y la lista de tools al endpoint compatible con OpenAI del gateway.
- OpenClaw y el LLM devuelven que tool usar y con que parametros.
- El backend ejecuta la tool con el usuario autenticado. El agente nunca indica el usuario.

Para usar OpenClaw como proveedor, en `backend/.env`:

```text
LLM_BASE_URL=http://127.0.0.1:18789/v1
LLM_API_KEY=<token del gateway>
LLM_MODEL=openclaw/finanzas_personales
```

Como el protocolo es el de OpenAI, el mismo backend puede apuntar directo a un
proveedor (por ejemplo Gemini), que es lo que se usa en el despliegue online,
donde no corre el gateway. Cambiar de proveedor no modifica la logica financiera.

## Puesta en marcha (Windows / PowerShell)

1. Copiar `.env.example` a `.env` y completar los valores.
2. Crear el entorno del servidor MCP:
   ```powershell
   cd openclaw\tools-mcp
   python -m venv .venv
   .\.venv\Scripts\pip install -r requirements.txt
   ```
3. En `openclaw.patch.json5`, reemplazar `RUTA_PROYECTO` por la ruta absoluta del repo,
   con barras `/` (ej. `C:/Users/nombre/TP_FINAL`).
4. Activar la config del proyecto y aplicar el parche:
   ```powershell
   cd openclaw
   . .\scripts\use-project.ps1
   openclaw config patch --file .\openclaw.patch.json5 --dry-run
   openclaw config patch --file .\openclaw.patch.json5
   ```
5. Elegir el modelo (`openclaw models set <proveedor/modelo>`) y levantar el gateway:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\start.ps1
   ```

`scripts/probe-models.ps1` prueba que modelos de Gemini tienen cuota con tu clave.

## Servidor MCP (`tools-mcp/`)

Alternativa para probar el agente desde la consola de OpenClaw. Llama a `/tools/*`
del backend con un usuario de prueba fijo (`AGENT_USER_EMAIL`). No se usa en el
canal web, porque ahi la identidad sale del login.
