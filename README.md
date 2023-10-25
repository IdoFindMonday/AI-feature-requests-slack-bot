# AI-feature-requests-slack-bot

This is a slack bot built to pull all the messages in a given slack chanel, ignore irrelevant messages and use OpenAI API to extract feature request from the pulled messages.
In addition to the feature extraction using LLM, the bot will generate and send a .txt file in the channel for further use.

### Features

- Retrieve messages from a specified time window in a Slack channel.
- Enable to change the starting date of the pulling to apply changing time-windows.
- Process messages and generate text files for analysis.


### Note
- This is not a production ready code
- The current code supports only the Completion API (DEVINCI-003) 


## Getting Started

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add the following environment variables:

```dotenv
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_SIGNING_SECRET=your_slack_signing_secret
OPENAI_API_KEY=your_openai_api_key
PORT=3000  # or your desired port
```

### Usage

1. Run the Flask application:

```bash
python main.py
```

2. Interact with the Slack Bot by mentioning it in a channel. For example:

```
@your-bot-name help
```

This will display usage instructions.

```
@your-bot-name run
```

This will activate the bot with the default params:  
`start_date`: (default=today), the format should be: 2023-10-18  
`n_hours`: (default=24), how many hours to look back from the `start_date`

example:
```
@your-bot-name run start_date=2023-09-25 n_hours=7
```

3. Debugging & admin commands

If for any reason you need to deactivate the bot, use the `@your-bot-name --deactivate` command.
This will make the bot not to respond the to run command.
To activate the bot use `@your-bot-name --activate`.
To check the current status of the bot use the `@your-bot-name --status` command.



