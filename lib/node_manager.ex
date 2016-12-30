_ = """
  @file node_manager.ex
  @author Marcus Edel

  Node handler.
"""

defmodule GymTcpApi.NodeManager do
  def all_nodes do
    [Node.self | Node.list]
  end

  def random_node do
    all_nodes |> Enum.random
  end
end