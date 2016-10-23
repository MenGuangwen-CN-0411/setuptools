import os
from distutils import log

from setuptools.extern.six.moves import map


class Installer:

    def install_namespaces(self):
        nsp = self._get_all_ns_packages()
        if not nsp:
            return
        filename, ext = os.path.splitext(self.target)
        filename += '-nspkg.pth'
        self.outputs.append(filename)
        log.info("Installing %s", filename)
        lines = map(self._gen_nspkg_line, nsp)

        if self.dry_run:
            # always generate the lines, even in dry run
            list(lines)
            return

        with open(filename, 'wt') as f:
            f.writelines(lines)

    _nspkg_tmpl = (
        "import sys, types, os",
        "pep420 = sys.version_info > (3, 3)",
        "p = os.path.join(sys._getframe(1).f_locals['sitedir'], *%(pth)r)",
        "ie = os.path.exists(os.path.join(p,'__init__.py'))",
        "m = not ie and not pep420 and "
            "sys.modules.setdefault(%(pkg)r, types.ModuleType(%(pkg)r))",
        "mp = (m or []) and m.__dict__.setdefault('__path__',[])",
        "(p not in mp) and mp.append(p)",
    )
    "lines for the namespace installer"

    _nspkg_tmpl_multi = (
        'm and setattr(sys.modules[%(parent)r], %(child)r, m)',
    )
    "additional line(s) when a parent package is indicated"

    @classmethod
    def _gen_nspkg_line(cls, pkg):
        # ensure pkg is not a unicode string under Python 2.7
        pkg = str(pkg)
        pth = tuple(pkg.split('.'))
        tmpl_lines = cls._nspkg_tmpl
        parent, sep, child = pkg.rpartition('.')
        if parent:
            tmpl_lines += cls._nspkg_tmpl_multi
        return ';'.join(tmpl_lines) % locals() + '\n'

    def _get_all_ns_packages(self):
        """Return sorted list of all package namespaces"""
        nsp = set()
        for pkg in self.distribution.namespace_packages or []:
            pkg = pkg.split('.')
            while pkg:
                nsp.add('.'.join(pkg))
                pkg.pop()
        return sorted(nsp)
