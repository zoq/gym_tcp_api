_ = """
  @file worker.ex
  @author Marcus Edel

  Worker module.
"""

defmodule GymTcpApi.Worker do
  use GenServer

  require Logger

  alias GymTcpApi.Server
  alias Application, as: App

  def start_link(_args) do
    priv_path = App.app_dir(:gym_tcp_api, "priv") |> to_char_list
    GenServer.start_link(__MODULE__, priv_path)
  end

  def init(python_path) do
    :python.start_link(python_path: python_path)
  end

  def handle_call({socket, data}, _, python) do
    response = :python.call(python, :worker, :process_response, [data])

    Server.write_line(socket, {:ok, response})
    {:reply, [response], python}
  end

  def handle_message(pid, socket) do
    case :gen_tcp.recv(socket, 0, 10000) do
      {:ok, data} = _ ->
        :gen_server.call(pid, {socket, data});
        handle_message(pid, socket);
      {:error, :timeout} = timeout ->
        Logger.info "Recv timeout.";
        exit(:shutdown);
      {:error, :closed} = _ ->
        Logger.info "Recv closed.";
        exit(:shutdown);
      {:error, _} = error ->
        Logger.info "Recv error.";
        exit(error);
    end
  end

  def process(pid, socket, data) do
    :gen_server.call(pid, {socket, data});
    handle_message(pid, socket)
  end
end
