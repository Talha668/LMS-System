from django import forms
from .models import Course, Lesson, QuizAttempt, UserAnswer, DiscussionThread, DiscussionReply, Rating, Category


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


class RatingForm(forms.ModelForm):
    """Form for rating courses""" 
    class Meta:
        model = Rating
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, f"{i}★") for i in range(1, 6)]),
            'review': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Share your'
            'thoughts about this course.....'}),
        }     


class DiscussionsThreadForm(forms.ModelForm):
    """forms for creating discussion threads"""
    class Meta:
        model = DiscussionThread
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }


class DiscussionReplyForm(forms.ModelForm):
    """Form for replying to discussions"""
    class Meta:
        model = DiscussionReply
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placehoder': 'Write your'
            'reply....'}),
        }


class UserAnswerForm(forms.Form):
    """Form for quiz answers"""
    def __init__(self, *args, **Kwargs):
        question = Kwargs.pop('question', None)
        super().__init__(*args, **Kwargs)

        if question:
            if question.question_type in ['multiple_choice', 'true_false']:
                choices = [(choice.id, choice.choice_text) for choice in question.choices.all()]
                self.fields['selected_choice'] = forms.ChoiceField(
                    choices=choices,
                    widget=forms.RadioSelect,
                    required=True
                )
            elif question.question_type == 'short_answer':
                self.fields['text_answer'] = forms.CharField(
                    widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
                    required=True
                )    


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug', 'description', 'icon', 'parent', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fas fa-code'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }