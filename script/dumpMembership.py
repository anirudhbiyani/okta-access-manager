#!/usr/bin/env python3

# pylint: disable=line-too-long,invalid-name,global-variable-undefined,missing-function-docstring,missing-module-docstring

import yaml
import boto3
from okta import okta

def main():
    lambda_handler(None, None)

def lambda_handler(event, context):
    ssm_client = boto3.client('ssm')
    token = ssm_client.get_parameter(Name="okta_token",WithDecryption=True)['Parameter']['Value']
    host = ssm_client.get_parameter(Name="okta_host",WithDecryption=True)['Parameter']['Value']
    headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": "SSWS " + token
    }

    # Get all groups that are present in Okta.
    okta_groups = okta.listGroups(host, headers)
    yaml_list=[]

    for i in range(0, len(okta_groups)):
        yaml_list.append(okta_groups[i][:1].lower())
    yaml_list = list(set(yaml_list))

    for i in yaml_list:
        account_membership={}
        filename = f'../files/{i}.yaml'
        res = [idx for idx in okta_groups if idx[0].lower() == i.lower()]
        for j in res:
            oktaList = okta.getGroupID(host, headers, j)
            account_membership[j] = okta.getMembers(host, headers, oktaList)
        with open(filename, 'w') as file:
            yaml.dump(account_membership, file, default_flow_style=False)

if __name__ == '__main__':
    main()
