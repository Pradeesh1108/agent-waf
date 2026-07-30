import os
import time
import uuid
import boto3
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
from .models import ToolCallRequest, RuleResult

DYNAMODB_TABLE_NAME = os.environ.get("DYNAMODB_TABLE_NAME")
USE_IN_MEMORY = not bool(DYNAMODB_TABLE_NAME)

class StateManager:
    def __init__(self):
        if not USE_IN_MEMORY:
            self.dynamodb = boto3.resource('dynamodb')
            self.table = self.dynamodb.Table(DYNAMODB_TABLE_NAME)
        else:
            self._in_memory_logs = []
            self._in_memory_rate_counters = {}
            self._in_memory_session_sequence = {}

    def get_rate_count(self, agent_id: str, tool: str, window_seconds: int) -> int:
        current_time = int(time.time())
        window_start = current_time - window_seconds
        
        if USE_IN_MEMORY:
            key = f"{agent_id}::{tool}"
            if key not in self._in_memory_rate_counters:
                self._in_memory_rate_counters[key] = []
            self._in_memory_rate_counters[key] = [t for t in self._in_memory_rate_counters[key] if t >= window_start]
            return len(self._in_memory_rate_counters[key])
        else:
            bucket = current_time // window_seconds
            pk = f"RATE::{agent_id}::{tool}::{bucket}"
            try:
                response = self.table.get_item(Key={'PK': pk, 'SK': 'COUNT'})
                if 'Item' in response:
                    return int(response['Item'].get('count', 0))
                return 0
            except ClientError as e:
                print(f"DynamoDB error: {e}")
                return 0
            
    def increment_rate_count(self, agent_id: str, tool: str, window_seconds: int):
        current_time = int(time.time())
        if USE_IN_MEMORY:
            key = f"{agent_id}::{tool}"
            if key not in self._in_memory_rate_counters:
                self._in_memory_rate_counters[key] = []
            self._in_memory_rate_counters[key].append(current_time)
        else:
            bucket = current_time // window_seconds
            pk = f"RATE::{agent_id}::{tool}::{bucket}"
            try:
                self.table.update_item(
                    Key={'PK': pk, 'SK': 'COUNT'},
                    UpdateExpression="SET #cnt = if_not_exists(#cnt, :start) + :inc",
                    ExpressionAttributeNames={'#cnt': 'count'},
                    ExpressionAttributeValues={':start': 0, ':inc': 1},
                    ReturnValues="UPDATED_NEW"
                )
            except ClientError as e:
                print(f"DynamoDB error: {e}")

    def get_session_sequence(self, agent_id: str, session_id: str) -> List[str]:
        if USE_IN_MEMORY:
            key = f"{agent_id}::{session_id}"
            return self._in_memory_session_sequence.get(key, [])
        else:
            pk = f"SEQ::{agent_id}::{session_id}"
            try:
                response = self.table.get_item(Key={'PK': pk, 'SK': 'HISTORY'})
                if 'Item' in response:
                    return response['Item'].get('tools', [])
                return []
            except ClientError as e:
                print(f"DynamoDB error: {e}")
                return []

    def append_session_sequence(self, agent_id: str, session_id: str, tool: str):
        if USE_IN_MEMORY:
            key = f"{agent_id}::{session_id}"
            if key not in self._in_memory_session_sequence:
                self._in_memory_session_sequence[key] = []
            self._in_memory_session_sequence[key].append(tool)
        else:
            pk = f"SEQ::{agent_id}::{session_id}"
            try:
                self.table.update_item(
                    Key={'PK': pk, 'SK': 'HISTORY'},
                    UpdateExpression="SET tools = list_append(if_not_exists(tools, :empty_list), :new_tool)",
                    ExpressionAttributeValues={':empty_list': [], ':new_tool': [tool]}
                )
            except ClientError as e:
                print(f"DynamoDB error: {e}")

    def log_invocation(self, request: ToolCallRequest, rule_results: List[RuleResult], disposition: str, result: Optional[Any] = None) -> str:
        log_id = str(uuid.uuid4())
        timestamp = int(time.time())
        log_entry = {
            'PK': 'LOG',
            'SK': f"{timestamp}::{log_id}",
            'log_id': log_id,
            'timestamp': timestamp,
            'agent_id': request.agent_id,
            'session_id': request.session_id,
            'tool': request.tool,
            'parameters': self._sanitize_params(request.parameters),
            'rule_results': [r.model_dump() for r in rule_results],
            'disposition': disposition
        }
        
        if USE_IN_MEMORY:
            self._in_memory_logs.append(log_entry)
        else:
            try:
                self.table.put_item(Item=log_entry)
            except ClientError as e:
                print(f"DynamoDB error: {e}")
        
        return log_id

    def get_recent_logs(self, since: int, limit: int = 100) -> List[Dict[str, Any]]:
        if USE_IN_MEMORY:
            logs = [log for log in self._in_memory_logs if log['timestamp'] >= since]
            return sorted(logs, key=lambda x: x['timestamp'], reverse=True)[:limit]
        else:
            try:
                response = self.table.query(
                    KeyConditionExpression="PK = :pk AND SK >= :sk",
                    ExpressionAttributeValues={
                        ':pk': 'LOG',
                        ':sk': f"{since}::"
                    },
                    ScanIndexForward=False,
                    Limit=limit
                )
                return response.get('Items', [])
            except ClientError as e:
                print(f"DynamoDB error: {e}")
                return []

    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        for k, v in params.items():
            if isinstance(v, str) and len(v) > 200:
                sanitized[k] = v[:200] + "... [TRUNCATED]"
            else:
                sanitized[k] = v
        return sanitized

state_manager = StateManager()
