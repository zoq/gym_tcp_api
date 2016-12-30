import SocketServer
from threading import Lock
import json
import sys
import uuid
import numpy as np
import gym

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

mutex = Lock()

########## Container for environments ##########
class Envs(object):
  """
  Container and manager for the environments instantiated
  on this server.

  When a new environment is created, such as with
  envs.create('CartPole-v0'), it is stored under a short
  identifier (such as '3c657dbc'). Future API calls make
  use of this instance_id to identify which environment
  should be manipulated.
  """
  def __init__(self):
    self.envs = {}
    self.id_len = 8

  def _lookup_env(self, instance_id):
    try:
      return self.envs[instance_id]
    except KeyError:
      raise InvalidUsage('Instance_id {} unknown'.format(instance_id))

  def _remove_env(self, instance_id):
    mutex.acquire()
    try:
      del self.envs[instance_id]
    except KeyError:
      raise InvalidUsage('Instance_id {} unknown'.format(instance_id))
    finally:
      mutex.release()

  def create(self, env_id):
    mutex.acquire()
    try:
      env = gym.make(env_id)
    except gym.error.Error:
      raise InvalidUsage(
          "Attempted to look up malformed environment ID '{}'".format(env_id))
    except Exception as e:
      print("Exception" + str(e))
    finally:
      mutex.release()

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
      # module can read and write such floats. So we only here fix "export version",
      # also make it flat.
      info['low']  = [(x if x != -np.inf else -1e100) for x in
          np.array(space.low ).flatten()]
      info['high'] = [(x if x != +np.inf else +1e100) for x in
          np.array(space.high).flatten()]
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
    env.monitor.start(directory, force=force, resume=resume)

  def monitor_close(self, instance_id):
    env = self._lookup_env(instance_id)
    env.monitor.close()

  def env_close(self, instance_id):
    env = self._lookup_env(instance_id)
    env.close()
    self._remove_env(instance_id)

########## Error handling ##########
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

def getOptionalParams(json, param1, param2):
  if (param1 in json):
    if param2 in json[param1]:
      return json[param1][param2]
    else:
      return None
  else:
      return None

def getOptionalParam(json, param):
  if (param in json):
    return json[param]
  else:
    return None

envs = Envs()

class ThreadedTCPRequestHandler(SocketServer.StreamRequestHandler):

  timeout = 200
  def handle(self):
    enviroment = None
    instance_id = None
    close = True

    try:
      while(1):
        data = self.rfile.readline().strip()

        if (len(data) == 0):
          break

        jsonMessage = json.loads(data)

        if enviroment is None:
          enviroment = getOptionalParams(jsonMessage, "env", "name")
          instance_id = envs.create(enviroment)

        actionspace = getOptionalParams(jsonMessage, "env", "actionspace")
        if isinstance(actionspace, basestring):
          if actionspace == "sample":
            sample = envs.get_action_space_sample(instance_id)

            data = json.dumps({"sample" : sample})
            self.wfile.write(data + "\r\n\r\n")

        envAction = getOptionalParams(jsonMessage, "env", "action")
        if isinstance(envAction, basestring):
          if envAction == "close":
            envs.env_close(instance_id)
            close = False
            break;
          elif envAction == "reset":
            observation = envs.reset(instance_id)
            data = json.dumps({"observation" : observation})
            self.wfile.write(data + "\r\n\r\n")
          elif envAction == "actionspace":
            info = envs.get_action_space_info(instance_id)
            data = json.dumps({"info" : info})
            self.wfile.write(data + "\r\n\r\n")
          elif envAction == "observationspace":
            info = envs.get_observation_space_info(instance_id)
            data = json.dumps({"info" : info})
            self.wfile.write(data + "\r\n\r\n")

        step = getOptionalParam(jsonMessage, "step")
        if step is not None:
          action = getOptionalParam(jsonMessage["step"], "action")
          render = getOptionalParam(jsonMessage["step"], "render")

          render = True if (render is not None and render == 1) else False

          [obs, reward, done, info] = envs.step(
                  instance_id, action, render)

          data = json.dumps({"observation" : obs,
                             "reward" : reward,
                             "done" : done,
                             "info" : info})
          self.wfile.write(data + "\r\n\r\n")

        monitor = getOptionalParam(jsonMessage, "monitor")
        if monitor is not None:
          directory = getOptionalParam(jsonMessage["monitor"], "directory")
          action = getOptionalParam(jsonMessage["monitor"], "action")

          force = getOptionalParam(jsonMessage["monitor"], "force")
          force = True if (force is not None and force == 1) else False

          resume = getOptionalParam(jsonMessage["monitor"], "resume")
          resume = True if (resume is not None and resume == 1) else False

          if action == "start":
            envs.monitor_start(instance_id, directory, force, resume)
          elif action == "close":
            envs.monitor_close(instance_id)

    except Exception as e:
      print("Exception" + str(e))
      if close and instance_id is not None:
        envs.env_close(instance_id)

    if close == True:
      envs.env_close(instance_id)

# class ThreadedTCPServer(SocketServer.ThreadingTCPServer, SocketServer.TCPServer):
class ThreadedTCPServer(SocketServer.ForkingTCPServer, SocketServer.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address,
            RequestHandlerClass)

if __name__ == "__main__":
  try:
    # Port 0 means to select an arbitrary unused port.
    HOST, PORT = "localhost", 5000

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # Terminate with Ctrl-C.
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)

  except Exception as e:
    print("Exception" + str(e))
