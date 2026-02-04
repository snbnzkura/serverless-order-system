import json
import boto3
import uuid
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Orders')

# helper function to convert decimal to int/float for json serialization
def decimal_to_number(obj):
    if isinstance(obj, list):
        return [decimal_to_number(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_number(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj

def lambda_handler(event, context):
    try:
        http_method = event.get('httpMethod')
        path_parameters = event.get('pathParameters') or {}
        
        # route to appropriate handler based on http method
        if http_method == 'POST':
            return create_order(event)
        elif http_method == 'GET' and 'order_id' in path_parameters:
            return get_order(path_parameters['order_id'])
        elif http_method == 'GET':
            return list_orders(event)
        elif http_method == 'PUT':
            return update_order(event, path_parameters['order_id'])
        elif http_method == 'DELETE':
            return delete_order(path_parameters['order_id'])
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'unsupported method'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# create new order
def create_order(event):
    body = json.loads(event['body'])
    
    # validate required fields
    if 'item' not in body or 'quantity' not in body:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'item and quantity are required'})
        }
    
    order_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat() + 'Z'
    
    item = {
        'order_id': order_id,
        'item': body['item'],
        'quantity': body['quantity'],
        'status': 'PENDING',
        'customer_name': body.get('customer_name', 'anonymous'),
        'customer_email': body.get('customer_email', ''),
        'created_at': created_at
    }
    
    table.put_item(Item=item)
    
    return {
        'statusCode': 201,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': 'order created successfully',
            'order': decimal_to_number(item)
        })
    }

# get single order by id
def get_order(order_id):
    response = table.get_item(Key={'order_id': order_id})
    
    if 'Item' not in response:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'order not found'})
        }
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'order': decimal_to_number(response['Item'])
        })
    }

# list all orders with optional filtering
def list_orders(event):
    query_params = event.get('queryStringParameters') or {}
    
    # scan table (for production, consider pagination)
    response = table.scan()
    items = response.get('Items', [])
    
    # filter by status if provided
    status_filter = query_params.get('status')
    if status_filter:
        items = [item for item in items if item.get('status') == status_filter.upper()]
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'count': len(items),
            'orders': decimal_to_number(items)
        })
    }

# update order status
def update_order(event, order_id):
    body = json.loads(event['body'])
    
    # validate status field
    if 'status' not in body:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'status field is required'})
        }
    
    allowed_statuses = ['PENDING', 'PROCESSING', 'COMPLETED', 'CANCELLED', 'EXPIRED']
    if body['status'].upper() not in allowed_statuses:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': f'status must be one of: {", ".join(allowed_statuses)}'
            })
        }
    
    # check if order exists
    existing = table.get_item(Key={'order_id': order_id})
    if 'Item' not in existing:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'order not found'})
        }
    
    # update the order
    response = table.update_item(
        Key={'order_id': order_id},
        UpdateExpression='SET #status = :status',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':status': body['status'].upper()},
        ReturnValues='ALL_NEW'
    )
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': 'order updated successfully',
            'order': decimal_to_number(response['Attributes'])
        })
    }

# delete order
def delete_order(order_id):
    # check if order exists
    existing = table.get_item(Key={'order_id': order_id})
    if 'Item' not in existing:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'order not found'})
        }
    
    table.delete_item(Key={'order_id': order_id})
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'message': 'order deleted successfully',
            'order_id': order_id
        })
    }