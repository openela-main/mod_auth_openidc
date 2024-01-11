%{!?_httpd_mmn: %{expand: %%global _httpd_mmn %%(cat %{_includedir}/httpd/.mmn 2>/dev/null || echo 0-0)}}
%{!?_httpd_moddir: %{expand: %%global _httpd_moddir %%{_libdir}/httpd/modules}}
%{!?_httpd_confdir: %{expand: %%global _httpd_confdir %{_sysconfdir}/httpd/conf.d}}

# Optionally build with hiredis if --with hiredis is passed
%{!?_with_hiredis: %{!?_without_hiredis: %global _without_hiredis --without-hiredis}}
# It is an error if both or neither required options exist.
%{?_with_hiredis: %{?_without_hiredis: %{error: both _with_hiredis and _without_hiredis}}}
%{!?_with_hiredis: %{!?_without_hiredis: %{error: neither _with_hiredis nor _without_hiredis}}}

# /etc/httpd/conf.d with httpd < 2.4 and defined as /etc/httpd/conf.modules.d with httpd >= 2.4
%{!?_httpd_modconfdir: %{expand: %%global _httpd_modconfdir %%{_sysconfdir}/httpd/conf.d}}

%global httpd_pkg_cache_dir /var/cache/httpd/mod_auth_openidc

Name:		mod_auth_openidc
Version:	2.4.9.4
Release:	1%{?dist}
Summary:	OpenID Connect auth module for Apache HTTP Server

License:	ASL 2.0
URL:		https://github.com/zmartzone/mod_auth_openidc
Source0:	https://github.com/zmartzone/mod_auth_openidc/archive/v%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:	httpd-devel
BuildRequires:	openssl-devel
BuildRequires:	curl-devel
BuildRequires:	jansson-devel
BuildRequires:	pcre-devel
BuildRequires:	autoconf
BuildRequires:	automake
BuildRequires:	cjose-devel
BuildRequires:	jq-devel
%{?_with_hiredis:BuildRequires: hiredis-devel}
Requires:	httpd-mmn = %{_httpd_mmn}

%description
This module enables an Apache 2.x web server to operate as
an OpenID Connect Relying Party and/or OAuth 2.0 Resource Server.

%prep
%setup -q

%build
# workaround rpm-buildroot-usage
export MODULES_DIR=%{_httpd_moddir}
export APXS2_OPTS='-S LIBEXECDIR=${MODULES_DIR}'
autoreconf
%configure \
  --with-jq=/usr/lib64/ \
  %{?_with_hiredis} \
  %{?_without_hiredis} \
  --with-apxs2=%{_httpd_apxs}


%{make_build}

%check
export MODULES_DIR=%{_httpd_moddir}
export APXS2_OPTS='-S LIBEXECDIR=${MODULES_DIR}'
make test

%install
mkdir -p $RPM_BUILD_ROOT%{_httpd_moddir}
make install MODULES_DIR=$RPM_BUILD_ROOT%{_httpd_moddir}

install -m 755 -d $RPM_BUILD_ROOT%{_httpd_modconfdir}
echo 'LoadModule auth_openidc_module modules/mod_auth_openidc.so' > \
	$RPM_BUILD_ROOT%{_httpd_modconfdir}/10-auth_openidc.conf

install -m 755 -d $RPM_BUILD_ROOT%{_httpd_confdir}
install -m 644 auth_openidc.conf $RPM_BUILD_ROOT%{_httpd_confdir}
# Adjust httpd cache location in install config file
sed -i 's!/var/cache/apache2/!/var/cache/httpd/!' $RPM_BUILD_ROOT%{_httpd_confdir}/auth_openidc.conf
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}/metadata
install -m 700 -d $RPM_BUILD_ROOT%{httpd_pkg_cache_dir}/cache


%files
%if 0%{?rhel} && 0%{?rhel} < 7
%doc LICENSE.txt
%else
%license LICENSE.txt
%endif
%doc ChangeLog
%doc AUTHORS
%doc README.md
%{_httpd_moddir}/mod_auth_openidc.so
%config(noreplace) %{_httpd_modconfdir}/10-auth_openidc.conf
%config(noreplace) %{_httpd_confdir}/auth_openidc.conf
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}/metadata
%dir %attr(0700, apache, apache) %{httpd_pkg_cache_dir}/cache

%changelog
* Fri Apr 8 2022 Tomas Halman <thalman@redhat.com> - 2.4.9.4-1
- Resolves: rhbz#2025368 - Rebase to new version

* Fri Jan 28 2022 Tomas Halman <thalman@redhat.com> - 2.3.7-11
- Resolves: rhbz#1987222 - CVE-2021-32792 XSS when using OIDCPreservePost On

* Fri Jan 28 2022 Tomas Halman <thalman@redhat.com> - 2.3.7-10
- Resolves: rhbz#1987216 - CVE-2021-32791 hardcoded static IV and AAD with a
                           reused key in AES GCM encryption [rhel-8] (edit) 

* Fri Oct 29 2021 Tomas Halman <thalman@redhat.com> - 2.3.7-9
- Resolves: rhbz#2001853 - CVE-2021-39191 open redirect by supplying a crafted URL
                           in the target_link_uri parameter

* Tue Nov 17 2020 Jakub Hrozek <jhrozek@redhat.com> - 2.3.7-8
- Resolves: rhbz#1823756 - Backport SameSite=None cookie from
                           mod_auth_openidc upstream to support latest browsers

* Tue Nov 17 2020 Jakub Hrozek <jhrozek@redhat.com> - 2.3.7-7
- Resolves: rhbz#1897992 - OIDCStateInputHeaders &
                           OIDCStateMaxNumberOfCookies in existing
                           mod_auth_openidc version
- Backport the OIDCStateMaxNumberOfCookies option
- Configure which header value is used to calculate the fingerprint of
  the auth state

* Sun May 10 2020 Jakub Hrozek <jhrozek@redhat.com> - 2.3.7-6
- Fix the previous backport
- Related: rhbz#1805749 - CVE-2019-14857 mod_auth_openidc:2.3/mod_auth_openidc:
                          Open redirect in logout url when using URLs with
                          leading slashes
- Related: rhbz#1805068 - CVE-2019-20479 mod_auth_openidc:2.3/mod_auth_openidc:
                          open redirect issue exists in URLs with slash and
                          backslash

* Sun May 10 2020 Jakub Hrozek <jhrozek@redhat.com> - 2.3.7-5
- Resolves: rhbz#1805749 - CVE-2019-14857 mod_auth_openidc:2.3/mod_auth_openidc:
                           Open redirect in logout url when using URLs with
                           leading slashes
- Resolves: rhbz#1805068 - CVE-2019-20479 mod_auth_openidc:2.3/mod_auth_openidc:
                           open redirect issue exists in URLs with slash and
                           backslash

* Thu Aug 16 2018  <jdennis@redhat.com> - 2.3.7-3
- Resolves: rhbz# 1614977 - fix unit test segfault,
  the problem was not limited exclusively to s390x, but s390x provoked it.

* Fri Aug 10 2018  <jdennis@redhat.com> - 2.3.7-2
- disable running check on s390x

* Wed Aug  1 2018  <jdennis@redhat.com> - 2.3.7-1
- upgrade to upstream 2.3.7

* Fri Jul 13 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2.3.5-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Wed May 23 2018 Patrick Uiterwijk <patrick@puiterwijk.org> - 2.3.5-1
- Rebase to 2.3.5

* Fri Feb 09 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 1.8.10.1-7
- Escape macros in %%changelog

* Thu Feb 08 2018 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.10.1-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Thu Aug 03 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.10.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.10.1-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Sat Feb 18 2017 John Dennis <jdennis@redhat.com> - 1.8.10.1-3
- Resolves: #1423956 fails to build with openssl 1.1.x
  Also rolls up all fixes to jose library before the change over to cjose

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.10.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Tue Jul 12 2016 John Dennis <jdennis@redhat.com> - 1.8.10.1-1
- Upgrade to new upstream
  See /usr/share/doc/mod_auth_openidc/ChangeLog for details

* Tue Mar 29 2016 John Dennis <jdennis@redhat.com> - 1.8.8-4
- Add %%check to run test

* Wed Mar 23 2016 John Dennis <jdennis@redhat.com> - 1.8.8-3
- Make building with redis support optional (defaults to without)

* Mon Mar 21 2016 John Dennis <jdennis@redhat.com> - 1.8.8-2
- Add missing unpackaged files/directories

  Add to doc: README.md, DISCLAIMER, AUTHORS
  Add to httpd/conf.d: auth_openidc.conf
  Add to /var/cache: /var/cache/httpd/mod_auth_openidc/cache
                     /var/cache/httpd/mod_auth_openidc/metadata

* Thu Mar 10 2016 Jan Pazdziora <jpazdziora@redhat.com> 1.8.8-1
- Update to 1.8.8 (#1316528)

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.8.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Sat Jan 09 2016 Fedora Release Monitoring <release-monitoring@fedoraproject.org> - 1.8.7-1
- Update to 1.8.7 (#1297080)

* Sat Nov 07 2015 Jan Pazdziora <jpazdziora@redhat.com> 1.8.6-1
- Initial packaging for Fedora 23.
