import logging
import os
import io
import re
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from datetime import datetime, timedelta
from flask import Flask, request
from openai_module import OpenAIModule
import Constansts

logging.basicConfig(level=logging.DEBUG)

azure_openai_key = os.getenv("AZURE_OPENAI_KEY")
azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")


app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

BOT_ID = app.client.api_call("auth.test")['user_id']
BOT_MENTION = f"<@{BOT_ID}>"

# Initialize the OpenAI module
openai_module = OpenAIModule(azure_openai_key=azure_openai_key,
                             azure_openai_endpoint=azure_openai_endpoint,
                             azure_api_version="2023-05-15",
                             model_name="text-davinci-003")


def get_messages_from_last_n_hours(channel_id, start_date, n_hours):
    try:
        # Calculate the timestamp for the start of the last hour
        oldest_timestamp = str((start_date - timedelta(hours=n_hours)).timestamp())
        # Call the conversations.history API method
        result = app.client.conversations_history(channel=channel_id, oldest=oldest_timestamp)
        # Extract and return the messages
        messages = []
        for message in result["messages"]:
            if Constansts.CLIENT_MSG_PREFIX in message.keys():
                if BOT_MENTION not in message["text"]:
                    user_info = app.client.users_info(user=message['user'])
                    user_name = user_info['user']['name']
                    msg_text = message["text"]
                    final_msg = f"user {user_name}: {msg_text}"
                    messages.append(final_msg)
        return messages
    except SlackApiError as e:
        print(f"Error: {e.response['error']}")
        return None


def generate_txt_file(channel_id, file_name, text, comment):
    # Create an in-memory file-like object
    in_memory_file = io.StringIO()

    in_memory_file.write(text)

    # Upload the text file to Slack
    response = app.client.files_upload_v2(
        channel=channel_id,
        content=in_memory_file.getvalue(),
        title=file_name,
        filename=f'{file_name}.txt',
        initial_comment=comment,
    )

    in_memory_file.close()

    # Check if the file upload was successful
    if response["ok"]:
        print(f"File uploaded successfully: {response['file']['name']}")
    else:
        print(f"File upload failed: {response['error']}")


@app.middleware  # or app.use(log_request)
def log_request(logger, body, next):
    logger.debug(body)
    return next()


def run(say, channel_id, text):
    say("The AI is working on it :robot_face: ... ")
    channel_info = app.client.conversations_info(channel=channel_id)
    channel_name = channel_info['channel']['name']

    if Constansts.N_HOURS in text:
        match = re.search(r'n_hours=(\d+)', text)
        n_hours = int(match.group(1))
    else:
        n_hours = Constansts.DEFAULT_N_HOURS  # default value

    start_date = datetime.utcnow()

    if Constansts.START_DATE in text:
        match = re.search(r'start_date=(\d{4}-\d{2}-\d{2})', text)
        if match:
            start_date = datetime.strptime(match.group(1), '%Y-%m-%d').replace(hour=12, minute=0, second=0)

    # Get messages from the last hour in the specified channel
    last_messages = get_messages_from_last_n_hours(channel_id=channel_id,
                                                   start_date=start_date,
                                                   n_hours=n_hours)

    if len(last_messages) > 0:
        start_date_str = start_date.strftime('%Y-%m-%d_%H_%M')

        print('start_date:', start_date)
        print('start_date_str:', start_date_str)

        # generate text file with all the last messages
        file_name = f'{n_hours}_hours_messages_channel_{channel_name}_{start_date_str}'
        comment = f"Here are the last {n_hours} hours messages:"

        last_messages_str = '\n'.join(last_messages)

        generate_txt_file(channel_id, file_name, last_messages_str, comment)

        # generate text file with the feature requests
        feature_requests = openai_module.extract_feature_requests(last_messages)
        if feature_requests:
            say(f"\n{feature_requests}")
        else:
            say("""Oops! It seems like your request exceeded the maximum token limit.\n""" + \
                """Please select a smaller time window""")
    else:
        say(f"No messages were found in the given timeframe")


@app.event("app_mention")
def event_test(body, say, logger):
    text = body['event']['text'].split(f"{BOT_MENTION} ")[1]
    channel_id = body['event']['channel']

    if text == "help":
        message = Constansts.HELP_MESSAGE.format(Constansts.START_DATE,
                                                 Constansts.N_HOURS,
                                                 Constansts.START_DATE,
                                                 Constansts.DEFAULT_N_HOURS)
        say(message)

    elif Constansts.ACTIVATION_STR in text:
        run(say, channel_id, text)


@app.event("message")
def handle_message():
    pass


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


if __name__ == "__main__":
    app.start(port=int(os.getenv("PORT")))
