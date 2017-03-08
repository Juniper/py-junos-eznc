# Examples of using the Docker image

## To run interactive PyEZ (aka Junos power shell):

`docker run -it juniper/pyez python`

```
$ docker run -it juniper/pyez python
Python 2.7.12 (default, Jun 29 2016, 08:57:23)
[GCC 5.3.0] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> from jnpr.junos import Device
>>> import sys
>>> dev = Device('vmx', user='user',passwd='pass')
>>> dev.open()
>>> print dev.facts
{'2RE': False, 'model': 'VMX'}
>>> quit()
$
```

## As an executable package: 

`docker run -it -v /some/dir:/scripts juniper/pyez python some_script.py options arguments`

```
$ cd fetcher/
$ docker run -it -v $PWD:/scripts juniper/pyez python fetcher.py
Enter filename: hosts.csv
Username: user
Password: 
====================================================================================================
Inventory Report
----------------------------------------------------------------------------------------------------
All done. Please see errors.txt for any errors.
```
 
In this way, we can use the combination of Docker image + pyez script as an executable. Pretty neat huh? Oh, and in case you were wondering about the error logs (in this case exceptions are logged to a file, not just to stdout), they are written to the file and accessible from the host.

```
$ cat fetcher/errors.txt 
Cannot connect to device: ConnectTimeoutError(vmx.local)
```

## As a PyEZ terminal

`docker run -it juniper/pyez`

```
$ cd fetcher/
$ docker run -it -v $PWD:/scripts juniper/pyez
/scripts # ls
README.md   errors.txt  fetcher.py  hosts.csv
/scripts # python fetcher.py
Enter filename: hosts.csv
Username: user
Password: 
====================================================================================================
Inventory Report
----------------------------------------------------------------------------------------------------
All done. Please see errors.txt for any errors.
```

## Make a bash alias to use it as an executable:

```
$ alias pyez="docker run -it --rm -v $PWD:/scripts juniper/pyez python"
$ pyez some_script.py
```