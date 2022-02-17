#!/usr/bin/env python3

# pylint: disable=line-too-long,invalid-name,global-variable-undefined,missing-function-docstring,missing-module-docstring, wrong-import-order, multiple-imports, consider-using-enumerate

import yaml, os, boto3, re, requests, sys, json

class okta:
    def listGroups(host, headers):
        oktagroups = []
        nexturl = None
        url = f"https://{host}/api/v1/groups?filter=type+eq+\"OKTA_GROUP\"&limit=200"
        response = requests.get(url, headers=headers)
        for value in response.json():
            oktagroups.append(value['profile']['name'])
        if "after" in response.headers['link']:
            nextlink = re.search("<(.*?)>", response.headers['link'].split(',')[1])
            nexturl = nextlink.group(0)[:-1][1:]

        while nexturl is not None:
            response = requests.get(nexturl, headers=headers)
            for value in response.json():
                groupname = value['_links']['group']['href']
                gresponse = requests.get(groupname, headers=headers)
                r = gresponse.json()['profile']['name']
                oktagroups.append(r)
            if "next" in response.headers['link']:
                nextlink = re.search("<(.*?)>", response.headers['link'].split(',')[1])
                nexturl = nextlink.group(0)[:-1][1:]
            else:
                nexturl = None
        print(oktagroups)
        return oktagroups

    def searchGroups(host, headers, group_name):
        url = f'https://{host}/api/v1/groups?q={group_name}&limit=100&filter=type+eq+%22OKTA_GROUP%22'
        response = requests.get(url, headers=headers)
        result = response.json()
        return result

    def getGroupID(host, headers, group_name):
        url = f'https://{host}/api/v1/groups?q={group_name}&limit=100&filter=type+eq+%22OKTA_GROUP%22'
        response = requests.get(url, headers=headers)
        if len(result) != 1:
            for i in range(0,len(result)):
                if result[i]['profile']['name'] == group_name:
                    return result[i]['id']
        else:
            return result[0]['id']

    def getUserID(host, headers, user_login):
        # GET /api/v1/users
        url = f'https://{host}/api/v1/users/{user_login}'
        response = requests.get(url, headers=headers)
        result = json.loads(response.text)
        if result['status'] == 'ACTIVE':
            return result['id']
        else:
            return None

    def addMember(host, headers, groupid, userid):
        # PUT /api/v1/groups/${groupId}/users/${userId}
        url = f'https://{host}/api/v1/groups/{groupid}/users/{userid}'
        response = requests.put(url, headers=headers)
        return response.status_code

    def createGroup(host, headers, group_name):
        desc = '{"profile": {"name":"' + group_name + '", "description": "Created by github.com/anirudhbiyani/okta-access-manager"}}'
        url = f"https://{host}/api/v1/groups"
        response = requests.post(url, data=desc, headers=headers)
        result = response.json()
        if result['id'] is not None:
            print("Okta Group created successfully.")
        else:
            print("Okta Group creation failed.")

    def deleteGroup(host, headers, group_name):
        gid = okta.getGroupID(host, headers, group_name)
        url = f"https://{host}/api/v1/groups/{gid}"
        response = requests.delete(url, headers=headers)
        if response.status_code == 204:
            print('Okta Group deleted successfully.')
        else:
            print('Okta Group could not be deleted.')

    def getUserID(host, headers, user_login):
        # GET /api/v1/users
        url = f'https://{host}/api/v1/users/{user_login}'
        response = requests.get(url, headers=headers)
        result = json.loads(response.text)
        if result['status'] == 'ACTIVE':
            return result['id']
        else:
            return None

    # add user to group
    def addMember(host, headers, groupid, userid):
        # PUT /api/v1/groups/${groupId}/users/${userId}
        url = f'https://{host}/api/v1/groups/{groupid}/users/{userid}'
        response = requests.put(url, headers=headers)
        return response.status_code

    # remove users from group
    def removeMember(host, headers, groupid, userid):
        # DELETE /api/v1/groups/${groupId}/users/${userId}
        url = f'https://{host}/api/v1/groups/{groupid}/users/{userid}'
        response = requests.delete(url, headers=headers)
        return response.status_code

    def getMembers(host, headers, groupid):
        group_membership = []
        url = f"https://{host}/api/v1/groups/{groupid}/users"
        response = requests.get(url, headers=headers)
        result = response.json()
        for x in range(len(result)):
            group_membership.append(result[x]['profile']['login'])

        return group_membership

    def diff(list1, list2):
        return list(list(set(list1)-set(list2)))
