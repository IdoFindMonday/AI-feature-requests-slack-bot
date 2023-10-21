import openai


class OpenAIModule:
    def __init__(self, api_key, model_name="text-davinci-002"):
        openai.api_key = api_key
        self.model_name = model_name

    def extract_feature_requests(self, messages):
        text_to_summarize = "\n".join(messages)

        prompt = f"""
        you are a very smart bot that extract feature requests out of a slack channel's messages history.
        make sure each request is short and informative. don't write the same feature request twice.
        for each feature, add the names of users that asked for it.
        example: 
        feature 1: 
            description: add the option to delete request 
            requested by: [user 1, user 2]
        feature 2: 
            description: enable to connect from mobile 
            requested by: [user 3]
        here is the list of messages:\n{text_to_summarize}
        """

        response = openai.Completion.create(
            engine=self.model_name,
            prompt=prompt,
            temperature=0.1,
            max_tokens=250,
        )

        generated_summary = response["choices"][0]["text"].strip()
        return generated_summary
