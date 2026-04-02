from django import forms

class VideoURLForm(forms.Form):
    video_url = forms.URLField(
        widget=forms.URLInput(attrs={
            'class': 'form-control url-input',
            'placeholder': 'Paste YouTube or Instagram Reels link...',
            'id': 'videoUrlInput',
        }),
        error_messages={'invalid': 'Please enter a valid URL.', 'required': 'Video URL is required.'}
    )
