# Building the Lambda Function and Layer packages

This document describes how to build a Python Lambda Layer and Lambda deployment package using the official AWS Lambda Python 3.13 container image.

## Prerequisites

* Docker installed
* PowerShell (for ZIP creation on Windows)

---

## Steps to create Ingestion Service Lambda Package 

#### Step 1: Create a Temporary Working Directory

Create a temporary folder and copy the following files into it:

* [requirements.txt](./ingestion_service/requirements.txt)
* [ingestion_service_lambda.py](./ingestion_service/ingestion_service_lambda.py)

Example:

```text
temp/
├── requirements.txt
└── ingestion_service_lambda.py
```

---

#### Step 2: Pull the AWS Lambda Python 3.13 Base Image

```bash
docker pull amazon/aws-lambda-python:3.13
```

---

#### Step 3: Start a Container and Mount the Local Directory

Run the container and mount your local working directory to `/var/task` inside the container.

##### Linux/macOS

```bash
docker run -it --rm \
  -v /path/to/your/code:/var/task \
  --entrypoint bash \
  amazon/aws-lambda-python:3.13
```

##### Example Using Current Directory

```bash
docker run -it --rm \
  -v "/$(pwd)":/var/task \
  --entrypoint bash \
  amazon/aws-lambda-python:3.13
```

##### Verify the Mount

After the container starts, verify that the files are visible:

```bash
ls /var/task
```

Expected output should include:

```text
requirements.txt
ingestion_service_lambda.py
```

If the files are listed, the volume mount is working correctly.

---

#### Step 4: Install Dependencies into the Lambda Layer Structure

> **Important:** Execute the following commands from inside the running container.

Create the Lambda Layer directory structure:

```bash
mkdir -p /var/task/python/lib/python3.13/site-packages
```

Install all dependencies from `requirements.txt` into the layer directory:

```bash
pip install \
    --target /var/task/python/lib/python3.13/site-packages \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all: \
    --upgrade \
    -r /var/task/requirements.txt
```

Run the following command from inside the container:

```bash
chmod 777 -R *
```

After the dependency installation completes, exit the container:

```bash
exit
```

---

#### Step 5: Create ZIP Packages

Open PowerShell and run the following commands.

##### Create Lambda Layer Package

```powershell
Compress-Archive -Path "python" -DestinationPath "lambda-layer.zip" -Force
```

##### Create Lambda Function Package

```powershell
Compress-Archive -Path "ingestion_service_lambda.py" -DestinationPath "lambda.zip" -Force
```

This will generate:

```text
lambda-layer.zip
lambda.zip
```

---

## Create Authorization Lambda Package 

Following the similar steps mentioned above to build authorization lambda package.

Source files: 

* [requirements.txt](../lambda_authorizer/requirements.txt)
* [apigateway_authorizer_lambda.py](../lambda_authorizer/apigateway_authorizer_lambda.py)

Output files:

```text
authorizer-lambda-layer.zip
authorizer-lambda.zip
```

- 📁 File Organization

```
├── /ingestion_service/                  # lambda script and requirement.txt for data ingestion service
├── /lambda_authorizer/                  # lambda function and requirement.txt for authorizator lambda used by api gateway
```
 
   
