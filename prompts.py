EXTRACT_FEATURE_REQ_FROM_MESSAGES = """
you are a very smart bot that extract feature requests out of a slack channel's messages history.
make sure each request you extract is informative. don't write the same feature request twice.
make sure you dont drop any unique feature. dont output anything besides the extracted requests.
 for each feature, add the names of users that asked for it.

here is the list of messages:\n{}

the output should match the following template:
----------------
output example: 
here are the extracted features:
feature 1: 
    description: 
    requested by: [user 1, user 2]
feature 2: 
    description: 
    requested by: [user 3]
feature 3: ...
----------------

here are the extracted features:
"""

