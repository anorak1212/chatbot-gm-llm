import os
from langchain_neo4j import Neo4jGraph, Neo4jVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

MAX_HISTORY = 10
INTENT_CACHE_SIZE = 128


class GraphRAGPipeline:
    def __init__(self):
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "admin1234")

        self.graph = Neo4jGraph(
            url=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password,
        )

        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

        self.vector_index = Neo4jVector.from_existing_graph(
            self.embeddings,
            url=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password,
            index_name='chunk_index',
            node_label='CHUNK',
            text_node_properties=['title', 'content', 'category'],
            embedding_node_property='embedding',
        )

        lm_studio_url = os.getenv("LM_STUDIO_URL", "http://192.168.1.80:1234")
        self.llm = ChatOpenAI(
            base_url=f"{lm_studio_url}/v1",
            api_key="lm-studio",
            model=os.getenv("LM_STUDIO_MODEL", "gemma-4-e4b-it"),
            temperature=0.3,
            max_tokens=2000,
            streaming=True,
        )

        self._intent_llm = ChatOpenAI(
            base_url=f"{lm_studio_url}/v1",
            api_key="lm-studio",
            model=os.getenv("LM_STUDIO_MODEL", "gemma-4-e4b-it"),
            temperature=0.0,
            max_tokens=16,
        )

        self._intent_cache: dict[str, str] = {}

    def _classify_intent(self, text: str, history: list[dict] | None = None) -> str:
        cache_key = text.lower().strip()
        if cache_key in self._intent_cache:
            return self._intent_cache[cache_key]

        history_summary = ""
        if history:
            last_turns = history[-3:]
            history_summary = "\n".join(
                f"{t['role']}: {t['content'][:100]}" for t in last_turns
            )

        prompt = (
            "Clasifica la intencion del usuario en EXACTAMENTE una de estas categorias.\n"
            "Responde SOLO con la palabra de la categoria, nada mas.\n\n"
            "Categorias:\n"
            "- conversational: saludos, despedidas, agradecimientos, preguntas sobre capacidades del asistente, charla casual\n"
            "- list_all: pedir la lista completa de todas las best practices, resumen general, enumerar todos los BPs\n"
            "- specific_query: pregunta tecnica sobre un BP especifico, un componente, un requisito, una dimension, un torque, clearance, etc.\n\n"
        )

        if history_summary:
            prompt += f"Contexto reciente de la conversacion:\n{history_summary}\n\n"

        prompt += f"Usuario: {text}\nCategoria:"

        response = self._intent_llm.invoke(prompt)
        result = response.content.strip().lower().replace("*", "").replace("_", "")

        if result in ("conversational", "list_all", "specific_query"):
            intent = result
        else:
            intent = "specific_query"

        self._intent_cache[cache_key] = intent
        return intent

    async def query(self, text: str, images: list[dict] | None = None, history: list[dict] | None = None):
        """
        history: list of {role: "user"|"assistant", content: str} from previous turns
        """
        try:
            has_images = images and len(images) > 0
            trimmed_history = self._trim_history(history) if history else []

            intent = self._classify_intent(text, trimmed_history)

            if intent == "conversational" and not has_images:
                async for token in self._handle_conversational_stream(text, images, trimmed_history):
                    yield token
                return

            async for token in self._handle_rag_stream(text, images, trimmed_history, intent):
                yield token

        except Exception as e:
            yield f"Error en la consulta RAG: {str(e)}"

    def _trim_history(self, history: list[dict]) -> list[dict]:
        return history[-MAX_HISTORY:]

    def _build_user_content(self, text: str, images: list[dict] | None = None):
        if not images:
            return text

        content = []
        if text:
            content.append({"type": "text", "text": text})

        for img in images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{img['mime']};base64,{img['base64']}"
                }
            })

        return content

    async def _handle_conversational_stream(self, text: str, images: list[dict] | None = None, history: list[dict] | None = None):
        system_msg = (
            "Eres un asistente experto en ingenieria automotriz para General Motors. "
            "Responde de forma amable y breve. Si te preguntan que puedes hacer, "
            "menciona que puedes responder preguntas sobre mejores practicas de ingenieria "
            "(Body Shop), interfaces de componentes, requisitos de seguridad y espacio libre, "
            "usando la base de conocimientos tecnica de GM. "
            "Si el usuario envia imagenes, describelas brevemente y explica como se relacionan con las BPs."
        )
        messages = [{"role": "system", "content": system_msg}]
        messages.extend(history)
        messages.append({"role": "user", "content": self._build_user_content(text, images)})

        async for chunk in self.llm.astream(messages):
            yield chunk.content

    async def _handle_rag_stream(self, text: str, images: list[dict] | None = None, history: list[dict] | None = None, intent: str = "specific_query"):
        try:
            if intent == "list_all":
                context = self._get_all_chunks_ordered()
            else:
                context = self._get_context_vector(text)

            if not context:
                yield "No encontre informacion en la base de conocimientos para tu pregunta."
                return

            system_msg = (
                "Eres un asistente experto en ingenieria automotriz para General Motors. "
                "Debes responder utilizando UNICAMENTE el contexto que se proporciona a continuacion. "
                "No inventes informacion. Si la respuesta no esta en el contexto, di claramente 'No tengo informacion suficiente en la base de conocimientos'. "
                "Incluye al final una seccion 'Fuentes' listando las fuentes concretas (ej: Source[1]) utilizadas para sostener la respuesta. "
                "Se conciso y tecnico. "
                "Si el usuario envio imagenes, analizalas y relaciona lo que ves con las best practices del contexto."
            )

            messages = [{"role": "system", "content": system_msg}]
            messages.extend(history)
            messages.append({"role": "system", "content": f"Contexto recuperado de la base de conocimientos:\n{context}"})
            messages.append({"role": "user", "content": self._build_user_content(text, images)})

            async for chunk in self.llm.astream(messages):
                yield chunk.content

            yield "\n\n*Fuente: Contexto recuperado de Neo4j (GraphRAG)*"

        except Exception as e:
            yield f"Error en la consulta RAG: {str(e)}"

    def _get_all_chunks_ordered(self) -> str:
        result = self.graph.query(
            "MATCH (c:CHUNK) RETURN c.id AS id, c.title AS title, c.content AS content, c.category AS category, c.priority AS priority ORDER BY c.id"
        )
        if not result:
            return ""
        parts = []
        for i, row in enumerate(result):
            parts.append(
                f"Source[{i+1}] {row.get('title', '')} (id={row.get('id', '')})\n"
                f"Categoria: {row.get('category', '')} | Prioridad: {row.get('priority', '')}\n"
                f"{row.get('content', '')}"
            )
        return "\n\n---\n\n".join(parts)

    def _get_context_vector(self, text: str) -> str:
        raw_docs = self.vector_index.similarity_search(text, k=6)
        if not raw_docs:
            return ""

        def score_doc(doc, question):
            q_tokens = set(w for w in question.lower().split() if len(w) > 2)
            c_tokens = set(w for w in (getattr(doc, 'page_content', '') or '').lower().split() if len(w) > 2)
            return len(q_tokens & c_tokens)

        scored = [(score_doc(d, text), d) for d in raw_docs]
        scored.sort(key=lambda x: x[0], reverse=True)

        top_docs = [d for s, d in scored[:5]]
        return "\n\n---\n\n".join(
            f"Source[{i+1}] {d.metadata.get('title', '')} (id={d.metadata.get('id', '')})\n{d.page_content}"
            for i, d in enumerate(top_docs)
        )
