"""

Copyright::
    +===================================================+
    |                 © 2019 Privex Inc.                |
    |               https://www.privex.io               |
    +===================================================+
    |                                                   |
    |        Postfix Log Parser / Web UI                |
    |                                                   |
    |        Core Developer(s):                         |
    |                                                   |
    |          (+)  Chris (@someguy123) [Privex]        |
    |                                                   |
    +===================================================+

"""
import re

find_to = re.compile(r'.*to=<([^><]+@[^><]+)>')
find_from = re.compile(r'.*from=<([^><]+@[^><]+)>')
find_message_id = re.compile(r'.*message-id=<(.*)>')
find_status = re.compile(r'.*status=([a-zA-Z0-9-_.]+) (.*)?')
find_relay = re.compile(r'.*relay=([a-zA-Z0-9-._]+)\[(.*)\]:([0-9]+)')
find_client = re.compile(r'.*client=([a-zA-Z0-9-._]+)\[(.*)\]')
find_reject = re.compile(r'.*(reject).*:(.*);')

find_empty_from = re.compile(r'.*(from=<>).*')
find_empty_to = re.compile(r'.*(to=<>).*')


async def parse_line(mline) -> dict:
    lm = {}

    _to = find_to.match(mline)
    _from = find_from.match(mline)
    _client = find_client.match(mline)
    _relay = find_relay.match(mline)

    _empty_from = find_empty_from.match(mline)
    _empty_to = find_empty_to.match(mline)
    
    if _to is not None: lm['mail_to'] = _to.group(1)
    if _from is not None: lm['mail_from'] = _from.group(1)
    if _client is not None: lm['client'] = dict(host=_client.group(1), ip=_client.group(2))
    if _relay is not None: lm['relay'] = dict(host=_relay.group(1), ip=_relay.group(2), port=_relay.group(3))

    if _empty_from is not None: lm['mail_from'] = "-@-"
    if _empty_to is not None: lm['mail_to'] = "-@-"

    _status = find_status.match(mline)
    _status_rejected = find_reject.match(mline)

    if _status_rejected is not None:
        lm['status'] = dict(code=_status_rejected.group(1), message="")
        if len(_status_rejected.groups()) > 1:
            lm['status']['message'] = _status_rejected.group(2)
    if _status is not None:
        lm['status'] = dict(code=_status.group(1), message="")
        if len(_status.groups()) > 1:
            lm['status']['message'] = _status.group(2)

    _message_id = find_message_id.match(mline)
    if _message_id is not None: lm['message_id'] = _message_id.group(1)

    return lm

