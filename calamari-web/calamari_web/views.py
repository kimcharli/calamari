

from django.views.static import serve as static_serve
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, \
    HttpResponseServerError
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.decorators.csrf import requires_csrf_token

import zerorpc

from calamari_common.config import CalamariConfig
config = CalamariConfig()


def home(request):
    return HttpResponseRedirect(reverse('dashboard', kwargs={'path': ''}))


@login_required
def serve_dir_or_index(request, path, document_root):
    if len(path) == 0:
        path = 'index.html'
    return static_serve(request, path, document_root)


@login_required
def dashboard(request, path, document_root):
    client = zerorpc.Client()
    client.connect(config.get('cthulhu', 'rpc_url'))
    try:
        clusters = client.list_clusters()
    finally:
        client.close()
    if not clusters:
        return redirect("/admin/#cluster")
    return serve_dir_or_index(request, path, document_root)


@requires_csrf_token
def server_error(request, template_name='500.html'):
    """
    Just like Django's default views.defaults.server_error, except we
    don't search for templates, because Graphite has its own set of
    templates that we don't want to use
    """
    return HttpResponseServerError('<h1>Server Error (500)</h1>')


BOOTSTRAP_TEMPLATE = """
# Calamari minion bootstrap script.
#
# When downloaded from a calamari server instance, downloads
# calamari-salt-minion from that URL before installing it and configuring
# it to point to the server address.
#
# The calamari server will attempt to infer the HTTP and Salt addresses
# from the Host: used to download the script, if this fails override them
# on the command line.  The HTTP URL and Salt master address are the first
# and second arguments to this script.
#
# This script will refuse to run if a supported operating system is not detected.
# In case the detection is not working correctly, you may override this by passing
# the distribution type on the command line as the third argument.


import sys
import os
import subprocess
import errno


CENTOS = 'centos'
REDHAT = 'redhat'
UBUNTU = 'ubuntu'
DEBIAN = 'debian'
DISTROS = [CENTOS, REDHAT, UBUNTU, DEBIAN]

SUPPORT_MATRIX = "Inktank Ceph Enterprise supports RHEL 6.3, RHEL 6.4, CentOS 6.3, CentOS 6.4, " \
                 "Ubuntu 12.04 LTS, and Debian 7."

SALT_PACKAGE = "salt-minion"
SALT_CONFIG_PATH = "/etc/salt/"

if len(sys.argv) > 1:
    BASE_URL = sys.argv[1]
else:
    BASE_URL = "{base_url}"

if len(sys.argv) > 2:
    MASTER = sys.argv[2]
else:
    MASTER = "{master}"

if len(sys.argv) > 3:
    distro = sys.argv[3]
    if distro not in DISTROS:
        print "Invalid distribution '%s', must be in %s" % (distro, DISTROS)
else:
    distro = None

try:
    ps = subprocess.Popen(["lsb_release", "-d", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    ps_out, ps_err = ps.communicate()
except OSError:
    print "Error querying LSB version"
    print SUPPORT_MATRIX
    sys.exit(-1)
else:
    lsb_release = ps_out.strip(" \\"")

if lsb_release.startswith("CentOS release 6."):
    distro = CENTOS
elif lsb_release.startswith("Red Hat Enterprise Linux Server release 6."):
    distro = REDHAT
elif lsb_release.startswith("Ubuntu 12.04"):
    distro = UBUNTU
elif lsb_release.startswith("Debian GNU/Linux 7."):
    distro = DEBIAN
else:
    print "Unsupported distribution '%s'" % lsb_release
    print SUPPORT_MATRIX
    sys.exit(-1)

# Configure package repository
if distro in [CENTOS, REDHAT]:
    open("/etc/yum.repos.d/calamari.repo", 'w').write(
    "[el6-calamari]\\n" \
"name=Calamari\\n" \
"baseurl={base_url}static/el6\\n" \
"gpgcheck=0\\n" \
"enabled=1\\n")
elif distro == UBUNTU:
    # Would be nice to use apt-add-repository, but it's not always there and
    # trying to apt-get install it from the net would be a catch-22
    open("/etc/apt/sources.list.d/calamari.list", 'w').write("deb {base_url}static/ubuntu precise main")
elif distro == DEBIAN:
    open("/etc/apt/sources.list.d/calamari.list", 'w').write("deb {base_url}static/debian wheezy main")
else:
    # Should never happen
    raise NotImplmentedError()

# Emplace minion config prior to installation so that it is present
# when the minion first starts.
try:
    os.makedirs(os.path.join(SALT_CONFIG_PATH, "minion.d"))
except OSError, e:
    if e.errno == errno.EEXIST:
        pass
    else:
        raise

open(os.path.join(SALT_CONFIG_PATH, "minion.d/calamari.conf"), 'w').write("master: %s\\n" % MASTER)

# Deploy salt minion
if distro in [CENTOS, REDHAT]:
    subprocess.call(["yum", "check-update"])
    subprocess.check_call(["yum", "install", "-y", SALT_PACKAGE])
    subprocess.check_call(["chkconfig", "salt-minion", "on"])
    subprocess.check_call(["service", "salt-minion", "start"])
else:
    subprocess.check_call(["apt-get", "update"])
    subprocess.check_call(["apt-get", "install", "-y", "--force-yes", SALT_PACKAGE])

"""


def bootstrap(request):
    # Best effort to work out the URL that the client used to access
    # this server
    proto = "https" if request.is_secure() else "http"
    http_host = request.META['HTTP_HOST']
    my_url = "{0}://{1}/".format(proto, http_host)
    my_hostname = http_host.split(":")[0]

    bootstrap_script = BOOTSTRAP_TEMPLATE.format(
        base_url=my_url, master=my_hostname
    )

    return HttpResponse(bootstrap_script)
