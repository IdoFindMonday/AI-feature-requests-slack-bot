import logging
import os
import io
import re
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from datetime import datetime, timedelta
from flask import Flask, request
from pathlib import Path
from dotenv import load_dotenv
from openai_module import OpenAIModule

logging.basicConfig(level=logging.DEBUG)

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

BOT_ID = app.client.api_call("auth.test")['user_id']
BOT_MENTION = f"<@{BOT_ID}>"
CLIENT_MSG_PREFIX = 'client_msg_id'
ACTIVATION_STR = 'run'
N_HOURS_PARAM = 'n_hours'

# Initialize the OpenAI module
openai_module = OpenAIModule(api_key=os.environ.get("OPENAI_API_KEY"))


def get_messages_from_last_n_hours(channel_id, n_hours):
    try:
        # Calculate the timestamp for the start of the last hour
        last_hour_timestamp = str((datetime.utcnow() - timedelta(hours=n_hours)).timestamp())
        # Call the conversations.history API method
        result = app.client.conversations_history(channel=channel_id, oldest=last_hour_timestamp)
        # Extract and return the messages
        messages = []
        for message in result["messages"]:
            if CLIENT_MSG_PREFIX in message.keys():
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


@app.event("app_mention")
def event_test(body, say, logger):
    text = body['event']['text'].split(f"{BOT_MENTION} ")[1]
    channel_id = body['event']['channel']

    if ACTIVATION_STR in text:
        say("The AI is working on it :robot_face: ... ")
        channel_info = app.client.conversations_info(channel=channel_id)
        channel_name = channel_info['channel']['name']

        if N_HOURS_PARAM in text:
            match = re.search(r'n_hours=(\d+)', text)
            n_hours = int(match.group(1))
        else:
            n_hours = 24  # default value

        # Get messages from the last hour in the specified channel
        last_messages = get_messages_from_last_n_hours(channel_id=channel_id, n_hours=n_hours)

        current_ts = datetime.utcnow().strftime('%Y-%m-%d-%H_%M')

        # generate text file with all the last messages
        file_name = f'{n_hours}_hours_messages_channel_{channel_name}_{current_ts}'
        comment = f"Here are the last {n_hours} hours messages:"

        last_messages_str = '\n'.join(last_messages)

        generate_txt_file(channel_id, file_name, last_messages_str, comment)

        # generate text file with the feature requests
        feature_requests = openai_module.extract_feature_requests(last_messages)
        say(f"{comment}:\n{feature_requests}")


@app.event("message")
def handle_message():
    pass


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT")))
