#!/usr/bin/env python3

import os
from azure.mgmt.compute import ComputeManagementClient
import azure.mgmt.resource
import automationassets

def get_automation_runas_credential(runas_connection):
    from OpenSSL import crypto
    import binascii
    from msrestazure import azure_active_directory
    import adal

    # Get the Azure Automation RunAs service principal certificate
    cert = automationassets.get_automation_certificate("AzureRunAsCertificate")
    pks12_cert = crypto.load_pkcs12(cert)
    pem_pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM,pks12_cert.get_privatekey())

    # Get run as connection information for the Azure Automation service principal
    application_id = runas_connection["ApplicationId"]
    thumbprint = runas_connection["CertificateThumbprint"]
    tenant_id = runas_connection["TenantId"]

    # Authenticate with service principal certificate
    resource ="https://management.core.windows.net/"
    authority_url = ("https://login.microsoftonline.com/"+tenant_id)
    context = adal.AuthenticationContext(authority_url)
    return azure_active_directory.AdalAuthentication(lambda: context.acquire_token_with_client_certificate(resource, application_id, pem_pkey, thumbprint))

# Authenticate to Azure using the Azure Automation RunAs service principal
runas_connection = automationassets.get_automation_connection("AzureRunAsConnection")
azure_credential = get_automation_runas_credential(runas_connection)

# Initialize the compute management client with the Run As credential and specify the subscription to work against.
compute_client = ComputeManagementClient(azure_credential, str(runas_connection["SubscriptionId"]))


print('\nStart script')
vmss = compute_client.virtual_machine_scale_sets.get(resource_group_name='udacity_eric', vm_scale_set_name='udacity-vmss')
print('SKU Before upgrade', vmss.sku.name)
vmss.sku.name = 'Standard_B1s' # old Standard_B1ls
# vmss.sku.name = 'Standard_B1ls' # Rollback upgrade: old Standard_B1s
compute_client.virtual_machine_scale_sets.create_or_update(resource_group_name='udacity_eric', vm_scale_set_name='udacity-vmss', parameters=vmss)
print('SKU After upgrade', vmss.sku.name)
print('\nEnd script')