# Class: pyez
#
# This module manages pyez
#
# Parameters: none
#
# Actions:
#
# Requires: see Modulefile
#
# Sample Usage:
#
class pyez (
  $packages  = $pyez::params::packages,
  $version  = $pyez::params::version,
  $freebsdsource = $pyez::params::freebsdsource,
  $mode = $pyez::params::mode,
  ) inherits pyez::params {
 
  # FreeBSD 9.2 has a buggy version of Puppet.  This is a hack for now.
  if $operatingsystem == 'FreeBSD' {	
	package { 'devel/py27-pip':
		ensure => installed,
		source => 'ftp://ftp.freebsd.org/pub/FreeBSD/ports/amd64/packages-9.2-release/devel/py27-pip-1.4.tbz',
		before => Package['junos-eznc'],
		}			
	package { 'textproc/libxml2':
		ensure => installed,
		source => 'ftp://ftp.freebsd.org/pub/FreeBSD/ports/amd64/packages-9.2-release/textproc/libxml2-2.8.0_2.tbz',
		before => Package['junos-eznc'],
		}	
	package { 'textproc/libxslt':
		ensure => installed,
		source => 'ftp://ftp.freebsd.org/pub/FreeBSD/ports/amd64/packages-9.2-release/textproc/libxslt-1.1.28_1.tbz',
		before => Package['junos-eznc'],
		}
		
	Package <| title == 'git' |> {
		name  => 'devel/git',
		source => 'ftp://ftp.freebsd.org/pub/FreeBSD/ports/amd64/packages-9.2-release/devel/git-1.8.3.4.tbz'
	}	
  } 

  else {
	package { $packages: ensure => 'present',
		before => Package['junos-eznc'],} 
	}
  
  
  if $mode == 'git' {
	package{ 'git':
	ensure => present,
	before => Package['junos-eznc'],
	}
  
	package{ 'junos-eznc':
	ensure   => $version,
	provider => 'pip',
	source   => 'git+https://github.com/Juniper/py-junos-eznc.git'
	}
  }
  
  else {
	package{ 'junos-eznc':
	ensure   => $version,
	provider => 'pip',	
	}
  }  

}
