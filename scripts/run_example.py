import importlib.machinery
import importlib.util
import datetime
import os

BASE_DIR = os.path.dirname(__file__)
def load_module_from_path(name, path):
	loader = importlib.machinery.SourceFileLoader(name, path)
	spec = importlib.util.spec_from_loader(loader.name, loader)
	module = importlib.util.module_from_spec(spec)
	loader.exec_module(module)
	return module

generate_chat = load_module_from_path('generate_chat', os.path.join(BASE_DIR, 'generate_chat.py'))
compile_images = load_module_from_path('compile_images', os.path.join(BASE_DIR, 'compile_images.py'))

lines = open(os.path.join(BASE_DIR, '..', 'assets', 'example', 'example_script.txt'), encoding='utf8').read().splitlines()
print('Starting save_images...')
generate_chat.save_images(lines, datetime.datetime.now(), dt=1)
print('Images generated')
print('Starting gen_vid...')
compile_images.gen_vid(os.path.join(BASE_DIR, '..', 'assets', 'example', 'example_script.txt'))
print('gen_vid finished')
