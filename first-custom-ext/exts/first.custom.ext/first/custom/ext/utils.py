import re

def format_string(input_string):
    # Remove non-alphanumeric characters (excluding spaces)
    alphanumeric_string = re.sub(r'[^a-zA-Z0-9 ]', '', input_string)
    
    # Replace spaces with underscores
    formatted_string = alphanumeric_string.replace(' ', '_')
    
    return formatted_string