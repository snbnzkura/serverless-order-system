import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Orders')

EXPIRY_HOURS = 24

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
    """
    scheduled lambda function to expire old pending orders
    triggered by eventbridge rule every hour
    """
    try:
        expired_count = 0
        expired_orders = []
        
        # calculate the cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=EXPIRY_HOURS)
        cutoff_timestamp = cutoff_time.isoformat() + 'Z'
        
        print(f"checking for pending orders older than {cutoff_timestamp}")
        
        # scan for pending orders
        response = table.scan(
            FilterExpression='#status = :pending',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':pending': 'PENDING'}
        )
        
        pending_orders = response.get('Items', [])
        print(f"found {len(pending_orders)} pending orders")
        
        for order in pending_orders:
            order_id = order['order_id']
            created_at = order.get('created_at', '')
            
            # skip orders without timestamp (legacy orders)
            if not created_at:
                print(f"skipping order {order_id} - no created_at timestamp")
                continue
            
            # check if order is older than threshold
            if created_at < cutoff_timestamp:
                # expire the order
                table.update_item(
                    Key={'order_id': order_id},
                    UpdateExpression='SET #status = :expired, expired_at = :expired_at',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':expired': 'EXPIRED',
                        ':expired_at': datetime.utcnow().isoformat() + 'Z'
                    }
                )
                
                expired_count += 1
                expired_orders.append({
                    'order_id': order_id,
                    'item': order.get('item'),
                    'created_at': created_at
                })
                
                print(f"expired order {order_id} (created: {created_at})")
        
        result = {
            'message': 'order expiry check completed',
            'checked_at': datetime.utcnow().isoformat() + 'Z',
            'total_pending_checked': len(pending_orders),
            'orders_expired': expired_count,
            'expired_order_ids': [o['order_id'] for o in expired_orders]
        }
        
        print(json.dumps(result))
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        print(f"error during order expiry check: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
