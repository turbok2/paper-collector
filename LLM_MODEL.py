from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser


class LocalApi:
    def __init__(self, model_name: str, base_url: str):
        self.llm = ChatOllama(model=model_name, temperature=0.0, base_url=base_url)

    def send_request(self, field_name, instruction_prompt, input_data):
        return _send_with_parser(self.llm, field_name, instruction_prompt, input_data)


class GPTApi:
    def __init__(self, model_name: str, api_key: str):
        self.llm = ChatOpenAI(model_name=model_name, openai_api_key=api_key, temperature=0.0)

    def send_request(self, field_name, instruction_prompt, input_data):
        return _send_with_parser(self.llm, field_name, instruction_prompt, input_data)


def _send_with_parser(llm, field_name, instruction_prompt, input_data):
    try:
        response_schema = ResponseSchema(name=field_name, description="Extracted value")
        output_parser = StructuredOutputParser.from_response_schemas([response_schema])

        prompt = ChatPromptTemplate.from_messages([
            HumanMessagePromptTemplate.from_template(
                "{instruction_prompt}\n\n### INPUT :\n{input_data}\n\n### OUTPUT FORMAT :\n{output_format_prompt}\n\n### OUTPUT :"
            )
        ])

        chain = prompt | llm | output_parser

        MODEL_INPUT = {
            "instruction_prompt": instruction_prompt,
            "input_data": input_data,
            "output_format_prompt": f"{field_name}: string"
        }

        raw_response = chain.invoke(MODEL_INPUT)

        # MODEL_RESPONSE 출력
        # print(f"[📥 RAW RESPONSE] - Field: {field_name}")
        # print("-" * 80)
        # print(str(raw_response))
        # print("=" * 80 + "\n")

        return {
            "parsed": raw_response.get(field_name, "ERROR"),
            "raw": str(raw_response)
        }

    except Exception as e:
        print(f"[❌ ERROR] in LLM call for field '{field_name}': {e}")
        return {
            "parsed": "ERROR",
            "raw": str(e)
        }