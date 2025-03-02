# coding: utf-8
from django.conf import settings
from django.urls import re_path
from django.contrib.contenttypes.models import ContentType

from tastypie.resources import ModelResource
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.utils import trailing_slash
from tastypie import fields
from main.models import Resource, ResourceThematic, Descriptor, SourceType, SourceLanguage

import requests
import urllib
import json

class LinkResource(ModelResource):

    class Meta:
        queryset = Resource.objects.filter(status=1)
        allowed_methods = ['get']
        resource_name = 'resource'
        filtering = {
            'thematic_area_id': 'exact',
        }
        include_resource_uri = False
        max_limit = settings.MAX_EXPORT_API_LIMIT

    def build_filters(self, filters=None, *args, **kwargs):
        orm_filters = super(LinkResource, self).build_filters(filters, *args, **kwargs)

        if 'thematic_area_id' in filters:
            orm_filters['thematics__thematic_area__exact'] = filters['thematic_area_id']
        return orm_filters

    def prepend_urls(self):
        return [
            re_path(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            re_path(r"^(?P<resource_name>%s)/get_last_id%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_last_id'), name="api_get_last_id"),
        ]


    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        q = request.GET.get('q', '')
        fq = request.GET.get('fq', '')
        start = request.GET.get('start', '')
        count = request.GET.get('count', '')
        lang = request.GET.get('lang', 'pt')
        op = request.GET.get('op', 'search')
        id = request.GET.get('id', '')
        sort = request.GET.get('sort', 'created_date desc')

        # filter result by approved resources (status=1)
        if fq != '':
            fq = '(status:1 AND django_ct:main.resource) AND %s' % fq
        else:
            fq = '(status:1 AND django_ct:main.resource)'

        # url
        search_url = "%siahx-controller/" % settings.SEARCH_SERVICE_URL

        search_params = {'site': settings.SEARCH_INDEX, 'op': op,'output': 'site', 'lang': lang,
                    'q': q , 'fq': fq,  'start': start, 'count': count, 'id' : id,'sort': sort}

        r = requests.post(search_url, data=search_params)
        try:
            response_json = r.json()
        except ValueError:
            response_json = json.loads('{"type": "error", "message": "invalid output"}')

        self.log_throttled_access(request)
        return self.create_response(request, response_json)


    def dehydrate(self, bundle):
        c_type = ContentType.objects.get_for_model(bundle.obj)

        source_types = SourceType.objects.filter(resource=bundle.obj.id)
        source_languages = SourceLanguage.objects.filter(resource=bundle.obj.id)
        descriptors = Descriptor.objects.filter(object_id=bundle.obj.id, content_type=c_type, status=1)
        thematic_areas = ResourceThematic.objects.filter(object_id=bundle.obj.id, content_type=c_type, status=1)

        # add fields to output
        bundle.data['link'] = [line.strip() for line in bundle.obj.link.split('\n') if line.strip()]
        bundle.data['descriptors'] = [{'text': descriptor.text, 'code': descriptor.code} for descriptor in descriptors]
        bundle.data['thematic_areas'] = [{'code': thematic.thematic_area.acronym, 'text': thematic.thematic_area.name} for thematic in thematic_areas]
        bundle.data['source_types'] = [source_type.acronym for source_type in source_types]
        bundle.data['source_languages'] = [source_language.acronym for source_language in source_languages]

        return bundle

    def get_last_id(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        response = Resource.objects.latest('pk').pk

        return self.create_response(request, response)
