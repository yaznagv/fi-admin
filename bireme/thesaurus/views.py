#! coding: utf-8

from django.core.urlresolvers import reverse, reverse_lazy
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect

from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.contenttypes.models import ContentType

from django.views import generic

from utils.views import LoginRequiredView, GenericUpdateWithOneFormset

from django.conf import settings

from models import *
from forms import *

from django.db.models import Prefetch
from django.db.models import Q

from django.utils.translation import ugettext_lazy as _, get_language
from django.core.paginator import Paginator


from django.contrib import messages

import datetime


ITEMS_PER_PAGE = 10

# form actions
ACTIONS = {
    'term_string': '',
    'filter_language': '',
    'descriptor_ui': '',

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

    'form_language': '',

    'choiced_thesaurus': '',

}



# Descriptors ------------------------------------------------------------------------
class DescUpdate(LoginRequiredView):
    """
    Handle creation and update of Descriptors objects
    Create the first form
    """
    model = IdentifierDesc
    success_url = reverse_lazy('create_concept_termdesc')
    
    form_class = IdentifierDescForm
    template_name = "thesaurus/descriptor_form_step1.html"

    def form_valid(self, form):

        formset_descriptor = DescriptionDescFormSet(self.request.POST, instance=self.object)
        formset_treenumber = TreeNumbersListDescFormSet(self.request.POST, instance=self.object)
        formset_pharmaco = PharmacologicalActionListDescFormSet(self.request.POST, instance=self.object)
        formset_related = SeeRelatedListDescFormSet(self.request.POST, instance=self.object)
        formset_previous = PreviousIndexingListDescFormSet(self.request.POST, instance=self.object)
        formset_entrycombination = EntryCombinationListDescFormSet(self.request.POST, instance=self.object)

        # run all validation before for display formset errors at form
        form_valid = form.is_valid()
        formset_descriptor_valid = formset_descriptor.is_valid()
        formset_treenumber_valid = formset_treenumber.is_valid()
        formset_pharmaco_valid = formset_pharmaco.is_valid()
        formset_related_valid = formset_related.is_valid()
        formset_previous_valid = formset_previous.is_valid()
        formset_entrycombination_valid = formset_entrycombination.is_valid()

        if (form_valid and 
            formset_descriptor_valid and 
            formset_treenumber_valid and 
            formset_pharmaco_valid and
            formset_related_valid and
            formset_previous_valid and
            formset_entrycombination_valid
            ):

            # Bring the choiced language_code from the first form
            registry_language = formset_descriptor.cleaned_data[0].get('language_code')

            # self.object = form.save()
            self.object = form.save(commit=False)
            
            # Get sequential number to write to decs_code
            seq = code_controller.objects.get(pk=1)
            nseq = str(int(seq.sequential_number) + 1)
            seq.sequential_number = nseq
            seq.save()

            self.object.decs_code = nseq
            self.object = form.save(commit=True)

            formset_descriptor.instance = self.object
            formset_descriptor.save()

            formset_treenumber.instance = self.object
            formset_treenumber.save()

            formset_pharmaco.instance = self.object
            formset_pharmaco.save()

            formset_related.instance = self.object
            formset_related.save()

            formset_previous.instance = self.object
            formset_previous.save()

            formset_entrycombination.instance = self.object
            formset_entrycombination.save()

            form.save()
            
            return redirect(reverse('create_concept_termdesc') + '?ths=' + self.request.GET.get("ths") + '&' + 'registry_language=' + registry_language)

        else:
            return self.render_to_response(
                        self.get_context_data(
                                            form=form,
                                            formset_descriptor=formset_descriptor,
                                            formset_treenumber=formset_treenumber,
                                            formset_pharmaco=formset_pharmaco,
                                            formset_related=formset_related,
                                            formset_previous=formset_previous,
                                            formset_entrycombination=formset_entrycombination,
                                            )
                                        )

    # Faz com que o forms.py tenha um pre filtro para abbreviation
    def get_form_kwargs(self):
        ths = self.request.GET.get("ths")
        kwargs = super(DescUpdate, self).get_form_kwargs()
        kwargs.update({'ths': ths})
        return kwargs

    def form_invalid(self, form):
        # force use of form_valid method to run all validations
        return self.form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(DescUpdate, self).get_context_data(**kwargs)

        context['language_system'] = get_language()

        if self.request.method == 'GET':

            context['formset_descriptor'] = DescriptionDescFormSet(instance=self.object)
            context['formset_treenumber'] = TreeNumbersListDescFormSet(instance=self.object)
            context['formset_pharmaco'] = PharmacologicalActionListDescFormSet(instance=self.object)
            context['formset_related'] = SeeRelatedListDescFormSet(instance=self.object)
            context['formset_previous'] = PreviousIndexingListDescFormSet(instance=self.object)
            context['formset_entrycombination'] = EntryCombinationListDescFormSet(instance=self.object)

        return context


class DescCreateView(DescUpdate, CreateView):
    """
    Used as class view to create Descriptors

    """
    # def get_success_url(self):
    #     messages.success(self.request, 'is created')
    #     return '/thesaurus/descriptors/edit/%s' % self.object.id


# No use
# class DescUpdateView(DescUpdate, UpdateView):
#     """
#     Used as class view to update Descriptors
#     Extend DescUpdate that do all the work
#     """
#     # def get_success_url(self):
#     #     messages.success(self.request, 'is updated')
#     #     return '/thesaurus/descriptors/edit/%s' % self.object.id


class DescDeleteView(DescUpdate, DeleteView):
    """
    Used as class view to delete Descriptors
    """
    model = IdentifierDesc
    template_name = 'thesaurus/descriptor_confirm_delete.html'

    def get_success_url(self):
        # messages.success(self.request, 'is deleted')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/descriptors/%s' % ths 


class DescRegisterUpdateView(LoginRequiredView, UpdateView):
    """
    Used as class view to update descriptor information
    """
    model = IdentifierDesc
    template_name = 'thesaurus/descriptor_edit_register.html'
    form_class = IdentifierDescForm

    def get_success_url(self):

        id_register = self.object.id
        # Search ID of the first concept of the record to then search first term of the concept
        concepts_of_register = IdentifierConceptListDesc.objects.filter(identifier_id=id_register).values('id')
        id_concept = concepts_of_register[0].get('id')
        # Search ID of the first term of this concept to redirect
        terms_of_concept = TermListDesc.objects.filter(identifier_concept_id=id_concept).values('id')
        id_term = terms_of_concept[0].get('id')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/descriptors/view/%s%s' % ( id_term, ths )

    def form_valid(self, form):
        formset_descriptor = DescriptionDescFormSet(self.request.POST, instance=self.object)
        formset_treenumber = TreeNumbersListDescFormSet(self.request.POST, instance=self.object)
        formset_pharmaco = PharmacologicalActionListDescFormSet(self.request.POST, instance=self.object)
        formset_related = SeeRelatedListDescFormSet(self.request.POST, instance=self.object)
        formset_previous = PreviousIndexingListDescFormSet(self.request.POST, instance=self.object)
        formset_entrycombination = EntryCombinationListDescFormSet(self.request.POST, instance=self.object)

        # run all validation before for display formset errors at form
        form_valid = form.is_valid()
        formset_descriptor_valid = formset_descriptor.is_valid()
        formset_treenumber_valid = formset_treenumber.is_valid()
        formset_pharmaco_valid = formset_pharmaco.is_valid()
        formset_related_valid = formset_related.is_valid()
        formset_previous_valid = formset_previous.is_valid()
        formset_entrycombination_valid = formset_entrycombination.is_valid()

        if (form_valid and 
            formset_descriptor_valid and 
            formset_treenumber_valid and 
            formset_related_valid and
            formset_pharmaco_valid and
            formset_previous_valid and
            formset_entrycombination_valid
            ):

            # Bring the choiced language_code from the first form
            registry_language = formset_descriptor.cleaned_data[0].get('language_code')

            self.object = form.save()

            formset_descriptor.instance = self.object
            formset_descriptor.save()

            formset_treenumber.instance = self.object
            formset_treenumber.save()

            formset_pharmaco.instance = self.object
            formset_pharmaco.save()

            formset_related.instance = self.object
            formset_related.save()

            formset_previous.instance = self.object
            formset_previous.save()

            formset_entrycombination.instance = self.object
            formset_entrycombination.save()

            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                        self.get_context_data(
                                            form=form,
                                            formset_descriptor=formset_descriptor,
                                            formset_treenumber=formset_treenumber,
                                            formset_pharmaco=formset_pharmaco,
                                            formset_related=formset_related,
                                            formset_previous=formset_previous,
                                            formset_entrycombination=formset_entrycombination,
                                            )
                                        )

    # Makes forms.py have a pre-filter for abbreviation
    def get_form_kwargs(self):
        ths = self.request.GET.get("ths")
        kwargs = super(DescRegisterUpdateView, self).get_form_kwargs()
        kwargs.update({'ths': ths})
        return kwargs

    def form_invalid(self, form):
        # force use of form_valid method to run all validations
        return self.form_valid(form)

    def get_context_data(self, **kwargs):

        context = super(DescRegisterUpdateView, self).get_context_data(**kwargs)

        context['language_system'] = get_language()

        if self.request.method == 'GET':

            context['formset_descriptor'] = DescriptionDescFormSet(instance=self.object)
            context['formset_treenumber'] = TreeNumbersListDescFormSet(instance=self.object)
            context['formset_pharmaco'] = PharmacologicalActionListDescFormSet(instance=self.object)
            context['formset_related'] = SeeRelatedListDescFormSet(instance=self.object)
            context['formset_previous'] = PreviousIndexingListDescFormSet(instance=self.object)
            context['formset_entrycombination'] = EntryCombinationListDescFormSet(instance=self.object)

        return context



class DescListView(LoginRequiredView, ListView):
    """
    List descriptor records
    """
    template_name = "thesaurus/thesaurus_home.html"
    context_object_name = "registers"
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self):
        lang_code = get_language()
        object_list = []
        registers_indexed = []
        concepts_indexed = []

        # getting action parameter
        self.actions = {}
        for key in ACTIONS.keys():
            self.actions[key] = self.request.GET.get(key, ACTIONS[key])

        # icontains X exact -------------------------------------------------------------------------------------
        if self.actions['exact']:
            q_term_string = Q(term_string=self.actions['s'])
        else:
            q_term_string = Q(term_string__icontains=self.actions['s'])

        # term_string
        if self.actions['filter_fields'] == 'term_string' and self.actions['exact']:
            q_term_string = Q(term_string=self.actions['s'])
        else:
            if self.actions['filter_fields'] == 'term_string' and not self.actions['exact']:
                q_term_string = Q(term_string__icontains=self.actions['s'])

        # concept_preferred_term='Y'
        q_concept_preferred_term = Q(concept_preferred_term='Y')

        # record_preferred_term='Y'
        q_record_preferred_term = Q(record_preferred_term='Y')

        # status
        if self.actions['filter_status']:
            q_filter_status = Q(status=self.actions['filter_status'])


        # Term
        # AND performance for Term ------------------------------------------------------------------------
        # Do the initial search in term_string field
        if self.actions['s'] and not self.actions['filter_fields']:
            object_list = TermListDesc.objects.filter( q_term_string ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')
        else:
            # bring all registers
            object_list = TermListDesc.objects.all().filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # term_string
        if self.actions['filter_fields'] == 'term_string' and self.actions['s']:
            object_list = TermListDesc.objects.filter( q_term_string ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])


        # Concept
        # AND performance for Concept ------------------------------------------------------------------------
        # when concept_preferred_term='Y' & record_preferred_term='Y'
        if self.actions['filter_fields'] == 'concept':
            object_list = TermListDesc.objects.filter( q_term_string & q_concept_preferred_term & q_record_preferred_term ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])


        # MESH Descriptor UI
        # AND performance for MESH Descriptor UI --------------------------------------------------------------
        if self.actions['filter_fields'] == 'descriptor_ui':
            id_register = IdentifierDesc.objects.filter(descriptor_ui=self.actions['s']).values('id')
            id_concept = IdentifierConceptListDesc.objects.filter(identifier_id=id_register,preferred_concept='Y').distinct().values('id')
            q_id_concept = Q(identifier_concept_id__in=id_concept)
            object_list = TermListDesc.objects.filter( q_concept_preferred_term & q_record_preferred_term & q_id_concept ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])



        # DeCS Descriptor UI
        # AND performance for DeCS Descriptor UI --------------------------------------------------------------
        if self.actions['filter_fields'] == 'decs_code':
            id_register = IdentifierDesc.objects.filter(decs_code=self.actions['s']).values('id')
            id_concept = IdentifierConceptListDesc.objects.filter(identifier_id=id_register,preferred_concept='Y').distinct().values('id')
            q_id_concept = Q(identifier_concept_id__in=id_concept)
            object_list = TermListDesc.objects.filter( q_concept_preferred_term & q_record_preferred_term & q_id_concept ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])


        # Tree Number
        # AND performance for Tree Number --------------------------------------------------------------
        if self.actions['filter_fields'] == 'tree_number':
            id_tree_number = TreeNumbersListDesc.objects.filter(tree_number=self.actions['s']).values('identifier_id')
            id_concept = IdentifierConceptListDesc.objects.filter(identifier_id__in=id_tree_number,preferred_concept='Y').distinct().values('id')
            q_id_concept = Q(identifier_concept_id__in=id_concept)
            object_list = TermListDesc.objects.filter( q_concept_preferred_term & q_record_preferred_term & q_id_concept ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])


        # order performance -------------------------------------------------------------------------------------
        if self.actions['order'] == "-":
            object_list = object_list.order_by("%s%s" % (self.actions["order"], self.actions["orderby"]))

        # if self.actions['visited'] != 'ok':
        # if not self.actions['visited']:
        #     object_list = object_list.none()

        return object_list


    def get_context_data(self, **kwargs):
        context = super(DescListView, self).get_context_data(**kwargs)
        context['actions'] = self.actions

        return context







# FORM 2
# Creates concept and term
class ConceptTermUpdate(LoginRequiredView):

    """
    Used as class view to create ConceptTermUpdate
    Extend ConceptTermUpdate that do all the work
    Create the second form
    """
    model = IdentifierConceptListDesc
    form_class = IdentifierConceptListDescForm
    template_name = 'thesaurus/descriptor_form_step2.html'

    def form_valid(self, form):

        formset_concept = ConceptListDescFormSet(self.request.POST, instance=self.object)
        formset_term = TermListDescFormSet(self.request.POST, instance=self.object)

        form_valid = form.is_valid()
        formset_concept_valid = formset_concept.is_valid()
        formset_term_valid = formset_term.is_valid()

        if (form_valid and formset_concept_valid and formset_term_valid):

            self.object = form.save()

            formset_concept.instance = self.object
            formset_concept.save()

            formset_term.instance = self.object
            formset_term.save()

            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(
                                            form=form,
                                            formset_concept=formset_concept,
                                            formset_term=formset_term,
                                            )
                        )

    def get_context_data(self, **kwargs):
        context = super(ConceptTermUpdate, self).get_context_data(**kwargs)

        context['language_system'] = get_language()

        if IdentifierDesc.objects.count() > 0:
            context['next_id'] = int(IdentifierDesc.objects.latest('id').id)
        else:
            context['next_id'] = 1


        if self.request.method == 'GET':

            context['formset_concept'] = ConceptListDescFormSet(instance=self.object)
            context['formset_term'] = TermListDescFormSet(instance=self.object)

        return context



class DescCreateView2(ConceptTermUpdate, CreateView):
    """
    Used as class view to create Descriptors
    """
    def get_success_url(self):
        # messages.success(self.request, 'is created')

        id_concept = self.object.id
        # Pesquisa ID do primeiro termo deste conceito para redirecionar
        terms_of_concept = TermListDesc.objects.filter(identifier_concept_id=id_concept).values('id')
        id_term = terms_of_concept[0].get('id')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/descriptors/view/%s%s' % ( id_term, ths )


# Pesquisa conceito para poder trazer ID do registro para novo conceito
# Não está sendo utilizado por enquanto
class ConceptListDescView(LoginRequiredView, ListView):
    """
    List descriptor records (used by relationship popup selection window)
    """
    template_name = "thesaurus/search_concept_desc.html"
    context_object_name = "registers"
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self):
        lang_code = get_language()
        object_list = []

        # getting action parameter
        self.actions = {}
        for key in ACTIONS.keys():
            self.actions[key] = self.request.GET.get(key, ACTIONS[key])

        # q_term_string = Q(term_string__icontains=self.actions['s'])
        q_term_string = Q(termdesc__term_string__icontains=self.actions['s'])
        q_preferred_concept = Q(preferred_concept='Y')

        object_list = IdentifierConceptListDesc.objects.filter( q_preferred_concept & q_term_string ).values('identifier_id','termdesc__term_string','termdesc__language_code')

        # order performance -------------------------------------------------------------------------------------
        if self.actions['order'] == "-":
            object_list = object_list.order_by("%s%s" % (self.actions["order"], self.actions["orderby"]))

        if self.actions['visited'] != 'ok':
            object_list = object_list.none()

        return object_list

    def get_context_data(self, **kwargs):
        context = super(ConceptListDescView, self).get_context_data(**kwargs)

        context['actions'] = self.actions

        return context




class ConceptListDescCreateView(LoginRequiredView, CreateView):
    """
    Used as class view to create Concept and Term
    """
    model = IdentifierConceptListDesc
    template_name = 'thesaurus/descriptor_new_concept.html'
    form_class = IdentifierConceptListDescForm

    def get_success_url(self):

        id_concept = self.object.id

        # Search ID of the first term of this concept to redirect
        terms_of_concept = TermListDesc.objects.filter(identifier_concept_id=id_concept).values('id')
        id_term = terms_of_concept[0].get('id')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/descriptors/view/%s%s' % ( id_term, ths )

    def form_valid(self, form):

        formset_concept = ConceptListDescFormSet(self.request.POST, instance=self.object)
        formset_term = TermListDescFormSet(self.request.POST, instance=self.object)

        form_valid = form.is_valid()
        formset_concept_valid = formset_concept.is_valid()
        formset_term_valid = formset_term.is_valid()

        if (form_valid and formset_concept_valid and formset_term_valid):

            self.object = form.save(commit=False)
            self.object.identifier_id = int(self.request.POST.get("identifier_id"))
            self.object = form.save(commit=True)

            formset_concept.instance = self.object
            formset_concept.save()

            formset_term.instance = self.object
            formset_term.save()

            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(
                                            form=form,
                                            formset_concept=formset_concept,
                                            formset_term=formset_term,
                                            )
                        )

    def get_context_data(self, **kwargs):
        context = super(ConceptListDescCreateView, self).get_context_data(**kwargs)

        if self.request.method == 'GET':

            context['formset_concept'] = ConceptListDescFormSet(instance=self.object)
            context['formset_term'] = TermListDescFormSet(instance=self.object)

        return context



class ConceptListDescUpdateView(LoginRequiredView, UpdateView):
    """
    Used as class view to update concept
    """
    model = IdentifierConceptListDesc
    template_name = 'thesaurus/descriptor_edit_concept.html'
    form_class = IdentifierConceptListDescForm

    def get_success_url(self):
        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/descriptors/view/%s%s' % ( int(self.request.POST.get("termdesc__id")), ths )

    def form_valid(self, form):

        formset_concept = ConceptListDescFormSet(self.request.POST, instance=self.object)

        form_valid = form.is_valid()
        formset_concept_valid = formset_concept.is_valid()

        if (form_valid and formset_concept_valid):

            self.object = form.save(commit=False)
            self.object.identifier_id = int(self.request.POST.get("identifier_id"))

            formset_concept.instance = self.object
            formset_concept.save()

            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(
                                            form=form,
                                            formset_concept=formset_concept,
                                            )
                        )

    def get_context_data(self, **kwargs):
        context = super(ConceptListDescUpdateView, self).get_context_data(**kwargs)

        if self.request.method == 'GET':
            context['formset_concept'] = ConceptListDescFormSet(instance=self.object)
        return context




class TermListDescCreateView(LoginRequiredView, CreateView):
    """
    Used as class view to create TermListDesc
    """
    # model = TermListDesc
    template_name = 'thesaurus/descriptor_new_term.html'
    form_class = TermListDescUniqueForm


    def get_context_data(self, **kwargs):
        data = super(TermListDescCreateView, self).get_context_data(**kwargs)
        if self.request.POST:
            data['formset_toccurrence'] = TheraurusOccurrenceListDescFormSet(self.request.POST)
        else:
            data['formset_toccurrence'] = TheraurusOccurrenceListDescFormSet()
        return data

    def form_valid(self, form):
        
        formset_toccurrence = TheraurusOccurrenceListDescFormSet(self.request.POST, instance=self.object)

        form_valid = form.is_valid()
        formset_toccurrence_valid = formset_toccurrence.is_valid()

        if (form_valid and formset_toccurrence_valid):

            identifier_concept_id = self.request.POST.get("identifier_concept_id")
            term_string = self.request.POST.get("term_string")
            language_code = self.request.POST.get("language_code")
            status = self.request.POST.get("status")

            has_term = TermListDesc.objects.filter(
                identifier_concept_id=identifier_concept_id,
                term_string__iexact=term_string,
                language_code=language_code,
                status=status,
                ).exists()

            if not has_term:
                self.object = form.save(commit=False)

                # prove the current date if you are not informed on the form
                if not self.object.date_created:
                    self.object.date_created = datetime.datetime.now().strftime('%Y-%m-%d')

                self.object.identifier_concept_id = self.request.POST.get("identifier_concept_id")
                self.object = form.save(commit=True)

                formset_toccurrence.instance = self.object
                formset_toccurrence.save()

                form.save()
                return HttpResponseRedirect(self.get_success_url())
            else:
                msg_erro =  _("This Term already exist!")
                return self.render_to_response(self.get_context_data(
                                                                    form=form,
                                                                    formset_toccurrence=formset_toccurrence,
                                                                    msg_erro=msg_erro,
                                                                    ))

    def get_success_url(self):
        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/descriptors/view/%s%s' % ( self.object.id, ths )




class TermListDescUpdateView(LoginRequiredView, UpdateView):
    """
    Used as class view to update Term
    """
    model = TermListDesc
    template_name = 'thesaurus/descriptor_edit_term.html'
    form_class = TermListDescUniqueForm

    def get_context_data(self, **kwargs):
        data = super(TermListDescUpdateView, self).get_context_data(**kwargs)
        if self.request.POST:
            data['formset_toccurrence'] = TheraurusOccurrenceListDescFormSet(self.request.POST)
        else:
            data['formset_toccurrence'] = TheraurusOccurrenceListDescFormSet(instance=self.object)
        return data

    def form_valid(self, form):

        formset_toccurrence = TheraurusOccurrenceListDescFormSet(self.request.POST, instance=self.object)

        form_valid = form.is_valid()
        formset_toccurrence_valid = formset_toccurrence.is_valid()

        if (form_valid and formset_toccurrence_valid):
            self.object = form.save(commit=False)

            # prove the current date if you are not informed on the form
            if not self.object.date_created:
                self.object.date_created = datetime.datetime.now().strftime('%Y-%m-%d')

            self.object.identifier_concept_id = self.request.POST.get("identifier_concept_id")
            self.object.date_altered = datetime.datetime.now().strftime('%Y-%m-%d')

            self.object = form.save(commit=True)

            formset_toccurrence.instance = self.object
            formset_toccurrence.save()

            form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(
                                                                form=form,
                                                                formset_toccurrence=formset_toccurrence,
                                                                ))
    def get_success_url(self):
        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/descriptors/view/%s%s' % ( self.object.id, ths )



    # def get_context_data(self, **kwargs):
    #     context = super(TermListDescUpdateView, self).get_context_data(**kwargs)
    #     return context

    #     if self.request.method == 'GET':
    #         context['formset_toccurrence'] = TheraurusOccurrenceListDescFormSet(instance=self.object)
    #     return context



class legacyInformationDescCreateView(LoginRequiredView, CreateView):
    """
    Used as class view to create legacy information
    """
    model = legacyInformationDesc
    template_name = 'thesaurus/descriptor_new_legacy.html'
    form_class = legacyInformationDescForm

    def get_success_url(self):

        id_identifier = self.request.GET.get("identifier_id")

        # Search ID of the first concept of this record
        concepts_of_registry = IdentifierConceptListDesc.objects.filter(identifier_id=id_identifier).values('id')
        id_concept = concepts_of_registry[0].get('id')

        # Search ID of the first term of this concept to redirect
        terms_of_concept = TermListDesc.objects.filter(identifier_concept_id=id_concept).values('id')
        id_term = terms_of_concept[0].get('id')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/descriptors/view/%s%s' % ( id_term, ths )

    def form_valid(self, form):

        if form.is_valid():

            self.object = form.save(commit=False)
            self.object.identifier_id = self.request.POST.get("identifier_id")
            self.object = form.save()
            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(legacyInformationDescCreateView, self).get_context_data(**kwargs)
        return context



class legacyInformationDescUpdateView(LoginRequiredView, UpdateView):
    """
    Used as class view to update a legacy information
    """
    model = legacyInformationDesc
    template_name = 'thesaurus/descriptor_edit_legacy.html'
    form_class = legacyInformationDescForm


    def get_success_url(self):

        id_identifier = self.request.GET.get("identifier_id")

        # Search ID of the first concept of this record
        concepts_of_registry = IdentifierConceptListDesc.objects.filter(identifier_id=id_identifier).values('id')
        id_concept = concepts_of_registry[0].get('id')

        # Search ID of the first term of this concept to redirect
        terms_of_concept = TermListDesc.objects.filter(identifier_concept_id=id_concept).values('id')
        id_term = terms_of_concept[0].get('id')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/descriptors/view/%s%s' % ( id_term, ths )

    def form_valid(self, form):

        if form.is_valid():

            self.object = form.save()
            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(legacyInformationDescUpdateView, self).get_context_data(**kwargs)
        return context




class PageViewDesc(LoginRequiredView, DetailView):
    """
    Used as class DetailView to list the result
    """
    model = TermListDesc
    template_name = 'thesaurus/page_view_desc.html'

    def get_context_data(self, **kwargs):
        lang_code = get_language()

        context = super(PageViewDesc, self).get_context_data(**kwargs)

        if self.object:

            # IdentifierConceptListDesc - recover pk from concept
            id_concept = IdentifierConceptListDesc.objects.filter(
                                            id=self.object.identifier_concept_id,
                                            ).values('identifier_id').distinct()

            # Usado para criar novo conceito
            for concept in id_concept:
                context['id_concept_new'] = concept


            # IdentifierConceptListDesc - retrieves pk's that has even identifier_id - can bring more than 1
            ids = IdentifierConceptListDesc.objects.filter(
                                            identifier_id=id_concept,
                                            ).values('id')

            # IdentifierDesc
            # Brings information to Active Descriptor Record
            context['identifierdesc_objects'] = IdentifierDesc.objects.filter(
                                            id=id_concept,
                                            )

            # IdentifierDesc
            context['id_register_objects'] = IdentifierDesc.objects.filter(
                                            id=id_concept,
                                            ).values(

                                                # IdentifierDesc
                                                'id',
                                                'thesaurus',
                                                'descriptor_class',
                                                'descriptor_ui',
                                                'decs_code',
                                                'external_code',
                                                'nlm_class_number',
                                                'date_created',
                                                'date_revised',
                                                'date_established',
                                                'abbreviation',
                                            )

            context['description_objects'] = IdentifierDesc.objects.filter(
                                            id=id_concept,
                                            ).values(
                                                # DescriptionDesc
                                                'descriptiondesc__identifier_id',
                                                'descriptiondesc__language_code',
                                                'descriptiondesc__annotation',
                                                'descriptiondesc__history_note',
                                                'descriptiondesc__online_note',
                                                'descriptiondesc__public_mesh_note',
                                                'descriptiondesc__consider_also',
                                            )

            # Usado para criar lista de Indexacao Previa
            context['previous_objects'] = IdentifierDesc.objects.filter(
                                            id=id_concept,
                                            ).values(
                                                # PreviousIndexingListDesc
                                                'previousdesc__identifier_id',
                                                'previousdesc__previous_indexing',
                                                'previousdesc__language_code',
                                            ).distinct().order_by('previousdesc__previous_indexing')

            # Usado para criar lista de Acao farmacologica
            context['pharmaco_objects'] = IdentifierDesc.objects.filter(
                                            id=id_concept,
                                            ).values(
                                                # PharmacologicalActionList
                                                'pharmacodesc__identifier_id',
                                                'pharmacodesc__term_string',
                                                'pharmacodesc__descriptor_ui',
                                                'pharmacodesc__language_code',
                                            ).distinct().order_by('pharmacodesc__term_string')

            # Usado para criar lista de tree number
            context['tree_numbers_objects'] = IdentifierDesc.objects.filter(
                                            id=id_concept,
                                            ).values(
                                                # TreeNumbersListDesc
                                                'dtreenumbers__identifier_id',
                                                'dtreenumbers__tree_number',
                                            ).distinct().order_by('dtreenumbers__tree_number')

            # Usado para criar lista de See Also - related
            context['related_objects'] = IdentifierDesc.objects.filter(
                                            id=id_concept,
                                            ).values(
                                                # TreeNumbersListDesc
                                                'relateddesc__term_string',
                                                'relateddesc__descriptor_ui',
                                            ).distinct().order_by('relateddesc__term_string')

            context['term_string_info_preferred_objects'] = IdentifierConceptListDesc.objects.filter(
                                            identifier=id_concept,termdesc__concept_preferred_term='Y',termdesc__record_preferred_term='Y',
                                            ).order_by('identifier_id',
                                                        'termdesc__identifier_concept_id',
                                                        '-preferred_concept',
                                                        '-termdesc__concept_preferred_term',
                                                        'termdesc__language_code',
                                                        'termdesc__term_string',
                                            ).values(
                                                    'id',
                                                    'termdesc__term_string',
                                                    'termdesc__language_code',
                                                    'identifier_id',
                                            )

            context['entry_terms_objects'] = IdentifierConceptListDesc.objects.filter(
                                            identifier=id_concept,termdesc__record_preferred_term='N',
                                            ).order_by('identifier_id',
                                                        'termdesc__language_code',
                                                        'termdesc__term_string',
                                            ).values(
                                                    'id',
                                                    'termdesc__id',
                                                    'termdesc__term_string',
                                                    'termdesc__language_code',
                                            )

            context['scope_note_objects'] = IdentifierConceptListDesc.objects.filter(
                                            identifier=id_concept,preferred_concept='Y',
                                            ).order_by('identifier_id',
                                            ).values(
                                                    'conceptdesc__language_code',
                                                    'conceptdesc__scope_note',
                                            ).distinct()

            context['legacy_objects'] = legacyInformationDesc.objects.filter(
                                            identifier=id_concept,
                                            ).values(
                                                'id',
                                                'pre_codificado',
                                                'desastre',
                                                'reforma_saude',
                                                'geografico',
                                                'mesh',
                                                'pt_lilacs',
                                                'nao_indexavel',
                                                'homeopatia',
                                                'repidisca',
                                                'saude_publica',
                                                'exploded',
                                                'geog_decs',
                                                'identifier_id',
                                            )

            context['entrycombination_objects'] = EntryCombinationListDesc.objects.filter(
                                            identifier=id_concept,
                                            ).values(
                                                'id',
                                                'ecin_qualif',
                                                'ecin_id',
                                                'ecout_desc',
                                                'ecout_desc_id',
                                                'ecout_qualif',
                                                'ecout_qualif_id',
                                                'identifier_id',
                                            )


            # Usado para mostrar informações de conceitos e termos
            context['identifierconceptlist_objects'] = IdentifierConceptListDesc.objects.filter(
                                            identifier=id_concept,
                                            ).order_by('identifier_id',
                                                        'termdesc__identifier_concept_id',
                                                        '-preferred_concept',
                                                        '-termdesc__concept_preferred_term',
                                                        'termdesc__language_code',
                                                        'termdesc__term_string',
                                            ).values(
                                                    'id',
                                                    'identifier_id',
                                                    'concept_ui',
                                                    'concept_relation_name',
                                                    'preferred_concept',
                                                    'casn1_name',
                                                    'registry_number',

                                                    'conceptdesc__identifier_concept_id',
                                                    'conceptdesc__language_code',
                                                    'conceptdesc__scope_note',

                                                    'termdesc__id',
                                                    'termdesc__identifier_concept_id',
                                                    'termdesc__status',
                                                    'termdesc__term_ui',
                                                    'termdesc__language_code',
                                                    'termdesc__term_string',
                                                    'termdesc__concept_preferred_term',
                                                    'termdesc__is_permuted_term',
                                                    'termdesc__lexical_tag',
                                                    'termdesc__record_preferred_term',
                                                    'termdesc__entry_version',
                                                    'termdesc__date_created',
                                                    'termdesc__date_altered',
                                                    'termdesc__historical_annotation',
                                            ).distinct()

            # Traz abbreviation e term_string do idioma da interface no momento
            id_abbrev = IdentifierDesc.objects.filter(id=id_concept).values('abbreviation')
            translation = IdentifierQualif.objects.filter(id__in=id_abbrev).order_by('abbreviation') # Usado __in pois pode haver mais que um resultado
            
            context['allowable_qualifiers_objects'] = translation

            # Informacoes para log
            # Registro
            # ID do model
            id_ctype_identifierdesc = ContentType.objects.filter(model='identifierdesc').values('id')
            context['id_ctype_identifierdesc'] = id_ctype_identifierdesc[0].get('id')
            # ID do registro
            id_identifierdesc = IdentifierDesc.objects.filter(id=id_concept).values('id')
            context['id_identifierdesc'] = id_identifierdesc[0].get('id')

            # # Concept e Term
            # id_ctype_identifierdesc = ContentType.objects.filter(model='identifierdesc').values('id')
            # context['id_ctype_identifierdesc'] = id_ctype_identifierdesc[0].get('id')
            # # ID do registro
            # id_identifierdesc = IdentifierDesc.objects.filter(id=id_concept).values('id')
            # context['id_identifierdesc'] = id_identifierdesc[0].get('id')

            return context




# Qualifiers -------------------------------------------------------------------------
class QualifUpdate(LoginRequiredView):
    """
    Handle creation and update of Qualifiers objects
    """
    model = IdentifierQualif
    # success_url = reverse_lazy('list_descriptor')
    success_url = reverse_lazy('create_concept_termqualif')

    
    form_class = IdentifierQualifForm
    template_name = "thesaurus/qualifier_form_step1.html"

    def form_valid(self, form):

        formset_descriptor = DescriptionQualifFormSet(self.request.POST, instance=self.object)
        formset_treenumber = TreeNumbersListQualifFormSet(self.request.POST, instance=self.object)

        # run all validation before for display formset errors at form
        form_valid = form.is_valid()
        formset_descriptor_valid = formset_descriptor.is_valid()
        formset_treenumber_valid = formset_treenumber.is_valid()

        if (form_valid and 
            formset_descriptor_valid and 
            formset_treenumber_valid
            ):

            # Bring the choiced language_code from the first form
            registry_language = formset_descriptor.cleaned_data[0].get('language_code')

            # self.object = form.save()
            self.object = form.save(commit=False)
            
            # Pega info de sequencial para salvar em decs_code
            seq = code_controller.objects.get(pk=1)
            nseq = str(int(seq.sequential_number) + 1)
            seq.sequential_number = nseq
            seq.save()


            self.object.decs_code = nseq
            self.object = form.save(commit=True)

            formset_descriptor.instance = self.object
            formset_descriptor.save()

            formset_treenumber.instance = self.object
            formset_treenumber.save()

            form.save()
            # form.save_m2m()

            return redirect(reverse('create_concept_termqualif') + '?ths=' + self.request.GET.get("ths") + '&' + 'registry_language=' + registry_language)

        else:
            return self.render_to_response(
                        self.get_context_data(
                                            form=form,
                                            formset_descriptor=formset_descriptor,
                                            formset_treenumber=formset_treenumber,
                                            )
                                        )

    def form_invalid(self, form):
        # force use of form_valid method to run all validations
        return self.form_valid(form)


    def get_context_data(self, **kwargs):
        context = super(QualifUpdate, self).get_context_data(**kwargs)

        context['language_system'] = get_language()

        if self.request.method == 'GET':

            context['formset_descriptor'] = DescriptionQualifFormSet(instance=self.object)
            context['formset_treenumber'] = TreeNumbersListQualifFormSet(instance=self.object)
      
        return context


class QualifCreateView(QualifUpdate, CreateView):
    """
    Used as class view to create Qualifiers
    """


class QualifDeleteView(QualifUpdate, DeleteView):
    """
    Used as class view to delete Qualifier
    """
    model = IdentifierQualif
    template_name = 'thesaurus/qualifier_confirm_delete.html'

    def get_success_url(self):
        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/qualifiers/%s' % ths 



class QualifRegisterUpdateView(LoginRequiredView, UpdateView):
    """
    Used as class view to update a register of qualifier
    """
    model = IdentifierQualif
    template_name = 'thesaurus/qualifier_edit_register.html'
    form_class = IdentifierQualifForm

    def get_success_url(self):

        id_register = self.object.id

        # Search ID of the first concept of the record to later search the first term of the concept
        concepts_of_register = IdentifierConceptListQualif.objects.filter(identifier_id=id_register).values('id')
        id_concept = concepts_of_register[0].get('id')

        # Search ID of the first term of this concept to redirect
        terms_of_concept = TermListQualif.objects.filter(identifier_concept_id=id_concept).values('id')
        id_term = terms_of_concept[0].get('id')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/qualifiers/view/%s%s' % ( id_term, ths )


    def form_valid(self, form):

        formset_descriptor = DescriptionQualifFormSet(self.request.POST, instance=self.object)
        formset_treenumber = TreeNumbersListQualifFormSet(self.request.POST, instance=self.object)

        # run all validation before for display formset errors at form
        form_valid = form.is_valid()
        formset_descriptor_valid = formset_descriptor.is_valid()
        formset_treenumber_valid = formset_treenumber.is_valid()

        if (form_valid and 
            formset_descriptor_valid and 
            formset_treenumber_valid
            ):

            # Bring the choiced language_code from the first form
            registry_language = formset_descriptor.cleaned_data[0].get('language_code')

            self.object = form.save()

            formset_descriptor.instance = self.object
            formset_descriptor.save()

            formset_treenumber.instance = self.object
            formset_treenumber.save()

            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(
                        self.get_context_data(
                                            form=form,
                                            formset_descriptor=formset_descriptor,
                                            formset_treenumber=formset_treenumber,
                                            )
                                        )

    def form_invalid(self, form):
        # force use of form_valid method to run all validations
        return self.form_valid(form)


    def get_context_data(self, **kwargs):
        context = super(QualifRegisterUpdateView, self).get_context_data(**kwargs)

        context['language_system'] = get_language()

        if self.request.method == 'GET':

            context['formset_descriptor'] = DescriptionQualifFormSet(instance=self.object)
            context['formset_treenumber'] = TreeNumbersListQualifFormSet(instance=self.object)
      
        return context



class QualifListView(LoginRequiredView, ListView):
    """
    List qualifier records
    """
    template_name = "thesaurus/qualifier_list.html"
    context_object_name = "registers"
    paginate_by = ITEMS_PER_PAGE

    def get_queryset(self):
        lang_code = get_language()
        object_list = []
        registers_indexed = []
        concepts_indexed = []

        # getting action parameter
        self.actions = {}
        for key in ACTIONS.keys():
            self.actions[key] = self.request.GET.get(key, ACTIONS[key])

        # icontains X exact -------------------------------------------------------------------------------------
        if self.actions['exact']:
            q_term_string = Q(term_string=self.actions['s'])
        else:
            q_term_string = Q(term_string__icontains=self.actions['s'])

        # term_string
        if self.actions['filter_fields'] == 'term_string' and self.actions['exact']:
            q_term_string = Q(term_string=self.actions['s'])
        else:
            if self.actions['filter_fields'] == 'term_string' and not self.actions['exact']:
                q_term_string = Q(term_string__icontains=self.actions['s'])

        # concept_preferred_term='Y'
        q_concept_preferred_term = Q(concept_preferred_term='Y')

        # record_preferred_term='Y'
        q_record_preferred_term = Q(record_preferred_term='Y')

        # status
        if self.actions['filter_status']:
            q_filter_status = Q(status=self.actions['filter_status'])


        # Term
        # AND performance for Term ------------------------------------------------------------------------
        # Do the initial search in term_string field
        if self.actions['s'] and not self.actions['filter_fields']:
            object_list = TermListQualif.objects.filter( q_term_string ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')
        else:
            # bring all registers
            object_list = TermListQualif.objects.all().filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # term_string
        if self.actions['filter_fields'] == 'term_string' and self.actions['s']:
            object_list = TermListQualif.objects.filter( q_term_string ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])


        # Concept
        # AND performance for Concept ------------------------------------------------------------------------
        # when concept_preferred_term='Y' & record_preferred_term='Y'
        if self.actions['filter_fields'] == 'concept':
            object_list = TermListQualif.objects.filter( q_term_string & q_concept_preferred_term & q_record_preferred_term ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])


        # Abbreviation
        # AND performance for Abbreviation --------------------------------------------------------------
        if self.actions['filter_fields'] == 'abbreviation':
            id_register = IdentifierQualif.objects.filter(abbreviation=self.actions['s']).values('id')
            id_concept = IdentifierConceptListQualif.objects.filter(identifier_id=id_register,preferred_concept='Y').distinct().values('id')
            q_id_concept = Q(identifier_concept_id__in=id_concept)
            object_list = TermListQualif.objects.filter( q_concept_preferred_term & q_record_preferred_term & q_id_concept ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])



        # MESH Qualifier UI
        # AND performance for MESH Qualifier UI --------------------------------------------------------------
        if self.actions['filter_fields'] == 'qualifier_ui':
            id_register = IdentifierQualif.objects.filter(qualifier_ui=self.actions['s']).values('id')
            id_concept = IdentifierConceptListQualif.objects.filter(identifier_id=id_register,preferred_concept='Y').distinct().values('id')
            q_id_concept = Q(identifier_concept_id__in=id_concept)
            object_list = TermListQualif.objects.filter( q_concept_preferred_term & q_record_preferred_term & q_id_concept ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])



        # DeCS Qualifier UI
        # AND performance for DeCS Qualifier UI --------------------------------------------------------------
        if self.actions['filter_fields'] == 'decs_code':
            id_register = IdentifierQualif.objects.filter(decs_code=self.actions['s']).values('id')
            id_concept = IdentifierConceptListQualif.objects.filter(identifier_id=id_register,preferred_concept='Y').distinct().values('id')
            q_id_concept = Q(identifier_concept_id__in=id_concept)
            object_list = TermListQualif.objects.filter( q_concept_preferred_term & q_record_preferred_term & q_id_concept ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])


        # Tree Number
        # AND performance for Tree Number --------------------------------------------------------------
        if self.actions['filter_fields'] == 'tree_number':
            id_tree_number = TreeNumbersListQualif.objects.filter(tree_number=self.actions['s']).values('identifier_id')
            id_concept = IdentifierConceptListQualif.objects.filter(identifier_id__in=id_tree_number,preferred_concept='Y').distinct().values('id')
            q_id_concept = Q(identifier_concept_id__in=id_concept)
            object_list = TermListQualif.objects.filter( q_concept_preferred_term & q_record_preferred_term & q_id_concept ).filter(term_thesaurus=self.actions['choiced_thesaurus']).order_by('term_string')

        # status
        if self.actions['filter_status']:
            object_list = object_list.filter(status=self.actions['filter_status'])

        # language
        if self.actions['filter_language']:
            object_list = object_list.filter(language_code=self.actions['filter_language'])


        # order performance -------------------------------------------------------------------------------------
        if self.actions['order'] == "-":
            object_list = object_list.order_by("%s%s" % (self.actions["order"], self.actions["orderby"]))

        # if self.actions['visited'] != 'ok':
        #     object_list = object_list.none()

        return object_list



    def get_context_data(self, **kwargs):
        context = super(QualifListView, self).get_context_data(**kwargs)

        context['actions'] = self.actions

        return context







# FORM 2
# Cria conceito e termo
class QualifConceptTermUpdate(LoginRequiredView):
    """
    Used as class view to create ConceptTermUpdate
    """
    model = IdentifierConceptListQualif
    form_class = IdentifierConceptListQualifForm
    template_name = 'thesaurus/qualifier_form_step2.html'

    def form_valid(self, form):

        formset_concept = ConceptListQualifFormSet(self.request.POST, instance=self.object)
        formset_term = TermListQualifFormSet(self.request.POST, instance=self.object)

        form_valid = form.is_valid()
        formset_concept_valid = formset_concept.is_valid()
        formset_term_valid = formset_term.is_valid()

        if (form_valid and formset_concept_valid and formset_term_valid):

            self.object = form.save()

            formset_concept.instance = self.object
            formset_concept.save()

            formset_term.instance = self.object
            formset_term.save()

            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(
                                            form=form,
                                            formset_concept=formset_concept,
                                            formset_term=formset_term,
                                            )
                        )


    def get_context_data(self, **kwargs):
        context = super(QualifConceptTermUpdate, self).get_context_data(**kwargs)

        context['language_system'] = get_language()

        if IdentifierQualif.objects.count() > 0:
            context['next_id'] = int(IdentifierQualif.objects.latest('id').id)
        else:
            context['next_id'] = 1


        if self.request.method == 'GET':

            context['formset_concept'] = ConceptListQualifFormSet(instance=self.object)
            context['formset_term'] = TermListQualifFormSet(instance=self.object)

        return context



class QualifCreateView2(QualifConceptTermUpdate, CreateView):
    """
    Used as class view to create qualifier
    """
    def get_success_url(self):

        id_concept = self.object.id

        # Search ID of the first term of this concept to redirect
        terms_of_concept = TermListQualif.objects.filter(identifier_concept_id=id_concept).values('id')
        id_term = terms_of_concept[0].get('id')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/qualifiers/view/%s%s' % ( id_term, ths )




class ConceptListQualifCreateView(LoginRequiredView, CreateView):
    """
    Used as class view to create concept and term of qualifier
    """
    model = IdentifierConceptListQualif
    template_name = 'thesaurus/qualifier_new_concept.html'
    form_class = IdentifierConceptListQualifForm

    def get_success_url(self):

        id_concept = self.object.id

        # Search ID of the first term of this concept to redirect
        terms_of_concept = TermListQualif.objects.filter(identifier_concept_id=id_concept).values('id')
        id_term = terms_of_concept[0].get('id')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/qualifiers/view/%s%s' % ( id_term, ths )

    def form_valid(self, form):

        formset_concept = ConceptListQualifFormSet(self.request.POST, instance=self.object)
        formset_term = TermListQualifFormSet(self.request.POST, instance=self.object)

        form_valid = form.is_valid()
        formset_concept_valid = formset_concept.is_valid()
        formset_term_valid = formset_term.is_valid()

        if (form_valid and formset_concept_valid and formset_term_valid):

            self.object = form.save(commit=False)
            self.object.identifier_id = int(self.request.POST.get("identifier_id"))
            self.object = form.save(commit=True)

            formset_concept.instance = self.object
            formset_concept.save()

            formset_term.instance = self.object
            formset_term.save()

            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(
                                            form=form,
                                            formset_concept=formset_concept,
                                            formset_term=formset_term,
                                            )
                        )

    def get_context_data(self, **kwargs):
        context = super(ConceptListQualifCreateView, self).get_context_data(**kwargs)

        if self.request.method == 'GET':

            context['formset_concept'] = ConceptListQualifFormSet(instance=self.object)
            context['formset_term'] = TermListQualifFormSet(instance=self.object)

        return context



class ConceptListQualifUpdateView(LoginRequiredView, UpdateView):
    """
    Used as class view to update a concept of qualifier
    """
    model = IdentifierConceptListQualif
    template_name = 'thesaurus/qualifier_edit_concept.html'
    form_class = IdentifierConceptListQualifForm

    def get_success_url(self):
        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/qualifiers/view/%s%s' % ( int(self.request.POST.get("termqualif__id")), ths )


    def form_valid(self, form):

        formset_concept = ConceptListQualifFormSet(self.request.POST, instance=self.object)

        form_valid = form.is_valid()
        formset_concept_valid = formset_concept.is_valid()

        if (form_valid and formset_concept_valid):

            self.object = form.save(commit=False)
            self.object.identifier_id = int(self.request.POST.get("identifier_id"))

            formset_concept.instance = self.object
            formset_concept.save()

            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(
                                            form=form,
                                            formset_concept=formset_concept,
                                            )
                        )

    def get_context_data(self, **kwargs):
        context = super(ConceptListQualifUpdateView, self).get_context_data(**kwargs)

        if self.request.method == 'GET':
            context['formset_concept'] = ConceptListQualifFormSet(instance=self.object)
        return context




class TermListQualifCreateView(LoginRequiredView, CreateView):
    """
    Used as class view to create a term
    """
    model = TermListQualif
    template_name = 'thesaurus/qualifier_new_term.html'
    form_class = TermListQualifUniqueForm

    def get_success_url(self):
        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/qualifiers/view/%s%s' % ( self.object.id, ths )

    def form_valid(self, form):
        
        if form.is_valid():
            identifier_concept_id = self.request.POST.get("identifier_concept_id")
            term_string = self.request.POST.get("term_string")
            language_code = self.request.POST.get("language_code")
            status = self.request.POST.get("status")

            has_term = TermListQualif.objects.filter(
                identifier_concept_id=identifier_concept_id,
                term_string__iexact=term_string,
                language_code=language_code,
                status=status,
                ).exists()

            if not has_term:
                self.object = form.save(commit=False)

                # prove the current date if you are not informed on the form
                if not self.object.date_created:
                    self.object.date_created = datetime.datetime.now().strftime('%Y-%m-%d')

                self.object.identifier_concept_id = self.request.POST.get("identifier_concept_id")

                form.save()
                return HttpResponseRedirect(self.get_success_url())
            else:
                msg_erro =  _("This Term already exist!")
                return self.render_to_response(self.get_context_data(form=form,msg_erro=msg_erro))

    def get_context_data(self, **kwargs):
        context = super(TermListQualifCreateView, self).get_context_data(**kwargs)
        return context



class TermListQualifUpdateView(LoginRequiredView, UpdateView):
    """
    Used as class view to update a term
    """
    model = TermListQualif
    template_name = 'thesaurus/qualifier_edit_term.html'
    form_class = TermListQualifUniqueForm

    def get_success_url(self):
        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/qualifiers/view/%s%s' % ( self.object.id, ths )

    def form_valid(self, form):

        if form.is_valid():
            self.object = form.save(commit=False)
            self.object.identifier_concept_id = self.request.POST.get("identifier_concept_id")
            self.object.date_altered = datetime.datetime.now().strftime('%Y-%m-%d')
            form.save()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(TermListQualifUpdateView, self).get_context_data(**kwargs)
        return context



class legacyInformationQualifCreateView(LoginRequiredView, CreateView):
    """
    Used as class view to create legacy information
    """
    model = legacyInformationQualif
    template_name = 'thesaurus/qualifier_new_legacy.html'
    form_class = legacyInformationQualifForm

    def get_success_url(self):

        id_identifier = self.request.GET.get("identifier_id")

        # Search ID of the first concept of this record
        concepts_of_registry = IdentifierConceptListQualif.objects.filter(identifier_id=id_identifier).values('id')
        id_concept = concepts_of_registry[0].get('id')

        # Search ID of the first term of this concept to redirect
        terms_of_concept = TermListQualif.objects.filter(identifier_concept_id=id_concept).values('id')
        id_term = terms_of_concept[0].get('id')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/qualifiers/view/%s%s' % ( id_term, ths )

    def form_valid(self, form):

        if form.is_valid():

            self.object = form.save(commit=False)
            self.object.identifier_id = self.request.POST.get("identifier_id")
            self.object = form.save()
            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(legacyInformationQualifCreateView, self).get_context_data(**kwargs)
        return context



class legacyInformationQualifUpdateView(LoginRequiredView, UpdateView):
    """
    Used as class view to update a legacy information
    """
    model = legacyInformationQualif
    template_name = 'thesaurus/qualifier_edit_legacy.html'
    form_class = legacyInformationQualifForm


    def get_success_url(self):

        id_identifier = self.request.GET.get("identifier_id")

        # Search ID of the first concept of this record
        concepts_of_registry = IdentifierConceptListQualif.objects.filter(identifier_id=id_identifier).values('id')
        id_concept = concepts_of_registry[0].get('id')

        # Search ID of the first term of this concept to redirect
        terms_of_concept = TermListQualif.objects.filter(identifier_concept_id=id_concept).values('id')
        id_term = terms_of_concept[0].get('id')

        ths = '?ths=' + self.request.GET.get("ths")
        return '/thesaurus/qualifiers/view/%s%s' % ( id_term, ths )

    def form_valid(self, form):

        if form.is_valid():

            self.object = form.save()
            form.save()

            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(legacyInformationQualifUpdateView, self).get_context_data(**kwargs)
        return context



class PageViewQualif(LoginRequiredView, DetailView):
    """
    Used as class view to list the result
    """
    model = TermListQualif
    template_name = 'thesaurus/page_view_qualif.html'

    def get_context_data(self, **kwargs):
        context = super(PageViewQualif, self).get_context_data(**kwargs)

        if self.object:

            # IdentifierConceptListQualif - recupera pk do conceito
            id_concept = IdentifierConceptListQualif.objects.filter(
                                            id=self.object.identifier_concept_id,
                                            ).values('identifier_id').distinct()

            # Used to create new concept
            for concept in id_concept:
                context['id_concept_new'] = concept

            # IdentifierConceptListQualif - retrieves pk's that has even identifier_id - can bring more than 1
            ids = IdentifierConceptListQualif.objects.filter(
                                            identifier_id=id_concept,
                                            ).values('id')

            # IdentifierQualif
            # Brings information to Active Descriptor Record
            context['identifierqualif_objects'] = IdentifierQualif.objects.filter(
                                            id=id_concept,
                                            )

            context['id_register_objects'] = IdentifierQualif.objects.filter(
                                            id=id_concept,
                                            ).values(

                                                # IdentifierQualif
                                                'id',
                                                'thesaurus',
                                                'qualifier_ui',
                                                'decs_code',
                                                'external_code',
                                                'abbreviation',
                                                'date_created',
                                                'date_revised',
                                                'date_established',
                                            )

            context['description_objects'] = IdentifierQualif.objects.filter(
                                            id=id_concept,
                                            ).values(
                                                # DescriptionQualif
                                                'descriptionqualif__identifier_id',
                                                'descriptionqualif__language_code',
                                                'descriptionqualif__annotation',
                                                'descriptionqualif__history_note',
                                                'descriptionqualif__online_note',
                                            )

            # Used to create tree number list
            context['tree_numbers_objects'] = IdentifierQualif.objects.filter(
                                            id=id_concept,
                                            ).values(
                                                # TreeNumbersListQualif
                                                'qtreenumbers__identifier_id',
                                                'qtreenumbers__tree_number',
                                            ).distinct().order_by('qtreenumbers__tree_number')

            context['term_string_info_preferred_objects'] = IdentifierConceptListQualif.objects.filter(
                                            identifier=id_concept,termqualif__concept_preferred_term='Y',termqualif__record_preferred_term='Y',
                                            ).order_by('identifier_id',
                                                        'termqualif__identifier_concept_id',
                                                        '-preferred_concept',
                                                        '-termqualif__concept_preferred_term',
                                                        'termqualif__language_code',
                                                        'termqualif__term_string',
                                            ).values(
                                                    'id',
                                                    'termqualif__term_string',
                                                    'termqualif__language_code',
                                                    'identifier_id',
                                            )

            context['entry_terms_objects'] = IdentifierConceptListQualif.objects.filter(
                                            identifier=id_concept,termqualif__record_preferred_term='N',
                                            ).order_by('identifier_id',
                                                        'termqualif__language_code',
                                                        'termqualif__term_string',
                                            ).values(
                                                    'id',
                                                    'termqualif__id',
                                                    'termqualif__term_string',
                                                    'termqualif__language_code',
                                            )

            context['scope_note_objects'] = IdentifierConceptListQualif.objects.filter(
                                            identifier=id_concept,preferred_concept='Y',
                                            ).order_by('identifier_id',
                                            ).values(
                                                    'conceptqualif__language_code',
                                                    'conceptqualif__scope_note',
                                            ).distinct()

            context['legacy_objects'] = legacyInformationQualif.objects.filter(
                                            identifier=id_concept,
                                            ).values(
                                                'id',
                                                'pre_codificado',
                                                'desastre',
                                                'reforma_saude',
                                                'geografico',
                                                'mesh',
                                                'pt_lilacs',
                                                'nao_indexavel',
                                                'homeopatia',
                                                'repidisca',
                                                'saude_publica',
                                                'exploded',
                                                'geog_decs',
                                                'identifier_id',
                                            )

            # Used to show concept and term information
            context['identifierconceptlist_objects'] = IdentifierConceptListQualif.objects.filter(
                                            identifier=id_concept,
                                            ).order_by('identifier_id',
                                                        'termqualif__identifier_concept_id',
                                                        '-preferred_concept',
                                                        '-termqualif__concept_preferred_term',
                                                        'termqualif__language_code',
                                                        'termqualif__term_string',
                                            ).values(
                                                    'id',
                                                    'identifier_id',
                                                    'concept_ui',
                                                    'concept_relation_name',
                                                    'preferred_concept',
                                                    'casn1_name',
                                                    'registry_number',

                                                    'conceptqualif__identifier_concept_id',
                                                    'conceptqualif__language_code',
                                                    'conceptqualif__scope_note',

                                                    'termqualif__id',
                                                    'termqualif__identifier_concept_id',
                                                    'termqualif__status',
                                                    'termqualif__term_ui',
                                                    'termqualif__language_code',
                                                    'termqualif__term_string',
                                                    'termqualif__concept_preferred_term',
                                                    'termqualif__is_permuted_term',
                                                    'termqualif__lexical_tag',
                                                    'termqualif__record_preferred_term',
                                                    'termqualif__entry_version',
                                                    'termqualif__date_created',
                                                    'termqualif__date_altered',
                                                    'termqualif__historical_annotation',
                                            ).distinct()

            # Informacoes para log
            # Registro
            # ID do model
            id_ctype_identifierqualif = ContentType.objects.filter(model='identifierqualif').values('id')
            context['id_ctype_identifierqualif'] = id_ctype_identifierqualif[0].get('id')
            # ID do registro
            id_identifierqualif = IdentifierQualif.objects.filter(id=id_concept).values('id')
            context['id_identifierqualif'] = id_identifierqualif[0].get('id')

            return context


