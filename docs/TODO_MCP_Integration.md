---

## Status (Dato: [Indsæt Dato Her])

**Hovedmål: Fuld integration af Model Context Protocol (MCP) i Jarvis-Lite.**

**Udført:**
1.  **MCP Server Submodule:** `mcp-server` er tilføjet som et Git-submodule, og dets afhængigheder er installeret i Jarvis-Lites virtuelle miljø.
2.  **Grundlæggende MCP Tool:** En `open_url.py` tool-fil er oprettet i `mcp-server/python/tools/`.
3.  **MCP Client Wrapper:** `JarvisMCP`-klassen er oprettet i `src/llm/mcp_client.py` for at håndtere kommunikation med MCP-serveren.
4.  **Integration i `jarvis_main.py`:**
    *   `JarvisMCP`-klienten initialiseres.
    *   `handle_command`-funktionen er opdateret til at:
        *   Pushe `user_input` og `CONVERSATION_HISTORY` til MCP.
        *   Hente (beriget) kontekst fra MCP (variablen `ctx` er dog ikke anvendt endnu).
        *   Forsøge at kalde `invoke_tool` på MCP-serveren, hvis `llm_response` er et dictionary med et `intent` (f.eks. `open_url`).
5.  **Afhængigheder:** `mcp` er tilføjet til `requirements.txt`.
6.  **Test:** En basal testfil `tests/test_mcp.py` er oprettet for at tjekke session og context push/get.
7.  **Dokumentation:** `README.md` er opdateret med instruktioner til MCP-integration.
8.  **Kode Upload:** Alle ændringer er committet og pushet til `optimize/lightweight`-branchen.

---

## Næste Gang: Fokusområder & Opgaver

1.  **Python Modulstruktur (`__init__.py`):**
    *   **Opgave:** Opret en tom fil ved navn `__init__.py` i mappen `src/llm/`.
    *   **Hvorfor:** Dette er nødvendigt for, at Python genkender `src/llm` som et pakke-modul, hvilket løser `ModuleNotFoundError` ved import af `llm.mcp_client`.

2.  **Kørsel af MCP Server:**
    *   **Opgave:** Start altid MCP-serveren fra dens egen Python-mappe for at undgå `ModuleNotFoundError` for `mcp_server`.
    *   **Kommando (fra projektrod):**
        ```powershell
        cd mcp-server/python
        uvicorn mcp_server:app --reload --host 127.0.0.1 --port 8000
        ```
        (Husk at køre denne i en separat terminal eller som en baggrundsproces).

3.  **Kørsel af Jarvis-Lite:**
    *   **Opgave:** Start `jarvis_main.py` med korrekt `PYTHONPATH` sat, så `src`-mappen er i Pythons søgesti.
    *   **Kommando (fra projektrod, i en ny terminal efter MCP-serveren er startet):**
        ```powershell
        $env:PYTHONPATH="src"; python src/jarvis_main.py
        ```

4.  **Test af MCP-integration (`pytest`):**
    *   **Opgave:** Kør `pytest tests/test_mcp.py` for at verificere, at basiskommunikationen med MCP-serveren virker (session oprettelse, context push/get).
    *   **Forudsætning:** MCP-serveren skal køre.

5.  **Tilpasning af `generate_response` for Tool-kald:**
    *   **Problem:** `handle_command` i `jarvis_main.py` tjekker `if isinstance(llm_response, dict) and llm_response.get("intent") == "open_url":` for at udføre et tool-kald. Den nuværende `generate_response`-funktion returnerer dog altid en streng.
    *   **Opgave:** Modificer `generate_response`-funktionen (eller den LLM-logik den kalder), så den kan returnere et dictionary (f.eks. `{"intent": "open_url", "url": "https://youtube.com"}`), når et tool skal aktiveres. Hvis det er et almindeligt tekstsvar, kan den stadig returnere en streng.
    *   **Hvorfor:** Uden denne ændring vil `mcp.invoke_tool("open_url", ...)` aldrig blive kaldt.

6.  **End-to-End Test af Jarvis:**
    *   **Opgave:** Når ovenstående er på plads, test hele flowet:
        *   Start MCP-server.
        *   Start Jarvis-Lite.
        *   Giv en kommando som "Åbn YouTube".
        *   Verificer at `open_url`-tool'et på MCP-serveren kaldes, og browseren åbner.
        *   Test også almindelige samtaler for at sikre, at den normale LLM-respons stadig fungerer.

7.  **Udvid med Flere Tools:**
    *   **Opgave:** Overvej og implementer flere tools i `mcp-server/python/tools/` (f.eks. `read_file`, `save_note`, `get_time_mcp` etc.) og tilpas `generate_response` til at kunne returnere intents for disse.

---

Ved at følge disse punkter systematisk burde I kunne få MCP-integrationen fuldt operationel. Held og lykke! 