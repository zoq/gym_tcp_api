"""
  @file worker.py
  @author Marcus Edel

  Container and manager for the environments instantiated on this server.
"""

import erlport
from erlport import erlang

import json
import uuid
import numpy as np

import gym
from gym.wrappers.monitoring import Monitor

try:
  import zlib
except ImportError:
  pass

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str,bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring

"""
  Container and manager for the environments instantiated
  on this server. The Envs class is based on the gym-http-api project

  @misc{gymhttpapi2016,
    title = {OpenAI gym-http-api},
    year = {2016},
    publisher = {GitHub},
    journal = {GitHub repository},
    howpublished = {\\url{https://github.com/openai/gym-http-api}}
  }
"""
class Envs(object):
  def __init__(self):
    self.envs = {}
    self.id_len = 13

  def _lookup_env(self, instance_id):
    try:
      return self.envs[instance_id]
    except KeyError:
      return None

  def _remove_env(self, instance_id):
    try:
      del self.envs[instance_id]
    except KeyError:
      raise InvalidUsage('Instance_id {} unknown'.format(instance_id))

  def create(self, env_id):
    try:
      env = gym.make(env_id)
    except gym.error.Error:
      raise InvalidUsage(
          "Attempted to look up malformed environment ID '{}'".format(env_id))

    instance_id = str(uuid.uuid4().hex)[:self.id_len]
    self.envs[instance_id] = env
    return instance_id

  def reset(self, instance_id):
    env = self._lookup_env(instance_id)
    obs = env.reset()
    return env.observation_space.to_jsonable(obs)

  def step(self, instance_id, action, render):
    env = self._lookup_env(instance_id)
    action_from_json = env.action_space.from_jsonable(action)
    if (not isinstance(action_from_json, (list))):
      action_from_json = int(action_from_json)

    if render: env.render()
    [observation, reward, done, info] = env.step(action_from_json)

    obs_jsonable = env.observation_space.to_jsonable(observation)
    return [obs_jsonable, reward, done, info]

  def seed(self, s):
    env = self._lookup_env(instance_id)
    env.seed(int(s))

  def get_action_space_info(self, instance_id):
    env = self._lookup_env(instance_id)
    return self._get_space_properties(env.action_space)

  def get_action_space_sample(self, instance_id):
    env = self._lookup_env(instance_id)
    return env.action_space.sample()

  def get_observation_space_info(self, instance_id):
    env = self._lookup_env(instance_id)
    return self._get_space_properties(env.observation_space)

  def _get_space_properties(self, space):
    info = {}
    info['name'] = space.__class__.__name__
    if info['name'] == 'Discrete':
      info['n'] = space.n
    elif info['name'] == 'Box':
      info['shape'] = space.shape
      # It's not JSON compliant to have Infinity, -Infinity, NaN.
      # Many newer JSON parsers allow it, but many don't. Notably python json
      # module can read and write such floats. So we only here fix
      # "export version", also make it flat.
      info['low'] = [(x if x != -np.inf else -1e100) for x
          in np.array(space.low ).flatten()]
      info['high'] = [(x if x != +np.inf else +1e100) for x
          in np.array(space.high).flatten()]
    elif info['name'] == 'HighLow':
      info['num_rows'] = space.num_rows
      info['matrix'] = [((float(x) if x != -np.inf else -1e100) if x != +np.inf
          else +1e100) for x in np.array(space.matrix).flatten()]
    elif info['name'] == 'MultiDiscrete':
      info['n'] = space.num_discrete_space
      info['low'] = [(x if x != -np.inf else -1e100) for x
          in np.array(space.low ).flatten()]
      info['high'] = [(x if x != +np.inf else +1e100) for x
          in np.array(space.high).flatten()]
    return info

  def monitor_start(self, instance_id, directory, force, resume):
    env = self._lookup_env(instance_id)
    self.envs[instance_id] = Monitor(env, directory, None, force, resume)

  def monitor_close(self, instance_id):
    env = self._lookup_env(instance_id)
    env.monitor.close()

  def env_close(self, instance_id):
    env = self._lookup_env(instance_id)

    if env != None:
      env.close()
      self._remove_env(instance_id)

  def env_close_all(self):
    for key in self.envs.keys():
        self.env_close(key)

"""
  Error handling.
"""
class InvalidUsage(Exception):
  status_code = 400
  def __init__(self, message, status_code=None, payload=None):
    Exception.__init__(self)
    self.message = message
    if status_code is not None:
      self.status_code = status_code
    self.payload = payload

  def to_dict(self):
    rv = dict(self.payload or ())
    rv['message'] = self.message
    return rv

"""
  Parse parameters.
"""
def get_optional_params(json, param1, param2):
  if (param1 in json):
    if param2 in json[param1]:
      return json[param1][param2]
    else:
      return None
  else:
      return None

def get_optional_param(json, param):
  if (param in json):
    return json[param]
  else:
    return None

envs = Envs()
enviroment = None
instance_id = None
close = True
compressionLevel = 0

def process_data(data, level = 0):
  if level > 0:
    return zlib.compress(data.encode(), level) + b"\r\n\r\n"

  return data + "\r\n\r\n"

"""
  Handle the incoming reponses.
"""
def process_response(response):
  global enviroment
  global instance_id
  global close
  global envs
  global compressionLevel

  response = unicode(response, "utf-8")
  data = response.strip()

  if (len(data) == 0):
    envs.env_close_all()
    return process_data("error", compressionLevel)

  jsonMessage = json.loads(data)

  enviroment = get_optional_params(jsonMessage, "env", "name")
  if isinstance(enviroment, basestring):
    compressionLevel = 0
    if instance_id != None:
      envs.env_close(instance_id)

    instance_id = envs.create(enviroment)
    data = json.dumps({"instance" : instance_id})
    return process_data(data, compressionLevel)

  compression = get_optional_params(jsonMessage, "server", "compression")
  if isinstance(compression, basestring):
    try:
      compressionLevel = int(compression)
    except ValueError:
      compressionLevel = 0
      close = True

  actionspace = get_optional_params(jsonMessage, "env", "actionspace")
  if isinstance(actionspace, basestring):
    if actionspace == "sample":
      sample = envs.get_action_space_sample(instance_id)

      data = json.dumps({"sample" : sample})
      return process_data(data, compressionLevel)

  envAction = get_optional_params(jsonMessage, "env", "action")
  if isinstance(envAction, basestring):
    if envAction == "close":
      envs.env_close(instance_id)
      close = False
      return ""
    elif envAction == "reset":
      observation = envs.reset(instance_id)
      data = json.dumps({"observation" : observation})
      return process_data(data, compressionLevel)
    elif envAction == "actionspace":
      info = envs.get_action_space_info(instance_id)
      data = json.dumps({"info" : info})
      return process_data(data, compressionLevel)
    elif envAction == "observationspace":
      info = envs.get_observation_space_info(instance_id)
      data = json.dumps({"info" : info})
      return process_data(data, compressionLevel)

  step = get_optional_param(jsonMessage, "step")
  if step is not None:
    action = get_optional_param(jsonMessage["step"], "action")
    render = get_optional_param(jsonMessage["step"], "render")

    render = True if (render is not None and render == 1) else False

    [obs, reward, done, info] = envs.step(
            instance_id, action, render)

    data = json.dumps({"observation" : obs,
                       "reward" : reward,
                       "done" : done,
                       "info" : info})
    return process_data(data, compressionLevel)

  seed = get_optional_params(jsonMessage, "env", "seed")
  if isinstance(seed, basestring):
    envs.seed(seed)

  monitor = get_optional_param(jsonMessage, "monitor")
  if monitor is not None:
    directory = get_optional_param(jsonMessage["monitor"], "directory")
    action = get_optional_param(jsonMessage["monitor"], "action")

    force = get_optional_param(jsonMessage["monitor"], "force")
    force = True if (force is not None and force == 1) else False

    resume = get_optional_param(jsonMessage["monitor"], "resume")
    resume = True if (resume is not None and resume == 1) else False

    if action == "start":
      envs.monitor_start(instance_id, directory, force, resume)
    elif action == "close":
      envs.monitor_close(instance_id)

  return ""
