# -*- python -*-

# slight code duplication with hamster/__init__.py, but this is finally cleaner.
from subprocess import getstatusoutput
rc, output = getstatusoutput("git describe --tags --always --dirty=+")
VERSION = "3.0-beta" if rc else output

APPNAME = 'hamster'

top = '.'
out = 'build'

import os
from waflib import Logs, Utils


def configure(conf):
    conf.load('gnu_dirs')  # for DATADIR
    
    if not conf.options.skip_gsettings:
        conf.load('glib2')  # for GSettings support
    
    conf.load('python')
    conf.check_python_version(minver=(3,4,0))

    conf.load('intltool')

    conf.env.ENABLE_NLS = 1
    conf.env.HAVE_BIND_TEXTDOMAIN_CODESET = 1

    conf.env.VERSION = VERSION
    conf.env.GETTEXT_PACKAGE = "hamster"
    conf.env.PACKAGE = "hamster"
    
    conf.recurse("help")
    
    # options are tied to a specific ./waf invocation (one terminal line),
    # and woud have to be given again at any other ./waf invocation
    # that is trouble when one wants to ./waf uninstall much later;
    # it can be hard to remember the exact options used at the install step.
    # So from now on, options have to be given at the configure step only.
    # copy the options to the persistent env:
    for name in ('prefix', 'skip_gsettings'):
        value = getattr(conf.options, name)
        setattr(conf.env, name, value)


# used first, should be at the top
def options(ctx):
    ctx.load('gnu_dirs')

    # the waf default value is /usr/local, which causes issues (e.g. #309)
    # ctx.parser.set_defaults(prefix='/usr') did not update the help string,
    # hence need to replace the whole option
    ctx.parser.remove_option('--prefix')
    default_prefix = '/usr'
    
    ctx.add_option('--prefix', dest='prefix', default=default_prefix,
                   help='installation prefix [default: {}]'.format(default_prefix))
    
    ctx.add_option('--skip-gsettings', dest='skip_gsettings', action='store_true',
                   help='skip gsettings schemas build and installation (for packagers)')
    

def build(bld):
    bld.install_as('${LIBEXECDIR}/hamster/hamster-service', "src/hamster-service.py", chmod=Utils.O755)
    bld.install_as('${LIBEXECDIR}/hamster/hamster-windows-service', "src/hamster-windows-service.py", chmod=Utils.O755)
    bld.install_as('${BINDIR}/hamster', "src/hamster-cli.py", chmod=Utils.O755)


    bld.install_files('${PREFIX}/share/bash-completion/completions',
                      'src/hamster.bash')


    bld(features='py',
        source=bld.path.ant_glob('src/hamster/**/*.py'),
        install_from='src')

    # set correct flags in defs.py
    bld(features="subst",
        source="src/hamster/defs.py.in",
        target="src/hamster/defs.py",
        install_path="${PYTHONDIR}/hamster"
        )

    bld(features="subst",
        source= "org.gnome.Hamster.service.in",
        target= "org.gnome.Hamster.service",
        install_path="${DATADIR}/dbus-1/services",
        )

    bld(features="subst",
        source= "org.gnome.Hamster.GUI.service.in",
        target= "org.gnome.Hamster.GUI.service",
        install_path="${DATADIR}/dbus-1/services",
        )

    bld(features="subst",
        source= "org.gnome.Hamster.WindowServer.service.in",
        target= "org.gnome.Hamster.WindowServer.service",
        install_path="${DATADIR}/dbus-1/services",
        )

    bld.recurse("po data help")

    if not bld.env.skip_gsettings:
        bld(features='glib2',
            settings_schema_files=['data/org.gnome.hamster.gschema.xml'])

    def update_icon_cache(ctx):
        """Update the gtk icon cache."""
        if ctx.cmd == "install":
            # adapted from the previous waf gnome.py
            icon_dir = os.path.join(ctx.env.DATADIR, 'icons/hicolor')
            cmd = 'gtk-update-icon-cache -q -f -t {}'.format(icon_dir)
            err = ctx.exec_command(cmd)
            if err:
                Logs.warn('The following  command failed:\n{}'.format(cmd))
            else:
                Logs.pprint('YELLOW', 'Successfully updated GTK icon cache')


    bld.add_post_fun(update_icon_cache)
