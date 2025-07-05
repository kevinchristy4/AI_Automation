# System Prompt: Modular Service-Based Intelligent Web Automation Agent System

## 🧩 Objective

Build a test automation AI agent system that can:

- Accept natural language instructions (e.g., "login to example.com and click 'OK'")
- Open a browser and navigate to the page using Playwright
- Capture DOM and screenshot of the current page
- Ask a locally hosted LLM (via Ollama) to resolve natural language to DOM locators (like `text="Login"`)
- Use the resolved locator to perform actions (click, fill, etc.)
- Track test steps, memory, retries, and page context across steps

## 🧱 Overall Architecture

This is a microservices-based system. Each module runs as a FastAPI service and communicates over HTTP JSON APIs. Here's the full list:

1. **LLM Service (/llm)**  
   - Purpose: Resolve locators and break down test instructions into plans  
   - Tech: FastAPI + Ollama REST calls  
   - Routes: `/llm/plan`, `/llm/resolve-locator`

2. **Observer Service (/observe)**  
   - Purpose: Launch browser and capture page state  
   - Tech: FastAPI + Playwright (persistent browser context)  
   - Routes: `/navigate`, `/state` (returns DOM + screenshot)

3. **Executor Service (/execute)**  
   - Purpose: Receive locator and perform an action (click, fill, etc.)  
   - Tech: FastAPI + Playwright  
   - Routes: `/execute`

4. **Memory Service (/memory)**  
   - Purpose: Save locator mappings, test state, step logs, retry info  
   - Tech: FastAPI + Redis or TinyDB  
   - Routes: `/get`, `/set`, `/append-log`

5. **Planner Service (/planner)**  
   - Purpose: Break instructions into action steps  
   - Tech: FastAPI + call `/llm/plan`  
   - Routes: `/plan`

6. **Locator Resolver Service (/resolve)**  
   - Purpose: Use LLM with DOM + screenshot to resolve Playwright locator  
   - Tech: FastAPI + call `/llm/resolve-locator`  
   - Routes: `/resolve-locator`

7. **MCP Orchestrator (/mcp)**  
   - Purpose: Run the full test plan by invoking services in sequence  
   - Tech: FastAPI + Async orchestration loop  
   - Routes: `/execute-plan`

---

## 🔄 End-to-End Sample Flow

Given input:  
Login to www.example.com using credentials, click preferences, and logout.


1. `/planner/plan` returns:
```json
[
  { "action": "navigate", "url": "https://example.com" },
  { "action": "fill", "field": "username", "value": "example" },
  { "action": "fill", "field": "password", "value": "example123" },
  { "action": "click", "description": "login button" },
  { "action": "click", "description": "preference button" },
  { "action": "click", "description": "logout" }
]
```
2./observe/state gives DOM + screenshot

3./llm/resolve-locator → returns Playwright locator

4./execute → performs click/fill

5./memory/append-log → tracks progress

6.Loop continues for each step


Tech Stack

    Python 3.10+
    FastAPI for all services
    Playwright (Python) for browser control
    Ollama (gemma3) for local LLM inference
    Redis or TinyDB for memory
    Docker Compose to wire services together

Docker Compose Services:
llm:
  build: ./services/llm_service
  ports: ["8001:8000"]

observer:
  build: ./services/observer_service
  ports: ["8002:8000"]

executor:
  build: ./services/executor_service
  ports: ["8003:8000"]

memory:
  build: ./services/memory_service
  ports: ["8004:8000"]

planner:
  build: ./services/planner_service
  ports: ["8005:8000"]

orchestrator:
  build: ./services/orchestrator_mcp
  ports: ["8000:8000"]


Implementation Notes

    - Each FastAPI service should expose JSON endpoints.
    - Shared objects like browser page must persist across requests.
    - DOM and screenshot should be sent to the LLM as input.
    - Playwright actions should log success/failure and update memory.
    - Prompt engineering is key to resolving fuzzy locator descriptions.

Codegen Goals

    - Start by scaffolding llm_service, observer_service, and executor_service.
    - All services must include:
        1.Pydantic request/response models
        2.FastAPI endpoints
        3.Logging
    - Orchestrator must be async-capable, able to call all services and retry if needed.
    - Generate OpenAPI-compatible APIs for each service.
    - Write clean, modular, containerizable Python code using best practices.

Proceed with generating service code step-by-step based on this architecture. 