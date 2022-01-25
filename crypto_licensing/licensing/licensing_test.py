# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
try:
    from future_builtins import zip, map # Use Python 3 "lazy" zip, map
except ImportError:
    pass

import json
import logging
import multiprocessing
import os
import pytest
import time

try: # Python2
    from urllib2 import urlopen
    from urllib import urlencode
except ImportError: # Python3
    from urllib.request import urlopen
    from urllib.parse import urlencode

from ..misc		import reprlib
from ..			import licensing

# If web.py or cpppo is unavailable, licensing.main cannot be used
try:
    from .main import main as licensing_main
except:
    licensing_main		= None

try:
    import web
except:
    web				= None
try:
    from cpppo.server import network		# network.bench
    from cpppo import dotdict			# multiprocessing.Manager().apidict
except ImportError:
    network			= None
try:
    import chacha20poly1305
except:
    chacha20poly1305		= None
    

log				= logging.getLogger( "lic.svr")

client_count			= 25
client_max			= 10

licensing_cli_kwds		= {
    "tests": [
        1,
        "abcdefghijklmnopqrstuvwxyz",
        str("a"),
        9999999,
        None,
    ],
}

CFGPATH				=  __file__[:-3] # trim off .py


def test_licensing_issue_query():
    # Issue a license to this machine-id, for client "End User, LLC".
    
    # TODO: XXX: These requests are signed, proving that they came from the holder of the client
    # signing key.  However, anyone who captures the request and the signature can ask for the same
    # License!  Then, if they forge the Machine ID, they can run the license on that machine.
    # 
    # This is only possible if the channel can be examined; public License Servers should be served
    # over SSL protected channels.
    request			= licensing.IssueRequest(
        client		= "End User, LLC",
        client_pubkey	= "O2onvM62pC1io6jQKm8Nc2UyFXcd4kOmOsBIoYtZ2ik=",
        author		= "Awesome, Inc.",
        author_pubkey	= "cyHOei+4c5X+D/niQWvDG5olR1qi4jddcPTDJv/UfrQ=",
        product		= "EtherNet/IP Tool",
        machine		= licensing.machine_UUIDv4( machine_id_path=__file__.replace( ".py", ".machine-id" )),
    )
    query			= request.query( sigkey="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA7aie8zrakLWKjqNAqbw1zZTIVdx3iQ6Y6wEihi1naKQ==" )
    #print( query )
    assert """\
author=Awesome%2C+Inc.&\
author_pubkey=cyHOei%2B4c5X%2BD%2FniQWvDG5olR1qi4jddcPTDJv%2FUfrQ%3D&\
client=End+User%2C+LLC&\
client_pubkey=O2onvM62pC1io6jQKm8Nc2UyFXcd4kOmOsBIoYtZ2ik%3D&\
machine=00010203-0405-4607-8809-0a0b0c0d0e0f&\
product=EtherNet%2FIP+Tool&\
signature=kDCDoWJ2xDcIg5HicihQeJBxbo8LK%2BDCI2FPogQD2q4Slxylyq7G5xuEaV%2BWa6STD7GvGUSNGcGWPqazy1xDCQ%3D%3D\
""" == query
    return query


def licensing_cli( number, tests=None, address=None ):
    """Makes a series of HTTP requests to the licensing server, testing the response.

    """
    log.info( "Client number={}; starting".format( number ))
    query			= test_licensing_issue_query()
    url				= "http://{host}:{port}/api/issue.json?{query}&number={number}".format(
        host	= address[0] if address else "localhost",
        port	= address[1] if address else 8000,
        query	= query,
        number	= number,
    )
    log.detail( "Client number={}; url: {}".format( number, misc.reprlib.repr( url )))
    response			= urlopen( url ).read()
    assert response
    log.detail( "Client number={}; response: {}".format( number, misc.reprlib.repr( response )))
    data			= json.loads( response )
    #print( data )
    assert data['list'] and data['list'][0]['signature'] == 'xnSfp/GDWsAvxVqarn+7AG8l0TIlSXD5kdHzb0sRxZsrm7o3uYLbPNxkcgvLV62m9V7BhKCU0unaMweSWX8TCA=='
    log.info( "Client number={}; done".format( number ))


def licensing_bench():
    with multiprocessing.Manager() as m:

        licensing_svr_kwds		= dict(
            argv	= [
                "--no-gui",
                "--config", CFGPATH,
                "--web", "127.0.0.1:0",
                #"--no-access",		# Do not redirect sys.stdout/stderr to an access log file
                #"--profile", "licensing.prof", # Optionally, enable profiling (pip install ed25519ll helps...)
            ],

            # The master server control dict; 'control' may be converted to a different form (eg. a
            # multiprocessing.Manager().dict()) if necessary.  Each of the Licensing server thread-specific
            # configs will be provided a reverence to this control (unless, for some reason, you don't want
            # them to share it).  If *any* thread shuts down, they will all be stopped.
            server	= dict(
                control		= m.apidict(
                    1.0,
                    done	= False
                ),
            ),

            # The licensing control system loop.  This runs various licensing state machinery
            ctl		= dict(
                cycle		= 1.0,
            ),

            # The Web API.  Remote web API access and web page.
            web		= dict(
                #access		= False,	# Do not redirect sys.stdout/stderr to an access log file
                #address	= "127.0.0.1:0",# Use a dynamic bind port for testing the server (force ipv4 localhost)
            ),

            # The Text GUI.  Controls the internals of the Licensing server from the server text console
            txt		= dict(
                title		= "Licensing",
            ),
        )

        # Start up the Web interface on a dynamic port, eg. "localhost:0"
        failed			= network.bench(
            server_func	= licensing_main,
            server_kwds	= licensing_svr_kwds,
            client_func	= licensing_cli,
            client_count= client_count,
            client_max	= client_max,
            client_kwds	= licensing_cli_kwds,
            address_delay= 5.0,
        )

    if failed:
        log.warning( "Failure" )
    else:
        log.info( "Succeeded" )

    return failed


@pytest.mark.skipif( not licensing_main or not web or not network or not chacha20poly1305,
                     reason="Licensing server needs web.py" )
def test_licensing_bench( tmp_path ):
    print( "Changing CWD to {}".format( tmp_path ))
    os.chdir( str( tmp_path ))
    assert not licensing_bench(), \
        "One or more licensing_banch clients reported failure"
