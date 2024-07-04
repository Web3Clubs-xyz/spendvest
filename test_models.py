import time
import random
from models import MpesaCustomer, SlotQuestion, AccountSummary, RequestTask, Settlement, load_slotquizes

def main():
    # Step 1: Register a new user
    whatsapp_client_number = '254703103960'
    mpesa_transaction_number = '254703103960'

    customer = MpesaCustomer.add_mpesa_customer(mpesa_transaction_number, whatsapp_client_number)
    if customer:
        print("User registered successfully.")
    else:
        print("User registration failed or user already exists.")
        return

    # Step 2: Set amount to save for the user
    AccountSummary.add_summary(whatsapp_client_number)
    summary = AccountSummary.get_acc_summary(whatsapp_client_number)
    print("Account Summary after registration:", summary)

    # Assume the user sets a saving percentage
    saving_percentage = 5  # Example: user sets 5% saving
    print(f"User sets saving percentage to {saving_percentage}%.")
    AccountSummary.update_acc_summary(whatsapp_client_number, {'saving_percentage':saving_percentage})

    # Step 3: Request a send money task with the deposited amount
    service_payload = {
        'TransactionReference': 'REF123456789',
        'amount': 1000,  # Assume the user deposits 1000 units
        'recipient': '254700000002'
    }
    RequestTask.add_request_task(whatsapp_client_number, 'SM', 'Send Money', service_payload)
    task = RequestTask.get_task(service_payload['TransactionReference'])
    print("Request Task added:", task)

    # Step 4: Complete the tasks and record the settlement and account summary
    RequestTask.complete_task(service_payload['AccountReference'])
    print("Request Task completed.")

    # Update account summary
    summary_payload = {
        'total_deposit': 1,
        'total_settlement': 1,
        'pending_settlement': 0,
        'amount_deposited': service_payload['amount'],
        'amount_settled': service_payload['amount'],
        'last_amount_saved': service_payload['amount'] * (saving_percentage / 100),
        'total_amount_saved': service_payload['amount'] * (saving_percentage / 100),
    }
    AccountSummary.update_acc_summary(whatsapp_client_number, summary_payload)
    updated_summary = AccountSummary.get_acc_summary(whatsapp_client_number)
    print("Updated Account Summary:", updated_summary)

    # Record the settlement
    Settlement.add_settlement(whatsapp_client_number, 'SM', service_payload['amount'], True, service_payload['AccountReference'])
    settlement = Settlement.get_customer_settlement(service_payload['AccountReference'])
    print("Settlement recorded:", settlement)

    # Mark settlement as completed
    Settlement.complete_customer_settlement(service_payload['AccountReference'])
    print("Settlement marked as completed.")

if __name__ == '__main__':
    # Load initial slot quizzes
    load_slotquizes()
    # Run the main flow
    main()
