#! coding: utf-8

from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect

from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.contenttypes.models import ContentType

# from utils.views import ACTIONS
from django.views import generic
from utils.views import LoginRequiredView, SuperUserRequiredView, GenericUpdateWithOneFormset

from django.conf import settings

from models import *
from forms import *

from django.db.models import Prefetch
from django.db.models import Q

from django.utils.translation import ugettext_lazy as _, get_language
from django.core.paginator import Paginator


from django.contrib import messages



ITEMS_PER_PAGE = 10


# form actions
ACTIONS = {
    'descriptor_name': '',
    'filter_language': '',
    'descriptor_ui': '',

    'qualifier_name': '',
    'abbreviation': '',
    'qualifier_ui': '',

    'filter_fields': '',
    'filter_status': '',

    'decs_code': '',
    'tree_number': '',

    'orderby': 'id',
    'order': '',
    'page': 1,

    'visited': '',
    's': '',
    'exact': '',
}

# Descriptors ------------------------------------------------------------------------

class DescUpdate(LoginRequiredView):
    """
    Handle creation and update of Descriptors objects
    """
    model = IdentifierDesc
    success_url = reverse_lazy('list_descriptor')
    form_class = IdentifierDescForm
    template_name = "thesaurus/descriptor_form.html"

    def form_valid(self, form):
        formset_descriptor = DescriptionDescFormSet(self.request.POST, instance=self.object)
        formset_category = TreeNumbersListDescFormSet(self.request.POST, instance=self.object)
        formset_concept = ConceptListDescFormSet(self.request.POST, instance=self.object)
        # formset_concept_relation = ConceptRelationDescFormSet(self.request.POST, instance=self.object)
        formset_previous = PreviousIndexingListDescFormSet(self.request.POST, instance=self.object)        
        formset_term = TermListDescFormSet(self.request.POST, instance=self.object)

        # run all validation before for display formset errors at form
        form_valid = form.is_valid()
        formset_descriptor_valid = formset_descriptor.is_valid()
        formset_category_valid = formset_category.is_valid()
        formset_concept_valid = formset_concept.is_valid()
        # formset_concept_relation_valid = formset_concept_relation.is_valid()
        formset_previous_valid = formset_previous.is_valid()
        formset_term_valid = formset_term.is_valid()

        if (form_valid and formset_descriptor_valid and formset_category_valid and formset_concept_valid and formset_previous_valid and formset_term_valid):
        # if (form_valid and formset_descriptor_valid and formset_category_valid and formset_concept_valid and formset_concept_relation_valid and formset_previous_valid and formset_term_valid):

            self.object = form.save()

            formset_descriptor.instance = self.object
            formset_descriptor.save()

            formset_category.instance = self.object
            formset_category.save()

            formset_concept.instance = self.object
            formset_concept.save()

            # formset_concept_relation.instance = self.object
            # formset_concept_relation.save()

            formset_previous.instance = self.object
            formset_previous.save()

            formset_term.instance = self.object
            formset_term.save()

            form.save()
            # form.save_m2m()
            return HttpResponseRedirect(self.get_success_url())

        else:
            return self.render_to_response(
                        self.get_context_data(
                                            form=form,
                                            formset_descriptor=formset_descriptor,
                                            formset_category=formset_category,
                                            formset_concept=formset_concept,
                                            formset_previous=formset_previous,
                                            formset_term=formset_term
                                            )
                                        )

    def form_invalid(self, form):
        # force use of form_valid method to run all validations
        return self.form_valid(form)


    def get_context_data(self, **kwargs):
        context = super(DescUpdate, self).get_context_data(**kwargs)

        context['descriptor_info'] = get_language()

        if IdentifierDesc.objects.count() > 0:
            context['next_id'] = int(IdentifierDesc.objects.latest('id').id) + 60000
        else:
            context['next_id'] = 1


        if self.request.method == 'GET':

            context['formset_descriptor'] = DescriptionDescFormSet(instance=self.object)
            context['formset_category'] = TreeNumbersListDescFormSet(instance=self.object)
            context['formset_concept'] = ConceptListDescFormSet(instance=self.object)

            # context['formset_concept_relation'] = ConceptRelationDescFormSet(instance=self.object)

            context['formset_previous'] = PreviousIndexingListDescFormSet(instance=self.object)
            context['formset_term'] = TermListDescFormSet(instance=self.object)

       
        return context


class DescCreateView(DescUpdate, CreateView):
    """
    Used as class view to create Descriptors
    Extend DescUpdate that do all the work
    """
    def get_success_url(self):
        messages.success(self.request, 'is created')
        return '/thesaurus/descriptors/edit/%s' % self.object.id


class DescUpdateView(DescUpdate, UpdateView):
    """
    Used as class view to update Descriptors
    Extend DescUpdate that do all the work
    """
    def get_success_url(self):
        messages.success(self.request, 'is updated')
        return '/thesaurus/descriptors/edit/%s' % self.object.id


class DescDeleteView(DescUpdate, DeleteView):
    """
    Used as class view to delete Descriptors
    Extend DescUpdate that do all the work
    """
    model = IdentifierDesc
    template_name = 'thesaurus/descriptor_confirm_delete.html'
    success_url = reverse_lazy('list_descriptor')


class DescListView(LoginRequiredView, ListView):
    """
    List descriptor records (used by relationship popup selection window)
    """
    template_name = "thesaurus/thesaurus_home.html"
    context_object_name = "registers"
    # paginate_by = settings.ITEMS_PER_PAGE
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self):
        lang_code = get_language()
        object_list = []

        # getting action parameter
        self.actions = {}
        for key in ACTIONS.keys():
            self.actions[key] = self.request.GET.get(key, ACTIONS[key])

        # icontains X exact -------------------------------------------------------------------------------------
        if self.actions['exact']:
            q_descriptor_name = Q(descriptors__descriptor_name=self.actions['s'])
        else:
            q_descriptor_name = Q(descriptors__descriptor_name__icontains=self.actions['s'])

        # term_string
        if self.actions['filter_fields'] == 'term_string' and self.actions['exact']:
            q_term_string = Q(termdesc__term_string=self.actions['s'])
        else:
            if self.actions['filter_fields'] == 'term_string' and not self.actions['exact']:
                q_term_string = Q(termdesc__term_string__icontains=self.actions['s'])

        # filter_language
        if self.actions['filter_language'] and not self.actions['filter_fields'] == 'term_string':
            q_filter_language = Q(descriptors__language_code=self.actions['filter_language'])
        else:
            q_filter_language = Q(termdesc__language_code=self.actions['filter_language'])

        # status
        if self.actions['filter_status']:
            q_filter_status = Q(status=self.actions['filter_status'])

        # icontains X exact -------------------------------------------------------------------------------------

        # AND performance for Descriptor ------------------------------------------------------------------------
        if not self.actions['filter_fields'] == 'term_string':
            if self.actions['s'] and not self.actions['filter_fields']:
                object_list = IdentifierDesc.objects.filter( q_descriptor_name ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')
            else:
                object_list = IdentifierDesc.objects.all().values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # descriptor_name
            if self.actions['filter_fields'] == 'descriptor_name' and self.actions['s']:
                object_list = IdentifierDesc.objects.filter( q_descriptor_name ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # The choice of language is mandatory to load the result and to use the filters of the next fields
            if self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierDesc.objects.filter( Q( q_descriptor_name & q_filter_language )
                    ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            if not self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierDesc.objects.filter( q_filter_language ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # status
            if self.actions['filter_status']:
                object_list = object_list.filter(status=self.actions['filter_status'])


            # descriptor_ui
            if self.actions['filter_fields'] == 'descriptor_ui' and self.actions['s']:
                object_list = IdentifierDesc.objects.filter(
                    descriptor_ui=self.actions['s'],
                    ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # descriptor_ui and filter_language
            if self.actions['filter_fields'] == 'descriptor_ui' and self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierDesc.objects.filter( Q( descriptor_ui=self.actions['s'] ) & q_filter_language ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # descriptor_ui and filter_status
            if self.actions['filter_fields'] == 'descriptor_ui' and self.actions['s'] and self.actions['filter_status']:
                object_list = IdentifierDesc.objects.filter( Q( descriptor_ui=self.actions['s'] ) & q_filter_status ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # descriptor_ui and filter_language and filter_status
            if self.actions['filter_fields'] == 'descriptor_ui' and self.actions['s'] and self.actions['filter_language'] and self.actions['filter_status']:
                object_list = IdentifierDesc.objects.filter( Q( descriptor_ui=self.actions['s'] ) & q_filter_language & q_filter_status ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')


            # decs_code
            if self.actions['filter_fields'] == 'decs_code' and self.actions['s']:
                object_list = IdentifierDesc.objects.filter(
                    decs_code=self.actions['s'],
                    ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # decs_code and filter_language
            if self.actions['filter_fields'] == 'decs_code' and self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierDesc.objects.filter( Q( decs_code=self.actions['s'] ) & q_filter_language ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # decs_code and filter_status
            if self.actions['filter_fields'] == 'decs_code' and self.actions['s'] and self.actions['filter_status']:
                object_list = IdentifierDesc.objects.filter( Q( decs_code=self.actions['s'] ) & q_filter_status ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # decs_code and filter_language and filter_status
            if self.actions['filter_fields'] == 'decs_code' and self.actions['s'] and self.actions['filter_language'] and self.actions['filter_status']:
                object_list = IdentifierDesc.objects.filter( Q( decs_code=self.actions['s'] ) & q_filter_language & q_filter_status ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')


            # tree_number
            if self.actions['filter_fields'] == 'tree_number' and self.actions['s']:
                object_list = IdentifierDesc.objects.filter(
                    dtreenumbers__tree_number=self.actions['s'],
                    ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # tree_number and filter_language
            if self.actions['filter_fields'] == 'tree_number' and self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierDesc.objects.filter( Q( dtreenumbers__tree_number=self.actions['s']) & q_filter_language ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # tree_number and filter_status
            if self.actions['filter_fields'] == 'tree_number' and self.actions['s'] and self.actions['filter_status']:
                object_list = IdentifierDesc.objects.filter( Q( dtreenumbers__tree_number=self.actions['s'] ) & q_filter_status ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')

            # tree_number and filter_language and filter_status
            if self.actions['filter_fields'] == 'tree_number' and self.actions['s'] and self.actions['filter_language'] and self.actions['filter_status']:
                object_list = IdentifierDesc.objects.filter( Q( dtreenumbers__tree_number=self.actions['s'] ) & q_filter_language & q_filter_status ).values('id','status','descriptor_ui','decs_code','descriptors__descriptor_name','descriptors__language_code')



        # when term_string selected -----------------------------------------------------------------------------
        if self.actions['filter_fields'] == 'term_string':
            if self.actions['s'] and not self.actions['s'] == '*':
                object_list = IdentifierDesc.objects.filter( q_term_string ).values('id','status','descriptor_ui','decs_code','termdesc__term_string','termdesc__language_code')
            else:
                object_list = IdentifierDesc.objects.filter( q_term_string ).values('id','status','descriptor_ui','decs_code','termdesc__term_string','termdesc__language_code')

            # filter_language
            if self.actions['filter_language']:
                object_list = IdentifierDesc.objects.filter( Q( q_term_string & q_filter_language )
                    ).values('id','status','descriptor_ui','decs_code','termdesc__term_string','termdesc__language_code')

            # status
            if self.actions['filter_status']:
                object_list = object_list.filter(status=self.actions['filter_status']).values('id','status','descriptor_ui','decs_code','termdesc__term_string','termdesc__language_code')


        # order performance -------------------------------------------------------------------------------------
        if self.actions['order'] == "-":
            object_list = object_list.order_by("%s%s" % (self.actions["order"], self.actions["orderby"]))
        else:
            if self.actions['filter_fields'] == 'term_string':
                object_list = object_list.order_by('termdesc__term_string')
            else:
                object_list = object_list.order_by('descriptors__descriptor_name')

        if self.actions['visited'] != 'ok':
            object_list = object_list.none()

        return object_list


    def get_context_data(self, **kwargs):
        context = super(DescListView, self).get_context_data(**kwargs)

        context['actions'] = self.actions

        return context



# class DescConceptRelationView(LoginRequiredView, FormView):
#     """
#     Handle creation and update of Concept List Descriptors objects
#     """
#     success_url = reverse_lazy('list_descriptor')
#     form_class = ConceptRelationDescForm
#     template_name = "thesaurus/edit_concept_relation_descriptor_form.html"




# Qualifiers -------------------------------------------------------------------------
class QualifUpdate(LoginRequiredView):
    """
    Handle creation and update of Qaulifier objects
    """
    model = IdentifierQualif
    success_url = reverse_lazy('list_qualifier')
    form_class = IdentifierQualifForm
    template_name = "thesaurus/qualifier_form.html"

    def dispatch(self, *args, **kwargs):
        return super(QualifUpdate, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        formset_descriptor = DescriptionQualifFormSet(self.request.POST, instance=self.object)
        formset_category = TreeNumbersListQualifFormSet(self.request.POST, instance=self.object)
        formset_concept = ConceptListQualifFormSet(self.request.POST, instance=self.object)
        formset_term = TermListQualifFormSet(self.request.POST, instance=self.object)        

        # run all validation before for display formset errors at form
        form_valid = form.is_valid()
        formset_descriptor_valid = formset_descriptor.is_valid()
        formset_category_valid = formset_category.is_valid()
        formset_concept_valid = formset_concept.is_valid()
        formset_term_valid = formset_term.is_valid()

        if (form_valid and formset_descriptor_valid and formset_concept_valid and formset_category_valid and formset_term_valid):
            self.object = form.save()

            formset_descriptor.instance = self.object
            formset_descriptor.save()

            formset_category.instance = self.object
            formset_category.save()

            formset_concept.instance = self.object
            formset_concept.save()

            formset_term.instance = self.object
            formset_term.save()

            form.save()
            return HttpResponseRedirect(self.get_success_url())

        else:
            return self.render_to_response(
                        self.get_context_data(
                                            form=form,
                                            formset_descriptor=formset_descriptor,
                                            formset_category=formset_category,
                                            formset_concept=formset_concept,
                                            formset_term=formset_term
                                            )
                                        )

    def form_invalid(self, form):
        # force use of form_valid method to run all validations
        return self.form_valid(form)


    def get_context_data(self, **kwargs):
        context = super(QualifUpdate, self).get_context_data(**kwargs)

        context['qualifier_info'] = get_language()

        if self.request.method == 'GET':

            context['formset_descriptor'] = DescriptionQualifFormSet(instance=self.object)
            context['formset_category'] = TreeNumbersListQualifFormSet(instance=self.object)
            context['formset_concept'] = ConceptListQualifFormSet(instance=self.object)
            context['formset_term'] = TermListQualifFormSet(instance=self.object)

        return context


class QualifCreateView(QualifUpdate, CreateView):
    """
    Used as class view to create Qualifiers
    Extend QualifUpdate that do all the work
    """
    def get_success_url(self):
        messages.success(self.request, 'is created')
        return '/thesaurus/qualifiers/edit/%s' % self.object.id


class QualifUpdateView(QualifUpdate, UpdateView):
    """
    Used as class view to update Qualifiers
    Extend QualifUpdate that do all the work
    """
    def get_success_url(self):
        messages.success(self.request, 'is updated')
        return '/thesaurus/qualifiers/edit/%s' % self.object.id


class QualifDeleteView(QualifUpdate, DeleteView):
    """
    Used as class view to delete Qualifiers
    Extend QualifUpdate that do all the work
    """
    model = IdentifierQualif
    template_name = 'thesaurus/qualifier_confirm_delete.html'
    success_url = reverse_lazy('list_qualifier')


class QualifListView(LoginRequiredView, ListView):
    """
    Handle list view for qualifier records
    """

    template_name = "thesaurus/qualifier_list.html"
    context_object_name = "registers"
    # paginate_by = settings.ITEMS_PER_PAGE
    paginate_by = ITEMS_PER_PAGE

    def dispatch(self, *args, **kwargs):
        return super(QualifListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        lang_code = get_language()

        # getting action parameter
        self.actions = {}
        for key in ACTIONS.keys():
            self.actions[key] = self.request.GET.get(key, ACTIONS[key])


        # icontains X exact -------------------------------------------------------------------------------------
        if self.actions['exact']:
            q_qualifier_name = Q(qualifiers__qualifier_name=self.actions['s'])
        else:
            q_qualifier_name = Q(qualifiers__qualifier_name__icontains=self.actions['s'])

        # term_string
        if self.actions['filter_fields'] == 'term_string' and self.actions['exact']:
            q_term_string = Q(termqualif__term_string=self.actions['s'])
        else:
            if self.actions['filter_fields'] == 'term_string' and not self.actions['exact']:
                q_term_string = Q(termqualif__term_string__icontains=self.actions['s'])

        # filter_language
        if self.actions['filter_language'] and not self.actions['filter_fields'] == 'term_string':
            q_filter_language = Q(qualifiers__language_code=self.actions['filter_language'])
        else:
            q_filter_language = Q(termqualif__language_code=self.actions['filter_language'])

        # status
        if self.actions['filter_status']:
            q_filter_status = Q(status=self.actions['filter_status'])

        # icontains X exact -------------------------------------------------------------------------------------

        # AND performance for Qualifier -------------------------------------------------------------------------
        if not self.actions['filter_fields'] == 'term_string':
            if self.actions['s'] and not self.actions['filter_fields']:
                object_list = IdentifierQualif.objects.filter( q_qualifier_name ).values('id','status','abbreviation','qualifier_ui','decs_code','qualifiers__qualifier_name','qualifiers__language_code')
            else:
                object_list = IdentifierQualif.objects.all().values('id','status','abbreviation','qualifier_ui','decs_code','qualifiers__qualifier_name','qualifiers__language_code')

            # qualifier_name
            if self.actions['filter_fields'] == 'qualifier_name' and self.actions['s']:
                object_list = IdentifierQualif.objects.filter( q_qualifier_name ).values('id','status','abbreviation','qualifier_ui','decs_code','qualifiers__qualifier_name','qualifiers__language_code')

            # The choice of language is mandatory to load the result and to use the filters of the next fields
            if self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierQualif.objects.filter( Q( q_qualifier_name & q_filter_language )).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')

            if not self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierQualif.objects.filter( q_filter_language ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')


            # status
            if self.actions['filter_status']:
                object_list = object_list.filter(status=self.actions['filter_status'])


            # abbreviation
            if self.actions['filter_fields'] == 'abbreviation' and self.actions['s']:
                object_list = IdentifierQualif.objects.filter(
                    abbreviation=self.actions['s'],
                    ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')

            # abbreviation and filter_language
            if self.actions['filter_fields'] == 'abbreviation' and self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierQualif.objects.filter( Q( abbreviation=self.actions['s'] ) & q_filter_language ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')

            # abbreviation and filter_language and filter_status
            if self.actions['filter_fields'] == 'abbreviation' and self.actions['s'] and self.actions['filter_language'] and self.actions['filter_status']:
                object_list = IdentifierQualif.objects.filter( Q( abbreviation=self.actions['s'] ) & q_filter_language & q_filter_status ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')


            # qualifier_ui
            if self.actions['filter_fields'] == 'qualifier_ui' and self.actions['s']:
                object_list = IdentifierQualif.objects.filter(
                    qualifier_ui=self.actions['s'],
                    ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')

            # qualifier_ui and filter_language
            if self.actions['filter_fields'] == 'qualifier_ui' and self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierQualif.objects.filter( Q( qualifier_ui=self.actions['s'] ) & q_filter_language ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')

            # qualifier_ui and filter_language and filter_status
            if self.actions['filter_fields'] == 'qualifier_ui' and self.actions['s'] and self.actions['filter_language'] and self.actions['filter_status']:
                object_list = IdentifierQualif.objects.filter( Q( qualifier_ui=self.actions['s'] ) & q_filter_language & q_filter_status ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')


            # decs_code
            if self.actions['filter_fields'] == 'decs_code' and self.actions['s']:
                object_list = IdentifierQualif.objects.filter(
                    decs_code=self.actions['s'],
                    ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')

            # decs_code and filter_language
            if self.actions['filter_fields'] == 'decs_code' and self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierQualif.objects.filter( Q( decs_code=self.actions['s'] ) & q_filter_language ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')

            # decs_code and filter_language and filter_status
            if self.actions['filter_fields'] == 'decs_code' and self.actions['s'] and self.actions['filter_language'] and self.actions['filter_status']:
                object_list = IdentifierQualif.objects.filter( Q( decs_code=self.actions['s'] ) & q_filter_language & q_filter_status ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')


            # tree_number
            if self.actions['filter_fields'] == 'tree_number' and self.actions['s']:
                object_list = IdentifierQualif.objects.filter(
                    qtreenumbers__tree_number=self.actions['s'],
                    ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')

            # tree_number and filter_language
            if self.actions['filter_fields'] == 'tree_number' and self.actions['s'] and self.actions['filter_language']:
                object_list = IdentifierQualif.objects.filter( Q( qtreenumbers__tree_number=self.actions['s'] ) & q_filter_language ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')

            # tree_number and filter_language and filter_status
            if self.actions['filter_fields'] == 'tree_number' and self.actions['s'] and self.actions['filter_language'] and self.actions['filter_status']:
                object_list = IdentifierQualif.objects.filter( Q( qtreenumbers__tree_number=self.actions['s'] ) & q_filter_language & q_filter_status ).values('id','status','abbreviation','qualifier_ui','decs_code','abbreviation','qualifiers__qualifier_name','qualifiers__language_code')


        # when term_string selected -----------------------------------------------------------------------------
        if self.actions['filter_fields'] == 'term_string':
            if self.actions['s'] and not self.actions['s'] == '*':
                object_list = IdentifierQualif.objects.filter( q_term_string ).values('id','status','abbreviation','qualifier_ui','decs_code','termqualif__term_string','termqualif__language_code')
            else:
                object_list = IdentifierQualif.objects.filter( q_term_string ).values('id','status','abbreviation','qualifier_ui','decs_code','termqualif__term_string','termqualif__language_code')

            # filter_language
            if self.actions['filter_language']:
                object_list = IdentifierQualif.objects.filter( Q( q_term_string & q_filter_language )
                    ).values('id','status','abbreviation','qualifier_ui','decs_code','termqualif__term_string','termqualif__language_code')

            # status
            if self.actions['filter_status']:
                object_list = object_list.filter(status=self.actions['filter_status']).values('id','status','abbreviation','qualifier_ui','decs_code','termqualif__term_string','termqualif__language_code')


        # order performance -------------------------------------------------------------------------------------
        if self.actions['order'] == "-":
            object_list = object_list.order_by("%s%s" % (self.actions["order"], self.actions["orderby"]))
        else:
            if self.actions['filter_fields'] == 'term_string':
                object_list = object_list.order_by('termqualif__term_string')
            else:
                object_list = object_list.order_by('qualifiers__qualifier_name')


        if self.actions['visited'] != 'ok':
            object_list = object_list.none()


        return object_list

    def get_context_data(self, **kwargs):
        context = super(QualifListView, self).get_context_data(**kwargs)

        context['actions'] = self.actions

        return context


