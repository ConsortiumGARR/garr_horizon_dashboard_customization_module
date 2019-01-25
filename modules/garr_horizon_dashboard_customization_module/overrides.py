# Copyright 2019 Consortium GARR
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# TODO: PEP-8

# References
# https://docs.openstack.org/horizon/latest/configuration/customizing.html
# https://stackoverflow.com/questions/10027232/how-to-overwrite-a-imported-python-class-for-all-calls

# OpenStack dashboard modules that we want to override
from openstack_dashboard.dashboards.identity.application_credentials import views
from openstack_dashboard.dashboards.identity.application_credentials import forms
from openstack_dashboard.dashboards.identity.application_credentials import urls

# other imports
import horizon
from django.conf.urls import url
from django.utils.translation import ugettext_lazy as _
from openstack_dashboard.dashboards.identity.application_credentials import forms as project_forms
from django.views.decorators.debug import sensitive_variables
from django.urls import reverse
import django.conf

import os
import hashlib


# ------------------------------------------------------------------------------
# remove the admin panels
# merged from ansible-fed-keystone
import garrcloud.override
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# define the function _GARR_get_context based on _get_context to add to the
# context some parameters that we need for the kubeconfig file
def _GARR_get_context(request):
    context = views._get_context(request)
    context['user'] = request.user 
    app_cred = request.session['application_credential']
    context['namespace'] = app_cred['namespace']
    return context

# and add the function to the views module
views._GARR_get_context = _GARR_get_context #XXX: do we need this line?

# add the template directory from the customization module to the django configuration
script_dir = os.path.dirname(__file__)
template_dir = os.path.join(script_dir, "templates")
django.conf.settings.TEMPLATES[0]['DIRS'].insert(0, template_dir)

# define a new function for downloading the kubeconfig file, which uses the _GARR_get_context function above
# and a customization module provided template
def download_kubeconfig_file(request):
    context = _GARR_get_context(request)
    template = 'kubeconfig.template'
    filename = 'app-cred-%s-kubeconfig' % context['application_credential_name']
    response = views._render_attachment(filename, template, context, request)
    return response

# and add it to the views
views.download_kubeconfig_file = download_kubeconfig_file #XXX: do we need this line?

# and to the URL patterns
urls.urlpatterns.append( url(r'^download_kubeconfig/$', download_kubeconfig_file, name='download_kubeconfig') )
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# create a new class for the successful credential creation form
# i.e. the form that appears when the user clicks on "Create Application Credential"
# by subclassing the existing one
class GARR_CreateSuccessfulView(views.CreateSuccessfulView):
    template_name = 'garr_success.html'
    download_kubeconfig_label = _("Download kubeconfig file")
    
    def get_context_data(self, **kwargs):
        context = views.CreateSuccessfulView.get_context_data(self, **kwargs)
        context['download_kubeconfig_label'] = self.download_kubeconfig_label
        context['download_kubeconfig_url'] = reverse(
            'horizon:identity:application_credentials:download_kubeconfig')
        return context

views.GARR_CreateSuccessfulView = GARR_CreateSuccessfulView 
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# create a new class for the credential application form
# i.e. the form that pops up when the user clicks on
# "Create Application Credential"
# by subclassing the existing one
class GARR_CreateApplicationCredentialForm(forms.CreateApplicationCredentialForm): 
    namespace = horizon.forms.CharField(max_length=255,
                                label=_("Namespace (Kubernetes)"),
                                required=False) 

    @sensitive_variables('data')
    def handle(self, request, data):
            forms.CreateApplicationCredentialForm.handle(self, request, data)
            self.request.session['application_credential']['namespace'] = data['namespace']
            return self.next_view.as_view()(request)
    
# and add it to the forms module
forms.GARR_CreateApplicationCredentialForm = GARR_CreateApplicationCredentialForm 
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def computeNamespaceName(os_name):
    # kubernetes allows only namespaces which are validated by the regular expression '[a-z0-9]([-a-z0-9]*[a-z0-9])?'
    # i.e. made by lowercase letters, numbers and '-' and starting with a lowercase letter
    # and not longer than 63 characters
    name = str(os_name)
    name = name.lower()
    name = "".join([ c for c in name if (ord(c) >= ord('a') and ord(c) <= ord('z')) or (ord(c) >= ord('0') and ord(c) <= ord('9')) or c == '@'])
    name = name.replace('@', '-')
    name = "g-" + name  # fix usernames beginning with numbers
    name = name[:60]
    return name

# Create a new view class which uses both
# GARR_CreateApplicationCredentialForm and GARR_CreateSuccessfulView
class GARR_CreateView(views.CreateView):
    form_class = project_forms.GARR_CreateApplicationCredentialForm

    def get_form_kwargs(self):
        kwargs = views.CreateView.get_form_kwargs(self)
        kwargs['next_view'] = GARR_CreateSuccessfulView
        kwargs['initial'] = {'namespace': computeNamespaceName(self.request.user)}
        return kwargs

# add it to the views module
views.GARR_CreateView = GARR_CreateView 

# and register it by replacing in the url patterns CreateView with GARR_CreateView
newurlpatterns = [up for up in urls.urlpatterns if up.name != "create"]
newurlpatterns.append( url(r'^create/$', views.GARR_CreateView.as_view(), name='create') )
urls.urlpatterns = newurlpatterns
# ------------------------------------------------------------------------------


