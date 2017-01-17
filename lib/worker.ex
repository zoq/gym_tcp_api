_ = """
  @file worker.ex
  @author Marcus Edel

  Worker module.
"""

defmodule GymTcpApi.Worker do
  use GenServer

  require Logger

  alias Application, as: App

  def start_link(_args) do
    priv_path = App.app_dir(:gym_tcp_api, "priv") |> to_char_list
    GenServer.start_link(__MODULE__, priv_path)
  end

  def init(python_path) do
    :python.start_link(python_path: python_path)
  end

  def handle_call({data, caller}, _, python) do
    response = :python.call(python, :worker, :process_response, [data])

    send(caller, {:response, response})
    {:reply, [response], python}
  end

  def process(pid, data, caller) do
    :gen_server.call(pid, {data, caller});
  end
end
