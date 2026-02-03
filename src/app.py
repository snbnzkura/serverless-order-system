import json
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Orders')

def lambda_handler(event, context):
    try:
        if 'body' in event:
            body = json.loads(event['body'])
        else:
            body = event

        order_id = str(uuid.uuid4())

        item = {
            'order_id': order_id,
            'item': body.get('item', 'unknown'),
            'quantity': body.get('quantity', 1),
            'status': 'PENDING'
        }

        table.put_item(Item=item)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Order placed', 'order_id': order_id})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }