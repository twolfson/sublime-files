import base64
import binascii
import os
import threading
from urllib.error import URLError
from urllib.request import build_opener, install_opener, ProxyHandler, urlopen

import sublime
import sublime_api
import sublime_plugin


class InstallPackageControlCommand(sublime_plugin.ApplicationCommand):

    error_prefix = 'Error installing Package Control: '
    filename = 'Package Control.sublime-package'
    public_key = (
        'MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEkiE2JtDn/IQDfVLso4HRg0BNMHNj'
        '5rpuEIVaX6txyFS0HoBmCgd+9AXKcgKAsBKbEBD6a9nVzLLmJrDVFafepQ==')

    def run(self):
        threading.Thread(target=self._install).start()

    def is_visible(self):
        ipp_path = os.path.join(sublime.installed_packages_path(), self.filename)
        p_path = os.path.join(sublime.packages_path(), self.filename.replace('.sublime-package', ''))

        return not os.path.exists(ipp_path) and not os.path.exists(p_path)

    def _install(self):
        """
        RUNS IN A THREAD

        Downloads and then installs Package Control, alerting the user to
        the result
        """

        try:
            package_data = self._download()
            if package_data is None:
                sublime.set_timeout(self._show_error, 10)
                return

            dest = os.path.join(sublime.installed_packages_path(), self.filename)

            with open(dest, 'wb') as f:
                f.write(package_data)

            sublime.set_timeout(self._show_success, 10)

        except (Exception) as e:
            print(self.error_prefix + str(e))
            sublime.set_timeout(self._show_error, 10)

    def _show_success(self):
        """
        RUNS IN THE MAIN THREAD
        """

        sublime.message_dialog(
            "Package Control was successfully installed\n\n"
            "Use the Command Palette and type \"Install Package\" to get started")

    def _show_error(self):
        """
        RUNS IN THE MAIN THREAD
        """

        sublime.error_message(
            "An error occurred installing Package Control\n\n"
            "Please check the Console for details\n\n"
            "Visit https://packagecontrol.io/installation for manual instructions")

    def _download(self):
        """
        RUNS IN A THREAD

        Attempts to download over TLS first, falling back to HTTP in case a
        user's proxy configuration doesn't work with TLS by default.

        Although a secure connection is made, Python 3.3 does not check the
        connection hostname against the certificate, so a TLS connection
        really only provides privacy. To ensure that the package has not been
        modified, we check a public-key signature of the file.

        :return:
            None or a byte string of the verified package file
        """

        host_path = 'packagecontrol.io/' + self.filename.replace(' ', '%20')
        # Don't be fooled by the TLS URL, Python 3.3 does not verify hostnames
        secure_url = 'https://' + host_path
        insecure_url = 'http://' + host_path

        secure_sig_url = secure_url + '.sig'
        insecure_sig_url = insecure_url + '.sig'

        install_opener(build_opener(ProxyHandler()))

        try:
            package_data = urlopen(secure_url).read()
            sig_data = urlopen(secure_sig_url).read()
        except (URLError) as e:
            print('%sHTTPS error encountered, falling back to HTTP - %s' % (self.error_prefix, str(e)))
            try:
                package_data = urlopen(insecure_url).read()
                sig_data = urlopen(insecure_sig_url).read()
            except (URLError) as e2:
                print('%sHTTP error encountered, giving up - %s' % (self.error_prefix, str(e2)))
                return None

        return self._verify(package_data, sig_data)

    def _verify(self, package_data, sig_data):
        """
        RUNS IN A THREAD

        Verifies the package is authentic

        :param package_data:
            A byte string of the .sublime-package data

        :param sig_data:
            A byte string of the .sig data

        :return:
            None if invalid, byte string of package file otherwise
        """

        try:
            armored_sig = sig_data.decode('ascii').strip()
        except (UnicodeDecodeError):
            print(self.error_prefix + 'invalid signature ASCII encoding')
            return None

        begin = '-----BEGIN PACKAGE CONTROL SIGNATURE-----'
        end = '-----END PACKAGE CONTROL SIGNATURE-----'
        pem_error = self.error_prefix + 'invalid signature PEM armor'

        b64_sig = ''

        in_body = None
        for line in armored_sig.splitlines():
            if not in_body:
                if line != begin:
                    print(pem_error)
                    return None
                in_body = True

            else:
                if line.startswith('-----'):
                    if line != end:
                        print(pem_error)
                        return None
                    break
                b64_sig += line

        try:
            sig = base64.b64decode(b64_sig)
        except (binascii.Error):
            print(self.error_prefix + 'invalid signature base64 decoding')
            return None

        public_key = base64.b64decode(self.public_key)
        if not sublime_api.verify_pc_signature(package_data, sig, public_key):
            print(self.error_prefix + 'signature could not be verified')
            return None

        return package_data
