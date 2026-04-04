import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import edge_tts
from groq import AsyncGroq

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ¡ASEGÚRATE DE PONER TU LLAVE AQUÍ!
cliente_groq = AsyncGroq(api_key="apiaqui")

@app.get("/")
async def get_dashboard():
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🟢 [SISTEMA] Cliente Web Conectado exitosamente.")
    historial = []
    
    voz = "es-MX-JorgeNeural"
    velocidad = "+15%"
    tono = "-10Hz"
    volumen = "+20%"

    try:
        while True:
            # NUEVO MÉTODO BLINDADO PARA RECIBIR DATOS
            texto_recibido = await websocket.receive_text()
            data = json.loads(texto_recibido)

            # 1. ENRUTADOR DE ESCENARIOS
            if "config_escenario" in data:
                print("⚙️ [SISTEMA] Recibiendo configuración del caso...")
                c = data["config_escenario"]
                tipo = c.get("tipo", "soporte")

                # --- NUEVA LÓGICA DE NOMBRES ---
                nombre_completo = c.get("nombre", "Cliente")
                nombre_corto = nombre_completo.split()[0] # Esto extrae solo la primera palabra (El primer nombre)
                # -------------------------------

                if tipo == "soporte":
                    prompt_dinamico = f"""ACTÚA EXCLUSIVAMENTE COMO {c['nombre']}, UN CLIENTE REAL Y MUY MOLESTO DE IZZI. EL USUARIO ES EL AGENTE DE SOPORTE.
REGLA DE ORO: TÚ ERES EL CLIENTE. NUNCA ofrezcas ayuda, nunca saludes primero y NUNCA preguntes "¿En qué puedo ayudar?". Tú eres quien tiene el problema y el agente debe resolvértelo.
REGLAS: Eres impaciente y sarcástico. Respuestas de máximo 15 palabras. RESPONDE SÓLO LO QUE TE PREGUNTAN. NO menciones tu problema hasta que el agente te pregunte el motivo de tu llamada.
MEMORIA:
- Identidad: Tu nombre COMPLETO oficial en la cuenta es "{nombre_completo}". 
  REGLA ESTRICTA: Al inicio de la llamada, si te preguntan con quién hablan, di SOLO tu primer nombre: "Soy {nombre_corto}". 
  NUNCA digas tus apellidos a menos que el agente te pida EXPLÍCITAMENTE que le "confirmes tu nombre completo" o "tus apellidos". Si te lo pide así, responde con fastidio: "Sí, soy {nombre_completo}, ¿qué no lo está viendo en su pantalla?".- Titular: Sí, yo soy el titular de la cuenta.
- Cuenta: Mi cuenta es {c['cuenta']} (Dala solo si la piden).
- Problema: {c['problema']} e improvisa algo mas relacionado al problema
- Tiempo de espera: Si te piden tiempo de espera, responde: si pero no te tardes
- OS/Folio: me dieron la {c['os']} (Dala solo si piden reporte, folio, orden de servicio).
- Exigencia Agenda: Acepta reagendar SÓLO si te ofrecen EXACTAMENTE la fecha {c.get('fecha', '')} en el turno {c.get('turno', '')}. Si te ofrecen eso, di: "Pésimo servicio, pero ni modo, reagéndelo". Si no, recházalo molesto.
- Cierre: No contestarás encuestas. Adiós."""

                elif tipo == "facturacion":
                    prompt_dinamico = f"""ACTÚA EXCLUSIVAMENTE COMO {c['nombre']}, UN CLIENTE REAL Y MUY MOLESTO DE IZZI POR COBROS EXCESIVOS. EL USUARIO ES EL AGENTE.
REGLA DE ORO: TÚ ERES EL CLIENTE. NUNCA ofrezcas ayuda ni preguntes "¿En qué puedo ayudar?". Tú eres quien exige respuestas.
REGLAS: Eres desconfiado. Respuestas cortas. RESPONDE SÓLO LO QUE TE PREGUNTAN. NO menciones tu saldo hasta que pregunten "¿En qué le ayudo?".
MEMORIA:
- Identidad: Si te preguntan con quién hablan, di SOLO: "Soy {c['nombre']}, explíqueme por qué me están robando."
- Titular: Sí, yo soy.
- Cuenta: {c['cuenta']} (Dala solo si la piden).
- Problema: {c['problema']}
- Saldo: Te cobran {c.get('saldo', '')}. Exiges explicación.
- Vencimiento: Sabes que vence el {c.get('vencimiento', '')}.
- Resolución: SÓLO te calmarás si te explican el cargo. Si solo dicen "tiene que pagar", exige un supervisor.
- Cierre: No contestarás encuestas. Adiós."""

                historial = [{"role": "system", "content": prompt_dinamico}]
                print(f"✅ [SISTEMA] Cerebro '{tipo.upper()}' inyectado. Listo para hablar.")
                await websocket.send_text(json.dumps({"tipo": "sistema", "texto": f"🚀 Escenario '{tipo.upper()}' cargado y listo."}))
                continue

            # 2. AUDITOR DE CALIDAD (QA) - VERSIÓN MANUAL IZZI
            elif "accion" in data and data["accion"] == "evaluar":
                transcripcion = data["transcripcion"]
                print("📊 [QA] Analizando transcripción con reglas de izzi...")
                
                prompt_qa = f"""ERES UN AUDITOR DE CALIDAD (QA) ESTRICTO DE IZZI. Tu misión es evaluar la llamada del agente según el manual oficial de calidad.

CRITERIOS DE EVALUACIÓN OFICIALES (Base 100 puntos):
1. APERTURA (20 pts): ¿El agente agradeció la llamada, dijo su nombre, identificó al cliente y mencionó explícitamente la empresa 'izzi'?
2. CORTESÍA Y ETIQUETA (20 pts): ¿Se dirigió al cliente de 'Usted', usó palabras de cortesía (por favor/gracias) y mantuvo el profesionalismo?
3. EMPATÍA Y DISCULPA (20 pts): Ante el reclamo del cliente, ¿ofreció una disculpa explícita por la falla del servicio o el inconveniente? (Obligatorio).
4. SONDEO Y VALIDACIÓN (20 pts): ¿Entendió el problema sin hacer que el cliente repitiera información que ya había dado?
5. SOLUCIÓN Y CIERRE (20 pts): ¿Confirmó la solución/acuerdo y realizó el cierre correcto (agradecer, ofrecer ayuda adicional y despedirse)?

TRANSCRIPCIÓN DE LA LLAMADA:
{transcripcion}

FORMATO DE RESPUESTA OBLIGATORIO:
CALIFICACIÓN FINAL: [X]/100 puntos

DETALLE POR RUBRO:
- Apertura: ✅ [o ❌] [Nota/20] - [Justificación corta]
- Cortesía: ✅ [o ❌] [Nota/20] - [Justificación corta]
- Empatía: ✅ [o ❌] [Nota/20] - [Justificación corta]
- Sondeo: ✅ [o ❌] [Nota/20] - [Justificación corta]
- Cierre: ✅ [o ❌] [Nota/20] - [Justificación corta]

💡 FEEDBACK PARA EL AGENTE:
[1 tip de mejora muy puntual y directo basado en los errores]"""
                try:
                    completion = await cliente_groq.chat.completions.create(
                        model="llama-3.3-70b-versatile", 
                        messages=[{"role": "user", "content": prompt_qa}], 
                        temperature=0.2 # Temperatura baja para que sea un juez estricto y objetivo
                    )
                    await websocket.send_text(json.dumps({"tipo": "evaluacion", "texto": completion.choices[0].message.content}))
                    print("✅ [QA] Evaluación de izzi enviada al navegador.")
                except Exception as e:
                    print(f"❌ [ERROR QA]: {e}")
                continue

            # 3. PROCESAMIENTO NORMAL DE VOZ
            texto_procesar = ""
            if "texto_agente" in data:
                texto_procesar = data["texto_agente"]
                print(f"🎙️ Agente: {texto_procesar}")
            elif "silencio" in data:
                texto_procesar = "[El agente se ha quedado en silencio por mucho tiempo. Quéjate amargamente por la espera]."
                print("⏳ [SISTEMA] Silencio detectado. Disparando queja.")

            if texto_procesar and historial:
                historial.append({"role": "user", "content": texto_procesar})
                try:
                    completion = await cliente_groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=historial, temperature=0.6)
                    respuesta_ia = completion.choices[0].message.content
                    print(f"🤖 Cliente: {respuesta_ia}")
                    historial.append({"role": "assistant", "content": respuesta_ia})
                    await websocket.send_text(json.dumps({"tipo": "respuesta", "texto": respuesta_ia}))

                    comunicador = edge_tts.Communicate(text=respuesta_ia, voice=voz, rate=velocidad, pitch=tono, volume=volumen)
                    audio_generado = b""
                    async for chunk in comunicador.stream():
                        if chunk["type"] == "audio":
                            audio_generado += chunk["data"]
                    await websocket.send_bytes(audio_generado)
                except Exception as e:
                    print(f"❌ [ERROR GROQ/TTS]: {e}")
                    await websocket.send_text(json.dumps({"tipo": "sistema", "texto": "⚠️ Error de red con la Inteligencia Artificial."}))

    except WebSocketDisconnect:
        print("🔴 [SISTEMA] Cliente Web Desconectado.")