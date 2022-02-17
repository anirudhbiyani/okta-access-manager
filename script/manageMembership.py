#!/usr/bin/env python3

import os
import json
import yaml
import boto3
from okta import okta

def main():
    lambda_handler(None, None)

def lambda_handler(event, context):
    print(event)
    bucket_name = os.environ['BUCKET_NAME']

    ssm_client = boto3.client('ssm')
    token = ssm_client.get_parameter(Name="okta-token",WithDecryption=True)['Parameter']['Value']
    host = ssm_client.get_parameter(Name="okta-host",WithDecryption=True)['Parameter']['Value']
    headers = {
        "Accept": "application/json",
        'Content-type': 'application/json',
        'Authorization': 'SSWS ' + token
    }

    s3_client = boto3.client('s3')
    files = [key['Key'] for key in s3_client.list_objects_v2(Bucket=bucket_name, Prefix='files/')['Contents']]
    if 'Records' in event:
        files = [json.loads(event['Records'][0]['Sns']['Message'])['Records'][0]['s3']['object']['key']]

    for file in files:
        f = '/tmp/' + os.path.basename(file)
        print('Running for - ' + f)
        s3_client.download_file(bucket_name, file, f)
        if os.path.exists(f):
            with open(f) as handle:
                groups = yaml.load(handle, Loader=yaml.FullLoader)
                for group in groups.keys():
                    print ('Checking group - ')
                    print(group)
                    g = okta.searchGroups(host, headers, group)
                    for i in range(len(g)):
                        groupID = g[i]['id']
                        okta_users = okta.getMembers(host, headers, groupID)

                    yaml_users = groups.get(group)
                    print("YAML Users - ", yaml_users)
                    print("Okta Users - ", okta_users)

                    users_to_add = okta.diff(yaml_users, okta_users)
                    print('Users to add - ')
                    print(users_to_add)
                    for user in users_to_add:
                        okta_user_id = okta.getUserID(host, headers, user)
                        if okta_user_id is not None:
                            status = okta.addMember(host, headers, groupID, okta_user_id)

                    users_to_remove = okta.diff(okta_users, yaml_users)
                    print('Users to remove - ')
                    print(users_to_remove)
                    for user in users_to_remove:
                        okta_user_id = okta.getUserID(host, headers, user)
                        if okta_user_id is not None:
                            status = okta.removeMember(host, headers, groupID, okta_user_id)

if __name__ == '__main__':
    main()
