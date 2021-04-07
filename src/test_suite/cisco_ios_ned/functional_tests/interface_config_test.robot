*** Settings ***
Library                 NsoSsh

*** Variables ***
${HOST}                 192.168.20.60
${PORT}                 8080
${USERNAME}             root
${PASSWORD}             dvrlab
${LOGPATH}              /var/log/ncs
@{LOG_FILES}            devel.log  ncs.log  audit.log  netconf-csr1000v.trace

*** Test Cases ***
Configure an interface with a cisco ios ned
    Given setup nso
    And get log files

*** Keywords ***
Setup Nso
    Setup All  ${USERNAME}  ${PASSWORD}  ${HOST}  ${PORT}

Get Log Files
    Get Files  ${LOG_FILES}  ${LOGPATH}