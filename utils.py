import os

def number_to_emoji(number):
    num_to_emoji = {
        '0': ':zero:',
        '1': ':one:',
        '2': ':two:',
        '3': ':three:',
        '4': ':four:',
        '5': ':five:',
        '6': ':six:',
        '7': ':seven:',
        '8': ':eight:',
        '9': ':nine:'
    }
    return ''.join(num_to_emoji[digit] for digit in str(number))

def check_file(filepath):
    return os.path.isfile(filepath)
