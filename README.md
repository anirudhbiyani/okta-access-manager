# okta-access-manager

okta-access-manager (OAM) is a simple tool that enables Okta Groups to be managed using a GitOps approach and the repo also acts as one single source of truth for all Okta Group and it's membership data. OAM can use perform the following operations by just updating the YAML files -
* Create Okta Group
* Delete Okta Group
* Add User to an Okta Group
* Remove User from an Okta Group

#### Why?
Generally, IdP (Identity Provider) like Okta, OneLogin or Azure Active Directory are linked with tools like Active Directory or OpenLDAP where the User Management Lifecycle occurs and it's the mainly source of information for all the other systems in the organization.

This tool is mainly written for environment where Active Directory like system is not present or there are large number of Okta Groups that needs to be maintained.

#### How?
OAM (Okta Access Manager) is meant to be deployed in Amazon Web Services (AWS) taking the advantage of serverless computing and object based storage to run itself. The YAML files are stored in AWS S3 Buckets and AWS Lambda is used for the execution of the Python scripts.

The YAML can be managed by any sort of versioning mechanism like git or svn and once the updated files are uploaded to S3, they are picked up automatically for execution. Once, the updated to the S3 Bucket using the CI/CD system of your choice. The file would be automatically picked up and checked for all the changes in the groups and their memberships.
̨̨̨̨̨
#### Deploy?

The aim was to make the deploy as easy as possible which is why we create a wrapper called `deploy.sh` which you use to deploy, update or remove OAM.

This is the current structure of the files that are present in this repository.
- cloudformation
  - infra.yaml - This cloudformation template create the S3 buckets, Lambda, SNS topics.
- files/ - This is the folder that would contain all the YAML files with all the group and membership data. The YAML files are grouped based on the Okta group name like b.yaml or 6.yaml for ease of management and readability.
- script/
  - okta.py - Contains all the functions that are needed for the manage* scripts to function.
  - manageGroups.py - Takes care of all the CRUD operations for Okta Groups.
  - manageMembership.py - Manages all the Group Membership CRUS Opertions.
  - dumpMembership.py - This is to dump existing state of Okta groups and their membership details from Okta into YAML files. Note - While running this, you will need to create files/ directory for dumpMembership.py.
- deploy.sh - This bash script is used to deploy/update/delete the tool. There are two parameters that are defined in `deploy.sh` that are hardcoded which needs to be modified before the first execution of the script. The variables are -
  - BUCKET_NAME - This is the name of the S3 Bucket that will hold all the YAML files that are to be used by AWS Lambda to get the latest membership date for it's execution.
  - ManagedResourcePrefix - This is the prefix that would be used by all the resources that would be created by the CloudFormation template.


Steps  to deploy okta-access-manager -

1. Run the deploy.sh script with the "create" option. The deploy script has multiple options that can be passed as parameters like create, update and delete.
2. AWS Lambda package is created with all the dependencies.
4. CloudFormation deployment is deployed via deploy.sh script which creates the lambda function, S3 Bucket, SSM parameters and any other supporting infrastructure that is needed.

There is also a temporary directory that is created called build which is used to hold all the temporary files that are needed to create AWS Lambda packages. All the temporary files are removed once they are not needed anymore.

The script does not deploy a way to sync files form git repository to S3 Bucket which is dependent on tools of your choice. Example of using GitHub Actions to upload to S3 after validating YAML all the files changed in the commit -

```
name: YAMLValidation
on:
  pull_request:

  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: checkout
        uses: actions/checkout@v2
        with:
          fetch-depth: 0

      - name: get changed files
        id: getfile
        run: |
           echo "::set-output name=yaml::$(git diff --name-only ${{ github.event.pull_request.base.sha }} ${{ github.sha }} | grep .yaml$ | xargs)"

      - name: install yq
        run: |
          sudo snap install yq
      - name: checkYAML
        run: |
          echo "Changed files - " ${{ steps.getfile.outputs.yaml }}
          for i in ${{ steps.getfile.outputs.yaml }}
          do
            echo "Running for file - " $i
            yq e -P $i > /dev/null
            echo "Exit Code for yq - " $?
          done
```

#### Known Issues?

* There is a limitation of the number of groups returned by Okta Search API is limited to 300 groups.

* In the rare event, you are hitting the rate limiting for your Okta subscription, it is not handled explicitly but the changes should be picked in next execution.

#### Issues/Feedback?
If there are any issues, please open an GitHub Issue.
