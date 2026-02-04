# Serverless Order System

A scalable, event-driven order processing system built with AWS Lambda, DynamoDB, and Terraform for infrastructure as code.

**Repository**: [Harshad-Gore/serverless-order-system](https://github.com/Harshad-Gore/serverless-order-system)

---

## Architecture Overview

This project implements a serverless order management system leveraging AWS cloud services for high availability and cost efficiency.

### Key Components

- **AWS Lambda**: Serverless compute for order processing
- **Amazon DynamoDB**: NoSQL database for order storage
- **Terraform**: Infrastructure as code for reproducible deployments
- **Python 3.x**: Lambda function runtime

---

## Features

- **RESTful API**: Full CRUD operations via API Gateway
- **Order Management**: Create, read, update, and delete orders
- **Status Tracking**: Track orders through PENDING → PROCESSING → COMPLETED/CANCELLED
- **Order Filtering**: List orders with optional status filtering
- **Customer Information**: Store customer name and email with orders
- **Serverless Architecture**: Auto-scaling with zero infrastructure management
- **Pay-per-Request Pricing**: Cost-effective DynamoDB billing model
- **Infrastructure as Code**: Version-controlled infrastructure deployment

---

## Project Structure

```
serverless-order-system/
├── src/
│   └── app.py              # lambda function handler
├── infra/
│   ├── main.tf             # terraform infrastructure definition
│   ├── terraform.tfstate   # terraform state file (gitignored)
│   └── terraform.tfstate.backup
├── tests/                  # test suite directory
├── requirements.txt        # python dependencies
├── .gitignore             # git ignore rules
└── readme.md              # project documentation
```

---

## Prerequisites

- **AWS Account** with appropriate permissions
- **AWS CLI** configured with credentials
- **Terraform** v1.0+ installed
- **Python** 3.8+ installed
- **Boto3** AWS SDK for Python

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Harshad-Gore/serverless-order-system.git
cd serverless-order-system
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure AWS Credentials

```bash
aws configure
```

Enter your AWS Access Key ID, Secret Access Key, and preferred region.

---

## Deployment

### Infrastructure Deployment

Navigate to the infrastructure directory and deploy using Terraform:

```bash
cd infra
terraform init
terraform plan
terraform apply
```

Review the planned changes and confirm with `yes` when prompted.

### Get API Endpoint

After deployment, get your API endpoint URL:

```bash
terraform output api_endpoint
```

This will display your API Gateway URL. Save this for testing.

---

## API Usage

Your API supports the following operations:

- **POST /orders** - Create a new order
- **GET /orders** - List all orders (with optional `?status=PENDING` filter)
- **GET /orders/{order_id}** - Get a specific order
- **PUT /orders/{order_id}** - Update order status
- **DELETE /orders/{order_id}** - Delete an order


### Quick Test

Create an order:
```bash
curl -X POST https://your-api-id.execute-api.ap-south-1.amazonaws.com/prod/orders \
  -H "Content-Type: application/json" \
  -d '{"item":"laptop","quantity":2,"customer_name":"john doe"}'
```

---

## AWS Free Tier

This project is designed to stay within AWS free tier limits:
- **API Gateway**: 1M requests/month (12 months free)
- **Lambda**: 1M requests/month (always free)
- **DynamoDB**: 25GB storage (always free)

---

## Clean Up

To avoid any charges, destroy the infrastructure when done:

```bash
cd infra
terraform destroy
```

Confirm with `yes` when prompted.

---

### Verify Deployment

After successful deployment, Terraform will output the Lambda function ARN and DynamoDB table name.

---

## Usage

### Order Schema

```json
{
  "item": "Product Name",
  "quantity": 5
}
```

### Lambda Function Response

**Success (200)**:
```json
{
  "message": "Order placed",
  "order_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error (500)**:
```json
{
  "error": "Error description"
}
```

### Testing Locally

Invoke the Lambda function using AWS CLI:

```bash
aws lambda invoke \
  --function-name order_system_lambda \
  --payload '{"body": "{\"item\": \"Laptop\", \"quantity\": 2}"}' \
  response.json

cat response.json
```

---

## DynamoDB Table Structure

**Table Name**: `Orders`

| Attribute   | Type   | Description                |
|-------------|--------|----------------------------|
| order_id    | String | Unique order identifier    |
| item        | String | Product or item name       |
| quantity    | Number | Quantity ordered           |
| status      | String | Order status (PENDING)     |

---

## IAM Permissions

The Lambda function has the following permissions:

- `dynamodb:PutItem` - Write orders to DynamoDB
- `dynamodb:GetItem` - Read orders from DynamoDB
- `logs:CreateLogGroup` - Create CloudWatch log groups
- `logs:CreateLogStream` - Create CloudWatch log streams
- `logs:PutLogEvents` - Write logs to CloudWatch

---

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Features

1. Create a new branch: `git checkout -b feature/new-feature`
2. Make your changes in `src/app.py`
3. Update infrastructure in `infra/main.tf` if needed
4. Test thoroughly before deployment
5. Submit a pull request

---

## Cleanup

To destroy all resources and avoid ongoing charges:

```bash
cd infra
terraform destroy
```

Confirm with `yes` when prompted.

---

## Configuration

### AWS Region

Default region is set to `ap-south-1` (Mumbai). To change:

1. Update the `region` in [infra/main.tf](infra/main.tf#L2)
2. Reconfigure AWS CLI: `aws configure`

### DynamoDB Configuration

The table uses **PAY_PER_REQUEST** billing mode for cost optimization. To change to provisioned capacity, modify the `billing_mode` in [infra/main.tf](infra/main.tf#L6).

---

## Monitoring

### CloudWatch Logs

View Lambda execution logs:

```bash
aws logs tail /aws/lambda/order_system_lambda --follow
```

### DynamoDB Metrics

Monitor table metrics in the AWS Console under DynamoDB > Tables > Orders > Metrics.

---

## Security Best Practices

- Never commit AWS credentials or sensitive data
- Use IAM roles with least privilege principle
- Enable DynamoDB encryption at rest
- Implement API Gateway with authentication for production
- Review CloudTrail logs regularly

---

## Troubleshooting

### Lambda Function Errors

Check CloudWatch Logs for detailed error messages:

```bash
aws logs describe-log-streams \
  --log-group-name /aws/lambda/order_system_lambda
```

### Terraform State Issues

If state becomes corrupted:

```bash
terraform state list
terraform state pull > backup.tfstate
```

### DynamoDB Access Denied

Verify IAM role permissions are correctly attached to the Lambda function.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contact

**Discord**: raybyte

