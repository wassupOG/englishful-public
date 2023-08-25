import re, string


# Apostrophes
def normalize_apostrophes(text):
    # Replace common apostrophe variations with standard apostrophe
    text = re.sub("[‘’ʼ´`′‵]", "'", text)
    return text


# st_answers replace
def replace_contractions(text, replacements):
    words = text.split()
    updated_words = []
    
    for word in words:
        # Check if the word ends with a punctuation mark
        if word[-1] in string.punctuation and word[:-1] in replacements:
            updated_words.append(replacements[word[:-1]] + word[-1])
        elif word in replacements:
            updated_words.append(replacements[word])
        else:
            updated_words.append(word)

    return ' '.join(updated_words)


def strip(text):
    return " ".join(text.strip().split())


def strip_lower(text):
    return " ".join(text.strip().lower().split())


# replace !?. st_answers
def replace_disallowed(strings, disallowed_characters):
    for character in disallowed_characters:
        strings = strings.replace(character, "")
        
    return strings


# disallowed !?.
disallowed_characters = ".!?"


# Replacements
replacements = {
    "aren't": 'are not',
    "Aren't": 'Are not',
    "can't": 'cannot',
    "Can't": 'Cannot',
    "couldn't": 'could not',
    "Couldn't": 'Could not',
    "didn't": 'did not',
    "Didn't": 'Did not',
    "doesn't": 'does not',
    "Doesn't": 'Does not',
    "don't": 'do not',
    "Don't": 'Do not',
    "wasn't": 'was not',
    "Wasn't": 'Was not',
    "hadn't": 'had not',
    "Hadn't": 'Had not',
    "hasn't": 'has not',
    "Hasn't": 'Has not',
    "haven't": 'have not',
    "Haven't": 'Have not',
    "I'm": 'I am',
    "I've": "I have",
    "isn't": 'is not',
    "Isn't": 'Is not',
    "mightn't": 'might not',
    "Mightn't": 'Might not',
    "mustn't": 'must not',
    "Mustn't": 'Must not',
    "shan't": 'shall not',
    "Shan't": 'Shall not',
    "shouldn't": 'should not',
    "Shouldn't": 'Should not',
    "it's": 'it is',
    "It's": 'It is',
    "they're": 'they are',
    "They're": 'They are',
    "they've": 'they have',
    "They've": 'They have',
    "we're": 'we are',
    "We're": 'We are',
    "we've": 'we have',
    "We've": 'We have',
    "weren't": 'were not',
    "Weren't": 'Were not',
    "what've": 'what have',
    "What've": 'What have',
    "who're": 'who are',
    "Who're": 'Who are',
    "who've": 'who have',
    "Who've": 'Who have',
    "won't": 'will not',
    "Won't": 'Will not',
    "wouldn't": 'would not',
    "Wouldn't": 'Would not',
    "you're": 'you are',
    "You're": 'You are',
    "you've": 'you have',
    "You've": 'You have',
    "it'll": 'it will',
    "It'll": 'It will',
    "he'll": 'he will',
    "He'll": 'He will',
    "she'll": 'she will',
    "She'll": 'She will',
    "they'll": 'they will',
    "They'll": 'They will',
    "we'll": 'we will',
    "We'll": 'We will',
    "you'll": 'you will',
    "You'll": 'You will',
    "there'll": 'there will',
    "There'll": 'There will',
    "I'll": 'I will',
}

def calculate_scores(results_dict, even_tasks, odd_tasks):
    scores = {}
    overall = 0
    for task_key, task_results in results_dict.items():
        score = 0
        if task_key in even_tasks:
            # Even point task (1 correct answer = 1 point)
            for st_answer, correct_answer in task_results:
                if st_answer in correct_answer.split('/'):
                    score += 1
        elif task_key in odd_tasks:
            # Odd point task (score based on number of correct answers)
            correct_count = sum(st_answer in correct_answer.split('/') for st_answer, correct_answer in task_results)
            if correct_count <= 3:
                score = 0
            elif correct_count == 4:
                score = 1
            elif correct_count == 5:
                score = 2
            elif correct_count == 6:
                score = 3
            elif correct_count == 7:
                score = 4
        scores[task_key] = score
        overall += score
    
    scores['overall'] = overall
    return scores

# Conversion for EGE
conversion_dict = {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 5,
    5: 6,
    6: 7,
    7: 8,
    8: 10,
    9: 11,
    10: 12,
    11: 13,
    12: 15,
    13: 16,
    14: 17,
    15: 18,
    16: 20,
    17: 21,
    18: 22,
    19: 23,
    20: 24,
    21: 25,
    22: 26,
    23: 27,
    24: 28,
    25: 29,
    26: 30,
    27: 31,
    28: 32,
    29: 33,
    30: 34,
    31: 35,
    32: 36,
    33: 37,
    34: 39,
    35: 40,
    36: 41,
    37: 42,
    38: 43,
    39: 44,
    40: 45,
    41: 46,
    42: 47,
    43: 48,
    44: 49,
    45: 50,
    46: 51,
    47: 52,
    48: 53,
    49: 55,
    50: 56,
    51: 57,
    52: 58,
    53: 59,
    54: 60,
    55: 61,
    56: 62,
    57: 63,
    58: 64,
    59: 65,
    60: 66,
    61: 67,
    62: 68,
    63: 69,
    64: 70,
    65: 72,
    66: 73,
    67: 74,
    68: 75,
    69: 76,
    70: 77,
    71: 78,
    72: 79,
    73: 80,
    74: 81,
    75: 82,
    76: 83,
    77: 84,
    78: 85,
    79: 86,
    80: 88,
    81: 90,
    82: 92,
    83: 94,
    84: 96,
    85: 98,
    86: 100
}