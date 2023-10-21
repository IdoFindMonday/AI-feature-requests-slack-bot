import openai
from tiktoken import get_encoding
import prompts
import Constansts


class OpenAIModule:
    def __init__(self, api_key, model_name="text-davinci-002"):
        openai.api_key = api_key
        self.model_name = model_name
        self.tokenizer = get_encoding("cl100k_base")
        self.max_input_tokens = Constansts.INPUT_MAX_TOKENS
        self.extract_from_msg_prompt = prompts.EXTRACT_FEATURE_REQ_FROM_MESSAGES

    def _call_llm(self, prompt):
        response = openai.Completion.create(
            engine=self.model_name,
            prompt=prompt,
            temperature=0.1,
            max_tokens=512,
        )

        generated_summary = response["choices"][0]["text"].strip()
        return generated_summary

    def extract_feature_requests(self, messages):
        text_to_summarize = "\n".join(messages)

        messages_token_num = len(self.tokenizer.encode(text_to_summarize))

        if messages_token_num > self.max_input_tokens:
            return None

        prompt = self.extract_from_msg_prompt.format(text_to_summarize)
        final_result = self._call_llm(prompt)
        return final_result
