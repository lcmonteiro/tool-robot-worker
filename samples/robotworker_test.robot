*** Settings ***
Documentation     Test Samples for Robotworker

*** Test Cases ***

Get Services
    [Documentation]    Get services available in this server.
    [Tags]  worker
    Log To Console  hi services
