from django import forms
from .models import Course, Lesson, Module, Quiz, Question, QuizAttempt, Choice, UserAnswer, DiscussionThread, DiscussionReply


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'price', 'thumbnail', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content', 'video_url', 'duration', 'order']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6}),
        }


class QuizAttemptForm(forms.ModelForm):
    class Meta:
        model = QuizAttempt
        fields = [] # We will handle answers separately


class UserAnswerForm(forms.ModelForm):
    class Meta:
        model = UserAnswer
        fields = ['selected_choice', 'text_answer']

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question', None)
        super().__init__(*args, **kwargs)

        if question and question.question_type == 'multiple_choice':
            self.fields['selected_choice'].queryset = question.choices.all()
            self.fields['selected_choice'].widget = forms.RadioSelect()
            self.fields['text_answer'].widget = forms.HiddenInput()
        elif question and question.question_type == 'true_false':
            self.fields['selected_choice'].queryset = question.choices.all()
            self.fields['selected_choice'].widget = forms.RadioSelect()
            self.fields['text_answer'].widget = forms.HiddenInput()
        else:
            self.fields['selected_choice'].widget = forms.HiddenInput()


class DiscussionThreadForm(forms.ModelForm):
    class Meta:
        model = DiscussionThread
        fields = ['title', 'content']
        widgeta = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter discussion title.....'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Start the discusson....'}),
        }


class DiscussionReplyForm(forms.ModelForm):
    class Meta:
        model = DiscussionReply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Write the reoly.....'}),
        }