from django.contrib.auth.models import AbstractUser, User
from django.db import models
from .helpers import conversion_dict
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg
from django.utils.text import slugify
from django.core.exceptions import ValidationError



class TestTypes(models.Model):
    order = models.PositiveIntegerField(unique=True)
    type = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.order} | {self.type}"


# Create your models here.
class TheoryTopics(models.Model):
    topic = models.CharField(max_length=255)
    order = models.PositiveIntegerField(unique=True)

    def __str__(self):
        return f"{self.order} | {self.topic}"
    

class Theory(models.Model):
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField()
    cefr = models.CharField(max_length=255)
    topic = models.ForeignKey(TheoryTopics, on_delete=models.CASCADE)
    url = models.URLField()

    def __str__(self):
        return f"{self.cefr} | {self.topic.topic}: {self.title}"


class Tests(models.Model):
    url = models.CharField(max_length=255, blank=True, unique=True)
    order = models.FloatField(blank=True, null=True)
    theory = models.ForeignKey(Theory, on_delete=models.CASCADE, blank=True, null=True)
    testname = models.CharField(max_length=255, unique=True)
    type = models.ForeignKey(TestTypes, on_delete=models.CASCADE)
    topic = models.ForeignKey(TheoryTopics, on_delete=models.CASCADE)
    lvl = models.CharField(max_length=255)
    sentences = models.JSONField()
    answers = models.JSONField()
    explanation = models.JSONField(blank=True, null=True)
    options = models.JSONField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    audio_path = models.CharField(max_length=255, blank=True)
    script = models.TextField(blank=True, null=True)
    case = models.BooleanField(default=False)
    task = models.TextField(blank=True)
    input_size = models.PositiveIntegerField(blank=True, null=True)
    picture = models.CharField(max_length=255, blank=True, null=True)
    part = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        self.url = slugify(self.testname)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.topic} | {self.testname}: {self.lvl}"
    

class Posts(models.Model):
    post_name = models.CharField(max_length=255, blank=True, unique=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.post_name} | {self.source}"


class FreeTests(models.Model):
    url = models.CharField(max_length=255, blank=True, unique=True)
    testname = models.CharField(max_length=255, unique=True)
    order = models.FloatField(blank=True, null=True)
    theory = models.ForeignKey(Theory, on_delete=models.CASCADE, blank=True, null=True)
    topic = models.ForeignKey(TheoryTopics, on_delete=models.CASCADE, blank=True, null=True)
    type = models.ForeignKey(TestTypes, on_delete=models.CASCADE, blank=True, null=True)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, blank=True, null=True)
    lvl = models.CharField(max_length=255, blank=True, null=True)
    sentences = models.JSONField(blank=True, null=True)
    answers = models.JSONField(blank=True, null=True)
    explanation = models.JSONField(blank=True, null=True)
    options = models.JSONField(blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    audio_path = models.CharField(max_length=255, blank=True)
    script = models.TextField(blank=True, null=True)
    case = models.BooleanField(default=False)
    task = models.TextField(blank=True)
    input_size = models.PositiveIntegerField(blank=True, null=True)
    picture = models.CharField(max_length=255, blank=True, null=True)
    part = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        self.url = slugify(self.testname)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.lvl} | {self.testname}"
    

class User(AbstractUser):
    comment = models.TextField(blank=True, null=True)
    cefr = models.CharField(max_length=20, blank=True)
    progress = models.IntegerField(blank=True, null=True)
    gpa = models.FloatField(blank=True, null=True)
    google = models.URLField(blank=True)
    topics = models.ManyToManyField(Theory, through='StudyPlan')
    teacher = models.BooleanField(default=False)

    def __str__(self):
        groups = Group.objects.filter(users=self)
        if groups:
            group_names = ', '.join(str(group.name) for group in groups)
            return f"{group_names} | {self.cefr} {self.first_name} {self.last_name}"
        else:
            return f"{self.cefr} {self.first_name} {self.last_name}"


class Group(models.Model):
    name = models.CharField(max_length=255)
    users = models.ManyToManyField(User, limit_choices_to={'teacher': False}, blank=True)

    def __str__(self):
        user_names = ', '.join([user.first_name for user in self.users.all()])
        return f"{self.name}: {user_names}"


class TeacherStudent(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'teacher': True}, related_name='teacher_students')
    students = models.ManyToManyField(User, limit_choices_to={'teacher': False}, related_name='student_teachers', blank=True)
    groups = models.ManyToManyField(Group, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        user_names = ', '.join([user.first_name for user in self.students.all()])
        return f"{self.teacher}: {user_names}"

    def clean(self):
        """
        Ensure that there are no duplicates in the M2M relationship between
        teachers and students.
        """
        if self.pk:
            # Only fetch the related students when the TeacherStudent instance
            # has been saved to the database.
            students = self.students.all()

            # Ensure that each student is unique in the M2M relationship.
            if len(set(students)) != len(students):
                raise ValidationError('Duplicate student found.')

            # Ensure that the teacher-student combination is unique.
            if TeacherStudent.objects.filter(teacher=self.teacher, students__in=students).exclude(pk=self.pk).exists():
                raise ValidationError('This teacher is already teaching one or more of these students.')
        else:
            super().clean()


class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.ForeignKey(Theory, on_delete=models.CASCADE, blank=True, null=True)
    grade = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], default=0)
    covered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user}: {self.title} | {self.covered} | {self.grade}"


class Results(models.Model):
    test_proper = models.ForeignKey(Tests, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    grade = models.FloatField()
    date = models.DateTimeField()
    answers = models.JSONField()
    answers_plain = models.JSONField()

    def __str__(self):
        return f"{self.user} - {self.test_proper.testname}: {self.grade} ({self.test_proper.topic})"


class Topic(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Words(models.Model):
    english_word = models.TextField()
    russian_word = models.TextField()
    context = models.TextField()
    date = models.DateTimeField(blank=True, null=True)
    user_added = models.BooleanField(default=False)
    contributor = models.ForeignKey(User, on_delete=models.CASCADE)
    topics = models.ManyToManyField(Topic, blank=True)
    certified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.english_word} - {self.russian_word}"


class UserWords(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    word = models.ForeignKey(Words, on_delete=models.CASCADE)
    progress = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0) 
    date = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username}: {self.word.english_word} - {self.word.russian_word}"


class Reviews(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    img = models.CharField(max_length=255, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    surname = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    social = models.URLField(blank=True, null=True)
    service = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} {self.surname}"


class EGEtests(models.Model):
    ege_testname = models.CharField(max_length=255)
    listening_path = models.CharField(max_length=255, blank=True, null=True)
    listening_1 = models.JSONField(blank=True, null=True)
    answers_1 = models.JSONField(blank=True, null=True)
    listening_2 = models.JSONField(blank=True, null=True)
    answers_2 = models.JSONField(blank=True, null=True)
    listening_3 = models.JSONField(blank=True, null=True)
    answers_3 = models.JSONField(blank=True, null=True)
    reading_10_options = models.JSONField(blank=True, null=True)
    reading_10 = models.JSONField(blank=True, null=True)
    answers_10 = models.JSONField(blank=True, null=True)
    reading_11_options =models.JSONField(blank=True, null=True)
    reading_11 =  models.TextField(blank=True, null=True)
    answers_11 =  models.JSONField(blank=True, null=True)
    reading_12_options = models.JSONField(blank=True, null=True)
    reading_12 = models.TextField(blank=True, null=True)
    answers_12 = models.JSONField(blank=True, null=True)
    grammar_19 = models.JSONField(blank=True, null=True)
    grammar_19_words = models.JSONField(blank=True, null=True)
    answers_19 = models.JSONField(blank=True, null=True)
    grammar_25 = models.JSONField(blank=True, null=True)
    grammar_25_words = models.JSONField(blank=True, null=True)
    answers_25 = models.JSONField(blank=True, null=True)
    grammar_30 = models.TextField(blank=True, null=True)
    grammar_30_options = models.JSONField(blank=True, null=True)
    answers_30 = models.JSONField(blank=True, null=True)
    letter_name = models.CharField(max_length=255, blank=True, null=True)
    letter = models.TextField(blank=True, null=True)
    letter_task = models.TextField(blank=True, null=True)
    essay_1_task = models.TextField(blank=True, null=True)
    essay_1_data = models.TextField(blank=True, null=True)
    essay_1_conclusion = models.TextField(blank=True, null=True)
    essay_2_task = models.TextField(blank=True, null=True)
    essay_2_data = models.TextField(blank=True, null=True)
    essay_2_conclusion = models.TextField(blank=True, null=True)
    speaking_text = models.TextField(blank=True, null=True)
    ad_img = models.CharField(max_length=255, blank=True, null=True)
    ad_header = models.CharField(max_length=255, blank=True, null=True)
    ad_task = models.TextField(blank=True, null=True)
    ad_questions = models.JSONField(blank=True, null=True)
    interview_path = models.CharField(max_length=255, blank=True, null=True)
    monologue_topic = models.CharField(max_length=255, blank=True, null=True)
    monologue_points = models.JSONField(blank=True, null=True)
    monologue_imgs = models.JSONField(blank=True, null=True)



    def __str__(self):
        return self.ege_testname
    

class EGEresults(models.Model):
    test_proper = models.ForeignKey(EGEtests, on_delete=models.CASCADE, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    checked = models.BooleanField(default=False)
    speaking_audio = models.BooleanField(default=False)
    converted_score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    raw = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(86)])
    date = models.DateTimeField()
    st_answers_1 = models.JSONField(blank=True, null=True)
    score_1 = models.IntegerField(default=0)
    st_answers_2 = models.JSONField(blank=True, null=True)
    score_2 = models.IntegerField(default=0)
    st_answers_3_9 = models.JSONField(blank=True, null=True)
    score_3_9 = models.IntegerField(default=0)
    st_answers_10 = models.JSONField(blank=True, null=True)
    score_10 = models.IntegerField(default=0)
    st_answers_11 = models.JSONField(blank=True, null=True)
    score_11 = models.IntegerField(default=0)
    st_answers_12_18 = models.JSONField(blank=True, null=True)
    score_12_18 = models.IntegerField(default=0)
    st_answers_19_24 = models.JSONField(blank=True, null=True)
    score_19_24 = models.IntegerField(default=0)
    st_answers_25_29 = models.JSONField(blank=True, null=True)
    score_25_29 = models.IntegerField(default=0)
    st_answers_30_36 = models.JSONField(blank=True, null=True)
    score_30_36 = models.IntegerField(default=0)
    st_letter = models.TextField(blank=True, null=True)
    letter_score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(6)])
    st_essay_38_1 = models.TextField(blank=True, null=True)
    st_essay_38_2 = models.TextField(blank=True, null=True)
    essay_score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(14)])
    listening = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(14)])
    reading = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(14)])
    grammar = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(18)])
    writing = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(20)])
    speaking_read = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(1)])
    speaking_questions = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(4)])
    speaking_interview = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    speaking_monologue = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    speaking = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(20)])
    st_answers = models.JSONField(blank=True, null=True)
    scores = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}: {self.test_proper.ege_testname} - {self.converted_score} (Checked: {self.checked}) | (Audio: {self.speaking_audio})"
    
    def save(self, *args, **kwargs):
        self.writing = self.essay_score + self.letter_score
        self.speaking = self.speaking_read + self.speaking_questions + self.speaking_interview + self.speaking_monologue
        self.raw = self.listening + self.reading + self.grammar + self.writing + self.speaking
        self.converted_score = conversion_dict[self.raw]
        
        super().save(*args, **kwargs)