from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.db.models import Avg
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from .models import *
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_exempt
import json
from .forms import *
import os
from django.conf import settings
import bleach
from .helpers import *
from datetime import datetime, timedelta
from django.utils.timezone import make_aware


# Create your views here.

### BASICS ###
def error_404(request, exception):
    return render(request, "website/login.html", {
        'message': 'Log in to access this page'
    })


def index(request):
    return render(request, "website/layout.html", {"reviews": Reviews.objects.all()})


def free_tests(request):
    theory_entries = TheoryTopics.objects.order_by('order')
    tests_by_topic = {}
    for theory_entry in theory_entries:
        tests = FreeTests.objects.filter(topic=theory_entry).order_by('order')
        if tests:
            tests_by_topic[theory_entry] = tests
    return render(request, "website/free_tests.html", {"tests_by_topic": tests_by_topic})


def single_test_free(request, free_testname):
    test = FreeTests.objects.get(url=free_testname)
    type = test.type.type
    
    if type in ['gaps', 'gaps_text', 'single_dropdown', 'single_inside_dropdown']:
        return render(request, "website/free_test.html", {
            'test': test,
            'type': type
        })
    
    
    elif type in ["many_dropdown", "inside_dropdown", "inside_dropdown_text"]:
        return render(request, "website/free_test.html", {
            'test': test,
            'type': type,
            'listening_task': zip(test.sentences, test.options)
        })


def free_check(request, free_testname):
    if request.method == 'POST':
        test = FreeTests.objects.get(url=free_testname)
        type = test.type.type
        case = test.case
        sentences = test.sentences
        answers = test.answers

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

        ### Clean st_answers
        st_answers_clean = []
        st_answers = []
        for key, value in request.POST.items():
            if key.startswith('answer'):
                value = bleach.clean(value, tags=[], strip=True)
                if type in ["gaps", "gaps_text"]:
                    if value != "":
                        value = normalize_apostrophes(value)
                        value = replace_disallowed(value, disallowed_characters)
                        if case:
                            value = strip(value)
                        else:
                            value = strip_lower(value)
                        value = replace_contractions(value, replacements)
                        st_answers.append(value)
                        st_answers_clean.append(value)
                    else:
                        st_answers.append("no answer")
                        st_answers_clean.append("no answer")
                else:
                    st_answers.append(value)
                    st_answers_clean.append(value)
        
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


        score_percent = round((score / len(answers))*100)
        gpa_score = round(score_percent / 10, 1)
        messages.success(request, f"{(round(gpa_score, 1)):g} / 10 ({score_percent}%)")
        
        context = {
            'answers': results,
            'score_percent': score_percent,
            'test': test,
        }

        return render(request, "website/checked-free-test.html", context)
        

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("results"))
        else:
            return render(request, "website/login.html", {
                "message": "Invalid username or password"
            })
    else:
        return render(request, "website/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


@staff_member_required
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        email = request.POST["email"]
        cefr = request.POST["cefr"]
        progress = request.POST["progress"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "website/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "website/register.html", {
                "message": "Username already taken."
            })
        # Log in & set CEFR, Progress, Name, and Surname
        login(request, user)
        f = User.objects.get(id = request.user.id)
        f.first_name = first_name
        f.last_name = last_name
        f.cefr = cefr
        f.progress = progress
        f.save()
        
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "website/register.html")
### BASICS END  ###

### DICTIONARY ###

def dictionary(request):
    if request.user.teacher == True:
        ### For teachers
        groups = Group.objects.filter(Q(teacherstudent__teacher=request.user)).distinct()
        students = request.user.teacher_students.all().values_list('students', flat=True)
        users_teacher = User.objects.filter(pk__in=students)
        ### For teachers

        all_groups = Group.objects.all()
        entries = Words.objects.all().order_by('-date')
        users = User.objects.exclude(teacher=True)
        topics = Topic.objects.all()
        form_topic = WordFilterForm(request.GET or None)
        form_contrib = ContribFilterForm(request.GET or None)
        return render(request, 'website/dictionary.html', {'entries': entries, 'users': users, "users_teacher": users_teacher, "groups": groups, "all_groups": all_groups, 'topics': topics, 'form_topic':form_topic, 'form_contrib': form_contrib})
    else:
        form_topic_user = WordFilterFormUser(request.GET or None, user=request.user)
        entries = UserWords.objects.filter(user_id = request.user.id).order_by('-date')
        average_progress = UserWords.objects.filter(user=request.user.id).aggregate(Avg('progress'))['progress__avg']
        distinct_topics = UserWords.objects.filter(user=request.user.id).values_list('word__topics__name', flat=True).distinct()

        topic_progress = []
        for topic in distinct_topics:
            num_words = UserWords.objects.filter(user=request.user.id, word__topics__name=topic).count()
            progress = UserWords.objects.filter(user=request.user.id, word__topics__name=topic).aggregate(avg_progress=Avg('progress'))['avg_progress']
            topic_name = topic if topic else 'No topic'
            topic_progress.append((topic_name, progress, num_words))
        topic_progress.sort(key=lambda x: x[1], reverse=True)

    return render(request, 'website/dictionary_user.html', {'entries': entries, 'form_topic_user': form_topic_user, 'average_progress': average_progress, "topic_progress": topic_progress})


def dictionary_filter(request):
    if request.user.teacher == True:
        ### For teachers
        groups = Group.objects.filter(Q(teacherstudent__teacher=request.user)).distinct()
        students = request.user.teacher_students.all().values_list('students', flat=True)
        users_teacher = User.objects.filter(pk__in=students)
        ### For teachers

        all_groups = Group.objects.all()
        users = User.objects.exclude(teacher=True)
        topics = Topic.objects.all()
        entries = Words.objects.all().order_by('-date')
        form_topic = WordFilterForm(request.GET or None)
        form_contrib = ContribFilterForm(request.GET or None)
        
        action = request.GET.get('action')

        date_from = request.GET.get('date-filter-from')
        date_to = request.GET.get('date-filter-to')

        if date_from:
            date_from = make_aware(datetime.strptime(date_from, '%Y-%m-%d'))
            entries = entries.filter(date__gte=date_from)
        if date_to:
            date_to = make_aware(datetime.strptime(str(date_to), '%Y-%m-%d')) + timedelta(days=1)
            entries = entries.filter(date__lt=date_to)

        if action == 'topic':
            if form_topic.is_valid():
                selected_topic = form_topic.cleaned_data.get('topics')
                if selected_topic is not None:
                    entries = entries.filter(topics=selected_topic).order_by('-date').distinct()
                else:
                    entries = entries.filter(topics=None).order_by('-date').distinct()
            else:
                pass

            return render(request, 'website/dictionary.html', {'entries': entries, 'users': users, "users_teacher": users_teacher, "groups": groups, "all_groups": all_groups, 'topics': topics, 'form_topic': form_topic, 'form_contrib': form_contrib})
        
        elif action == 'contrib':
            contributor_usernames = request.GET.getlist('contributor')
            if contributor_usernames:
                entries = Words.objects.filter(contributor__id__in=[username for username in contributor_usernames]).order_by('-date')

            return render(request, 'website/dictionary.html', {'entries': entries, 'users': users, "users_teacher": users_teacher, "groups": groups, "all_groups": all_groups, 'topics': topics, 'form_topic': form_topic, 'form_contrib': form_contrib})
        
        elif action == 'certified':
            entries = Words.objects.filter(certified=True).order_by('-date')
            if form_topic.is_valid():
                selected_topic = form_topic.cleaned_data.get('topics')
                contributor_usernames = request.GET.getlist('contributor')
                if selected_topic is not None:
                    if contributor_usernames:
                        entries = entries.filter(topics=selected_topic, contributor__id__in=[username for username in contributor_usernames]).order_by('-date')
                    else:
                        entries = entries.filter(topics=selected_topic).order_by('-date')
                elif contributor_usernames != []:
                    entries = entries.filter(contributor__id__in=[username for username in contributor_usernames]).order_by('-date')
                    
            return render(request, 'website/dictionary.html', {'entries': entries, 'users': users, "users_teacher": users_teacher, "groups": groups, "all_groups": all_groups, 'topics': topics, 'form_topic': form_topic, 'form_contrib': form_contrib})
            
    else:
        entries = UserWords.objects.filter(user_id=request.user.id).order_by('-date')
        form_topic_user = WordFilterFormUser(request.GET or None, user=request.user)
        average_progress = UserWords.objects.filter(user=request.user.id).aggregate(Avg('progress'))['progress__avg']
        distinct_topics = UserWords.objects.filter(user=request.user.id).values_list('word__topics__name', flat=True).distinct()

        topic_progress = []
        for topic in distinct_topics:
            num_words = UserWords.objects.filter(user=request.user.id, word__topics__name=topic).count()
            progress = UserWords.objects.filter(user=request.user.id, word__topics__name=topic).aggregate(avg_progress=Avg('progress'))['avg_progress']
            topic_name = topic if topic else 'No topic'
            topic_progress.append((topic_name, progress, num_words))
        topic_progress.sort(key=lambda x: x[1], reverse=True)

        filter_from = request.GET.get('progress-filter-from', '0')  # set default value to 0
        filter_to = request.GET.get('progress-filter-to', '100')  # set default value to 100
        
        date_from = request.GET.get('date-filter-from')
        date_to = request.GET.get('date-filter-to')

        if date_from:
            date_from = make_aware(datetime.strptime(date_from, '%Y-%m-%d'))
            entries = entries.filter(date__gte=date_from)
        if date_to:
            date_to = make_aware(datetime.strptime(str(date_to), '%Y-%m-%d')) + timedelta(days=1)
            entries = entries.filter(date__lt=date_to)

        entries = entries.filter(progress__gte=filter_from, progress__lte=filter_to)

        if form_topic_user.is_valid():
            selected_topic = form_topic_user.cleaned_data.get('topics')
            if selected_topic is not None:
                entries = entries.filter(word__topics=selected_topic).order_by('-date').distinct()
            else:
                entries = entries.filter(word__topics__isnull=True).order_by('-date').distinct()
        else:
            pass

        return render(request, 'website/dictionary_user.html', {'entries': entries, 'form_topic_user': form_topic_user, 'average_progress': average_progress, "topic_progress": topic_progress})
            

def dictionary_search(request):
    if request.user.teacher == True:
        ### For teachers
        groups = Group.objects.filter(Q(teacherstudent__teacher=request.user)).distinct()
        students = request.user.teacher_students.all().values_list('students', flat=True)
        users_teacher = User.objects.filter(pk__in=students)
        ### For teachers

        all_groups = Group.objects.all()
        users = User.objects.exclude(teacher=True)
        topics = Topic.objects.all()
        entries = Words.objects.all()
        form_topic = WordFilterForm(request.GET or None)
        form_contrib = ContribFilterForm(request.GET or None)
        query = request.GET.get('search_query')

        if query:
            entries = entries.filter(Q(english_word__icontains=query) | Q(russian_word__icontains=query)).order_by('-date')
        return render(request, 'website/dictionary.html', {'entries': entries, 'users': users, "users_teacher": users_teacher, "groups": groups, "all_groups": all_groups, 'topics': topics, 'form_topic': form_topic, 'form_contrib': form_contrib})
    else:
        entries = UserWords.objects.filter(user_id = request.user.id)
        form_topic_user = WordFilterFormUser(request.GET or None, user=request.user)
        query = request.GET.get('search_query')

        average_progress = UserWords.objects.filter(user=request.user.id).aggregate(Avg('progress'))['progress__avg']
        distinct_topics = UserWords.objects.filter(user=request.user.id).values_list('word__topics__name', flat=True).distinct()

        topic_progress = []
        for topic in distinct_topics:
            num_words = UserWords.objects.filter(user=request.user.id, word__topics__name=topic).count()
            progress = UserWords.objects.filter(user=request.user.id, word__topics__name=topic).aggregate(avg_progress=Avg('progress'))['avg_progress']
            topic_name = topic if topic else 'No topic'
            topic_progress.append((topic_name, progress, num_words))
        topic_progress.sort(key=lambda x: x[1], reverse=True)

        if query:
            entries = entries.filter(Q(word__english_word__icontains=query) | Q(word__russian_word__icontains=query)).order_by('-date')
        return render(request, 'website/dictionary_user.html', {'entries': entries, 'form_topic_user': form_topic_user, 'average_progress': average_progress, "topic_progress": topic_progress})


# Add word Staff / User
def add_word(request):
    if request.method == 'POST' and request.user.teacher == True:
        english = request.POST['english'].replace('\n', '').replace('\r', '')
        russian = request.POST['russian'].replace('\n', '').replace('\r', '')
        context = request.POST['context'].replace('\n', '').replace('\r', '')

        topic_ids = request.POST.getlist('topics')
        topics = Topic.objects.filter(id__in=topic_ids)
        f = Words(english_word = english, russian_word = russian, context=context, date=timezone.localtime(), contributor_id=request.user.id)
        f.save()
        f.topics.set(topics)
        return HttpResponseRedirect(reverse("dictionary"))
    
    elif request.method == 'POST':
        english = request.POST['english'].replace('\n', '').replace('\r', '')
        russian = request.POST['russian'].replace('\n', '').replace('\r', '')
        context = request.POST['context'].replace('\n', '').replace('\r', '')
        f = Words(english_word = english, russian_word = russian, context=context, user_added = True, date=timezone.localtime(), contributor_id=request.user.id)
        f.save()
        d = UserWords(user_id = request.user.id, word=f, date=timezone.localtime())
        d.save()

        return HttpResponseRedirect(reverse("dictionary"))

@csrf_exempt
def update_progress(request):
    data = json.loads(request.body)
    word_id = data['word_id']
    type = data['type']

    # Retrieve UserWords instance for the current user and the requested word_id
    user_word = UserWords.objects.get(id=word_id)
    
    # Update progress for the word
    if type == '+':
        user_word.progress += 5
    else:
        user_word.progress -= 5

    user_word.progress = min(user_word.progress, 100) # make sure progress doesn't exceed 100
    user_word.progress = max(user_word.progress, 0) # make sure progress doesn't go below 0
    user_word.save()

    return JsonResponse({'success': True})

# Add words to users
@require_http_methods(["POST", "DELETE"])
@transaction.atomic
def add_delete_words(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            # Get the selected users and words from the form
            selected_users = request.POST.getlist('users')
            selected_groups = request.POST.getlist('groups')
            selected_words = request.POST.getlist('words[]')
            if not selected_words:
                error_message = 'Error, no selected items!'
                return HttpResponseRedirect(reverse('dictionary') + '?error_message=' + error_message)
            # Add each selected word to each selected user's dictionary
            for user_id in selected_users:
                user = User.objects.get(pk=user_id)
                for word_id in selected_words:
                    word = Words.objects.get(pk=word_id)

                    if not UserWords.objects.filter(user=user, word=word).exists():
                        UserWords.objects.get_or_create(user=user, word=word, date=timezone.localtime())
            
            # For groups
            for group_id in selected_groups:
                group_users = User.objects.filter(group__id=group_id)
                for user in group_users:
                    for word_id in selected_words:
                        word = Words.objects.get(pk=word_id)

                        if not UserWords.objects.filter(user=user, word=word).exists():
                            UserWords.objects.get_or_create(user=user, word=word, date=timezone.localtime())

            # Redirect back to the main page
            success_message = 'Success!'
            return HttpResponseRedirect(reverse("dictionary") + '?success_message=' + success_message)
   
        elif action == 'delete':
            selected_words = request.POST.getlist('words[]')
            if not selected_words:
               error_message = 'Error, no selected items!'
               return HttpResponseRedirect(reverse('dictionary') + '?error_message=' + error_message)
            for word_id in selected_words:
                # Delete the Word object
                word = Words.objects.get(pk=word_id)
                word.delete()

                # Delete all UserWords objects that reference this Word object
                user_words = UserWords.objects.filter(word=word)
                user_words.delete()

            # Redirect back to the main page
            success_message = 'Success!'
            return HttpResponseRedirect(reverse("dictionary") + '?success_message=' + success_message)
        
        elif action == 'set':
            selected_topics = request.POST.getlist('topics')
            selected_words = request.POST.getlist('words[]')
            if not selected_words:
                error_message = 'Error, no selected items!'
                return HttpResponseRedirect(reverse("dictionary") + '?error_message=' + error_message)
            
            if selected_topics == None:
                for word_id in selected_words:
                    word = Words.objects.get(pk=word_id)
                    word.topics.set("")
            
            for word_id in selected_words:
                word = Words.objects.get(pk=word_id)
                word.topics.set(selected_topics)

            success_message = 'Success!'
            return HttpResponseRedirect(reverse("dictionary") + '?success_message=' + success_message)

        elif action == 'certify':
            selected_words = request.POST.getlist('words[]')
            if not selected_words:
                error_message = 'Error, no selected items!'
                return HttpResponseRedirect(reverse("dictionary") + '?error_message=' + error_message)
            
            for word_id in selected_words:
                word = Words.objects.get(pk=word_id)
                word.certified = True
                word.save()
            
            success_message = 'Success!'
            return HttpResponseRedirect(reverse("dictionary") + '?success_message=' + success_message)
        
        elif action == 'decertify':
            selected_words = request.POST.getlist('words[]')
            if not selected_words:
                error_message = 'Error, no selected items!'
                return HttpResponseRedirect(reverse("dictionary") + '?error_message=' + error_message)
            
            for word_id in selected_words:
                word = Words.objects.get(pk=word_id)
                word.certified = False
                word.save()
            
            success_message = 'Success!'
            return HttpResponseRedirect(reverse("dictionary") + '?success_message=' + success_message)


@require_POST
@csrf_exempt
def dictionary_edit(request):
    data = json.loads(request.body)
    id = data.get('id')
    name = data.get('name')
    value = data.get('value')

    value = bleach.clean(data.get('value'), tags=[], strip=True)
    value = " ".join(value.strip().split())
    value = value.replace('&nbsp;', '')

    word = Words.objects.get(id=id)
    setattr(word, name, value)
    word.save()

    return JsonResponse({'success': True})
### DICTIONARY END ###


### EGE ###
@staff_member_required
def ege_tests(request):
    return render(request, "website/ege_tests.html", {
        'ege_tests': EGEtests.objects.all()
    })


@login_required
def ege_single_test(request, ege_testname):
    test = EGEtests.objects.get(ege_testname=ege_testname)
    grammar19 = zip(test.grammar_19, test.grammar_19_words)
    grammar25 = zip(test.grammar_25, test.grammar_25_words)
    return render(request, "website/ege_test.html", {'test': test, 'grammar19': grammar19, 'grammar25': grammar25, })


def ege_check(request, ege_testname):
    ege_test = EGEtests.objects.get(ege_testname=ege_testname)
    st_answers_dict = {}
    correct_answers_dict = {}
    results_dict = {}
    questions = [("1", 6), ("2", 7), ("3", 7), ("10", 7), ("11", 6), ("12", 7), ("19", 6), ("25", 5), ("30", 7)]
    even_tasks = ["3", "12", "19", "25", "30"]
    odd_tasks = ["1", "2", "10", "11"]

    # st_answers
    for name in questions:
        question_type = name[0]
        question_count = name[1]

        for i in range(1, question_count + 1):
            key = f"{i}_{question_type}st_answers"
            answer = request.POST.get(key)

            if answer == "":
                answer = "-"
            
            if question_type in ["19", "25"]:
                answer = strip_lower(answer)
            
            # Store the answer in the dictionary
            if question_type in st_answers_dict:
                st_answers_dict[question_type].append(answer)
            else:
                st_answers_dict[question_type] = [answer]
    
    # correct_answers
    for question_type, question_count in questions:
        answer_field_name = f"answers_{question_type}"
        correct_answer = getattr(ege_test, answer_field_name)

        correct_answers_dict[question_type] = correct_answer

    # results_dict
    for question_type, question_count in questions:
        st_answers = st_answers_dict[question_type]
        correct_answers = correct_answers_dict[question_type]
        results = []

        for st_answer, correct_answer in zip(st_answers, correct_answers):
            result = (st_answer, correct_answer)
            results.append(result)

        results_dict[question_type] = results

    scores = calculate_scores(results_dict, even_tasks, odd_tasks)
    converted_score = conversion_dict[scores['overall']]
    listening = scores['1'] + scores['2'] + scores['3']
    reading = scores['10'] + scores['11'] + scores['12']
    grammar = scores['19'] + scores['25'] + scores['30']

    check = EGEresults.objects.filter(user_id = request.user.id, test_proper__ege_testname = ege_testname)
    
    if not check:
        f = EGEresults(test_proper = ege_test, user_id=request.user.id, raw=scores['overall'], converted_score=converted_score, date=timezone.localtime(), st_answers_1=st_answers_dict["1"], st_answers_2=st_answers_dict["2"], st_answers_3_9=st_answers_dict["3"], st_answers_10=st_answers_dict["10"], st_answers_11=st_answers_dict["11"], st_answers_12_18=st_answers_dict["12"], st_answers_19_24=st_answers_dict["19"], st_answers_25_29=st_answers_dict["25"], st_answers_30_36=st_answers_dict["30"], st_letter=request.POST.get("letter"), st_essay_38_1=request.POST.get("essay_1"), st_essay_38_2=request.POST.get("essay_2"), listening=listening, reading=reading, grammar=grammar, writing=None, speaking=None, score_1=scores['1'], score_2=scores['2'], score_3_9=scores['3'], score_10=scores['10'], score_11=scores['11'], score_12_18=scores['12'], score_19_24=scores['19'], score_25_29=scores['25'], score_30_36=scores['30'], st_answers=results_dict, scores=scores)
        f.save()
    
    return render(request, "website/ege_result.html", {
        'result': EGEresults.objects.get(user_id = request.user.id, test_proper__ege_testname=ege_testname)
    })


@login_required
def ege_result(request, ege_testname):
    return render(request, "website/ege_result.html", {
        "result": EGEresults.objects.get(user_id = request.user.id, test_proper__ege_testname = ege_testname)
    })


def ege_result_admin(request, ege_testname, student_id):
    return render(request, "website/ege_result.html", {
        "result": EGEresults.objects.get(user_id = student_id, test_proper__ege_testname = ege_testname)
    })


@login_required
@csrf_exempt
def save_audio(request, ege_testname):
    ege_test = EGEtests.objects.get(ege_testname = ege_testname)
    result = EGEresults.objects.get(user_id = request.user.id, test_proper__ege_testname = ege_testname)
    if request.method == "POST":
        audio_file = request.FILES['audio']
        file_name = f"{request.user.username}_{ege_test.ege_testname}.ogg"
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        with open(file_path, 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)
        result.speaking_audio = True
        result.save()
        
    return render(request, "website/ege_speaking.html", {"variant": ege_test})


@staff_member_required
def download_audio(request):
    if request.method == 'POST':
        selected_testname = request.POST.get('testname')
        selected_username = request.POST.get('username')
        
        # Construct the file path with the given username and testname
        file_path = os.path.join(settings.MEDIA_ROOT, f"{selected_username}_{selected_testname}.ogg")
        
        # Open the file and read its contents
        with open(file_path, 'rb') as file:
            file_contents = file.read()
        
        # Construct the response with the file contents and appropriate content type
        response = HttpResponse(file_contents, content_type='audio/ogg')
        response['Content-Disposition'] = f'attachment; filename="{selected_username}_{selected_testname}.ogg"'
        
        return response
    else:
        unique_testnames = EGEresults.objects.values_list('test_proper__ege_testname', flat=True).distinct()
        unique_usernames = EGEresults.objects.filter(speaking_audio=True).values_list('user__username', flat=True).distinct()
        context = {'unique_testnames': unique_testnames, 'unique_usernames': unique_usernames}
        return render(request, 'website/download_audio.html', context)
### EGE END ###

### THEORY ###

@login_required
def theory(request):
    topics = TheoryTopics.objects.order_by('order')
    entries_by_topic = {}
    for topic in topics:
        entries = Theory.objects.filter(topic=topic).order_by('order')
        if entries:
            entries_by_topic[topic] = entries
    return render(request, 'website/theory.html', {'entries_by_topic': entries_by_topic})

### THEORY END ###


### TESTS START ###
@login_required
def results(request):
    theory_entries = TheoryTopics.objects.order_by('order')
    
    # Study plan
    entries_by_topic = {theory_entry: StudyPlan.objects.filter(user=request.user.id, title__topic=theory_entry).order_by('title__order') for theory_entry in theory_entries if StudyPlan.objects.filter(user=request.user.id, title__topic=theory_entry)}

    # Test results for all
    results_by_topic = {theory_entry: {'results': Results.objects.filter(user_id=request.user.id, test_proper__topic=theory_entry).order_by('-date'), 'average_grade': Results.objects.filter(user_id=request.user.id, test_proper__topic=theory_entry).aggregate(Avg('grade'))['grade__avg']} for theory_entry in theory_entries if Results.objects.filter(user_id=request.user.id, test_proper__topic=theory_entry)}

    # Worth revising for all
    distinct_theories = set()
    for theory_entry, results_data in results_by_topic.items():
        for result in results_data['results']:
            if result.grade < 8 and result.test_proper.theory:
                distinct_theories.add(result.test_proper.theory)
    distinct_theories = list(distinct_theories)

    ### For me
    results_checked, results_test, results_speaking = EGEresults.objects.filter(checked=True), EGEresults.objects.filter(checked=False, speaking_audio=False), EGEresults.objects.filter(checked=False, speaking_audio=True)
    ### for students & me
    ege_results = EGEresults.objects.filter(user_id = request.user.id).order_by('-date')
    # gpa if any
    avg_gpa = Results.objects.filter(user_id = request.user.id).aggregate(Avg('grade'))
    user = request.user
    
    if user.teacher == True:
        # Teachers
        form_teacher = StudyPlanFormTeacher(request.POST or None, user=user)
        form_plan_teacher = GetStudyPlanTeacher(request.POST or None, user=user)

        # Admin
        form = StudyPlanForm(request.POST or None)
        form_plan = GetStudyPlan(request.POST or None)

        # Entries
        average_progress = None
        topic_progress = []
        entries_by_topic_admin = {}
        student_results = {}
        distinct_theories_admin = set()
        selected_user = None
        student_gpa = None
        if request.method == "POST":
            # get action
            action = request.POST.get('action')
            
            ### SET
            if action == 'set':
                if form.is_valid() and user.id == 45:
                    form.save()
                    return HttpResponseRedirect(reverse("results"))
                elif form_teacher.is_valid():
                    form_teacher.save()
                    return HttpResponseRedirect(reverse("results"))

            ### SHOW
            elif action == 'show':
                if form_plan.is_valid() and user.id == 45:
                    selected_user = form_plan.cleaned_data['users_show']
                    selected_user = selected_user.id
                    student_gpa = Results.objects.filter(user_id = selected_user).aggregate(Avg('grade'))

                    average_progress = UserWords.objects.filter(user_id=selected_user).aggregate(Avg('progress'))['progress__avg']
                    distinct_topics = UserWords.objects.filter(user_id=selected_user).values_list('word__topics__name', flat=True).distinct()
                    
                    for topic in distinct_topics:
                        num_words = UserWords.objects.filter(user_id=selected_user, word__topics__name=topic).count()
                        progress = UserWords.objects.filter(user_id=selected_user, word__topics__name=topic).aggregate(avg_progress=Avg('progress'))['avg_progress']
                        topic_name = topic if topic else 'No topic'
                        topic_progress.append((topic_name, progress, num_words))
                    topic_progress.sort(key=lambda x: x[1], reverse=True)

                    for theory_entry in theory_entries:
                        entries = StudyPlan.objects.filter(user=selected_user, title__topic=theory_entry).order_by('title__order')
                        if entries:
                            entries_by_topic_admin[theory_entry] = entries
                    
                    for theory_entry in theory_entries:
                        results = Results.objects.filter(user_id=selected_user, test_proper__topic=theory_entry).order_by('-date')
                        average_grade = results.aggregate(Avg('grade'))['grade__avg']
                        if results:
                            student_results[theory_entry] = {'results': results, 'average_grade': average_grade}
                    
                    for theory_entry, results_data in student_results.items():
                        for result in results_data['results']:
                            if result.grade < 8 and result.test_proper.theory:
                                distinct_theories_admin.add(result.test_proper.theory)
                    distinct_theories_admin = list(distinct_theories_admin)
                            
                elif form_plan_teacher.is_valid():
                    selected_user = form_plan_teacher.cleaned_data['users_show_teacher']
                    selected_user = selected_user.id
                    student_gpa = Results.objects.filter(user_id = selected_user).aggregate(Avg('grade'))

                    average_progress = UserWords.objects.filter(user_id=selected_user).aggregate(Avg('progress'))['progress__avg']
                    distinct_topics = UserWords.objects.filter(user_id=selected_user).values_list('word__topics__name', flat=True).distinct()
                    
                    for topic in distinct_topics:
                        num_words = UserWords.objects.filter(user_id=selected_user, word__topics__name=topic).count()
                        progress = UserWords.objects.filter(user_id=selected_user, word__topics__name=topic).aggregate(avg_progress=Avg('progress'))['avg_progress']
                        topic_name = topic if topic else 'No topic'
                        topic_progress.append((topic_name, progress, num_words))
                    topic_progress.sort(key=lambda x: x[1], reverse=True)

                    for theory_entry in theory_entries:
                        entries = StudyPlan.objects.filter(user=selected_user, title__topic=theory_entry)
                        if entries:
                            entries_by_topic_admin[theory_entry] = entries
                    
                    for theory_entry in theory_entries:
                        results = Results.objects.filter(user_id=selected_user, test_proper__topic=theory_entry).order_by('-date')
                        average_grade = results.aggregate(Avg('grade'))['grade__avg']
                        if results:
                            student_results[theory_entry] = {'results': results, 'average_grade': average_grade}
                    
                    for theory_entry, results_data in student_results.items():
                        for result in results_data['results']:
                            if result.grade < 8 and result.test_proper.theory:
                                distinct_theories_admin.add(result.test_proper.theory)
                    distinct_theories_admin = list(distinct_theories_admin)
        
        return render(request, "website/profile-teacher.html", {
            'ege_results': ege_results,
            "results_test": results_test,
            "results_speaking": results_speaking,
            "results_checked": results_checked,
            "form": form,
            "form_plan": form_plan,
            "form_teacher": form_teacher,
            "form_plan_teacher": form_plan_teacher,
            "entries_by_topic_admin": entries_by_topic_admin,
            'gpa': avg_gpa['grade__avg'],
            'results_by_topic': results_by_topic,
            'student_results': student_results,
            "student_id": selected_user,
            "student_gpa": student_gpa,
            "distinct_theories": distinct_theories,
            "distinct_theories_admin": distinct_theories_admin,
            "average_progress": average_progress,
            "topic_progress": topic_progress
        })
    
    else:
        return render(request, "website/profile-student.html", {
            'gpa': avg_gpa['grade__avg'],
            'ege_results': ege_results,
            "entries_by_topic": entries_by_topic,
            'results_by_topic': results_by_topic,
            "distinct_theories": distinct_theories
        })


@require_POST
@csrf_exempt
def results_edit(request):
    data = json.loads(request.body)
    id = data.get('id')
    new_grade = bleach.clean(data.get('grade'), tags=[], strip=True)
    
    topic_mark = StudyPlan.objects.get(id=id)
    topic_mark.grade = new_grade
    topic_mark.save()

    return JsonResponse({'status': 'success'})


@login_required
def all_tests(request):
    theory_entries = TheoryTopics.objects.order_by('order')
    tests_by_topic = {}
    for theory_entry in theory_entries:
        tests = Tests.objects.filter(topic=theory_entry).order_by('order')
        if tests:
            tests_by_topic[theory_entry] = tests
            
    user_results = Results.objects.filter(user=request.user)
    solved = set(user_results.values_list('test_proper__url', flat=True))
    return render(request, "website/all_tests.html", {"solved_set": solved, "tests_by_topic": tests_by_topic})


def solved_test(request, testname):
    results_query = Results.objects.get(user_id = request.user.id, test_proper__url = testname)
    
    context = {
            'answers': results_query.answers,
            'test_proper': results_query.test_proper,
        }

    if results_query.test_proper.explanation:
        explained = zip(results_query.answers, results_query.test_proper.explanation)
        context['explained'] = explained

    return render(request, "website/solved_test.html", context)


def solved_test_teacher(request, testname, student_id):
    results_query = Results.objects.get(user_id = student_id, test_proper__url = testname)

    context = {
            'answers': results_query.answers,
            'test_proper': results_query.test_proper,
        }

    if results_query.test_proper.explanation:
        explained = zip(results_query.answers, results_query.test_proper.explanation)
        context['explained'] = explained

    return render(request, "website/solved_test.html", context)


@login_required
def single_test(request, testname):
    test = Tests.objects.get(url=testname)
    type = test.type.type

    if type == 'gaps' or type == 'gaps_text' or type == 'single_dropdown' or type == 'single_inside_dropdown':
        return render(request, "website/test.html", {
            'test': test,
            'type': type
        })
    
    elif type == "many_dropdown" or type == "inside_dropdown" or type == "inside_dropdown_text":
        return render(request, "website/test.html", {
            'test': test,
            'type': type,
            'listening_task': zip(test.sentences, test.options)
        })
    

def lower(request, testname):
    if request.method == 'POST':
        test = Tests.objects.get(url=testname)
        type = test.type.type
        case = test.case
        sentences = test.sentences
        answers = test.answers
        
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

                
        ### Clean st_answers
        st_answers_clean = []
        st_answers = []
        for key, value in request.POST.items():
            if key.startswith('answer'):
                value = bleach.clean(value, tags=[], strip=True)
                if type in ["gaps", "gaps_text"]:
                    if value != "":
                        value = normalize_apostrophes(value)
                        value = replace_disallowed(value, disallowed_characters)
                        if case:
                            value = strip(value)
                        else:
                            value = strip_lower(value)
                        value = replace_contractions(value, replacements)
                        st_answers.append(value)
                        st_answers_clean.append(value)
                    else:
                        st_answers.append("no answer")
                        st_answers_clean.append("no answer")
                else:
                    st_answers.append(value)
                    st_answers_clean.append(value)


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


        score_percent = round((score / len(answers))*100)
        gpa_score = round(score_percent / 10, 1)
        messages.success(request, f"{(round(gpa_score, 1)):g} / 10 ({score_percent}%)")
        result_check = Results.objects.filter(user_id = request.user.id, test_proper__url = test.url)
        
        if not result_check:
            f = Results(test_proper=test, answers = results, answers_plain=st_answers_clean, grade = gpa_score, date = timezone.localtime(), user_id = request.user.id)
            f.save()
        
        context = {
            'answers': results,
            'score_percent': score_percent,
            'test': test,
        }

        if test.explanation:
            explained = zip(results, test.explanation)
            context['explained'] = explained

        return render(request, "website/checked-test.html", context)