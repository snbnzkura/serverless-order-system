provider "aws" {
  region = "ap-south-1"
}

resource "aws_dynamodb_table" "orders_table" {
  name           = "Orders"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/app.py"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_iam_role" "lambda_role" {
  name = "order_system_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "dynamodb_access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Scan",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_lambda_function" "order_receiver" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "OrderReceiver"
  role             = aws_iam_role.lambda_role.arn
  handler          = "app.lambda_handler"
  runtime          = "python3.9"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
}

# api gateway rest api
resource "aws_api_gateway_rest_api" "order_api" {
  name        = "OrderAPI"
  description = "API Gateway for Order System"
}

# /orders resource
resource "aws_api_gateway_resource" "orders" {
  rest_api_id = aws_api_gateway_rest_api.order_api.id
  parent_id   = aws_api_gateway_rest_api.order_api.root_resource_id
  path_part   = "orders"
}

# /orders/{order_id} resource
resource "aws_api_gateway_resource" "order_by_id" {
  rest_api_id = aws_api_gateway_rest_api.order_api.id
  parent_id   = aws_api_gateway_resource.orders.id
  path_part   = "{order_id}"
}

# post method for /orders (create order)
resource "aws_api_gateway_method" "create_order" {
  rest_api_id   = aws_api_gateway_rest_api.order_api.id
  resource_id   = aws_api_gateway_resource.orders.id
  http_method   = "POST"
  authorization = "NONE"
}

# get method for /orders (list all orders)
resource "aws_api_gateway_method" "list_orders" {
  rest_api_id   = aws_api_gateway_rest_api.order_api.id
  resource_id   = aws_api_gateway_resource.orders.id
  http_method   = "GET"
  authorization = "NONE"
}

# get method for /orders/{order_id} (get single order)
resource "aws_api_gateway_method" "get_order" {
  rest_api_id   = aws_api_gateway_rest_api.order_api.id
  resource_id   = aws_api_gateway_resource.order_by_id.id
  http_method   = "GET"
  authorization = "NONE"
}

# put method for /orders/{order_id} (update order)
resource "aws_api_gateway_method" "update_order" {
  rest_api_id   = aws_api_gateway_rest_api.order_api.id
  resource_id   = aws_api_gateway_resource.order_by_id.id
  http_method   = "PUT"
  authorization = "NONE"
}

# delete method for /orders/{order_id} (delete order)
resource "aws_api_gateway_method" "delete_order" {
  rest_api_id   = aws_api_gateway_rest_api.order_api.id
  resource_id   = aws_api_gateway_resource.order_by_id.id
  http_method   = "DELETE"
  authorization = "NONE"
}

# lambda integrations
resource "aws_api_gateway_integration" "create_order_integration" {
  rest_api_id             = aws_api_gateway_rest_api.order_api.id
  resource_id             = aws_api_gateway_resource.orders.id
  http_method             = aws_api_gateway_method.create_order.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.order_receiver.invoke_arn
}

resource "aws_api_gateway_integration" "list_orders_integration" {
  rest_api_id             = aws_api_gateway_rest_api.order_api.id
  resource_id             = aws_api_gateway_resource.orders.id
  http_method             = aws_api_gateway_method.list_orders.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.order_receiver.invoke_arn
}

resource "aws_api_gateway_integration" "get_order_integration" {
  rest_api_id             = aws_api_gateway_rest_api.order_api.id
  resource_id             = aws_api_gateway_resource.order_by_id.id
  http_method             = aws_api_gateway_method.get_order.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.order_receiver.invoke_arn
}

resource "aws_api_gateway_integration" "update_order_integration" {
  rest_api_id             = aws_api_gateway_rest_api.order_api.id
  resource_id             = aws_api_gateway_resource.order_by_id.id
  http_method             = aws_api_gateway_method.update_order.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.order_receiver.invoke_arn
}

resource "aws_api_gateway_integration" "delete_order_integration" {
  rest_api_id             = aws_api_gateway_rest_api.order_api.id
  resource_id             = aws_api_gateway_resource.order_by_id.id
  http_method             = aws_api_gateway_method.delete_order.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.order_receiver.invoke_arn
}

# lambda permission for api gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.order_receiver.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.order_api.execution_arn}/*/*"
}

# api gateway deployment
resource "aws_api_gateway_deployment" "order_api_deployment" {
  depends_on = [
    aws_api_gateway_integration.create_order_integration,
    aws_api_gateway_integration.list_orders_integration,
    aws_api_gateway_integration.get_order_integration,
    aws_api_gateway_integration.update_order_integration,
    aws_api_gateway_integration.delete_order_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.order_api.id
  stage_name  = "prod"
}

# outputs
output "api_endpoint" {
  value       = "${aws_api_gateway_deployment.order_api_deployment.invoke_url}/orders"
  description = "API Gateway endpoint URL"
}

output "lambda_function_name" {
  value       = aws_lambda_function.order_receiver.function_name
  description = "Lambda function name"
}

output "dynamodb_table_name" {
  value       = aws_dynamodb_table.orders_table.name
  description = "DynamoDB table name"
}
