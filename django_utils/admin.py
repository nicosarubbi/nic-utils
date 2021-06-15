from django.contrib import admin
from django.core import serializers
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import mark_safe


def inline_generator(mymodel, fields_list=None):
    fields_list = fields_list or []
    fields_list.insert(0, 'get_id_link')

    class CustomInline(LinkedInline):
        custom_fields = fields_list
        model = mymodel
        fields = custom_fields
        readonly_fields = custom_fields

    return CustomInline


class LinkedInline(admin.TabularInline):
    template = 'tabular.html'
    extra = 0

    def get_id_link(self, obj):
        if obj.pk:
            url = reverse('admin:%s_%s_change' % (obj._meta.app_label, obj._meta.model_name), args=[obj.pk])
            return mark_safe('<a href="%s">%s</a>' % (url, obj.pk))
        return None

    get_id_link.short_description = 'id'


def download_fixture(modeladmin, request, queryset):
    """ action for ModelAdmin that returns the queryset as a fixture.json file """
    #
    # class MiModelAdmin(admin.ModelAdmin):
    #     actions = (download_fixture,)
    #

    stream = serializers.serialize("json", queryset, indent=2)
    response = HttpResponse(stream, content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="wording.json"'
    return response


class InputFilter(admin.SimpleListFilter):
    """Filter for admin, that doesn't show all the items like a list, but it shows an input instead."""

    template = 'input_filter.html'
    def lookups(self, request, model_admin):
        return (((), ),)

    def choices(self, changelist):
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


###########################
######## examples #########
###########################

RelatedModel = None  # just for example purpose.

class ExampleFilter(InputFilter):
    title = 'Example'
    parameter_name = 'example'

    def queryset(self, request, queryset):
        if value is not None:
            # do something
            pass
        return queryset


class ExampleAdmin(admin.ModelAdmin):
    list_filter = (ExampleFilter,)
    actions = (download_fixture,)
    inlines = [
        inline_generator(RelatedModel, fields_list=['field1', 'field2', 'field3']),
    ]