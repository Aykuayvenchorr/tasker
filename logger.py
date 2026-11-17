import logging

app_logger = logging.getLogger("brd-geo-umzr-tasks")      # ----------------------------------- Нужно уникальное наименование, рекомендация: блок-до-подразделение-приложение
app_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s — %(levelname)s — %(message)s')
handler.setFormatter(formatter)
app_logger.addHandler(handler)


class CEFFormatter(logging.Formatter):
    def __init__(self, device_vendor, device_product, device_version, signature_id, name, version="0", **kwargs):
        super().__init__(**kwargs)
        self.cef_version = version
        self.device_vendor = device_vendor
        self.device_product = device_product
        self.device_version = device_version
        self.signature_id = signature_id
        self.name = name
        self.severity_map = {
            logging.DEBUG: 0,
            logging.INFO: 3,
            logging.WARNING: 6,
            logging.ERROR: 8,
            logging.CRITICAL: 10,
        }

    def format(self, record):
        message = super().format(record)
        severity = self.severity_map.get(record.levelno, 6)
        extensions = {
            "rt": int(record.created * 1000),
            "suid": getattr(record, "session_state", "-"),
            "cs1Label": "user",
            "cs1": getattr(record, "user", "-"),
            "msg": message
        }
        ext_str = " ".join(f"{k}={v}" for k, v in extensions.items())
        cef_header = (
            f"CEF:{self.cef_version}|{self.device_vendor}|{self.device_product}|"
            f"{self.device_version}|{self.signature_id}|{self.name}|{severity}|"
        )
        return cef_header + ext_str


app_logger = logging.getLogger("streamlit_cef")                                    
app_logger.setLevel(logging.INFO)

if not app_logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(CEFFormatter(
        device_vendor="GazpromNeft",
        device_product="brd-geo-umzr-tasks",       #------------------------------как ранее указали
        device_version="1.0",
        signature_id="100",
        name="brd-geo-umzr-tasks"                  #------------------------------как ранее указали
    ))
    app_logger.addHandler(handler)
