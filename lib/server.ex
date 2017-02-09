_ = """
  @file server.ex
  @author Marcus Edel

  Server module.
"""

defmodule GymTcpApi.Server do
  require Logger

  alias GymTcpApi.NodeManager

  def accept(port) do
    opt = [:binary, packet: :line, active: false, reuseaddr: true]

    case :gen_tcp.listen(port, opt) do
      {:ok, socket} = {:ok, socket} ->
        Logger.info "Accepting connections on port #{port}";
        loop_acceptor(socket);
      {:error, :eaddrinuse} = _ ->
        Logger.info "Already accepting connections on port #{port}.";
    end
  end

  defp loop_acceptor(socket) do
    {:ok, client} = :gen_tcp.accept(socket)

    {:ok, pid} = Task.Supervisor.start_child(GymTcpApi.TaskSupervisor,
        fn -> serve(client) end)
    :ok = :gen_tcp.controlling_process(client, pid)
    loop_acceptor(socket)
  end

  defp serve(socket) do
    case :gen_tcp.recv(socket, 0, 1000) do
      {:ok, data} = _ ->
        node = NodeManager.random_node(data)
        current = self()

        if Application.get_env(:gym_tcp_api, :distributed) == true do
          Node.spawn(node, __MODULE__, :pool_process, [data, current])
        else
          pool_process(data, current)
        end

        receive do
          {:response, response, worker} ->
            write_line(socket, {:ok, response});
            handle(socket, worker)
        end
      {:error, :timeout} = _ ->
        exit(:shutdown);
      {:error, :closed} = _ ->
        exit(:shutdown);
      {:error, _} = error ->
        exit(error);
    end
  end

  defp handle(socket, worker) do
    case :gen_tcp.recv(socket, 0, 1000) do
      {:ok, data} = _ ->
        current = self()
        send(worker, {:data, data, current})

        receive do
          {:response, response, worker} ->
            write_line(socket, {:ok, response})
            handle(socket, worker)
        end

      {:error, :timeout} = _ ->
        send(worker, {:close, "timeout"})
        exit(:shutdown);
      {:error, :closed} = _ ->
        send(worker, {:close, "shutdown"})
        exit(:shutdown);
      {:error, _} = error ->
        send(worker, {:close, "error"})
        exit(error);
    end
  end

  def read_line(socket) do
    :gen_tcp.recv(socket, 0)
  end

  def write_line(socket, {:ok, text}) do
    if String.strip(text) === "" do
    else
      :gen_tcp.send(socket, text)
    end
  end

  def pool_process(data, caller) do
    worker = :poolboy.checkout(:gym_pool)
    spawn(fn() -> GymTcpApi.Worker.process(worker, data, caller) end)
  end
end
