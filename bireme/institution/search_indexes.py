import datetime
from institution.models import Institution,Type, Adm, URL, UnitLevel, Contact
from django.contrib.contenttypes.models import ContentType
from haystack import indexes

class InstitutionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField()
    unit = indexes.MultiValueField()
    address = indexes.CharField(model_attr='address', null=True)
    city = indexes.CharField(model_attr='city', null=True)
    state = indexes.CharField(model_attr='state', null=True)
    zipcode = indexes.CharField(model_attr='zipcode', null=True)
    country = indexes.CharField()
    country_code = indexes.CharField()
    institution_type = indexes.MultiValueField()
    institution_thematic = indexes.MultiValueField()
    contact = indexes.MultiValueField()
    link = indexes.MultiValueField()
    user = indexes.MultiValueField() # used for search by type field
    cat = indexes.MultiValueField()  # used for by category field

    cooperative_center_code = indexes.CharField(model_attr='cc_code', null=False)
    created_date = indexes.CharField()
    updated_date = indexes.CharField()
    status = indexes.IntegerField(model_attr='status')

    def get_model(self):
        return Institution

    def prepare_title(self, obj):
        return str(obj)

    def prepare_unit(self, obj):
        units = [unit_level.unit for unit_level in UnitLevel.objects.filter(institution=obj.id).order_by('level')]

        return units

    def prepare_contact(self, obj):
        output_list = []

        contact_list = Contact.objects.filter(institution=obj.id)
        for contact in contact_list:
            if contact.country_area_code:
                contact_phone = "+" + contact.country_area_code + " " + contact.phone_number
            else:
                contact_phone = contact.phone_number

            if contact.job_title:
                contact_name = u"{0} ({1})".format(contact.name, contact.job_title)
            else:
                contact_name = contact.name

            contact_details = [contact_name, contact.email, contact_phone]
            # remove empty data
            contact_details = filter(None, contact_details)

            contact_item = " | ".join(contact_details)

            output_list.append(contact_item)

        return output_list

    def prepare_link(self, obj):
        output_list = []

        link_list = URL.objects.filter(institution=obj.id)
        for link in link_list:
            output_list.append(link.url)

        return output_list


    def prepare_country(self, obj):
        if obj.country:
            translations = obj.country.get_translations()
            return "|".join(translations)

    def prepare_country_code(self, obj):
        if obj.country:
            return obj.country.code

    def prepare_user(self, obj):
        output_list = []
        inst_list = Adm.objects.filter(institution=obj.id)
        for inst in inst_list:
            for type in inst.type.all():
                type_translated = type.get_translations()
                output_list.append(type_translated)

        return output_list

    def prepare_cat(self, obj):
        output_list = []
        try:
            adm = Adm.objects.get(institution=obj.id)
        except Adm.DoesNotExist:
            adm = None

        if adm:
            for category in adm.category.all():
                category_translated = category.get_translations()
                output_list.append(category_translated)

        return output_list

    def prepare_institution_type(self, obj):
        type_list = []
        try:
            adm = Adm.objects.get(institution=obj.id)
        except Adm.DoesNotExist:
            adm = None

        if adm:
            adm_type_list = [type.name for type in adm.type.all()]
            if 'CCR' in adm_type_list:
                type_list.append('CoordinatingCentersRg')
            if 'CCN' in adm_type_list:
                type_list.append('CoordinatingCentersNc')
            if any(value in adm_type_list for value in ['REDEBR/CC', 'REDEAL/CC', 'MEDCARIB/CC']):
                type_list.append('CooperatingCenters')
            if 'LILACS' in adm_type_list:
                type_list.append('CooperatingCentersLILACS')
            if 'LEYES' in adm_type_list:
                type_list.append('CooperatingCentersLEYES')
            if  any(value in adm_type_list for value in ['REDEBR/UP', 'REDEAL/UP', 'MEDCARIB/UP']):
                type_list.append('ParticipantsUnits')
            if  any(value in adm_type_list for value in ['REDEAL', 'REDEBR', 'EPORT', 'MEDCARIB']):
                type_list.append('VHLNetwork')

        return type_list


    def prepare_institution_thematic(self, obj):
        type_list = []
        try:
            adm = Adm.objects.get(institution=obj.id)
        except Adm.DoesNotExist:
            adm = None

        if adm:
            adm_type_list = [type.name for type in adm.type.all()]
            if 'MEDCARIB' in adm_type_list:
                type_list.append('MedCarib')
            if 'ENFERMAGEM' in adm_type_list:
                type_list.append('Nursing')
            if 'FRONTERIZA' in adm_type_list:
                type_list.append('Border')
            if 'DESASTRES' in adm_type_list:
                type_list.append('Disastres')
            if 'PSICOLOGIA' in adm_type_list:
                type_list.append('Psychology')
            if 'MTCI' in adm_type_list:
                type_list.append('MTCI')

        return type_list


    def prepare_created_date(self, obj):
        if obj.created_time:
            return obj.created_time.strftime('%Y%m%d')

    def prepare_updated_date(self, obj):
        if obj.updated_time:
            return obj.updated_time.strftime('%Y%m%d')

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(created_time__lte=datetime.datetime.now())
