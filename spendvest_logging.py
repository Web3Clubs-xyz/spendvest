import logging
import colorlog
import os
from pythonjsonlogger import jsonlogger

# Logs Direcotery
file_directory = os.path.dirname(os.path.abspath(__file__))
log_directory = os.path.join(file_directory, os.getenv("LOG_DIR", "logs/"))

# Root logger configuration
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Stream handler
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)

# File handler for registration log messages
registration_file_handler = logging.FileHandler(f"{log_directory}registration.json")
registration_file_handler.setLevel(logging.DEBUG)

# File handler for registration log messages
send_money_file_handler = logging.FileHandler(f"{log_directory}send_money.json")
send_money_file_handler.setLevel(logging.DEBUG)

# File handler for registration log messages
withdraw_file_handler = logging.FileHandler(f"{log_directory}withdraw.json")
withdraw_file_handler.setLevel(logging.DEBUG)

# File handler for registration log messages
router_file_handler = logging.FileHandler(f"{log_directory}withdraw.json")
router_file_handler.setLevel(logging.DEBUG)

# Create a JSON formatter
json_formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(name)s %(levelname)s %(message)s"
)

# Coloured formatter
color_formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(levelname)s: %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)

stream_handler.setFormatter(color_formatter)
registration_file_handler.setFormatter(json_formatter)
send_money_file_handler.setFormatter(json_formatter)
withdraw_file_handler.setFormatter(json_formatter)

# Logger for `Registration` module
registration_logger = logging.getLogger("registration")
registration_logger.setLevel(logging.DEBUG)
registration_logger.addHandler(stream_handler)
registration_logger.addHandler(registration_file_handler)

# Logger for `SendMoney` module
send_money_logger = logging.getLogger("send_money")
send_money_logger.setLevel(logging.DEBUG)
send_money_logger.addHandler(stream_handler)
send_money_logger.addHandler(send_money_file_handler)

# Logger for `Withdraw` module
withdraw_logger = logging.getLogger("withdraw")
withdraw_logger.setLevel(logging.DEBUG)
withdraw_logger.addHandler(stream_handler)
withdraw_logger.addHandler(withdraw_file_handler)

# Logger for payment gateway
payment_gateway_logger = logging.getLogger("payment_gateway")
payment_gateway_logger.setLevel(logging.DEBUG)
payment_gateway_logger.addHandler(stream_handler)
payment_gateway_logger.addHandler(withdraw_file_handler)

# Logger for wallet service
wallet_service_logger = logging.getLogger("wallet_service")
wallet_service_logger.setLevel(logging.DEBUG)
wallet_service_logger.addHandler(stream_handler)
wallet_service_logger.addHandler(withdraw_file_handler)

# Logger for fastapi
fastapi_logger = logging.getLogger("fastapi")
fastapi_logger.setLevel(logging.DEBUG)
fastapi_logger.addHandler(stream_handler)

# Logger for router
router_logger = logging.getLogger("router")
router_logger.setLevel(logging.DEBUG)
router_logger.addHandler(stream_handler)
router_logger.addHandler(router_file_handler)
