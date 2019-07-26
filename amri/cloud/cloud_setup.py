import os
import platform

# Constants
amri_root_path = __file__.split('/')[:-2]
amri_venv_path = os.path.join('/', *amri_root_path, 'amri-venv')
requirements_path = __file__.split('/')[:-1]
requirements_path = os.path.join('/', *requirements_path, 'cloud-requirements.txt')
if 'Windows' in platform.system():
    pip_path = os.path.join(amri_venv_path, 'Scripts', 'pip')
else:
    pip_path = os.path.join(amri_venv_path, 'bin', 'pip')

print('AMRI virtualenv path = {}'.format(amri_venv_path))
print('Requirements path = {}'.format(requirements_path))
print('pip path = {}'.format(pip_path))

# Setup virtualenv
if not os.path.exists(requirements_path):
    print('{} not found'.format(requirements_path))
elif not os.path.exists(amri_venv_path):
    os.system('python3 -m venv {}'.format(amri_venv_path))
    os.system('{} install -r {}'.format(pip_path, requirements_path))
    os.system('{} list'.format(pip_path))
else:
    print('AMRI virtualenv found, skipping setup...'.format(amri_venv_path))
