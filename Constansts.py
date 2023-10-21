CLIENT_MSG_PREFIX = 'client_msg_id'
ACTIVATION_STR = 'run'
N_HOURS = 'n_hours'
START_DATE = 'start_date'
DEFAULT_N_HOURS = 24
INPUT_MAX_TOKENS = 3500
HELP_MESSAGE = """Hello I'm a feature-extractor AI bot :robot_face:\n\nTo use me type the `run` command """ + \
               """followed by some optional arguments:\n""" + \
               """ - `{}`: Specify the date from which we will lookback to collect messages (default=current date)\n""" + \
               """ - `{}`: Specify the number hours for the lookback window starting from `{}` (default={})\n""" + \
               """Lets go!"""
