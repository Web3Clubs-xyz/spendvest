mpesa_ref_structure = [
    {
        "min" : 1,
        "max": 49,
        "agent_withdrawal":None,
        "send_customer":0,
        "send_pochi_and_till":0
    }, 
    {
        "min" : 50,
        "max": 100,
        "agent_withdrawal":11,
        "send_customer":0,
        "send_pochi_and_till":0
    },
    {
        "min" : 101,
        "max": 500,
        "agent_withdrawal":29,
        "send_customer":7,
        "send_pochi_and_till":7
    },
    {
        "min" : 501,
        "max": 1000,
        "agent_withdrawal":29,
        "send_customer":13,
        "send_pochi_and_till":13
    },
    {
        "min" : 1001,
        "max": 1500,
        "agent_withdrawal":29,
        "send_customer":23,
        "send_pochi_and_till":23
    },
    {
        "min" : 1501,
        "max": 2500,
        "agent_withdrawal":29,
        "send_customer":33,
        "send_pochi_and_till":33
    },
    {
        "min" : 2501,
        "max": 3500,
        "agent_withdrawal":52,
        "send_customer":53,
        "send_pochi_and_till":53
    },
    {
        "min" : 3501,
        "max": 5000,
        "agent_withdrawal":69,
        "send_customer":57,
        "send_pochi_and_till":57
    },
    {
        "min" : 5001,
        "max": 7500,
        "agent_withdrawal":87,
        "send_customer":78,
        "send_pochi_and_till":78
    },
    {
        "min" : 7501,
        "max": 1000,
        "agent_withdrawal":115,
        "send_customer":90,
        "send_pochi_and_till":90
    },
    {
        "min" : 10001,
        "max": 15000,
        "agent_withdrawal":167,
        "send_customer":100,
        "send_pochi_and_till":100
    },
    {
        "min" : 15001,
        "max": 20000,
        "agent_withdrawal":185,
        "send_customer":105,
        "send_pochi_and_till":105
    },
    {
        "min" : 20001,
        "max": 35000,
        "agent_withdrawal":197,
        "send_customer":108,
        "send_pochi_and_till":108
    },
    {
        "min" : 35001,
        "max": 50000,
        "agent_withdrawal":278,
        "send_customer":108,
        "send_pochi_and_till":108
    },
    {
        "min" : 50001,
        "max": 250000,
        "agent_withdrawal":309,
        "send_customer":108,
        "send_pochi_and_till":108
    },
]


customer_max_balance = 500000
customer_daily_max_transx = 500000
customer_single_max_transx = 250000
customer_withdrawal_min_transx = 50


def get_all_registered_mpesa_customers():
    pass 

def generate_mpesa_send_save_pattern(transaction_type, amount):
    pass 

def dispatch_mpesa_send_pattern(dispatch_uid, dispatch_payload):
    pass 

def dispatch_payment_centrally():
    pass 