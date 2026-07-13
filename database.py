"""
database.py — DynamoDB persistence for chat history
"""
import json
import boto3
from datetime import datetime
from config import AWS_REGION, DYNAMO_TABLE

_table = None

def get_table():
    global _table
    if _table is not None:
        return _table
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        existing = [t.name for t in dynamodb.tables.all()]
        if DYNAMO_TABLE not in existing:
            t = dynamodb.create_table(
                TableName=DYNAMO_TABLE,
                KeySchema=[
                    {'AttributeName': 'session_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp',  'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'session_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp',  'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            t.wait_until_exists()
            _table = t
        else:
            _table = dynamodb.Table(DYNAMO_TABLE)
        return _table
    except Exception:
        return None


def save_chat(session_id: str, title: str, messages: list):
    t = get_table()
    if not t:
        return
    try:
        t.put_item(Item={
            'session_id': session_id,
            'timestamp':  'latest',
            'title':      title,
            'messages':   json.dumps(messages, ensure_ascii=False),
            'date_label': datetime.utcnow().strftime('%b %d')
        })
    except Exception:
        pass


def load_all_chats() -> list:
    t = get_table()
    if not t:
        return []
    try:
        items = t.scan().get('Items', [])
        seen, unique = {}, []
        for item in items:
            sid = item.get('session_id', '')
            if sid not in seen:
                seen[sid] = True
                unique.append(item)
        return sorted(unique, key=lambda x: x.get('date_label', ''), reverse=True)[:30]
    except Exception:
        return []


def load_chat(session_id: str) -> list:
    t = get_table()
    if not t:
        return []
    try:
        items = t.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('session_id').eq(session_id)
        ).get('Items', [])
        return json.loads(items[0].get('messages', '[]')) if items else []
    except Exception:
        return []
