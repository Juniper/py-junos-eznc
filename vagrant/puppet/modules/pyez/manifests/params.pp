class pyez::params {
	$packages = $operatingsystem ? {
		/(?i-mx:ubuntu|debian)/        => ['python-pip', 'python-dev', 'libxml2-dev', 'libxslt-dev'],		
		/(?i-mx:centos|fedora|redhat)/ => ['python-pip', 'python-devel', 'libxml2-devel', 'libxslt-devel', 'gcc'],
		/(?i-mx:freebsd)/        => ['devel/py27-pip', 'textproc/libxml2', 'textproc/libxslt'],
	}
	$version = 'present'
	$mode = 'pypi'
	}