__author__ = 'rohe0002'

import time

from pytest import raises

from oic.utils.sdb import SessionDB
from oic.utils.sdb import ExpiredToken
from oic.oic.message import AuthorizationRequest
from oic.oic.message import OpenIDRequest

#from oic.oauth2 import message

AREQ = AuthorizationRequest(response_type="code",
               client_id="client1", redirect_uri="http://example.com/authz",
               scope=["openid"], state="state000")

AREQN = AuthorizationRequest(response_type="code",
                client_id="client1", redirect_uri="http://example.com/authz",
                scope=["openid"], state="state000", nonce="something")

OIDR = OpenIDRequest(response_type="code", client_id="client1",
               redirect_uri="http://example.com/authz", scope=["openid"],
               state="state000")

OAUTH2_AREQ = AuthorizationRequest(response_type="code",
                      client_id="client1",
                      redirect_uri="http://example.com/authz",
                      scope=["openid"], state="state000")

def _eq(l1, l2):
    return set(l1) == set(l2)

def test_token():
    sdb = SessionDB()
    sid = sdb.token.key(areq=AREQ)
    assert len(sid) == 28

    sdb = SessionDB({"a":"b"})
    sid = sdb.token.key(areq=AREQ)
    assert len(sid) == 28

def test_new_token():
    sdb = SessionDB()
    sid = sdb.token.key(areq=AREQ)
    assert len(sid) == 28

    code2 = sdb.token('T', sid=sid)
    assert len(sid) == 28

    code3 = sdb.token(type="", prev=code2)
    assert code2 != code3
    
    sid2 = sdb.token.key(areq=AREQ, user="jones")
    assert len(sid2) == 28
    assert sid != sid2

def test_type_and_key():
    sdb = SessionDB()
    sid = sdb.token.key(areq=AREQ)
    code = sdb.token(sid=sid)
    print sid
    part = sdb.token.type_and_key(code)
    print part
    assert part[0] == "A"
    assert part[1] == sid

def test_setitem():
    sdb = SessionDB()
    sid = sdb.token.key(areq=AREQ)
    code = sdb.token(sid=sid)

    sdb[sid] = {"indo":"china"}

    info = sdb[sid]
    assert info == {"indo":"china"}

    info = sdb[code]
    assert info == {"indo":"china"}

    raises(KeyError, 'sdb["abcdefghijklmnop"]')

def test_update():
    sdb = SessionDB()
    sid = sdb.token.key(areq=AREQ)
    code = sdb.token(sid=sid)

    raises(KeyError, 'sdb.update(sid, "indo", "nebue")')
    raises(KeyError, 'sdb.update(code, "indo", "nebue")')

    sdb[sid] = {"indo":"china"}

    sdb.update(sid, "indo", "nebue")
    sdb.update(code, "indo", "second")

    raises(KeyError, 'sdb.update("abcdefghijklmnop", "indo", "bar")')

    #noinspection PyUnusedLocal
    sid2 = sdb.token.key(areq=AREQ)

    raises(KeyError, 'sdb.update(sid2, "indo", "bar")')

def test_create_authz_session():
    sdb = SessionDB()
    sid = sdb.create_authz_session("user_id", AREQ)

    info = sdb[sid]
    print info
    assert info["oauth_state"] == "authz"

    sdb = SessionDB()
    # Missing nonce property
    sid = sdb.create_authz_session("user_id", OAUTH2_AREQ)
    info = sdb[sid]
    print info
    assert info["oauth_state"] == "authz"

    sid2 = sdb.create_authz_session("user_id", AREQN)

    info = sdb[sid2]
    print info
    assert info["nonce"] == "something"

    sid3 = sdb.create_authz_session("user_id", AREQN, id_token="id_token")

    info = sdb[sid3]
    print info
    assert info["id_token"] == "id_token"

    sid4 = sdb.create_authz_session("user_id", AREQN, oidreq=OIDR)

    info = sdb[sid4]
    print info
    assert "id_token" not in info
    assert "oidreq" in info

def test_create_authz_session_with_sector_id():
    sdb = SessionDB(seed="foo")
    sid5 = sdb.create_authz_session("user_id", AREQN, oidreq=OIDR,
                                    si_redirects=["http://example.com/"],
                                    sector_id="http://example.com/si.jwt")

    info_1 = sdb[sid5]
    print info_1
    assert "id_token" not in info_1
    assert "oidreq" in info_1
    assert info_1["user_id"] != "user_id"

    sid6 = sdb.create_authz_session("user_id2", AREQN, oidreq=OIDR,
                                    si_redirects=["http://example.com/"],
                                    sector_id="http://example.com/si.jwt")

    info_2 = sdb[sid6]
    print info_2
    assert info_2["user_id"] != "user_id"
    assert info_2["user_id"] != info_1["user_id"]

def test_update_to_token():
    sdb = SessionDB()
    sid = sdb.create_authz_session("user_id", AREQ)
    grant = sdb[sid]["code"]
    _dict = sdb.update_to_token(grant)

    print _dict.keys()
    assert _eq(_dict.keys(), ['code', 'oauth_state', 'issued', 'expires_at',
                              'token_type', 'client_id', 'authzreq',
                              'refresh_token', 'user_id', 'access_token',
                              'expires_in', 'state', 'redirect_uri',
                              'code_used', 'scope', 'access_token_scope',
                              'revoked'])

    raises(Exception, 'sdb.update_to_token(grant)')

    raises(Exception, 'sdb.update_to_token(_dict["access_token"]')

    sdb = SessionDB()
    sid = sdb.create_authz_session("another_user_id", AREQ)
    grant = sdb[sid]["code"]

    _dict = sdb.update_to_token(grant, id_token="id_token", oidreq=OIDR)
    print _dict.keys()
    assert _eq(_dict.keys(), ['code', 'oauth_state', 'issued', 'expires_at',
                              'token_type', 'client_id', 'authzreq',
                              'refresh_token', 'user_id', 'oidreq',
                              'access_token', 'expires_in', 'state',
                              'redirect_uri', 'code_used', 'id_token',
                              'scope', 'access_token_scope', 'revoked'])

    assert _dict["id_token"] == "id_token"
    assert _dict["oidreq"].type() == "OpenIDRequest"
    token = _dict["access_token"]
    raises(Exception, 'sdb.update_to_token(token)')


def test_refresh_token():
    sdb = SessionDB()
    sid = sdb.create_authz_session("user_id", AREQ)
    grant = sdb[sid]["code"]
    _dict = sdb.update_to_token(grant)
    dict1 = _dict.copy()

    rtoken = _dict["refresh_token"]
    time.sleep(1)
    dict2 = sdb.refresh_token(rtoken)
    print dict2
    
    assert dict1["issued"] != dict2["issued"]
    assert dict1["access_token"] != dict2["access_token"]

    raises(Exception, 'sdb.refresh_token(dict2["access_token"])')


def test_is_valid():
    sdb = SessionDB()
    sid = sdb.create_authz_session("user_id", AREQ)
    grant = sdb[sid]["code"]

    assert sdb.is_valid(grant)

    _dict = sdb.update_to_token(grant)
    assert sdb.is_valid(grant) == False
    token1 = _dict["access_token"]
    assert sdb.is_valid(token1)

    rtoken = _dict["refresh_token"]
    assert sdb.is_valid(rtoken)

    dict2 = sdb.refresh_token(rtoken)
    token2 = dict2["access_token"]
    assert sdb.is_valid(token2)

    # replace refresh_token

    dict2["refresh_token"] = token2
    assert sdb.is_valid(rtoken) == False
    
    # mess with the time-line

    dict2["issued"] = time.time() - 86400 # like yesterday
    assert sdb.is_valid(token2) == False

    # replace access_token

    dict2["access_token"] = token1
    assert sdb.is_valid(token2) == False

    sid = sdb.create_authz_session("another:user", AREQ)
    grant = sdb[sid]["code"]

    gdict = sdb[grant]
    gdict["issued"] = time.time() - 86400 # like yesterday
    assert sdb.is_valid(grant) == False

def test_revoke_token():
    sdb = SessionDB()
    sid = sdb.create_authz_session("user_id", AREQ)

    grant = sdb[sid]["code"]
    _dict = sdb.update_to_token(grant)

    token = _dict["access_token"]
    rtoken = _dict["refresh_token"]
    
    assert sdb.is_valid(token)

    sdb.revoke_token(token)
    assert sdb.is_valid(token) == False

    dict2 = sdb.refresh_token(rtoken)
    token = dict2["access_token"]
    assert sdb.is_valid(token)

    sdb.revoke_token(rtoken)
    assert sdb.is_valid(rtoken) == False

    raises(ExpiredToken, 'sdb.refresh_token(rtoken)')

    assert sdb.is_valid(token)

    # --- new token ----

    sdb = SessionDB()
    sid = sdb.create_authz_session("user_id", AREQ)

    grant = sdb[sid]["code"]
    sdb.revoke_token(grant)
    assert sdb.is_valid(grant) == False