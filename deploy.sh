#!/usr/bin/env bash

BUCKET_NAME="okta-access-manager"
ManagedResourcePrefix="okta-access-manager"

removetemp()
{
  echo 'Removing temporary files'
  rm -rf build/
  rm lambda.zip

}
lambda()
{
  echo 'Starting build:' && date
  mkdir build
  pip3 install -t ./build pyyaml requests charset-normalizer > /dev/null
  cd build; rm -rf *.dist-info; rm -rf _*;
  zip -r ../lambda.zip .; cd .. ;
  zip -U lambda.zip --output-file manageGroups.zip > /dev/null
  zip -U lambda.zip --output-file manageMemberships.zip > /dev/null
  cd script/;
  zip -g ../manageGroups.zip okta.py > /dev/null
  zip -g ../manageGroups.zip manageGroups.py > /dev/null
  zip -g ../manageMemberships.zip okta.py > /dev/null
  zip -g ../manageMemberships.zip manageMembership.py > /dev/null
  cd ..
}
create()
{
  echo "Input your Okta Domain - "
  read -r domain
  echo "Input your Okta Token - "
  read -r token

  aws ssm put-parameter --name "okta-host" --value "${domain}" --type "SecureString"
  aws ssm put-parameter --name "okta-token" --value "${token}" --type "SecureString"

  aws cloudformation deploy --template-file cloudformation/infra.yaml --stack-name "${ManagedResourcePrefix}" --capabilities CAPABILITY_NAMED_IAM --parameter-overrides ParameterKey=BucketName,ParameterValue="${BUCKET_NAME}",ParameterKey=ManagedResourcePrefix,ParameterValue="${ManagedResourcePrefix}"

  aws lambda update-function-code --function-name accesss-manager-manageGroups --zip-file fileb://manageGroups.zip
  aws lambda update-function-code --function-name accesss-manager-manageMemberships --zip-file fileb://manageMemberships.zip

  aws s3 cp manageGroups.zip s3://$BUCKET_NAME/lambda/manageGroups.zip --sse aws:kms
  aws s3 cp manageMemberships.zip s3://$BUCKET_NAME/lambda/manageMemberships.zip --sse aws:kms

  aws s3 cp files/ s3://$BUCKET_NAME/files/ --recursive --sse aws:kms
}

update()
{
  aws cloudformation deploy --template-file cloudformation/infra.yaml --stack-name "${ManagedResourcePrefix}" --capabilities CAPABILITY_NAMED_IAM --parameter-overrides ParameterKey=BucketName,ParameterValue="${BUCKET_NAME}",ParameterKey=ManagedResourcePrefix,ParameterValue="${ManagedResourcePrefix}"

  aws lambda update-function-code --function-name accesss-manager-manageGroups --zip-file fileb://manageGroups.zip
  aws lambda update-function-code --function-name accesss-manager-manageMemberships --zip-file fileb://manageMemberships.zip

  aws s3 cp manageGroups.zip s3://$BUCKET_NAME/lambda/manageGroups.zip --sse aws:kms
  aws s3 cp manageMemberships.zip s3://$BUCKET_NAME/lambda/manageMemberships.zip --sse aws:kms
}

delete()
{
  echo "Inside delete"
  aws s3 rm s3://$BUCKET_NAME --recursive

  aws ssm delete-parameter --name "okta-host"
  aws ssm delete-parameter --name "okta-token"

  aws cloudformation delete-stack --stack-name "${ManagedResourcePrefix}"

  if [[ "$?" -eq 0 ]]; then
    echo "Stack deleted scuessfully"
  else
    echo "There was an issue(s) while deleting the CloudFormation stack."
  fi
}

showUsage()
{
  echo "Usage - $0 [options [paramters]]"
  echo ""
  echo "--profile or -p for the AWS Profile that is to be used to run this script"
  echo "--action or -a for action that is going to be performed. Valid actions - create, update, delete."
}

dir=$(pwd)
echo "Running from Directory: $dir"

# Actions - update-lambda, create, delete.

while [ -n "$1" ]; do
  case "$1" in
     --profile|-p)
         shift
         echo "Profile Entered: $1"
         PROFILE=$1
         ;;
      --action|-a)
        shift
        echo "Action Entered: $1"
        ACTION=$1
        ;;
     *)
        showUsage
        exit 1
        ;;
  esac
shift
done

if [ -z "$PROFILE" ]; then
  echo "AWS Profile is a required option."
  showUsage
  exit 1
fi

if [ -z "$ACTION" ]; then
  echo "action is a required option."
  showUsage
  exit 1
fi

case $ACTION in
  create)
    lambda
    create
    removetemp
    ;;
  update)
    lambda
    update
    removetemp
    ;;
  delete)
    delete
    ;;
  *)
    showUsage
    exit 1
    ;;
esac
