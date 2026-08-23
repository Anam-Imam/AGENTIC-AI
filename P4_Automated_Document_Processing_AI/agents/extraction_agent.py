from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from models.schemas import DocumentResult
from core.config import GROQ_API_KEY, GROQ_MODEL

class ExtractionAgent:
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing. Add it to .env.")
        llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0)
        self.llm = llm.with_structured_output(DocumentResult)
        system = (
            "You are AURELIA, a precise document extraction agent. "
            "Extract only facts supported by the source. Never invent facts. "
            "Return every field required by the schema. Use empty lists when absent."
        )
        human = (
            "DOCUMENT:\n{document}\n\n"
            "RETRIEVED CONTEXT:\n{context}\n\n"
            "FOCUS:\n{instruction}\n\n"
            "If previous validation feedback is present, correct the result using the source."
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            ("human", human)
        ])

    def extract(self, document, context, instruction):
        return (self.prompt | self.llm).invoke({
            "document": document, "context": context, "instruction": instruction
        })
