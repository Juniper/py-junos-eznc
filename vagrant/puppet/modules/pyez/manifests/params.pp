class pyez::params {
	$packages = $operatingsystem ? {
		/(?i-mx:ubuntu)/        => ['python-pip', 'libpython2.7-dev', 'libxml2-dev', 'libxslt-dev'],
		/(?i-mx:debian)/        => ['python-pip', 'python2.7-dev', 'libxml2-dev', 'libxslt-dev'],
		/(?i-mx:centos|fedora|redhat)/ => ['python-pip', 'python-devel', 'libxml2-devel', 'libxslt-devel'],
		/(?i-mx:freebsd)/        => ['devel/py27-pip', 'textproc/libxml2', 'textproc/libxslt'],
	}
	$version = 'present'
	$mode = 'pypi'
	}