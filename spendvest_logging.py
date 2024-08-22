import logging
import os
from pythonjsonlogger import jsonlogger

# Logs Direcotery
file_directory = os.path.dirname(os.path.abspath(__file__))
log_directory = os.path.join(file_directory, os.getenv("LOG_DIR", "logs/"))

# Root logger configuration
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# File handler for registration log messages
registration_file_handler = logging.FileHandler(f"{log_directory}registration.json")
registration_file_handler.setLevel(logging.DEBUG)

# File handler for registration log messages
send_money_file_handler = logging.FileHandler(f"{log_directory}send_money.json")
send_money_file_handler.setLevel(logging.DEBUG)

# File handler for registration log messages
withdraw_file_handler = logging.FileHandler(f"{log_directory}withdraw.json")
withdraw_file_handler.setLevel(logging.DEBUG)

# Create a JSON formatter
json_formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(name)s %(levelname)s %(message)s"
)
registration_file_handler.setFormatter(json_formatter)
send_money_file_handler.setFormatter(json_formatter)
withdraw_file_handler.setFormatter(json_formatter)

# Logger for `Registration` module
registration_logger = logging.getLogger("registration")
registration_logger.setLevel(logging.DEBUG)
registration_logger.addHandler(registration_file_handler)

# Logger for `SendMoney` module
send_money_logger = logging.getLogger("send_money")
send_money_logger.setLevel(logging.DEBUG)
send_money_logger.addHandler(send_money_file_handler)

# Logger for `Withdraw` module
withdraw_logger = logging.getLogger("withdraw")
withdraw_logger.setLevel(logging.DEBUG)
withdraw_logger.addHandler(withdraw_file_handler)

# Logger for payment gateway
payment_gateway_logger = logging.getLogger("payment_gateway")
payment_gateway_logger.setLevel(logging.DEBUG)
payment_gateway_logger.addHandler(withdraw_file_handler)

# Logger for payment gateway
wallet_service_logger = logging.getLogger("wallet_service")
wallet_service_logger.setLevel(logging.DEBUG)
wallet_service_logger.addHandler(withdraw_file_handler)
