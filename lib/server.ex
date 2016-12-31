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
    pid = Node.spawn(NodeManager.random_node(),
        fn() -> pool_process(socket) end )

    # Start monitoring `pid`
    ref = Process.monitor(pid)

    # Wait until the process monitored by `ref` is down.
    receive do
      {:DOWN, ^ref, _, _, _} ->
          IO.puts "Handled #{inspect(pid)}."
    end
  end

  def read_line(socket) do
    :gen_tcp.recv(socket, 0)
  end

  def write_line(_, {:ok, ""}) do
  end

  def write_line(socket, {:ok, text}) do
    :gen_tcp.send(socket, text)
  end

  def pool_process(socket) do
    case :gen_tcp.recv(socket, 0, 10000) do
      {:ok, data} = _ ->
        :poolboy.transaction(
          GymTcpApi.pool_name(),
          fn(pid) -> GymTcpApi.Worker.process(pid, socket, data) end,
          :infinity
        );
      {:error, :timeout} = timeout ->
        exit(:shutdown);
      {:error, :closed} = _ ->
        exit(:shutdown);
      {:error, _} = error ->
        exit(error);
    end

    # :poolboy.transaction(
    #   GymTcpApi.pool_name(),
    #   fn(pid) -> GymTcpApi.Worker.process(pid, socket) end,
    #   :infinity
    # )
  end
end
