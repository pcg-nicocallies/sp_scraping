import json

def cloud_logging(severity, message, custom_property=None):
    log_entry = {"severity": severity, "message": message}
    if custom_property:
        log_entry["custom_property"] = custom_property
    print(json.dumps(log_entry))