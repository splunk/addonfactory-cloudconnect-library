import os
from helmut.splunk.local import LocalSplunk
import logging
import time
from download_package import install_cc_ucc

from helmut.manager.jobs import Jobs
from helmut_lib.SearchUtil import SearchUtil
import use_latest_build

SPLUNK_HOME = os.environ.get("SPLUNK_HOME")
if SPLUNK_HOME is None:
    SPLUNK_HOME = "/usr/local/bamboo/splunk-install"

os.environ["SPLUNK_HOME"] = SPLUNK_HOME
working_directory = os.environ.get("working_directory")
# if working_directory is None:
#     working_directory = "/Users/cloris/cloud-connect-engine"
ta_orig_path_temp = "{}/test/functional/sample_ta/{}".format(working_directory,"{}")
ta_dest_path_temp ="{}/etc/apps/{}".format(SPLUNK_HOME,{})
test_data = "{}/test/functional/data/{}".format(working_directory,"{}")



local_splunk = LocalSplunk(SPLUNK_HOME)
logger  = logging.getLogger(__name__)

def splunk_login(splunk,logger):
    conn = splunk.create_logged_in_connector()
    jobs = Jobs(conn)
    searchutil = SearchUtil(jobs, logger)
    return searchutil
#

def clean_local_splunk():
    stop_splunk_cmd = " $SPLUNK_HOME/bin/splunk  stop"
    os.system(stop_splunk_cmd)
    splunk_clean_all_cmd = " $SPLUNK_HOME/bin/splunk  clean all -f"
    os.system(splunk_clean_all_cmd)
    splunk_remove_all_ta_cmd = "rm -rf $SPLUNK_HOME/etc/apps/Splunk_TA_*"
    os.system(splunk_remove_all_ta_cmd)


def cp_ta_to_splunk(ta_list):
    cp_ta_cmd_format = "cp -rf {} $SPLUNK_HOME/etc/apps/ "
    if isinstance(ta_list,list):
        for item in ta_list:
            cp_ta_cmd = cp_ta_cmd_format.format(item)
            os.system(cp_ta_cmd)
    else:
        cp_ta_cmd = cp_ta_cmd_format.format(ta_list)
        os.system(cp_ta_cmd)


def cp_conf_to_ta(conf_path, ta_path,conf_type="dir"):
    ta_local_folder = os.path.join(ta_path,"local")
    if not os.path.exists(ta_local_folder):
        mkdir_local_cmd = "mkdir {}".format(ta_local_folder)
        os.system(mkdir_local_cmd)
    # else:
    #     clean_local_folder_cmd = "rm -f {}/*".format(ta_local_folder)
    #     os.system(clean_local_folder_cmd)
    if conf_type =="dir":
        cp_conf_cmd = "cp -f {}/* {}/".format(conf_path,ta_local_folder)
    elif conf_type =="inputs":
        cp_conf_cmd = "cp -f {} {}/inputs.conf".format(conf_path,ta_local_folder)
    elif conf_type == "account":
        ta_name = os.path.basename(ta_path)
        cp_conf_cmd = "cp -f  {} {}/{}_account.conf".format(conf_path,ta_local_folder,ta_name.lower())
    elif conf_type == "settings":
        ta_name = os.path.basename(ta_path)
        cp_conf_cmd = "cp -f {} {}/{}_settings.conf".format(conf_path,ta_local_folder,ta_name.lower())
    else:
        cp_conf_cmd = "cp -f {} {}/".format(conf_path,ta_local_folder)
    os.system(cp_conf_cmd)

def cp_cc_json_to_ta(cc_json_path,dst_ta_path,mod_input_name):
    json_file_name = "{}.cc.json".format(mod_input_name)
    json_dst_path_file = os.path.join(dst_ta_path,'bin',json_file_name)
    if os.path.exists(json_dst_path_file):
        rm_legacy_json_file = "rm -f {}".format(json_dst_path_file)
        os.system(rm_legacy_json_file)
    cp_cc_json_to_ta_cmd = "cp  -f {} {}".format(cc_json_path,json_dst_path_file)
    os.system(cp_cc_json_to_ta_cmd)


def test_start():
    install_cc_ucc.install_cc_ucc_libs()
    basedir = os.path.join(working_directory,"test","functional")
    cclib_path = os.path.join(basedir,"download_package","cc_ucc_lib","cloudconnectlib")
    ucclib_path = os.path.join(basedir,"download_package","cc_ucc_lib","splunktaucclib")
    logger.info("cclib path is %s", cclib_path)
    logger.info("ucclib path is %s",ucclib_path)
    sample_ta_path = os.path.join(basedir,"sample_ta")
    assert os.path.exists(cclib_path)
    assert os.path.exists(ucclib_path)
    use_latest_build.use_latest_cc_build(cclib_path,sample_ta_path)
    use_latest_build.use_latestucc_build(ucclib_path,sample_ta_path)

def test_snow_data_in():
    ta_name = "Splunk_TA_mysnow"
    snow_ta_path = ta_orig_path_temp.format(ta_name)
    conf_file_path = test_data.format("mysnow")
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(snow_ta_path)
    cp_conf_to_ta(conf_file_path,splunk_ta_path)
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string ="search index=main  sourcetype=my_snow_test1 "
    assert  searchutil.checkQueryCountIsGreaterThanZero(search_string)
    assert  searchutil.checkQueryCount(search_string,30)
    time.sleep(60)
    assert  searchutil.checkQueryCount(search_string,60)
    time.sleep(60)
    assert  searchutil.checkQueryCount(search_string,90)
    time.sleep(60)
    assert  searchutil.checkQueryCount(search_string,96)
    search_string ="search index=_internal source=*splunk_ta_my* ERROR"
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_snow_temp_certs_folder_created():
    okta2_temp_certs_folder_path = "{}/etc/apps/Splunk_TA_mysnow/temp_certs".format(SPLUNK_HOME)
    assert  os.path.exists(okta2_temp_certs_folder_path)

def test_okta2_data_in():

    ta_name = "Splunk_TA_myokta2"
    okta2_ta_path = ta_orig_path_temp.format(ta_name)
    conf_file_path = test_data.format("myokta2")
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(okta2_ta_path)
    cp_conf_to_ta(conf_file_path,splunk_ta_path)
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=_internal  source=*okta*  Update checkpoint \"tev68Sjkzb5SDuwxiJs1jh-Eg1352128663000\""
    searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal  source=*okta*  Update checkpoint \"tev6ciaHBwXRAerA4qVbW6T4A1352316074000\""
    searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal  source=*okta*  Update checkpoint \"tev6e8pxqEWRB2T7OBO3woNAA1354864915000\""
    searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal  source=*okta*  Get checkpoint \"tev6e8pxqEWRB2T7OBO3woNAA1354864915000\""
    time.sleep(60)
    # the second first
    search_string = "search index=_internal  source=*okta*  Update checkpoint \"tev70JF0jKPTh-KDm-bzxeP1Q1354916744000\""
    searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=main  sourcetype=my_okta2_test1 "
    assert  searchutil.checkQueryCount(search_string,18)
    search_string ="search index=_internal source=*splunk_ta_my* ERROR"
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_okta2_checkpoint_created():
    okta2_checkpoint_path = "{}/var/lib/splunk/modinputs/okta_inputs".format(SPLUNK_HOME)
    if os.path.exists(okta2_checkpoint_path):
        logger.info("checkpoint folder exists")
        okta2_checkpoint_name = os.path.join(okta2_checkpoint_path,"a513366788cad3face3bec0fb4dd8c16c68d1e0039703e46a2c64ca880e5be60")
        logger.info("checkpoint file %s",okta2_checkpoint_name)
        assert os.path.exists(okta2_checkpoint_name)
        return
    assert 0

def test_okta2_temp_certs_folder_created():
    okta2_temp_certs_folder_path = "{}/etc/apps/Splunk_TA_myokta2/temp_certs".format(SPLUNK_HOME)
    assert  os.path.exists(okta2_temp_certs_folder_path)

def test_mytest2_json_list_to_events():
    ta_name = "Splunk_TA_mytest2"
    test2_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(test2_ta_path)
    inputs_conf_file = "{}/inputs_bamboo.conf".format(test_data.format("mytest2"))
    account_conf_file = "{}/splunk_ta_mytest2_account.conf".format(test_data.format("mytest2"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,conf_type="inputs")
    cp_conf_to_ta(account_conf_file,splunk_ta_path,conf_type="account")
    local_splunk.start()
    searchutil = splunk_login(local_splunk,logger)
    time.sleep(60)
    search_string ="search index=main  sourcetype=test_bamboo "
    assert searchutil.checkQueryCount(search_string,25)
    time.sleep(60)
    assert searchutil.checkQueryCount(search_string,50)
    search_string ="search index=_internal source=*splunk_ta_my* ERROR"
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)




def test_mytest2_different_chaset():
    ta_name = "Splunk_TA_mytest2"
    mytest2_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(mytest2_ta_path)
    json_file = "{}/inputs_02_chaset.cc.json".format(test_data.format("mytest2"))
    cp_cc_json_to_ta(json_file,splunk_ta_path,"inputs_02")
    inputs_conf_file = "{}/inputs_charset.conf".format(test_data.format("mytest2"))
    accont_conf_file = "{}/splunk_ta_mytest2_account.conf".format(test_data.format("mytest2"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,conf_type="inputs")
    cp_conf_to_ta(accont_conf_file,splunk_ta_path,conf_type="account")
    local_splunk.start()
    searchutil = splunk_login(local_splunk,logger)
    time.sleep(60)
    search_string ="search index=main  sourcetype=test_charset_jd"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string ="search index=main  sourcetype=test_charset_google"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* google WARNING \"Failure decoding response content\""
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string ="search index=_internal source=*splunk_ta_my* ERROR earliest= -60s"
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)


def test_mytest2_pre_process():
    ta_name = "Splunk_TA_mytest2"
    test2_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)

    clean_local_splunk()
    cp_ta_to_splunk(test2_ta_path)
    json_file_path = "{}/inputs_02_pre_process.cc.json".format(test_data.format("mytest2"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"inputs_02")
    inputs_conf_file = "{}/inputs_pre_process.conf".format(test_data.format("mytest2"))
    account_conf_file = "{}/splunk_ta_mytest2_account.conf".format(test_data.format("mytest2"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,conf_type="inputs")
    cp_conf_to_ta(account_conf_file,splunk_ta_path,conf_type="others")

    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    searchstring = "search index=main sourcetype=pre_process_test"
    assert searchutil.checkQueryCount(searchstring,1)
    searchstring = "search index=main sourcetype =test_bamboo"
    assert searchutil.checkQueryCount(searchstring,50)



def test_mytest2_extracted_data_int():
    ta_name = "Splunk_TA_mytest2"
    mytest2_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(mytest2_ta_path)
    json_file_path = "{}/inputs_02_ADDON_13267.cc.json".format(test_data.format("mytest2"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"inputs_02")
    inputs_conf_file = "{}/inputs_int.conf".format(test_data.format("mytest2"))
    account_conf_file = "{}/splunk_ta_mytest2_account_int.conf".format(test_data.format("mytest2"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,conf_type="account")
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,conf_type="inputs")
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    searchstring = "search index=main sourcetype=test_int"
    assert searchutil.checkQueryCount(searchstring,3)
    searchstring = "search index=_internal source=*splunk_ta_my* ERROR"
    assert  not searchutil.checkQueryCountIsGreaterThanZero(searchstring)

def test_https_cert_warning():
    ta_name = "Splunk_TA_mytest2"
    mytest2_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(mytest2_ta_path)
    json_file_path = "{}/inputs_01_https_warning.cc.json".format(test_data.format("mytest2"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"inputs_01")
    inputs_conf_file = "{}/inputs_tenable.conf".format(test_data.format("mytest2"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/splunk_ta_mytest2_account_tenable.conf".format(test_data.format("mytest2"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=main sourcetype=test_https_waring \"utf-8\""
    assert searchutil.checkQueryCount(search_string,1)
    search_string = "search index=_internal source=*splunk_ta_my* log_level=warning  \"SSL: CERTIFICATE_VERIFY_FAILED\""
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)





def test_mytest_kvstore():
    ta_name = "Splunk_TA_mytest_kvstore"
    kvstore_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(kvstore_ta_path)
    inputs_conf_file = "{}/inputs.conf".format(test_data.format("kvstore"))
    account_conf_file = "{}/splunk_ta_mytest_kvstore_account.conf".format(test_data.format("kvstore"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,conf_type="others")
    local_splunk.start()
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,conf_type="inputs")
    local_splunk.restart()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    searchstring = "search index=main sourcetype=test_kv_1"
    assert searchutil.checkQueryCountIsGreaterThanZero(searchstring)
    searchstring = "search index=main sourcetype=test_kv_2"
    assert searchutil.checkQueryCountIsGreaterThanZero(searchstring)
    collection_file_path = os.path.join(splunk_ta_path,'local',"collections.conf")
    assert  os.path.exists(collection_file_path)
    searchstring = "search index=_internal source=*splunk_ta_my* \"Using KV store for checkpoint\""
    assert  searchutil.checkQueryCountIsGreaterThanZero(searchstring)
    time.sleep(60)
    search_string = "search index=_internal  source=*kv_1*  Get checkpoint \"tev6e8pxqEWRB2T7OBO3woNAA1354864915000\""
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal  source=*kv_2*  Get checkpoint \"tev6e8pxqEWRB2T7OBO3woNAA1354864915000\""
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal  source=*kv_1*  Update checkpoint \"tev70JF0jKPTh-KDm-bzxeP1Q1354916744000\""
    assert  searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal  source=*kv_2*  Update checkpoint \"tev70JF0jKPTh-KDm-bzxeP1Q1354916744000\""
    assert  searchutil.checkQueryCountIsGreaterThanZero(search_string)
    searchstring = "search index=_internaal  sourcetype=*splunk_ta_my* ERROR"
    assert not searchutil.checkQueryCountIsGreaterThanZero(searchstring)





def test_time_convert_epoch_time():
    ta_name = "Splunk_TA_myokta2"
    okta2_ta_path = ta_orig_path_temp.format(ta_name)
    conf_file_path = test_data.format("timeconvert")
    cc_json_path = "{}/okta_inputs_timeconvert.cc.json".format(conf_file_path)
    splunk_ta_path = "$SPLUNK_HOME/etc/apps/Splunk_TA_myokta2"
    clean_local_splunk()
    cp_ta_to_splunk(okta2_ta_path)
    cp_conf_to_ta(conf_file_path,splunk_ta_path)
    cp_cc_json_to_ta(cc_json_path,splunk_ta_path,"okta_inputs")
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=main  sourcetype=\"test_timeconvert\"  1352128663"

    assert searchutil.checkQueryCount(search_string,1)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR  limit=31352128663"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_time_convert_remove_T():
    ta_name = "Splunk_TA_myokta2"
    okta2_ta_path = ta_orig_path_temp.format(ta_name)
    conf_file_path = test_data.format("timeconvert")
    cc_json_path = "{}/okta_inputs_timeconvert2.cc.json".format(conf_file_path)
    splunk_ta_path = "$SPLUNK_HOME/etc/apps/Splunk_TA_myokta2"
    clean_local_splunk()
    cp_ta_to_splunk(okta2_ta_path)
    cp_conf_to_ta(conf_file_path,splunk_ta_path)
    cp_cc_json_to_ta(cc_json_path,splunk_ta_path,"okta_inputs")
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=main  sourcetype=test_timeconvert  \"2012-11-05 15:17:43\""

    assert searchutil.checkQueryCount(search_string,1)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR  limit=32012-11-05"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)




def test_proxy_http_no_auth():
    ta_name = "Splunk_TA_myokta"
    okta_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(okta_ta_path)
    proxy_conf = "{}/splunk_ta_myokta_settings_no_auth.conf".format(test_data.format("proxy"))
    cp_conf_to_ta(proxy_conf,splunk_ta_path,conf_type="settings")
    input_conf = "{}/inputs_no_auth.conf".format(test_data.format("proxy"))
    local_splunk.restart()
    cp_conf_to_ta(input_conf,splunk_ta_path,conf_type="inputs")
    local_splunk.restart()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=_internal source=*splunk_ta_my* \"Proxy is not enabled\""
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=main sourcetype=test_proxy_no_auth"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)


def test_proxy_http_auth():
    ta_name = "Splunk_TA_myokta"
    okta_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(okta_ta_path)
    proxy_conf = "{}/splunk_ta_myokta_settings_auth.conf".format(test_data.format("proxy"))
    cp_conf_to_ta(proxy_conf,splunk_ta_path,conf_type="settings")
    input_conf = "{}/inputs_auth.conf".format(test_data.format("proxy"))
    local_splunk.restart()
    cp_conf_to_ta(input_conf,splunk_ta_path,conf_type="inputs")
    local_splunk.restart()
    time.sleep(80)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=_internal source=*splunk_ta_my* \"Proxy is not enabled\""
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=main sourcetype=test_proxy_auth"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_proxy_http_auth_special_character():
    ta_name = "Splunk_TA_myokta"
    okta_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(okta_ta_path)
    proxy_conf = "{}/splunk_ta_myokta_settings_auth_special_character.conf".format(test_data.format("proxy"))
    cp_conf_to_ta(proxy_conf,splunk_ta_path,conf_type="settings")
    input_conf = "{}/inputs_auth_special_character.conf".format(test_data.format("proxy"))
    local_splunk.restart()
    cp_conf_to_ta(input_conf,splunk_ta_path,conf_type="inputs")
    local_splunk.restart()
    time.sleep(80)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=_internal source=*splunk_ta_my* \"Proxy is not enabled\""
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=main sourcetype=test_proxy_auth_special_character"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_proxy_http_wrong_auth():
    ta_name = "Splunk_TA_myokta"
    okta_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(okta_ta_path)
    proxy_conf = "{}/splunk_ta_myokta_settings_invalid_proxy.conf".format(test_data.format("proxy"))
    cp_conf_to_ta(proxy_conf,splunk_ta_path,conf_type="settings")
    input_conf = "{}/inputs_wrong_auth.conf".format(test_data.format("proxy"))
    local_splunk.restart()
    cp_conf_to_ta(input_conf,splunk_ta_path,conf_type="inputs")
    local_splunk.restart()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=_internal source=*splunk_ta_my* \"Proxy is not enabled\""
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=main sourcetype=test_proxy_wrong_auth"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR Proxy Authentication Required"
    assert  searchutil.checkQueryCountIsGreaterThanZero(search_string)


def test_update_proxy_from_backend():

    ta_name = "Splunk_TA_myokta"
    okta_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(okta_ta_path)
    proxy_conf = "{}/splunk_ta_myokta_settings_invalid_proxy.conf".format(test_data.format("proxy"))
    cp_conf_to_ta(proxy_conf,splunk_ta_path,conf_type="settings")
    input_conf = "{}/inputs_update.conf".format(test_data.format("proxy"))
    local_splunk.restart()
    cp_conf_to_ta(input_conf,splunk_ta_path,conf_type="inputs")
    local_splunk.restart()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=main sourcetype=test_proxy_update"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR Proxy Authentication Required"
    assert  searchutil.checkQueryCountIsGreaterThanZero(search_string)
    proxy_conf = "{}/splunk_ta_myokta_settings_auth_special_character.conf".format(test_data.format("proxy"))
    cp_conf_to_ta(proxy_conf,splunk_ta_path,conf_type="settings")
    time.sleep(120)
    search_string = "search index=main sourcetype=test_proxy_update"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_proxy_disabled():
    ta_name = "Splunk_TA_myokta"
    okta_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(okta_ta_path)
    proxy_conf = "{}/splunk_ta_myokta_settings_disabled.conf".format(test_data.format("proxy"))
    cp_conf_to_ta(proxy_conf,splunk_ta_path,conf_type="settings")
    input_conf = "{}/inputs_proxy_disabled.conf".format(test_data.format("proxy"))
    local_splunk.restart()
    cp_conf_to_ta(input_conf,splunk_ta_path,conf_type="inputs")
    local_splunk.restart()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=_internal source=*splunk_ta_my* \"Proxy is not enabled\""
    assert  searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=main sourcetype=test_proxy_disabled"
    assert  searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)


def test_logging_INFO():
    ta_name = "Splunk_TA_myokta"
    okta_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(okta_ta_path)
    logging_conf = "{}/splunk_ta_myokta_settings_INFO.conf".format(test_data.format("logging"))
    cp_conf_to_ta(logging_conf,splunk_ta_path,conf_type="settings")
    input_conf = "{}/inputs_INFO.conf".format(test_data.format("logging"))
    cp_conf_to_ta(input_conf,splunk_ta_path,conf_type="inputs")
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=main  sourcetype=test_logging_INFO "
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal log_level=INFO source=*splunk_ta_my*"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal  source=*splunk_ta_my* AND ( \"DEBUG\" OR \"ERROR\")"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_logging_ERROR():
    ta_name = "Splunk_TA_myokta"
    okta_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(okta_ta_path)
    logging_conf = "{}/splunk_ta_myokta_settings_ERROR.conf".format(test_data.format("logging"))
    cp_conf_to_ta(logging_conf,splunk_ta_path,conf_type="settings")
    input_conf = "{}/inputs_ERROR.conf".format(test_data.format("logging"))
    cp_conf_to_ta(input_conf,splunk_ta_path,conf_type="inputs")
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=_internal  source=*splunk_ta_my* log_level=ERROR \"The response status=400 for request which url=https://acme2.okta.com/api/v1/events?after=tev68-xxxxx&limit=3\""
    assert  searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal log_level=INFO source=*splunk_ta_my*"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_logging_WARNING():
    ta_name = "Splunk_TA_mytest2"
    mytest2_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(mytest2_ta_path)
    json_file_path = "{}/inputs_01_https_warning.cc.json".format(test_data.format("mytest2"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"inputs_01")
    inputs_conf_file = "{}/inputs_WARNING.conf".format(test_data.format("logging"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/splunk_ta_mytest2_account_tenable.conf".format(test_data.format("mytest2"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    logging_conf = "{}/splunk_ta_myokta_settings_WARNING.conf".format(test_data.format("logging"))
    cp_conf_to_ta(logging_conf,splunk_ta_path,"settings")
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=main sourcetype=test_logging_waring \"utf-8\""
    assert searchutil.checkQueryCount(search_string,1)
    search_string = "search index=_internal source=*splunk_ta_my* log_level=warning  \"SSL: CERTIFICATE_VERIFY_FAILED\""
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* INFO"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_logging_CRITICAL():
    ta_name = "Splunk_TA_myokta"
    okta_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(okta_ta_path)
    logging_conf = "{}/splunk_ta_myokta_settings_CRITICAL.conf".format(test_data.format("logging"))
    cp_conf_to_ta(logging_conf,splunk_ta_path,conf_type="settings")
    input_conf = "{}/inputs_CRITICAL.conf".format(test_data.format("logging"))
    cp_conf_to_ta(input_conf,splunk_ta_path,conf_type="inputs")
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=_internal  source=*splunk_ta_my* log_level=ERROR"
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal log_level=INFO source=*splunk_ta_my*"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=main sourcetype=test_logging_critical2"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_interation_count_0():
    ta_name = "Splunk_TA_mytest2"
    mytest2_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(mytest2_ta_path)
    json_file_path = "{}/inputs_01_interatoin_count_0.cc.json".format(test_data.format("interation_count"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"inputs_01")
    inputs_conf_file = "{}/inputs_01_interation_0.conf".format(test_data.format("interation_count"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/splunk_ta_mytest2_account.conf".format(test_data.format("interation_count"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    local_splunk.start()
    searchutil = splunk_login(local_splunk,logger)
    time.sleep(180)
    search_string = "search index=main sourcetype=test_interation_count_0"
    assert searchutil.checkQueryCount(search_string,100)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)


def test_interation_count_minus1():
    ta_name = "Splunk_TA_mytest2"
    mytest2_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(mytest2_ta_path)
    json_file_path = "{}/inputs_01_interation_count_minus_1.cc.json".format(test_data.format("interation_count"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"inputs_01")
    inputs_conf_file = "{}/inputs_01_interation_minus_1.conf".format(test_data.format("interation_count"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/splunk_ta_mytest2_account.conf".format(test_data.format("interation_count"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    local_splunk.start()
    searchutil = splunk_login(local_splunk,logger)
    time.sleep(200)
    search_string = "search index=main sourcetype=test_interation_count_minus_1"
    assert searchutil.checkQueryCount(search_string,100)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_interation_count_1000():
    ta_name = "Splunk_TA_mytest2"
    mytest2_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(mytest2_ta_path)
    json_file_path = "{}/inputs_01_interation_count_1000.cc.json".format(test_data.format("interation_count"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"inputs_01")
    inputs_conf_file = "{}/inputs_01_interation_1000.conf".format(test_data.format("interation_count"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/splunk_ta_mytest2_account.conf".format(test_data.format("interation_count"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    local_splunk.start()
    searchutil = splunk_login(local_splunk,logger)
    time.sleep(200)
    search_string = "search index=main sourcetype=test_interation_count_1000"
    assert searchutil.checkQueryCount(search_string,100)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string)
#
def test_two_inputs_does_not_impact_each_fake_account():
    ta_name = "Splunk_TA_mysnow"
    snow_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(snow_ta_path)
    json_file_path = "{}/snow_interation_count_minus1.cc.json".format(test_data.format("multiple_input"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"snow_inputs")
    inputs_conf_file = "{}/snow_inputs_2_one_using_fake_account.conf".format(test_data.format("multiple_input"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/snow_account_one_wrong.conf".format(test_data.format("multiple_input"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    local_splunk.start()
    time.sleep(120)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=main sourcetype=test_snow_input_correct_account"
    assert searchutil.checkQueryCount(search_string,96)
    search_string = "search index=_internal source=*splunk_ta_my*  snow_input_correct_account ERROR"
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string,retries=2)
    search_string = "search index=_internal source=*splunk_ta_my* snow_input_fake_account ERROR"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)


def test_two_inputs_does_not_impact_each_fake_server():
    ta_name = "Splunk_TA_mysnow"
    snow_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(snow_ta_path)
    json_file_path = "{}/snow_interation_count_minus1.cc.json".format(test_data.format("multiple_input"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"snow_inputs")
    inputs_conf_file = "{}/snow_inputs_2_one_wrong_server.conf".format(test_data.format("multiple_input"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/snow_account.conf".format(test_data.format("multiple_input"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    local_splunk.start()
    time.sleep(120)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=main sourcetype=test_snow_input_right_server"
    assert searchutil.checkQueryCount(search_string,96)
    search_string = "search index=_internal source=*splunk_ta_my*  snow_input_right_server ERROR"
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string,retries=2)
    search_string = "search index=_internal source=*splunk_ta_my* snow_input_wrong_server ERROR"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_32_inputs_data_all_in():
    ta_name = "Splunk_TA_mysnow"
    snow_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(snow_ta_path)
    json_file_path = "{}/snow_interation_count_minus1.cc.json".format(test_data.format("multiple_input"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"snow_inputs")
    inputs_conf_file = "{}/snow_32_inputs.conf".format(test_data.format("multiple_input"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/snow_account.conf".format(test_data.format("multiple_input"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    local_splunk.start()
    searchutil = splunk_login(local_splunk,logger)
    time.sleep(240)
    search_string ="search index=main  sourcetype=test_snow_input_multi*|dedup sourcetype "
    assert  searchutil.checkQueryCount(search_string,32)
    search_string = "search index=main sourcetype=test_snow_input_multi_9"
    assert  searchutil.checkQueryCount(search_string,96)
    search_string = "search index=main sourcetype=test_snow_input_multi*"
    assert  searchutil.checkQueryCount(search_string,3072)
    search_string ="search index=_internal source=*splunk_ta_my* ERROR"
    assert  not searchutil.checkQueryCountIsGreaterThanZero(search_string)

def test_remove_checkpoint_file_recovery():
    ta_name = "Splunk_TA_mysnow"
    snow_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(snow_ta_path)
    json_file_path = "{}/snow_interation_count_minus1.cc.json".format(test_data.format("checkpoint"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"snow_inputs")
    inputs_conf_file = "{}/snow_inputs.conf".format(test_data.format("checkpoint"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/snow_account.conf".format(test_data.format("checkpoint"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    local_splunk.start()
    searchutil = splunk_login(local_splunk,logger)
    time.sleep(120)
    search_string ="search index=main  sourcetype=test_checkpoint_remove_recovery"
    assert searchutil.checkQueryCount(search_string,96)
    checkpoint_file_dir="{}/var/lib/splunk/modinputs/snow_inputs/ceb30d5cc2cdb107c7e631b994d8075956e48ab0875e35f7390f6c1faf865bdf".format(SPLUNK_HOME)
    assert os.path.exists(checkpoint_file_dir)
    remove_checkpoint_file_cmd = "rm -f {}".format(checkpoint_file_dir)
    os.system(remove_checkpoint_file_cmd)
    time.sleep(120)
    assert searchutil.checkQueryCount(search_string,192)

def test_namespace_used_generated_checkpoint():
      ta_name = "Splunk_TA_mysnow"
      snow_ta_path = ta_orig_path_temp.format(ta_name)
      splunk_ta_path = ta_dest_path_temp.format(ta_name)
      clean_local_splunk()
      cp_ta_to_splunk(snow_ta_path)
      json_file_path = "{}/snow_namespace_as_checkpoint.cc.json".format(test_data.format("checkpoint"))
      cp_cc_json_to_ta(json_file_path,splunk_ta_path,"snow_inputs")
      inputs_conf_file = "{}/snow_inputs_namespace.conf".format(test_data.format("checkpoint"))
      cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
      account_conf_file = "{}/snow_account.conf".format(test_data.format("checkpoint"))
      cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
      local_splunk.start()
      searchutil = splunk_login(local_splunk,logger)
      time.sleep(120)
      search_string ="search index=main  sourcetype=test_namespace_as_checkpoint"
      assert searchutil.checkQueryCount(search_string,96)
      checkpoint_file_dir="{}/var/lib/splunk/modinputs/snow_inputs/ff4bb432b6a7d0cac35577bafbef0c130affa9e3a00f2f99790f8a1582a7ba3b".format(SPLUNK_HOME)
      assert os.path.exists(checkpoint_file_dir)

def test_api_version_check():
    ta_name = "Splunk_TA_mytest2"
    mytest2_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(mytest2_ta_path)
    json_file_path = "{}/inputs_01_api_version_check.cc.json".format(test_data.format("others"))
    cp_cc_json_to_ta(json_file_path,splunk_ta_path,"inputs_01")
    inputs_conf_file = "{}/inputs_01_api_version_check.conf".format(test_data.format("others"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/splunk_ta_mytest2_account.conf".format(test_data.format("others"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=_internal source=*splunk_ta_my* \"Unsupported schema version 1.1.0\""
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=main sourcetype=test_api_version_check"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string,retries=2)

def test_no_logging_used_static_url():
    ta_name = "Splunk_TA_mytest"
    mytest_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(mytest_ta_path)
    inputs_conf_file =  "{}/inputs_01_no_logging_used.conf".format(test_data.format("others"))
    cp_conf_to_ta(inputs_conf_file,splunk_ta_path,"inputs")
    account_conf_file = "{}/splunk_ta_mytest_no_logging_account.conf".format(test_data.format("others"))
    cp_conf_to_ta(account_conf_file,splunk_ta_path,"account")
    local_splunk.start()
    time.sleep(60)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=main sourcetype=test_use_no_logging"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string,retries=2)
    search_string = "search index=_internal source=*splunk_ta_my* The log level \"None\" is invalid, set it to default: \"INFO\""
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)


def test_solarwind_data_in():
    ta_name = "Splunk_TA_mysolarwinds"
    mytest_ta_path = ta_orig_path_temp.format(ta_name)
    splunk_ta_path = ta_dest_path_temp.format(ta_name)
    clean_local_splunk()
    cp_ta_to_splunk(mytest_ta_path)
    local_splunk.start()
    time.sleep(120)
    searchutil = splunk_login(local_splunk,logger)
    search_string = "search index=main sourcetype=test_solarwind_data_in"
    assert searchutil.checkQueryCountIsGreaterThanZero(search_string)
    search_string = "search index=_internal source=*splunk_ta_my* ERROR"
    assert not searchutil.checkQueryCountIsGreaterThanZero(search_string,retries=2)

def test_teardown():
    local_splunk.stop()

