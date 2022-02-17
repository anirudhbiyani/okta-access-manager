#!/usr/bin/env python3

# pylint: disable=invalid-name

import os
import json
import boto3
import yaml
from okta import okta

def groupsDiff(yamllist, oktalist):
    groupstoAdd = diff(yamllist, oktalist)
    print("Groups to add - " )
    print(groupstoAdd)
    for i in groupstoAdd:
        if not resource[i]:
            print('Skipping creation of group ' + i + ' - no memebers present')
        else:
            okta.createGroup(host, headers, i)
            groupID = okta.getGroupID(host, headers, i)
            users_to_add = resource[i]
            for user in users_to_add:
                okta_user_id = okta.getUserID(host, headers, user)
                if okta_user_id is not None:
                    status = okta.addMember(host, headers, groupID, okta_user_id)
                    if status == 204:
                        print('User added successfully to the group - ', i, 'for user - ', user)
                    else:
                        print('User addition failed for group ', i, 'for user - ', user)

    groupstoRemove = diff(oktalist, yamllist)
    print("Groups to remove - ")
    print(groupstoRemove)
    for i in groupstoRemove:
        okta.deleteGroup(host, headers, i)

# Python code to get difference of two lists
def diff(list1, list2):
    return list(list(set(list1)-set(list2)))

def main():
    lambda_handler(None, None)

def lambda_handler(event, context):
    global token
    global host
    global headers
    global awsgroups
    global resource

    bucket_name = os.environ['BUCKET_NAME']
    ssm_client = boto3.client('ssm')
    token = ssm_client.get_parameter(Name="okta-token",WithDecryption=True)['Parameter']['Value']
    host = ssm_client.get_parameter(Name="okta-host",WithDecryption=True)['Parameter']['Value']
    headers = {
        "Accept": "application/json",
        'Content-type': 'application/json',
        'Authorization': 'SSWS ' + token
    }

    awsgroups = []
    s3_client = boto3.client('s3')
    files = [key['Key'] for key in s3_client.list_objects_v2(Bucket=bucket_name, Prefix='files/')['Contents']]

    if 'Records' in event:
        files = [json.loads(event['Records'][0]['Sns']['Message'])['Records'][0]['s3']['object']['key']]

    print(files)
    for file in files:
        groupname = os.path.splitext(os.path.basename(file))[0]
        print("Running for groups that start with", groupname, "using file -", file)

        g = []
        filename = f'/tmp/{groupname}.yaml'
        s3_client.download_file(bucket_name, file, filename)
        if os.path.exists(filename):
            oktaList = okta.searchGroups(host, headers, groupname)
            for x in range(len(oktaList)):
                g.append(oktaList[x]['profile']['name'])
            with open(filename,'r+') as f:
            #f = open(filename, 'r+')
                resource = yaml.load(f, Loader=yaml.FullLoader)
                groupList = resource.keys()
                print("groupList - ", groupList)
                print("g - ", g)
                groupsDiff(groupList, g)

if __name__ == '__main__':
    main()
