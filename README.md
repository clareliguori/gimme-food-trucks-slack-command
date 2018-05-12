# /gimmefoodtrucks Slack Command
Demo serverless application: Slack command that returns that current day's local food trucks (/gimmefoodtrucks).

Configure the slash command in Slack:
1. Navigate to https://<your-team-domain>.slack.com/apps
1. Search for and select "Slash Commands".
1. Click "Add Configuration".
1. Enter a name for your command (/gimmefoodtrucks) and click "Add Slash Command Integration".
1. Copy the token string from the integration settings.

Don't close the browser page; you'll need to enter the URL for the command later.

Store the token in Parameter Store:
```
aws ssm put-parameter --name gimme-food-trucks-token --type SecureString --value <token>
```

Create continuous deployment resources:
```
aws cloudformation create-stack --stack-name gimme-food-trucks --template-body file://continuous-deployment.yml --parameters ParameterKey=Address,ParameterValue="2111 7th Ave" ParameterKey=Token,ParameterValue=gimme-food-trucks-token --capabilities CAPABILITY_NAMED_IAM

aws cloudformation wait stack-create-complete --stack-name gimme-food-trucks
```

Push to the newly created git repository:
```
git config --global credential.helper '!aws codecommit credential-helper $@'

git config --global credential.UseHttpPath true

git remote add app `aws cloudformation describe-stacks --stack-name gimme-food-trucks --query 'Stacks[0].Outputs[?OutputKey==\`RepositoryCloneUrl\`].OutputValue' --output text`

git push app master
```

Go to the pipeline console page, and wait for the pipeline to finish deploying:
```
aws cloudformation describe-stacks --stack-name gimme-food-trucks --query 'Stacks[0].Outputs[?OutputKey==`PipelineConsoleUrl`].OutputValue' --output text
```

Get the URL of the newly deployed application:
```
aws cloudformation describe-stacks --stack-name gimme-food-trucks-application --query 'Stacks[0].Outputs[?OutputKey==`SlackURL`].OutputValue' --output text
```

Go back to the Slash Command integration at slack.com.  Enter the URL of the deployed application in the URL field under Integration Settings.

In your Slack room, try it out!
```
/gimmefoodtrucks
```

## Local testing

API:
```
AWS_REGION="eu-central-1" ADDRESS="2111 7th Ave" TOKEN_PARAMETER="gimme-food-trucks-token" DATA_TABLE="blah" sam local start-api

export TOKEN=<token>

curl --header "application/x-www-form-urlencoded" --request POST --data "token=$TOKEN&team_id=T0001&team_domain=example&channel_id=C2147483705&channel_name=test&user_id=U2147483697&user_name=Steve&command=/gimmefoodtrucks" http://localhost:3000/slack

```

Canary:
```
echo '{"body": "token='$TOKEN'&team_id=T0001&team_domain=example&channel_id=C2147483705&channel_name=test&user_id=U2147483697&user_name=Steve&command=/gimmefoodtrucks", "trigger": "canary" }' | AWS_REGION="eu-central-1" ADDRESS="2111 7th Ave" TOKEN_PARAMETER="gimme-food-trucks-token" DATA_TABLE="blah" sam local invoke "SlackCommand"
```
