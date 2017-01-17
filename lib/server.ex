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

    worker = NodeManager.random_node()
    {:ok, pid} = Task.Supervisor.start_child(GymTcpApi.TaskSupervisor,
        fn -> serve(client, worker) end)
    :ok = :gen_tcp.controlling_process(client, pid)
    loop_acceptor(socket)
  end

  defp serve(socket, worker) do
    case :gen_tcp.recv(socket, 0, 10000) do
      {:ok, data} = _ ->
        current = self()
        pid = Node.spawn(worker, __MODULE__, :pool_process, [data, current])

        # Start monitoring `pid`
        ref = Process.monitor(pid)

        # Wait until the process monitored by `ref` is down.
        receive do
          {:response, response} -> write_line(socket, {:ok, response})
          {:DOWN, ^ref, _, _, _} -> IO.puts "Handled #{inspect(pid)}."
        end

        serve(socket, worker)
      {:error, :timeout} = _ ->
        exit(:shutdown);
      {:error, :closed} = _ ->
        exit(:shutdown);
      {:error, _} = error ->
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
    :poolboy.transaction(
      GymTcpApi.pool_name(),
      fn(pid) -> GymTcpApi.Worker.process(pid, data, caller) end,
      :infinity
    );
  end
end
