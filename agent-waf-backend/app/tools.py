def get_customer_record(customer_id: str):
    return {"customer_id": customer_id, "name": "Alice"}

def send_email(to: str, body: str):
    return {"status": "sent", "to": to}

def run_query(query: str):
    return {"rows_returned": 1, "data": [{"result": "fake"}]}

def refund_payment(payment_id: str):
    return {"status": "refunded", "payment_id": payment_id}

TOOL_REGISTRY = {
    "get_customer_record": get_customer_record,
    "send_email": send_email,
    "run_query": run_query,
    "refund_payment": refund_payment,
}
