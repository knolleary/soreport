Daily Stack Overflow report for Little Printer
=======

Django app for a Little Printer publication that generates a daily report of your StackOverflow activity

http://kahiti.knolleary.net/soreport/sample

It *could* be used for other sites in the Stack Exchange network, but is currently hardcoded to Stack Overflow.

Subscribe your Little Printer to the publication on the [BERG Cloud Remote](http://remote.bergcloud.com/publications/181)


### Settings

To install this app, a new application must be registered at http://stackapps.com to allow authenticated access to the StackOverflow API.

Once registered, the following options must be provided in the django app's settings:

    SOREPORT_CLIENT_ID
    SOREPORT_CLIENT_SECRET
    SOREPORT_KEY
