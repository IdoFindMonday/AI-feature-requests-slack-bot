import logging
import os
import io
import re
from slackeventsapi import SlackEventAdapter
from slack_sdk.errors import SlackApiError
from datetime import datetime, timedelta
from flask import Flask, make_response
from openai_module import OpenAIModule
from slack_sdk import WebClient
import Constansts
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

azure_openai_key = os.environ.get('AZURE_OPENAI_KEY')
azure_openai_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
slack_bot_token = os.environ.get('SLACK_BOT_TOKEN')
slack_signing_secret = os.environ.get('SLACK_SIGNING_SECRET')

app = Flask(__name__)

slack_events_adapter = SlackEventAdapter(
    slack_signing_secret, "/slack/events", app
)

# instantiating slack client
slack_client = WebClient(slack_bot_token)

BOT_ID = slack_client.api_call("auth.test")['user_id']
BOT_MENTION = f"<@{BOT_ID}>"

# Initialize the OpenAI module
openai_module = OpenAIModule(azure_openai_key=azure_openai_key,
                             azure_openai_endpoint=azure_openai_endpoint,
                             azure_api_version="2023-05-15",
                             model_name="text-davinci-003")

# handling slack retires while processing the request
CAN_PROCESS = 1
# enable to shut-down the bot activity
ACTIVE_BOT = True


def get_messages_from_last_n_hours(channel_id, start_date, n_hours):
    try:
        # Calculate the timestamp for the start of the last hour
        oldest_timestamp = str((start_date - timedelta(hours=n_hours)).timestamp())
        # Call the conversations.history API method
        result = slack_client.conversations_history(channel=channel_id, oldest=oldest_timestamp)
        # Extract and return the messages
        messages = []
        for message in result["messages"]:
            if Constansts.CLIENT_MSG_PREFIX in message.keys():
                if BOT_MENTION not in message["text"]:
                    user_info = slack_client.users_info(user=message['user'])
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
    response = slack_client.files_upload_v2(
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


def run(channel_id, text):
    slack_client.chat_postMessage(channel=channel_id, text="The AI is working on it :robot_face: ... ")
    channel_info = slack_client.conversations_info(channel=channel_id)
    channel_name = channel_info['channel']['name']

    n_hours = Constansts.DEFAULT_N_HOURS  # default value
    if Constansts.N_HOURS in text:
        match = re.search(r'n_hours=(\d+)', text)
        if match:
            n_hours = int(match.group(1))

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

        # generate text file with all the last messages
        file_name = f'{n_hours}_hours_messages_channel_{channel_name}_{start_date_str}'
        comment = f"Here are all the messages from the last {n_hours} hours:"

        last_messages_str = '\n'.join(last_messages)

        generate_txt_file(channel_id, file_name, last_messages_str, comment)

        # generate text file with the feature requests
        feature_requests = openai_module.extract_feature_requests(last_messages)
        if feature_requests:
            slack_client.chat_postMessage(channel=channel_id,
                                          text=f"Here are the extracted feature requests:\n{feature_requests}")
        else:
            message = "Oops! It seems like your request exceeded the maximum token limit.\n" + \
                      "Please select a smaller time window"
            slack_client.chat_postMessage(channel=channel_id,
                                          text=message)
    else:
        slack_client.chat_postMessage(channel=channel_id, text=f"No messages were found in the given timeframe")


def update_current_proc_state():
    global CAN_PROCESS
    CAN_PROCESS = CAN_PROCESS * -1


def update_bot_activity_status(value):
    global ACTIVE_BOT
    ACTIVE_BOT = value


@slack_events_adapter.on("app_mention")
def event_test(event_data):
    try:
        text = event_data['event']['text'].split(f"{BOT_MENTION} ")[1]
        channel_id = event_data['event']['channel']

        if text == "help":
            message = Constansts.HELP_MESSAGE.format(Constansts.START_DATE,
                                                     Constansts.N_HOURS,
                                                     Constansts.START_DATE,
                                                     Constansts.DEFAULT_N_HOURS)

            slack_client.chat_postMessage(channel=channel_id, text=message)

        elif (Constansts.ACTIVATION_STR in text) & ACTIVE_BOT:
            print("\n\n ******** CURRENTLY_PROCESSING:", CAN_PROCESS)
            if CAN_PROCESS == 1:
                update_current_proc_state()
                run(channel_id, text)
                update_current_proc_state()

        elif text == "--status":
            slack_client.chat_postMessage(channel=channel_id,
                                          text=f"Bot active:{ACTIVE_BOT}\ncan_process:{CAN_PROCESS}")

        elif text == "--activate":
            update_bot_activity_status(True)

        elif text == "--deactivate":
            update_bot_activity_status(False)

        elif text == "--refresh_can_process":
            update_current_proc_state()
    except:
        pass

    return make_response("", 200)


if __name__ == "__main__":
    app.run(port=8080, debug=False)
