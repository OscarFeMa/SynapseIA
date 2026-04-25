"""Test debug de OpenRouter SSE"""
import asyncio
import httpx
import json

async def test():
    settings = {
        "OPENROUTER_API_KEY": "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",
        "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
        "OPENROUTER_HTTP_REFERER": "http://localhost:3000",
        "OPENROUTER_APP_NAME": "SynapseCouncil"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings['OPENROUTER_API_KEY']}",
        "HTTP-Referer": settings["OPENROUTER_HTTP_REFERER"],
        "X-Title": settings["OPENROUTER_APP_NAME"]
    }
    
    payload = {
        "model": "anthropic/claude-3.5-haiku",
        "messages": [{"role": "user", "content": "Hola, responde brevemente."}],
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": True
    }
    
    print("📡 Enviando petición a OpenRouter...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream(
            "POST",
            f"{settings['OPENROUTER_BASE_URL']}/chat/completions",
            json=payload,
            headers=headers
        ) as response:
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print("\n📨 Respuesta SSE:")
            
            line_count = 0
            async for line in response.aiter_lines():
                line_count += 1
                if line.strip():
                    print(f"L{line_count}: {line[:100]}")
                    
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            print("✅ Stream completado ([DONE])")
                            break
                        try:
                            data = json.loads(data_str)
                            print(f"  Parsed: {json.dumps(data, indent=2)[:200]}")
                            
                            # Ver estructura
                            if "choices" in data:
                                for i, choice in enumerate(data["choices"]):
                                    print(f"  Choice[{i}]: {choice.keys()}")
                                    if "delta" in choice:
                                        print(f"    Delta: {choice['delta']}")
                                    if "text" in choice:
                                        print(f"    Text: {choice['text'][:50]}")
                                    if "content" in choice:
                                        print(f"    Content: {choice['content'][:50]}")
                        except json.JSONDecodeError as e:
                            print(f"  JSON Error: {e}")
                
                if line_count > 50:  # Límite de seguridad
                    print("⚠️ Límite de líneas alcanzado")
                    break

if __name__ == "__main__":
    asyncio.run(test())
