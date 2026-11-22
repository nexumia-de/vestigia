project('vestigia',
  version: '0.1.0',
  meson_version: '>= 1.0',
  license: 'AGPL-3.0-or-later',
)

base_id = 'de.nexumia.Vestigia'
# Nightly app next to the stable one (phosh-toolkit docs/flatpak-workflow.md).
nightly = get_option('profile') == 'development'
app_id = nightly ? base_id + '.Devel' : base_id

python = import('python').find_installation('python3')
pythondir = python.get_install_dir()

python.install_sources(
  'vestigia/__init__.py',
  'vestigia/__main__.py',
  'vestigia/account/__init__.py',
  'vestigia/account/errors.py',
  'vestigia/account/otp_page.py',
  'vestigia/account/setup_page.py',
  'vestigia/api/__init__.py',
  'vestigia/api/client.py',
  'vestigia/api/mobile_settings.py',
  'vestigia/api/recorded.py',
  'vestigia/api/upload_target.py',
  'vestigia/api/version.py',
  'vestigia/day/__init__.py',
  'vestigia/day/cache.py',
  'vestigia/day/day_bar.py',
  'vestigia/day/marks.py',
  'vestigia/day/model.py',
  'vestigia/day/page.py',
  'vestigia/day/period.py',
  'vestigia/day/sidebar.py',
  'vestigia/day/states.py',
  'vestigia/day/summary.py',
  'vestigia/map/__init__.py',
  'vestigia/map/fit.py',
  'vestigia/map/view.py',
  'vestigia/demo.py',
  'vestigia/main.py',
  'vestigia/preferences.py',
  'vestigia/settings.py',
  'vestigia/stats/__init__.py',
  'vestigia/stats/model.py',
  'vestigia/stats/page.py',
  'vestigia/tracker/__init__.py',
  'vestigia/tracker/backoff.py',
  'vestigia/tracker/config.py',
  'vestigia/tracker/filter.py',
  'vestigia/tracker/fix.py',
  'vestigia/tracker/gpx.py',
  'vestigia/tracker/protocols.py',
  'vestigia/tracker/scheduler.py',
  'vestigia/tracker/source.py',
  'vestigia/tracker/store.py',
  'vestigia/tracker/target.py',
  'vestigia/tracker/uploader.py',
  'vestigia/secrets.py',
  'vestigia/tracking/__init__.py',
  'vestigia/tracking/background.py',
  'vestigia/tracking/export.py',
  'vestigia/tracking/service.py',
  'vestigia/tracking/settings_page.py',
  'vestigia/tracking/status.py',
  'vestigia/tracking/sync.py',
  'vestigia/visits/__init__.py',
  'vestigia/visits/actions.py',
  'vestigia/visits/page.py',
  'vestigia/window.py',
  preserve_path: true,
)
# Loaded next to the Python files, also from the source tree.
install_data('vestigia/style.css', install_dir: pythondir / 'vestigia')

conf = configuration_data()
conf.set('PYTHON', python.full_path())
conf.set('PYTHONDIR', get_option('prefix') / pythondir)
configure_file(
  input: 'data/vestigia.in',
  output: 'vestigia',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

config = configuration_data()
config.set('APP_ID', app_id)
config.set('BUILD_LABEL', get_option('build_label'))
configure_file(
  input: 'vestigia/config.py.in',
  output: 'config.py',
  configuration: config,
  install: true,
  install_dir: pythondir / 'vestigia',
)

if nightly
  # The stable files in data/ stay the only source; the nightly app gets
  # its own id and the name "Travel Log (Nightly)".
  sed = find_program('sed')
  variant = [sed, '-e', 's/' + base_id + '/' + app_id + '/g',
             '-e', 's/^Name=Travel Log$/Name=Travel Log (Nightly)/',
             '-e', 's|<name>Travel Log</name>|<name>Travel Log (Nightly)</name>|',
             '@INPUT@']
  desktop = configure_file(input: 'data' / base_id + '.desktop',
    output: app_id + '.desktop', command: variant, capture: true)
  metainfo = configure_file(input: 'data' / base_id + '.metainfo.xml',
    output: app_id + '.metainfo.xml', command: variant, capture: true)
else
  desktop = files('data' / base_id + '.desktop')
  metainfo = files('data' / base_id + '.metainfo.xml')
endif
install_data(desktop, install_dir: get_option('datadir') / 'applications')
install_data(metainfo, install_dir: get_option('datadir') / 'metainfo')
install_data('data/icons/hicolor/scalable/apps' / base_id + '.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/scalable/apps',
  rename: app_id + '.svg')
# The start page shows <app id>-symbolic (vestigia/window.py).
install_data('data/icons/hicolor/symbolic/apps' / base_id + '-symbolic.svg',
  install_dir: get_option('datadir') / 'icons/hicolor/symbolic/apps',
  rename: app_id + '-symbolic.svg')

desktop_file_validate = find_program('desktop-file-validate', required: false)
if desktop_file_validate.found()
  test('validate-desktop', desktop_file_validate, args: [desktop])
endif
appstreamcli = find_program('appstreamcli', required: false)
if appstreamcli.found()
  test('validate-metainfo', appstreamcli,
    args: ['validate', '--no-net', metainfo])
endif
