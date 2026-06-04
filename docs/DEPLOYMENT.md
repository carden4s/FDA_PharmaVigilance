# Deployment Guide

Production deployment instructions for FDA PharmaVigilance platform.

## Deployment Architectures

### Option 1: Self-Hosted (Recommended for Enterprise)

```
┌─────────────────────────────────────────┐
│      Local or On-Premise Servers        │
│  ├─ Python Ingestion (VM/Container)    │
│  ├─ dbt Scheduler (VM/Container)       │
│  └─ Streamlit App (VM/Container)       │
└──────────────┬──────────────────────────┘
               │
        ┌──────▼──────────────────┐
        │   Snowflake Cloud       │
        │  (Bronze, Silver, Gold) │
        └──────────────────────────┘
```

### Option 2: AWS (Recommended for Cloud)

```
┌────────────────────────────────────────────────┐
│            AWS Infrastructure                  │
│  ├─ Lambda: Ingestion (scheduled)              │
│  ├─ Glue: dbt transformations                  │
│  ├─ ECS: Streamlit dashboard                   │
│  └─ CloudWatch: Monitoring                     │
└────────────────┬─────────────────────────────┘
                 │
          ┌──────▼──────────────────┐
          │   Snowflake Cloud       │
          │  (Bronze, Silver, Gold) │
          └──────────────────────────┘
```

## Production Checklist

- [ ] Credentials securely managed (AWS Secrets Manager, Azure Key Vault)
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] Error notifications enabled
- [ ] Performance optimization complete
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Team training completed
- [ ] Disaster recovery plan established
- [ ] Compliance review completed

## AWS Deployment

### Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured
- IAM roles created
- VPC configured

### 1. Set Up S3 for Code Storage

```bash
# Create S3 bucket
aws s3 mb s3://pharma-vigilance-prod-code

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket pharma-vigilance-prod-code \
    --versioning-configuration Status=Enabled
```

### 2. Create IAM Roles

```bash
# Lambda execution role
aws iam create-role \
    --role-name pharma-lambda-ingestion-role \
    --assume-role-policy-document file://trust-policy.json

# Permissions policy
aws iam put-role-policy \
    --role-name pharma-lambda-ingestion-role \
    --policy-name pharma-lambda-policy \
    --policy-document file://lambda-policy.json
```

### 3. Deploy Ingestion via Lambda

```bash
# Package code
cd ingestion
pip install -r requirements.txt -t package/
cd package
zip -r ../lambda_function.zip .
cd ..
zip -r lambda_function.zip src/

# Upload to AWS
aws s3 cp lambda_function.zip s3://pharma-vigilance-prod-code/

# Create function
aws lambda create-function \
    --function-name pharma-fda-ingestion \
    --runtime python3.11 \
    --role arn:aws:iam::ACCOUNT_ID:role/pharma-lambda-ingestion-role \
    --handler src.main.lambda_handler \
    --s3-bucket pharma-vigilance-prod-code \
    --s3-key lambda_function.zip \
    --timeout 900 \
    --memory-size 1024 \
    --environment file://env-vars.json
```

### 4. Schedule Daily Runs with EventBridge

```bash
# Create schedule rule
aws events put-rule \
    --name pharma-daily-ingestion \
    --schedule-expression 'cron(0 2 * * ? *)'  # 2 AM UTC daily

# Add Lambda as target
aws events put-targets \
    --rule pharma-daily-ingestion \
    --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT_ID:function:pharma-fda-ingestion"

# Grant EventBridge permission
aws lambda add-permission \
    --function-name pharma-fda-ingestion \
    --statement-id AllowEventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:REGION:ACCOUNT_ID:rule/pharma-daily-ingestion
```

### 5. Deploy Streamlit via ECS

Create `ecs-task-definition.json`:

```json
{
  "family": "pharma-streamlit-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "streamlit",
      "image": "AWS_ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/pharma-streamlit:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "hostPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "SNOWFLAKE_ACCOUNT", "value": "xyzabc.us-east-1"},
        {"name": "ENV", "value": "production"}
      ],
      "secrets": [
        {
          "name": "SNOWFLAKE_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:snowflake/password"
        }
      ]
    }
  ]
}
```

Deploy:

```bash
# Push image to ECR
aws ecr create-repository --repository-name pharma-streamlit
aws ecr get-login-password --region REGION | docker login --username AWS --password-stdin AWS_ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com
docker build -t pharma-streamlit .
docker tag pharma-streamlit:latest AWS_ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/pharma-streamlit:latest
docker push AWS_ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/pharma-streamlit:latest

# Create ECS cluster
aws ecs create-cluster --cluster-name pharma-prod

# Create service
aws ecs create-service \
    --cluster pharma-prod \
    --service-name pharma-streamlit \
    --task-definition pharma-streamlit-app \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### 6. Set Up CloudWatch Monitoring

```bash
# Create custom metric for ingestion
aws cloudwatch put-metric-alarm \
    --alarm-name pharma-ingestion-failure \
    --alarm-description "Alert on ingestion failures" \
    --metric-name IngestionFailures \
    --namespace Pharma \
    --statistic Sum \
    --period 300 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold \
    --evaluation-periods 1

# Create SNS topic for alerts
aws sns create-topic --name pharma-prod-alerts

# Subscribe email
aws sns subscribe \
    --topic-arn arn:aws:sns:REGION:ACCOUNT_ID:pharma-prod-alerts \
    --protocol email \
    --notification-endpoint ops@example.com
```

## Docker Deployment

### Build Docker Images

Create `Dockerfile.ingestion`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ingestion/src/ src/

# Set environment
ENV ENV=production

# Run ingestion
CMD ["python", "src/main.py"]
```

Create `Dockerfile.streamlit`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY streamlit/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY streamlit/ .

# Create streamlit config directory
RUN mkdir -p .streamlit

# Copy streamlit config
COPY streamlit/.streamlit/config.toml .streamlit/

# Expose port
EXPOSE 8501

# Run streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"]
```

Build:

```bash
docker build -f Dockerfile.ingestion -t pharma-ingestion:latest .
docker build -f Dockerfile.streamlit -t pharma-streamlit:latest .
```

### Docker Compose for Local Stack

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  ingestion:
    build:
      context: .
      dockerfile: Dockerfile.ingestion
    environment:
      SNOWFLAKE_ACCOUNT: ${SNOWFLAKE_ACCOUNT}
      SNOWFLAKE_USER: ${SNOWFLAKE_USER}
      SNOWFLAKE_PASSWORD: ${SNOWFLAKE_PASSWORD}
      LOG_LEVEL: INFO
    schedule: "0 2 * * *"  # Daily 2 AM

  dbt:
    image: ghcr.io/dbt-labs/dbt-snowflake:latest
    environment:
      SNOWFLAKE_ACCOUNT: ${SNOWFLAKE_ACCOUNT}
      SNOWFLAKE_USER: ${SNOWFLAKE_USER}
      SNOWFLAKE_PASSWORD: ${SNOWFLAKE_PASSWORD}
    volumes:
      - ./dbt:/dbt
    working_dir: /dbt
    command: dbt run
    depends_on:
      - ingestion

  streamlit:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    ports:
      - "8501:8501"
    environment:
      SNOWFLAKE_ACCOUNT: ${SNOWFLAKE_ACCOUNT}
      SNOWFLAKE_USER: ${SNOWFLAKE_USER}
      SNOWFLAKE_PASSWORD: ${SNOWFLAKE_PASSWORD}
    depends_on:
      - dbt
```

Run:

```bash
docker-compose up
```

## Kubernetes Deployment

Create `ingestion-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pharma-ingestion
  namespace: pharma
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pharma-ingestion
  template:
    metadata:
      labels:
        app: pharma-ingestion
    spec:
      containers:
      - name: ingestion
        image: pharma-ingestion:latest
        env:
        - name: SNOWFLAKE_ACCOUNT
          valueFrom:
            secretKeyRef:
              name: snowflake-creds
              key: account
        - name: SNOWFLAKE_USER
          valueFrom:
            secretKeyRef:
              name: snowflake-creds
              key: user
        - name: SNOWFLAKE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: snowflake-creds
              key: password
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pharma-ingestion-schedule
  namespace: pharma
spec:
  schedule: "0 2 * * *"  # 2 AM UTC daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: ingestion
            image: pharma-ingestion:latest
          restartPolicy: OnFailure
```

Deploy:

```bash
kubectl apply -f ingestion-deployment.yaml
```

## CI/CD Pipeline

Create `.github/workflows/deploy-prod.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run tests
        run: |
          pip install -r ingestion/requirements.txt
          pytest ingestion/tests/
      
      - name: dbt tests
        run: |
          cd dbt
          dbt deps
          dbt test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and push Docker images
        run: |
          docker build -f Dockerfile.ingestion -t pharma-ingestion:${{ github.sha }} .
          docker push $ECR_REGISTRY/pharma-ingestion:${{ github.sha }}
      
      - name: Deploy to AWS Lambda
        run: |
          # Lambda deployment steps
      
      - name: Deploy to ECS
        run: |
          # ECS deployment steps
```

## Monitoring & Alerting

### CloudWatch Dashboards

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Create dashboard
dashboard_body = {
    'widgets': [
        {
            'type': 'metric',
            'properties': {
                'metrics': [
                    ['Pharma', 'IngestionDuration', {'stat': 'Average'}],
                    ['.', 'IngestionFailures', {'stat': 'Sum'}],
                    ['.', 'RecordsLoaded', {'stat': 'Sum'}]
                ],
                'period': 300,
                'stat': 'Average',
                'region': 'us-east-1',
                'title': 'FDA Ingestion Metrics'
            }
        }
    ]
}

cloudwatch.put_dashboard(
    DashboardName='pharma-prod',
    DashboardBody=json.dumps(dashboard_body)
)
```

### Alerts

- Ingestion failure rate > 0%
- Data freshness > 24 hours
- Query latency > 5 seconds
- Error rate > 1%
- Snowflake warehouse offline

## Backup & Disaster Recovery

### Snowflake Configuration

```sql
-- Enable Time Travel (30 days)
ALTER DATABASE pharma_db SET DATA_RETENTION_TIME_IN_DAYS = 30;

-- Create backup schema
CREATE SCHEMA backup;

-- Backup critical tables
CREATE TABLE backup.raw_fda_adverse_events AS
  SELECT * FROM raw_fda_adverse_events
  WHERE loaded_at >= CURRENT_DATE - 7;
```

### AWS Backup

```bash
# Create backup vault
aws backup create-backup-vault --backup-vault-name pharma-backups

# Create backup plan
aws backup create-backup-plan --backup-plan file://backup-plan.json
```

## Performance Tuning

### Snowflake Optimization

```sql
-- Create clustering keys
ALTER TABLE raw_fda_adverse_events
  CLUSTER BY (drug_name, loaded_at);

-- Create search optimization
ALTER TABLE agg_drug_safety_profile
  ADD SEARCH OPTIMIZATION ON (drug_name);

-- Analyze query performance
EXPLAIN SELECT * FROM agg_drug_safety_profile WHERE drug_name = 'Aspirin';
```

### dbt Optimization

```yaml
# dbt_project.yml
models:
  gold:
    materialized: table
    pre-hook: "{{ log('Building ' ~ this.name, info=true) }}"
    indexes:
      - columns: [drug_name]
        type: clustering
```

## Rollback Procedures

### Application Rollback

```bash
# If new version has issues
aws lambda update-function-code \
    --function-name pharma-fda-ingestion \
    --s3-bucket pharma-vigilance-prod-code \
    --s3-key lambda_function_v1.0.zip
```

### Data Rollback

```sql
-- Restore from Time Travel
CREATE TABLE raw_fda_adverse_events AS
SELECT * FROM raw_fda_adverse_events
  AT (TIMESTAMP => '2026-06-02'::timestamp_ntz)
WHERE loaded_at >= '2026-06-02';
```

## Post-Deployment

1. ✅ Verify ingestion runs successfully
2. ✅ Check dbt transformations complete
3. ✅ Validate dashboard shows data
4. ✅ Test alerting system
5. ✅ Review logs for errors
6. ✅ Get team sign-off
7. ✅ Document any manual steps
8. ✅ Schedule training if needed

## Support & Troubleshooting

See [SETUP.md](./SETUP.md) for common issues.

---

**Last Updated**: June 3, 2026
