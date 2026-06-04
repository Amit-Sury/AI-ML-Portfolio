# AWS Cloudformation stacks

- 📁 File Organization

```
├── cfn-infra-stack.yaml            # Creates infrastructure resources (IAM roles, cognito, APIGateway, VPC Link) 
├── cfn-integration-stack.yaml      # Creates NLB ApiGw Integration, APIGateway route and stage 
├── cfn-s3-stack.yaml               # Creates lambda-artifacts s3 bucket 
├── cfn-services-stack.yaml         # Creates OS Serverless Collection and lambda 
```
