import chainlit as cl
from src.graph.rag_pipeline import GraphRAGPipeline

rag_pipeline = GraphRAGPipeline()


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(content="Hola! Soy tu asistente de ingenieria de General Motors impulsado por RAG y Gemma local. Puedes enviarme texto o imagenes de planos/diagramas. En que te puedo ayudar sobre mejores practicas (Body Shop)?").send()


@cl.on_message
async def main(message: cl.Message):
    history = cl.user_session.get("history", [])

    image_data = []
    if message.elements:
        for elem in message.elements:
            if elem.mime and elem.mime.startswith("image/"):
                try:
                    import base64
                    with open(elem.path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")
                    image_data.append({
                        "name": elem.name,
                        "mime": elem.mime,
                        "base64": b64,
                    })
                except Exception as e:
                    await cl.Message(content=f"Error al procesar la imagen {elem.name}: {e}").send()
                    return

    user_content = message.content
    if image_data:
        image_names = [img["name"] for img in image_data]
        user_content = f"{message.content} [Imagenes adjuntas: {', '.join(image_names)}]"

    history.append({"role": "user", "content": user_content})

    msg = cl.Message(content="")
    await msg.send()

    full_response = ""
    async for token in rag_pipeline.query(message.content, images=image_data, history=history):
        full_response += token
        await msg.stream_token(token)

    history.append({"role": "assistant", "content": full_response})
    cl.user_session.set("history", history)
