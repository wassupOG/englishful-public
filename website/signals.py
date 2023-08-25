from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
from .helpers import *

@receiver(post_save, sender=Tests)
def update_results(sender, instance, **kwargs):
    st_results = Results.objects.filter(test_proper=instance)
    for st_result in st_results:
        type = st_result.test_proper.type.type
        case = st_result.test_proper.case
        sentences = st_result.test_proper.sentences
        st_answers = st_result.answers_plain
        answers = st_result.test_proper.answers

        ### Clean answers
        if type in ["gaps", "gaps_text"]:
            for i, answer in enumerate(answers):
                answer = normalize_apostrophes(answer)
                answer = replace_disallowed(answer, disallowed_characters)
                if case:
                    answer = strip(answer)
                else:
                    answer = strip_lower(answer)
                answer = replace_contractions(answer, replacements)
                answers[i] = answer
        

        score = 0
        results = []

        # Results inside
        if type in ["gaps", "inside_dropdown", "inside_dropdown_text", "gaps_text", "single_inside_dropdown"]:
            counter = 0
            for i in range(len(sentences)):
                words = sentences[i].split()
                for x in range(len(words)):
                    if words[x] == '_':
                        if st_answers[counter] in answers[counter].split('/'):
                            words[x] = f"<span class='correct-answer'>{answers[counter]}</span>"
                            counter += 1
                            score += 1
                        else:
                            if st_answers[counter] != "no answer" and type in ["gaps", "gaps_text"]:
                                st_words = st_answers[counter].split()
                                correct_words = answers[counter].split()
                                st_words = [
                                    f"<u>{st_word}</u>"
                                    if i >= len(correct_words) or st_word != correct_words[i]
                                    else st_word
                                    for i, st_word in enumerate(st_words)
                                ]
                                st_answers[counter] = ' '.join(st_words)
                            
                            words[x] = f"<span class='wrong-answer'>({st_answers[counter]})</span> <span class='correct-answer'>{answers[counter]}</span>"
                            counter += 1

                results.append(' '.join(words))
        
        # Results after
        elif type in ["many_dropdown", "single_dropdown"]:
            for i in range(len(answers)):
                if st_answers[i] in answers[i].split('/'):
                    score += 1
                    results.append(f"{sentences[i]} <span class='correct-answer'>{answers[i]}</span>")
                else:
                    results.append(f"{sentences[i]} <span class='wrong-answer'>({st_answers[i]})</span> <span class='correct-answer'>{answers[i]}</span>")

        ### Get the result in %
        score_percent = round((score / len(answers))*100)

        ### Divide % by ten to convert it to GPA(0-10)
        gpa_score = round(score_percent / 10, 1)
             
        st_result.grade = gpa_score
        st_result.answers = results
        st_result.save()