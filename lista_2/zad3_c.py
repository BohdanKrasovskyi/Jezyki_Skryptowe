import sys
from utils import remove_extra_spaces
from utils import  is_sentence_with_proper_noun


def zad3_c():
    sentences = 0
    sentences_with_proper_noun = 0
    sentence = ""

    for line in sys.stdin:
        line = remove_extra_spaces(line)
        if line == "" and sentence != "":
            sentences += 1
            if is_sentence_with_proper_noun(sentence):
                sentences_with_proper_noun += 1
            sentence = ""

        for char in line:
            if char == '.' or char == '?' or char == '!' or char == "…":
                sentences += 1
                if is_sentence_with_proper_noun(sentence):
                    sentences_with_proper_noun += 1
                sentence = ""
            else:
                sentence += char

    if sentences == 0:
        raise Exception("No sentences was found")

    return float(sentences_with_proper_noun) / float(sentences) * 100

def main():
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        print(str(zad3_c()) + "%")
    except BrokenPipeError:
        sys.exit(0)
    finally:
        sys.stdout.close()

if __name__ == "__main__":
    main()