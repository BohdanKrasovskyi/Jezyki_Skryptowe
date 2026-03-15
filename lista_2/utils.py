def remove_extra_spaces(text):
    text = text.strip()
    result = ""
    last_was_space = False

    for char in text:
        if char == ' ' or char == '\t':
            if not last_was_space:
                result += ' '
                last_was_space = True
        else:
            result += char
            last_was_space = False
    return result