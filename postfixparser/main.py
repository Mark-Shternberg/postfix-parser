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
import asyncio
import logging
import re
import rethinkdb.query
from enum import Enum
from typing import Dict
from postfixparser import settings
from postfixparser.core import get_rethink
from postfixparser.objects import PostfixLog, PostfixMessage
from postfixparser.parser import parse_line
import datetime

log = logging.getLogger(__name__)

_match = r'([A-Za-z]+[ \t]+[0-9]+[ \t]+[0-9]+\:[0-9]+:[0-9]+).*'
"""(0) Regex to match the Date/Time at the start of each log line"""

_match += r'\: ([A-F0-9]*)\:[ \t]+?(.*)'
"""Regex to match the (1) Queue ID and the (2) Log Message"""

match = re.compile(_match)

_match_noqid = r'([A-Za-z]+[ \t]+[0-9]+[ \t]+[0-9]+\:[0-9]+:[0-9]+).*'
_match_noqid += r'NOQUEUE\: (reject.*)'

match_noqid = re.compile(_match_noqid)

class ObjectExists(BaseException):
    pass


class OnConflict(Enum):
    QUIET = "quiet"
    EXCEPT = "except"
    UPDATE = "update"


async def save_obj(table, data, primary=None, onconflict: OnConflict = OnConflict.EXCEPT):
    r, conn, _ = await get_rethink()
    _data = dict(data)
    if primary is not None:
        if 'id' not in _data: _data['id'] = _data[primary]
        g = await r.table(table).get(data[primary]).run(conn)

        if g is not None:
            if onconflict == OnConflict.QUIET:
                return None
            if onconflict == OnConflict.EXCEPT:
                raise ObjectExists(f"Table '{table}' entry with '{primary} = {data[primary]}' already exists!")
            if onconflict == OnConflict.UPDATE:
                return await r.table(table).get(data[primary]).update(_data).run(conn)
            raise AttributeError("'saveobj' onconflict must be either 'quiet', 'except', or 'update'")
    return await r.table(table).insert(_data).run(conn)


async def import_log(logfile: str) -> Dict[str, PostfixMessage]:
    log.info('Opening log file %s', logfile)
    messages = {}
    with open(logfile, 'r') as f:
        while True:
            line = f.readline()
            if not line: break

            m = match.match(line)
            if not m: continue

            dtime, qid, msg = m.groups()
            date = date_converter(dtime)
            if qid not in messages:
                messages[qid] = PostfixMessage(timestamp=dtime, queue_id=qid, date=date)

            messages[qid].merge(await parse_line(msg))
            messages[qid].lines.append(PostfixLog(timestamp=dtime, queue_id=qid, message=msg))
    
    with open(logfile, 'r') as g:
        while True:
            line = g.readline()
            if not line: break

            m = match_noqid.match(line)
            if not m: continue

            dtime2, msg2 = m.groups()
            date = date_converter(dtime2)
            today = datetime.date.today()
            dtime = dtime2 + str(today.year)
            noqid = id_converter(dtime)
            if noqid not in messages:
                messages[noqid] = PostfixMessage(timestamp=dtime2, queue_id=noqid, date=date)

            messages[noqid].merge(await parse_line(msg2))
            messages[noqid].lines.append(PostfixLog(timestamp=dtime2, queue_id=noqid, message=msg2))

    log.info('Finished parsing log file %s', logfile)
    return messages


async def main():
    r, conn, r_q = await get_rethink()
    r_q: rethinkdb.query

    log.info('Importing log file')
    msgs = await import_log(settings.mail_log)
    log.info('Converting log data into list')
    msg_list = [{"id": qid, **msg.clean_dict(convert_time=r_q.expr)} for qid, msg in msgs.items()]
    log.info('Total of %d message entries', len(msg_list))
    log.info('Generating async batch save list')
    save_list = []
    for m in msg_list:
        try:
            mfrom, mto = m.get('mail_from'), m.get('mail_to')
            mfrom_dom, mto_dom = mfrom.split('@')[1], mto.split('@')[1]
            if mfrom_dom in settings.ignore_domains or mto_dom in settings.ignore_domains:
                continue
            save_list.append(save_obj('sent_mail', m, primary="id", onconflict=OnConflict.UPDATE))
        except Exception:
            log.exception('Error while parsing email %s', m)
    log.info('Firing off asyncio.gather(save_list)...')
    await asyncio.gather(*save_list)
    log.info('Finished!')


def date_converter(ldate: str):
    if 'Jan ' in ldate: 
        ldate = ldate.replace('Jan','01')
    elif 'Feb ' in ldate: 
        ldate = ldate.replace('Feb','02')
    elif 'Mar ' in ldate: 
        ldate = ldate.replace('Mar','03')
    elif 'Apr ' in ldate: 
        ldate = ldate.replace('Apr','04')
    elif 'May ' in ldate: 
        ldate = ldate.replace('May','05')
    elif 'Jun ' in ldate: 
        ldate = ldate.replace('Jun','06')
    elif 'Jul ' in ldate: 
        ldate = ldate.replace('Jul','07')
    elif 'Aug ' in ldate: 
        ldate = ldate.replace('Aug','08')
    elif 'Sep ' in ldate: 
        ldate = ldate.replace('Sep','09')
    elif 'Oct ' in ldate: 
        ldate = ldate.replace('Oct','10')
    elif 'Nov ' in ldate: 
        ldate = ldate.replace('Nov','11')
    elif 'Dec ' in ldate: 
        ldate = ldate.replace('Dec','12')
    today = datetime.date.today()
    date = re.sub(r'[0-9][0-9]:[0-9][0-9]:[0-9][0-9]', str(today.year), ldate)
    date = date.split(' ')[2]+"-"+date.split(' ')[0]+"-"+date.split(' ')[1]
    return date

def id_converter(date: str):
    if 'Jan ' in date: 
        date = date.replace('Jan','01')
    elif 'Feb ' in date: 
        date = date.replace('Feb','02')
    elif 'Mar ' in date: 
        date = date.replace('Mar','03')
    elif 'Apr ' in date: 
        date = date.replace('Apr','04')
    elif 'May ' in date: 
        date = date.replace('May','05')
    elif 'Jun ' in date: 
        date = date.replace('Jun','06')
    elif 'Jul ' in date: 
        date = date.replace('Jul','07')
    elif 'Aug ' in date: 
        date = date.replace('Aug','08')
    elif 'Sep ' in date: 
        date = date.replace('Sep','09')
    elif 'Oct ' in date: 
        date = date.replace('Oct','10')
    elif 'Nov ' in date: 
        date = date.replace('Nov','11')
    elif 'Dec ' in date: 
        date = date.replace('Dec','12')
    date = date.replace(' ','')
    date = date.replace(':','')
    return date