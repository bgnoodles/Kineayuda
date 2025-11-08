from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions

# Credenciales SANDBOX oficiales de Webpay Plus (solo integración)
# Fuente: Transbank Developers (Referencia API Webpay)
COMMERCE_CODE = "597055555532"
API_KEY_SECRET = "579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C"

# Configuración para ambiente de pruebas (TEST)
options = WebpayOptions(
    commerce_code=COMMERCE_CODE,
    api_key=API_KEY_SECRET,
    integration_type=IntegrationType.TEST
)

def create_transaction(buy_order: str, session_id: str, amount: float, return_url: str):
    tx = Transaction(options=options)
    return tx.create(buy_order=buy_order, session_id=session_id, amount=amount, return_url=return_url)

def commit_transaction(token_ws: str):
    tx = Transaction(options=options)
    return tx.commit(token_ws)

def get_status(token_ws: str):
    tx = Transaction(options=options)
    return tx.status(token_ws)