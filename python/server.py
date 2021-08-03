import json
import uuid
import numpy as np
import socket
import os
from _thread import *
import glob

import gym
from gym.wrappers import Monitor

try:
  import zlib
except ImportError:
  pass

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


ServerSocket = socket.socket()
ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

host = '127.0.0.1'
port = 4040
ThreadCount = 0
try:
    ServerSocket.bind((host, port))
except socket.error as e:
    print(str(e))

print('Waitiing for a Connection..')
ServerSocket.listen(5)


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
    howpublished = {https://github.com/openai/gym-http-api}
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
    self.envs[instance_id] = Monitor(env, "/var/log/gym/" + str(instance_id), None, True, resume)

  def monitor_close(self, instance_id):
    env = self._lookup_env(instance_id)
    #env.monitor.close()

    if env != None:
        env.monitor.close()

  def env_close(self, instance_id):
    env = self._lookup_env(instance_id)

    if env != None:
      env.close()
      self._remove_env(instance_id)

  def env_close_all(self):
    for key in list(self.envs.keys()):
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
Json does not support float32/int64  serialization
The following class converts to json defaults.
So that json.dumps can serialize the dict to json.
"""
class NDArrayEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, np.ndarray):
      return obj.tolist()
    try:
      return json.JSONEncoder.default(self, obj)
    except:
      return obj.tolist()


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


def process_data(data, level = 0):
  if level > 0:
    return zlib.compress(data.encode(), level) + b"\r\n\r\n"

  return str.encode(data + "\r\n\r\n")


def recv_client(connection):
    data_len = 0
    buffer = ''
    while 1:
        try:
          data = connection.recv(1).decode("utf-8")
        except:
          return ""
        buffer += data
        data_len = data_len + 1
        if data_len >= 2 and buffer[data_len - 2:data_len] == '\r\n':
            break
    return buffer

def threaded_client(connection):
    #connection.send(str.encode('Welcome to the Server\n'))
    envs = Envs()
    enviroment = None
    instance_id = None
    close = True
    compressionLevel = 0
    connection.settimeout(60 * 20)

    """
      Handle the incoming reponses.
    """
    def process_response(response, connection, envs, enviroment, instance_id, close, compressionLevel):
      print("process")

      print(instance_id)

      #response = unicode(response, "utf-8")
      data = response.strip()

      if (len(data) == 0):
        envs.env_close_all()
        connection.send(str.encode(process_data("error", compressionLevel)))
        return enviroment, instance_id, close, compressionLevel

      jsonMessage = json.loads(data)
      print(jsonMessage)

      enviroment = get_optional_params(jsonMessage, "env", "name")
      if isinstance(enviroment, basestring):
        compressionLevel = 0
        if instance_id != None:
          envs.env_close(instance_id)

        instance_id = envs.create(enviroment)
        data = json.dumps({"instance" : instance_id}, cls = NDArrayEncoder)
        connection.send(process_data(data, compressionLevel))
        return enviroment, instance_id, close, compressionLevel

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

          data = json.dumps({"sample" : sample}, cls = NDArrayEncoder)
          connection.send(process_data(data, compressionLevel))
          return enviroment, instance_id, close, compressionLevel

      envAction = get_optional_params(jsonMessage, "env", "action")
      if isinstance(envAction, basestring):
        if envAction == "close":
          envs.env_close(instance_id)
          close = False
          connection.send(str.encode(""))
          return enviroment, instance_id, close, compressionLevel
        elif envAction == "reset":
          observation = envs.reset(instance_id)
          data = json.dumps({"observation" : observation}, cls = NDArrayEncoder)
          connection.send(process_data(data, compressionLevel))
          return enviroment, instance_id, close, compressionLevel
        elif envAction == "actionspace":
          info = envs.get_action_space_info(instance_id)
          data = json.dumps({"info" : info}, cls = NDArrayEncoder)
          connection.send(process_data(data, compressionLevel))
          return enviroment, instance_id, close, compressionLevel
        elif envAction == "observationspace":
          info = envs.get_observation_space_info(instance_id)
          data = json.dumps({"info" : info}, cls = NDArrayEncoder)
          connection.send(process_data(data, compressionLevel))
          return enviroment, instance_id, close, compressionLevel

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
                           "info" : info}, cls = NDArrayEncoder)
        connection.send(process_data(data, compressionLevel))
        return enviroment, instance_id, close, compressionLevel

      seed = get_optional_params(jsonMessage, "env", "seed")
      if isinstance(seed, basestring):
        envs.seed(seed)

      url = get_optional_param(jsonMessage, "url")
      if url is not None:
          files = glob.glob("/var/log/gym/" + instance_id + "/*.mp4")
          if len(files) > 0:
              print(files)
              os.system("ffmpeg -y -i " + files[0]  + " -c:v libvpx -crf 10 -b:v 1M -c:a libvorbis /var/log/gym/" + instance_id + "/output.webm")

          data = json.dumps({"url" : "https://gym.kurg.org/" + instance_id + "/output.webm"}, cls = NDArrayEncoder)
          connection.send(process_data(data, compressionLevel))
          enviroment, instance_id, close, compressionLevel

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

      connection.send(str.encode(""))
      return enviroment, instance_id, close, compressionLevel

    try:
        while True:
            buffer = recv_client(connection)
            if len(buffer) == 0:
                return
            enviroment, instance_id, close, compressionLevel = process_response(buffer, connection, envs, enviroment, instance_id, close, compressionLevel)
    except:
        #connection.close()
        return
    connection.close()

while True:
    Client, address = ServerSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(threaded_client, (Client, ))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))
ServerSocket.close()