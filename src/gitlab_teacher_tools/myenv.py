import configparser
import gitlab
from gitlab import Gitlab

config = configparser.ConfigParser()
config.read('gitlab-brightspace.ini')

gl: Gitlab = gitlab.Gitlab.from_config('hva', ['./gl.cfg'])