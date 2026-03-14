from django.contrib import admin

from journal.models import JournalEntry, JournalPrompt, JournalReadEvent, JournalTag


@admin.register(JournalTag)
class JournalTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
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
