import json 
import time

from anchore_engine.db import db_services, session_scope
from anchore_engine.subsys import logger
import anchore_engine.configuration.localconfig

service_statuses = {}

def set_status(service_record, up=True, available=True, busy=False, message="all good", detail={}, update_db=False):
    global service_statuses
    hostid = service_record['hostid']
    servicename = service_record['servicename']
    service = '__'.join([service_record['hostid'], service_record['servicename']])

    if service not in service_statuses:
        service_statuses[service] = {}

    service_statuses[service]['up']= up
    service_statuses[service]['available'] = available
    service_statuses[service]['busy'] = busy 
    service_statuses[service]['message'] = message
    if detail:
        service_statuses[service]['detail'] = detail

    if update_db:
        with session_scope() as dbsession:
            my_service_record = db_services.get(hostid, servicename, session=dbsession)
            if my_service_record:
                my_service_record['short_description'] = json.dumps(service_statuses[service])
                db_services.update_record(my_service_record, session=dbsession)

def get_status(service_record):
    global service_statuses
    service = '__'.join([service_record['hostid'], service_record['servicename']])

    if service in service_statuses:
        ret = service_statuses[service]
    else:
        raise Exception("no service status set for service: " + str(service))
    return(ret)

def initialize_status(service_record, up=True, available=True, busy=False, message="all good", detail={}):
    global service_statuses
    service = '__'.join([service_record['hostid'], service_record['servicename']])
    if service not in service_statuses:
        set_status(service_record, up=up, available=available, busy=busy, message=message, detail=detail)
    return(True)

def has_status(service_record):
    global service_statuses
    service = '__'.join([service_record['hostid'], service_record['servicename']])
    ret = False
    if service in service_statuses:
        ret = True

    return(ret)

def handle_service_heartbeat(*args, **kwargs):
    cycle_timer = kwargs['mythread']['cycle_timer']
    localconfig = anchore_engine.configuration.localconfig.get_config()
    try:
        servicename = args[0]
    except Exception as err:
        raise Exception("BUG: need to provide service name as first argument to function: " + str(args))

    while(True):
        logger.debug("setting service status: " + str(servicename))
        try:
            service_record = {'hostid': localconfig['host_id'], 'servicename': servicename}
            set_status(service_record, up=True, available=True, update_db=True)
            logger.debug("service status set: next in "+str(cycle_timer))
        except Exception as err:
            logger.error(str(err))

        time.sleep(cycle_timer)

    return(True)

