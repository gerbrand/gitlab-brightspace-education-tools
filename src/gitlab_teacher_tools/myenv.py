import configparser
import gitlab

config = configparser.ConfigParser()
config.read('gitlab-brightspace.ini')

gl = gitlab.Gitlab.from_config('hva', ['./gl.cfg'])