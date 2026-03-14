from django import forms
from django.contrib import admin

from journal.models import JournalEntry, JournalPrompt, JournalReadEvent, JournalTag


class JournalEntryAdminForm(forms.ModelForm):
    """Use checkboxes for cognitive distortions instead of raw JSON editing."""
    cognitive_distortions = forms.MultipleChoiceField(
        choices=JournalEntry.COGNITIVE_DISTORTIONS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text='Select one or more distortions. Leave empty if none apply.',
    )

    class Meta:
        model = JournalEntry
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['cognitive_distortions'].initial = self.instance.cognitive_distortions or []

    def clean_cognitive_distortions(self):
        values = self.cleaned_data.get('cognitive_distortions', [])
        # Store as a JSON list of keys in the model field.
        return list(values)


@admin.register(JournalTag)
class JournalTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    form = JournalEntryAdminForm
    list_display = (
        'id',
        'user',
        'title',
        'mood',
        'entry_date',
        'is_favorite',
        'is_archived',
        'read_count',
        'created_at',
    )
    list_filter = ('mood', 'is_favorite', 'is_archived', 'entry_date')
    search_fields = ('title', 'content', 'user__username', 'user__email', 'tags__name')
    filter_horizontal = ('tags',)
    raw_id_fields = ('user',)


@admin.register(JournalReadEvent)
class JournalReadEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'entry', 'user', 'source', 'read_at')
    list_filter = ('source', 'read_at')
    search_fields = ('entry__title', 'user__username', 'user__email')
    raw_id_fields = ('entry', 'user')


@admin.register(JournalPrompt)
class JournalPromptAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'prompt_text', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('prompt_text',)
