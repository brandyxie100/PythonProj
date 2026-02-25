"""
xw2.py
"""

import redis
import uuid
import json

R = redis.Redis()

def process_payment(request):
    token = request.header.get('Idempotency-Key')
    if not token:
        return Response({'error': 'Missing idempotency key'}, status=400)

    # check whether token already was tackled
    if R.exists(f'idempotency:{token}'):
        return Response({'error': 'Idempotency key already processed'}, status=400)
    
    # deal with payment logic
    result = process_payment(request.data)
    
    # store the result and set the expiration time
    if result['status'] == 'success':
        R.set(f'idempotency:{token}', 'success', ex=3600)
        return Response(result, status=200)
    else:
        R.setex(f'idempotency:{token}', 86400, json.dumps(result))
        return Response(result, status=400)

    # generate a new token
    token = str(uuid.uuid4())
    R.set(f'idempotency:{token}', 'processing', ex=3600)

    # process the payment
    result = process_payment(request.data)
    