*** Settings ***
Library                 NsoSsh
Library                 Nso  ${HOST}  ${USERNAME}  ${PASSWORD}

*** Variables ***
${HOST}                 192.168.20.60
${PORT}                 8080
${USERNAME}             root
${PASSWORD}             dvrlab
${LOGPATH}              /var/log/ncs
@{LOG_FILES}            devel.log  ncs.log  audit.log  netconf-csr1000v.trace
${DEVICE_NAME}          csr1000v

*** Test Cases ***
Configure an interface with the cisco ios ned
    Given setup nso
    And verify device
    Then verify compare config
    And get log files

*** Keywords ***
Setup Nso
    Setup All  ${USERNAME}  ${PASSWORD}  ${HOST}  ${PORT}

Verify Device
    Validate Device Exists  ${DEVICE_NAME}

Verify Compare Config
    Compare Config  ${DEVICE_NAME}

Get Log Files
    Get Files  ${LOG_FILES}  ${LOGPATH}