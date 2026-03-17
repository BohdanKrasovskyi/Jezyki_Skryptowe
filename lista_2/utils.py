def remove_extra_spaces(text):
    text = text.strip()
    result = ""
    last_was_space = False

    for char in text:
        if char == ' ' or char == '\t' or char == '\n':
            if not last_was_space:
                result += ' '
                last_was_space = True
        else:
            result += char
            last_was_space = False
    return result

def remove_all_white_symbols(text):
    result = ""
    for char in text:
        if char == ' ' or char == '\t' or char == '\n' or char == '\r':
            continue
        result += char
    return result

def is_sentence_with_proper_noun(sentence):
    word = ""
    first_word = True
    for char in sentence + " ":
        if char.isalpha():
            word += char
        else:
            if word != "":
                if not first_word and word[0].isupper():
                    return True
                first_word = False
                word = ""
    return False

def if_two_words_starts_with_same_letter(sentence):
    word1 = ""
    word2 = ""
    for char in sentence + " ":
        if char.isalpha():
            word1 += char
        elif word1 != "":
            if word2 != "" and word1[0].lower() == word2[0].lower():
                return True
            word2 = word1
            word1 = ""
    return False

def count_comas_in_sentence(sentence):
    counter = 0
    for char in sentence:
        if char == ",":
            counter += 1
    return counter

def count_words_in_sentence(sentence):
    counter = 0
    word = ""
    for char in sentence:
        if (char in ",;:()\"' ") and word != "":
            counter += 1
            word = ""
        elif char not in ",;:()\"' ":
            word += char
    if word != "":
        counter += 1
    return counter

def count_special_words(sentence):
    counter = 0
    word = ""
    special_words = ["i", "oraz", "ale", "że", "lub"]
    for char in sentence + " ":
        if char in ",;:()\"' " and word != "":
            if word in special_words:
                counter += 1
            word = ""
        elif char not in ",;:()\"' ":
            word += char
    return counter